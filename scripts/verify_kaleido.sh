#!/usr/bin/env bash
# Verify that Kaleido is available either locally, in a running service, or inside an image.
set -euo pipefail

SERVICE=""
IMAGE=""
COMPOSE_CMD=""

usage() {
    cat <<USAGE
Usage: $0 [--service SERVICE_NAME] [--image IMAGE_NAME]

Without flags, the script checks the current Python environment.
- --service: runs 'docker compose exec -T SERVICE python -c "import kaleido"'
- --image:   runs 'docker run --rm IMAGE python -c "import kaleido"'
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --service)
            SERVICE=${2:-}
            shift 2
            ;;
        --image)
            IMAGE=${2:-}
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

python_check() {
    python3 - <<'PY'
import plotly.io as pio
import kaleido
scope = getattr(pio, 'kaleido', None) or getattr(pio.defaults, 'kaleido_scope', None)
if scope is None:
    raise SystemExit('Plotly is installed but kaleido scope is missing.')
print('Kaleido ready (version %s) with renderer %s' % (kaleido.__version__, scope.__class__.__name__))
PY
}

if [[ -n "$IMAGE" ]]; then
    docker run --rm "$IMAGE" python - <<'PY'
import plotly.io as pio
import kaleido
scope = getattr(pio, 'kaleido', None) or getattr(pio.defaults, 'kaleido_scope', None)
if scope is None:
    raise SystemExit('Plotly is installed but kaleido scope is missing.')
print('Kaleido ready (version %s) inside image.' % kaleido.__version__)
PY
    exit 0
fi

if [[ -n "$SERVICE" ]]; then
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        echo "docker compose is required to target services" >&2
        exit 1
    fi
    $COMPOSE_CMD exec -T "$SERVICE" python - <<'PY'
import plotly.io as pio
import kaleido
scope = getattr(pio, 'kaleido', None) or getattr(pio.defaults, 'kaleido_scope', None)
if scope is None:
    raise SystemExit('Plotly is installed but kaleido scope is missing.')
print('Kaleido ready (version %s) inside service.' % kaleido.__version__)
PY
    exit 0
fi

python_check
