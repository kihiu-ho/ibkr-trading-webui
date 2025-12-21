#!/bin/bash
# Start IBKR Client Portal Gateway
set -euo pipefail

PORT="${GATEWAY_LISTEN_PORT:-5055}"
echo "Starting IBKR Client Portal Gateway (listen port ${PORT}, external port 5055)"

cd gateway

# Keep conf.yaml in sync if a custom port is supplied
if grep -q "^listenPort:" root/conf.yaml; then
    if ! grep -q "^listenPort: ${PORT}$" root/conf.yaml; then
        sed -i "s/^listenPort:.*/listenPort: ${PORT}/" root/conf.yaml
    fi
else
    echo "listenPort: ${PORT}" >> root/conf.yaml
fi

exec sh bin/run.sh root/conf.yaml
