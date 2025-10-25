#!/bin/bash

# Stop all services including Docker containers

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=============================================="
echo "Stopping IBKR Trading WebUI"
echo "==============================================${NC}"
echo ""

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure Docker daemon is running before attempting shutdown
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker CLI not found. Nothing to stop.${NC}"
    exit 0
fi

if ! docker info &> /dev/null 2>&1; then
    echo -e "${YELLOW}Docker daemon not running. Containers already stopped.${NC}"
    exit 0
fi

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${YELLOW}docker-compose not found${NC}"
    exit 0
fi

# Stop Docker services
cd "$PROJECT_ROOT"

echo -e "${YELLOW}Stopping all Docker containers...${NC}"
echo ""

$COMPOSE_CMD down

echo ""
echo -e "${GREEN}✓ All containers stopped${NC}"

# Optional: Remove volumes
read -p "Remove all data volumes? This will delete all data! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${RED}Removing volumes...${NC}"
    $COMPOSE_CMD down -v
    echo -e "${GREEN}✓ Volumes removed${NC}"
fi

echo ""
echo -e "${GREEN}=============================================="
echo "✓ All services stopped!"
echo "==============================================${NC}"
echo ""
echo -e "${BLUE}To start again:${NC} ./start-webapp.sh"
echo ""

