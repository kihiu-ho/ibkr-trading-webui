#!/bin/bash

# Start Required Services (PostgreSQL and Redis) using Docker

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=================================="
echo "Starting Required Services"
echo "==================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Start PostgreSQL
echo ""
echo -e "${BLUE}Starting PostgreSQL...${NC}"
if docker ps -a --format '{{.Names}}' | grep -q "^ibkr-postgres$"; then
    if docker ps --format '{{.Names}}' | grep -q "^ibkr-postgres$"; then
        echo -e "${GREEN}✓ PostgreSQL already running${NC}"
    else
        docker start ibkr-postgres
        echo -e "${GREEN}✓ PostgreSQL started${NC}"
    fi
else
    docker run -d \
        --name ibkr-postgres \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=ibkr_trading \
        -p 5432:5432 \
        postgres:15 > /dev/null
    echo -e "${GREEN}✓ PostgreSQL created and started${NC}"
    echo -e "${YELLOW}ℹ Waiting for PostgreSQL to be ready...${NC}"
    sleep 5
fi

# Start Redis
echo ""
echo -e "${BLUE}Starting Redis...${NC}"
if docker ps -a --format '{{.Names}}' | grep -q "^ibkr-redis$"; then
    if docker ps --format '{{.Names}}' | grep -q "^ibkr-redis$"; then
        echo -e "${GREEN}✓ Redis already running${NC}"
    else
        docker start ibkr-redis
        echo -e "${GREEN}✓ Redis started${NC}"
    fi
else
    docker run -d \
        --name ibkr-redis \
        -p 6379:6379 \
        redis:7-alpine > /dev/null
    echo -e "${GREEN}✓ Redis created and started${NC}"
fi

echo ""
echo -e "${GREEN}=================================="
echo "✓ All services started!"
echo "==================================${NC}"
echo ""
echo -e "${BLUE}Service Status:${NC}"
echo "  PostgreSQL: localhost:5432"
echo "  Redis:      localhost:6379"
echo ""
echo -e "${BLUE}Connection Info:${NC}"
echo "  Database:   postgresql://postgres:postgres@localhost:5432/ibkr_trading"
echo "  Redis:      redis://localhost:6379/0"
echo ""
echo -e "${YELLOW}To stop services:${NC}"
echo "  docker stop ibkr-postgres ibkr-redis"
echo ""
echo -e "${YELLOW}To remove services:${NC}"
echo "  docker rm ibkr-postgres ibkr-redis"
echo ""
echo -e "${GREEN}Ready to start webapp:${NC}"
echo "  ./start-webapp.sh"
echo ""

