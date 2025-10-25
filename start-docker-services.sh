#!/bin/bash

# Start only Docker services (PostgreSQL and Redis)
# Use this if you want to run backend/celery manually

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}=================================="
echo "Starting Docker Services"
echo "==================================${NC}"
echo ""

# Check if Docker is running
if ! command -v docker &> /dev/null || ! docker info &> /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo ""
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Check docker-compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}✗ docker-compose not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ docker-compose available${NC}"
echo ""

# Start services
echo -e "${YELLOW}Starting PostgreSQL and Redis...${NC}"
cd "$PROJECT_ROOT"
$COMPOSE_CMD -f docker-compose.services.yml up -d

echo ""
echo -e "${YELLOW}Waiting for services to be ready...${NC}"

# Wait for PostgreSQL
for i in {1..30}; do
    if docker exec ibkr-postgres pg_isready -U postgres &> /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ PostgreSQL failed to start${NC}"
        docker logs ibkr-postgres
        exit 1
    fi
    sleep 1
done

# Wait for Redis
for i in {1..30}; do
    if docker exec ibkr-redis redis-cli ping &> /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Redis failed to start${NC}"
        docker logs ibkr-redis
        exit 1
    fi
    sleep 1
done

echo ""
echo -e "${GREEN}=================================="
echo "✓ Docker services started!"
echo "==================================${NC}"
echo ""
echo -e "${BLUE}Services running:${NC}"
echo "  PostgreSQL: localhost:5432"
echo "  Redis:      localhost:6379"
echo ""
echo -e "${BLUE}Connection URLs:${NC}"
echo "  DATABASE_URL: postgresql+psycopg://postgres:postgres@localhost:5432/ibkr_trading"
echo "  REDIS_URL:    redis://localhost:6379/0"
echo ""
echo -e "${BLUE}Management:${NC}"
echo "  View logs:  docker-compose -f docker-compose.services.yml logs -f"
echo "  Stop:       docker-compose -f docker-compose.services.yml down"
echo "  Restart:    docker-compose -f docker-compose.services.yml restart"
echo ""
echo -e "${GREEN}Ready to start webapp:${NC}"
echo "  ./start-webapp.sh"
echo ""

