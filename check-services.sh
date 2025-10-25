#!/bin/bash

# Quick diagnostics script to check all services

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== IBKR Trading WebUI - Service Diagnostics ===${NC}"
echo ""

# Python version
echo -e "${BLUE}Python:${NC} $(python3 --version 2>&1)"

# Virtual environment
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
    if [ -f "venv/bin/activate" ]; then
        echo -e "${GREEN}✓ Virtual environment is valid${NC}"
    else
        echo -e "${RED}✗ Virtual environment is corrupted${NC}"
    fi
else
    echo -e "${RED}✗ Virtual environment missing${NC}"
    echo -e "  Fix: python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt"
fi

echo ""
echo -e "${BLUE}=== Required Services ===${NC}"

# PostgreSQL
if lsof -i :5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL running on port 5432${NC}"
else
    echo -e "${RED}✗ PostgreSQL not running${NC}"
    echo -e "  Fix: ./start-services.sh"
fi

# Redis
if lsof -i :6379 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis running on port 6379${NC}"
else
    echo -e "${RED}✗ Redis not running${NC}"
    echo -e "  Fix: ./start-services.sh"
fi

echo ""
echo -e "${BLUE}=== WebApp Services ===${NC}"

# Backend
if lsof -i :8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend running on port 8000${NC}"
else
    echo -e "${RED}✗ Backend not running${NC}"
    echo -e "  Fix: ./start-webapp.sh"
fi

# Celery worker
if pgrep -f "celery.*backend.celery_app" > /dev/null; then
    echo -e "${GREEN}✓ Celery worker running${NC}"
else
    echo -e "${RED}✗ Celery worker not running${NC}"
    echo -e "  Fix: ./start-webapp.sh"
fi

echo ""
echo -e "${BLUE}=== Configuration ===${NC}"

# .env file
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
else
    echo -e "${RED}✗ .env file missing${NC}"
    echo -e "  Fix: cp .env.example .env"
fi

# Database init
if [ -f "database/init.sql" ]; then
    echo -e "${GREEN}✓ Database schema file exists${NC}"
else
    echo -e "${RED}✗ Database schema file missing${NC}"
fi

echo ""
echo -e "${BLUE}=== Testing Connections ===${NC}"

# Test Redis
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis: PONG${NC}"
    else
        echo -e "${RED}✗ Redis: Not responding${NC}"
    fi
else
    echo -e "${RED}✗ redis-cli not installed${NC}"
fi

# Test PostgreSQL
if command -v psql &> /dev/null; then
    if psql -h localhost -U postgres -d ibkr_trading -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL: Connected${NC}"
    else
        echo -e "${RED}✗ PostgreSQL: Cannot connect${NC}"
        echo -e "  Try: psql -h localhost -U postgres -c 'CREATE DATABASE ibkr_trading'"
    fi
else
    echo -e "${RED}✗ psql not installed${NC}"
fi

# Test Backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend: Healthy${NC}"
else
    echo -e "${RED}✗ Backend: Not responding${NC}"
    echo -e "  Check: tail -f logs/backend.log"
fi

echo ""
echo -e "${BLUE}=== Docker Status ===${NC}"

if command -v docker &> /dev/null; then
    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Docker is running${NC}"
        
        # Check Docker containers
        if docker ps --format '{{.Names}}' | grep -q "ibkr-postgres"; then
            echo -e "${GREEN}✓ ibkr-postgres container running${NC}"
        else
            echo -e "${RED}✗ ibkr-postgres container not running${NC}"
        fi
        
        if docker ps --format '{{.Names}}' | grep -q "ibkr-redis"; then
            echo -e "${GREEN}✓ ibkr-redis container running${NC}"
        else
            echo -e "${RED}✗ ibkr-redis container not running${NC}"
        fi
    else
        echo -e "${RED}✗ Docker is not running${NC}"
        echo -e "  Fix: Start Docker Desktop"
    fi
else
    echo -e "${RED}✗ Docker not installed${NC}"
    echo -e "  Alternative: Use Homebrew (see SETUP_DEPENDENCIES.md)"
fi

echo ""
echo -e "${BLUE}=== Summary ===${NC}"

# Count issues
ISSUES=0
[ ! -d "venv" ] && ((ISSUES++))
! lsof -i :5432 > /dev/null 2>&1 && ((ISSUES++))
! lsof -i :6379 > /dev/null 2>&1 && ((ISSUES++))
[ ! -f ".env" ] && ((ISSUES++))

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    if ! lsof -i :8000 > /dev/null 2>&1; then
        echo -e "${BLUE}Ready to start:${NC} ./start-webapp.sh"
    else
        echo -e "${GREEN}✓ WebApp is running!${NC}"
        echo -e "${BLUE}Access at:${NC} http://localhost:8000"
    fi
else
    echo -e "${RED}✗ Found $ISSUES issue(s)${NC}"
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  1. Read TROUBLESHOOTING.md"
    echo -e "  2. Run ./start-services.sh (if Docker available)"
    echo -e "  3. Run ./start-webapp.sh"
fi

echo ""

