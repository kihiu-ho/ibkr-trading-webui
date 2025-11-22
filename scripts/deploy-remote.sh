#!/usr/bin/env bash
# Deploy the IBKR Trading WebUI to a remote server using credentials in .env
# Prefers SSH key at ./ .ssh_key (or SSH_KEY_FILE). Falls back to password (server_password) if no key.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ENV_FILE="$ROOT_DIR/.env"
SSH_KEY_FILE="${SSH_KEY_FILE:-$ROOT_DIR/.ssh_key}"
SSH_PORT="${SSH_PORT:-22}"
REMOTE_DIR_DEFAULT="/home/${server_user:-root}/ibkr-trading-webui"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing .env at repo root; copy env.example to .env and populate values."
  exit 1
fi

# helper to read value after first '='
get_env() {
  local key="$1"
  local val
  val=$(grep -E "^${key}=" "$ENV_FILE" | head -n1 | cut -d= -f2- || true)
  printf '%s' "$val"
}

server_ip="$(get_env server_ip)"
server_user="$(get_env server_user)"
server_password="$(get_env server_password)"
DATABASE_URL="$(get_env DATABASE_URL)"

REMOTE_DIR="${REMOTE_DIR:-${REMOTE_DIR_DEFAULT}}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://localhost:8000/health}"

if [ -z "$server_ip" ] || [ -z "$server_user" ] || [ -z "$DATABASE_URL" ]; then
  echo "Missing required values in .env (server_ip, server_user, DATABASE_URL)."
  exit 1
fi

USE_KEY=false
if [ -f "$SSH_KEY_FILE" ]; then
  if ssh-keygen -y -f "$SSH_KEY_FILE" >/dev/null 2>&1; then
    USE_KEY=true
  else
    echo "SSH key at $SSH_KEY_FILE is invalid; falling back to password if available..."
  fi
fi

if ! $USE_KEY && [ -z "$server_password" ]; then
  echo "No usable SSH key and server_password missing; cannot authenticate."
  exit 1
fi

if $USE_KEY; then
  required_cmds=(rsync ssh)
else
  required_cmds=(sshpass rsync ssh)
fi

for cmd in "${required_cmds[@]}"; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Required command not found: $cmd"; exit 1; }
done

ssh_opts=(-p "$SSH_PORT" -o StrictHostKeyChecking=no)
if $USE_KEY; then
  ssh_opts+=(-i "$SSH_KEY_FILE" -o PreferredAuthentications=publickey -o PasswordAuthentication=no)
else
  ssh_opts+=(-o PreferredAuthentications=password -o PubkeyAuthentication=no)
fi

echo "Checking rsync availability on server..."
if $USE_KEY; then
  ssh "${ssh_opts[@]}" "${server_user}@${server_ip}" "command -v rsync >/dev/null 2>&1" || {
    echo "rsync is not available on the server; install it and rerun."
    exit 1
  }
else
  sshpass -p "$server_password" ssh "${ssh_opts[@]}" "${server_user}@${server_ip}" \
    "command -v rsync >/dev/null 2>&1" || {
    echo "rsync is not available on the server; install it and rerun."
    exit 1
  }
fi

echo "Preparing remote directory: $REMOTE_DIR"
if $USE_KEY; then
  ssh "${ssh_opts[@]}" "${server_user}@${server_ip}" "mkdir -p \"$REMOTE_DIR\""
else
  sshpass -p "$server_password" ssh "${ssh_opts[@]}" "${server_user}@${server_ip}" \
    "mkdir -p \"$REMOTE_DIR\""
fi

# Create sanitized env (omit local-only server creds)
temp_env="$(mktemp)"
trap 'rm -f "$temp_env"' EXIT
grep -Ev '^(server_ip|server_user|server_password)=' "$ENV_FILE" > "$temp_env"

echo "Syncing repository to server (excluding build artifacts)..."
if $USE_KEY; then
  rsync -az --delete --progress \
    -e "ssh -p $SSH_PORT -i $SSH_KEY_FILE -o StrictHostKeyChecking=no -o PreferredAuthentications=publickey -o PasswordAuthentication=no" \
    --exclude ".git/" \
    --exclude "node_modules/" \
    --exclude "logs/" \
    --exclude "reference/airflow/logs/" \
    --exclude "airflow/logs/" \
    --exclude "__pycache__/" \
    --exclude ".pytest_cache/" \
    --exclude "venv/" \
    --exclude ".env" \
    --exclude "tests/playwright-report/" \
    "$ROOT_DIR/" "${server_user}@${server_ip}:$REMOTE_DIR/"
else
  sshpass -p "$server_password" rsync -az --delete --progress \
    -e "ssh -p $SSH_PORT -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no" \
    --exclude ".git/" \
    --exclude "node_modules/" \
    --exclude "logs/" \
    --exclude "reference/airflow/logs/" \
    --exclude "airflow/logs/" \
    --exclude "__pycache__/" \
    --exclude ".pytest_cache/" \
    --exclude "venv/" \
    --exclude ".env" \
    --exclude "tests/playwright-report/" \
    "$ROOT_DIR/" "${server_user}@${server_ip}:$REMOTE_DIR/"
fi

echo "Pushing sanitized .env to server..."
if $USE_KEY; then
  scp -P "$SSH_PORT" -i "$SSH_KEY_FILE" -o StrictHostKeyChecking=no -o PreferredAuthentications=publickey -o PasswordAuthentication=no \
    "$temp_env" "${server_user}@${server_ip}:$REMOTE_DIR/.env"
else
  sshpass -p "$server_password" scp -P "$SSH_PORT" -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no \
    "$temp_env" "${server_user}@${server_ip}:$REMOTE_DIR/.env"
fi

read -r -d '' REMOTE_SCRIPT <<'EOF'
set -euo pipefail

if command -v docker-compose >/dev/null 2>&1; then
  compose_cmd="docker-compose"
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  compose_cmd="docker compose"
else
  echo "Docker Compose is not installed on the server. Install Docker + Compose and retry." >&2
  exit 1
fi

cd "$REMOTE_DIR"
eval "$compose_cmd pull"
eval "$compose_cmd up -d --build"
eval "$compose_cmd ps"

if command -v curl >/dev/null 2>&1; then
  if curl -fsSL "$HEALTHCHECK_URL" >/dev/null 2>&1; then
    echo "Healthcheck OK: $HEALTHCHECK_URL"
  else
    echo "Healthcheck failed or endpoint unavailable (non-blocking)"
  fi
else
  echo "curl not available on server; skipping healthcheck."
fi
EOF

echo "Starting remote deployment via Docker Compose..."
if $USE_KEY; then
  ssh "${ssh_opts[@]}" \
    "${server_user}@${server_ip}" \
    "REMOTE_DIR='$REMOTE_DIR' HEALTHCHECK_URL='$HEALTHCHECK_URL' bash -s" <<<"$REMOTE_SCRIPT"
else
  sshpass -p "$server_password" ssh "${ssh_opts[@]}" \
    "${server_user}@${server_ip}" \
    "REMOTE_DIR='$REMOTE_DIR' HEALTHCHECK_URL='$HEALTHCHECK_URL' bash -s" <<<"$REMOTE_SCRIPT"
fi

echo "Deployment finished. Review docker compose logs on the server if needed:"
echo "  ssh -p $SSH_PORT ${server_user}@${server_ip} \"cd $REMOTE_DIR && docker compose logs --tail=50\""
