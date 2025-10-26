#!/bin/bash
# Quick Fix and Start Script
# Applies fixes and starts the IBKR Trading WebUI

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  IBKR Trading WebUI - Fix & Start                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}✓${NC} Fixes already applied:"
echo "  - SQLAlchemy JSONB → JSON import"
echo "  - Docker image tag to :latest"
echo ""

echo -e "${YELLOW}➤${NC} Stopping existing containers..."
docker-compose down 2>/dev/null || true
echo ""

echo -e "${YELLOW}➤${NC} Removing old images (if any)..."
docker rmi ibkr-gateway 2>/dev/null || echo "  No old image to remove"
docker rmi ibkr-backend 2>/dev/null || echo "  No old backend image to remove"
echo ""

echo -e "${YELLOW}➤${NC} Building and starting all services..."
echo ""
docker-compose up --build -d

echo ""
echo -e "${GREEN}✓${NC} Services started!"
echo ""

echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 5

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Services Started Successfully! ✅                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "Access Points:"
echo "  Dashboard:  http://localhost:8000/dashboard"
echo "  Portfolio:  http://localhost:8000/portfolio"
echo "  Orders:     http://localhost:8000/orders"
echo "  API Docs:   http://localhost:8000/docs"
echo ""

echo "View logs:"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f ibkr-gateway"
echo ""

echo -e "${GREEN}Ready for trading! 🚀${NC}"

