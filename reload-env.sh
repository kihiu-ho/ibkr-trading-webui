#!/bin/bash
# Reload Environment Variables from .env File
# Use this script when you've updated .env and need containers to pick up changes

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Reloading Environment Variables"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo ""
    echo "Please create .env file with required variables:"
    echo "  cp env.example .env"
    echo "  nano .env  # Edit with your values"
    exit 1
fi

# Check if DATABASE_URL is set in .env
if ! grep -q "DATABASE_URL=" .env; then
    echo -e "${RED}ERROR: DATABASE_URL not found in .env!${NC}"
    echo ""
    echo "Please add DATABASE_URL to your .env file:"
    echo "  DATABASE_URL=postgresql+psycopg2://user:pass@host/db"
    exit 1
fi

# Show current DATABASE_URL (masked)
DB_URL=$(grep "DATABASE_URL=" .env | cut -d'=' -f2-)
DB_URL_MASKED=$(echo "$DB_URL" | sed -E 's|(://[^:]+:)[^@]+(@)|\1****\2|')
echo -e "${YELLOW}DATABASE_URL in .env:${NC} $DB_URL_MASKED"
echo ""

# Step 1: Stop containers
echo -e "${BLUE}[1/4] Stopping containers...${NC}"
docker-compose down
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Step 2: Recreate containers with new environment
echo -e "${BLUE}[2/4] Recreating containers with new environment...${NC}"
docker-compose up -d --force-recreate
echo -e "${GREEN}✓ Containers recreated${NC}"
echo ""

# Step 3: Wait for services to be ready
echo -e "${BLUE}[3/4] Waiting for services to start...${NC}"
sleep 5

# Check if backend is running
if docker ps | grep -q "ibkr-backend"; then
    echo -e "${GREEN}✓ Backend container is running${NC}"
else
    echo -e "${RED}✗ Backend container failed to start${NC}"
    echo ""
    echo "Check logs with: docker logs ibkr-backend"
    exit 1
fi

echo ""

# Step 4: Verify DATABASE_URL is loaded
echo -e "${BLUE}[4/4] Verifying DATABASE_URL is loaded...${NC}"

# Get DATABASE_URL from running container
CONTAINER_DB_URL=$(docker-compose exec -T backend printenv DATABASE_URL 2>/dev/null || echo "")

if [ -z "$CONTAINER_DB_URL" ]; then
    echo -e "${RED}✗ DATABASE_URL not found in container!${NC}"
    echo ""
    echo "This might be a Docker Compose issue. Try:"
    echo "  docker-compose down -v"
    echo "  docker-compose up -d"
    exit 1
fi

# Mask password in container URL for display
CONTAINER_DB_URL_MASKED=$(echo "$CONTAINER_DB_URL" | sed -E 's|(://[^:]+:)[^@]+(@)|\1****\2|')
echo -e "${GREEN}✓ DATABASE_URL loaded: ${CONTAINER_DB_URL_MASKED}${NC}"

# Check if backend logs show any errors
echo ""
echo -e "${BLUE}Checking backend logs for errors...${NC}"
sleep 2

if docker logs ibkr-backend 2>&1 | grep -i "error\|traceback" | grep -v "healthcheck" | head -5; then
    echo ""
    echo -e "${RED}⚠️  Backend has errors. Showing last 20 lines:${NC}"
    echo ""
    docker logs ibkr-backend --tail 20
    echo ""
    echo -e "${YELLOW}Tip: Check full logs with: docker logs -f ibkr-backend${NC}"
    exit 1
else
    echo -e "${GREEN}✓ No errors found${NC}"
fi

echo ""
echo -e "${GREEN}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Environment Reload Complete! ✅"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo ""
echo "🌐 Services are now running with updated environment:"
echo "  Web UI:       http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Prompt Manager: http://localhost:8000/prompts"
echo ""
echo "📋 Useful commands:"
echo "  View logs:    docker logs -f ibkr-backend"
echo "  Check env:    docker-compose exec backend printenv | grep DATABASE"
echo "  Stop all:     ./stop-all.sh"
echo ""

