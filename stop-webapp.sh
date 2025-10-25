#!/bin/bash

# IBKR Trading WebUI Stop Script
# Gracefully stops all running services

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping IBKR Trading WebUI services...${NC}"
echo ""

# Function to kill process by name
kill_process() {
    local process_name=$1
    local pids=$(pgrep -f "$process_name" 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}Stopping $process_name...${NC}"
        echo "$pids" | while read pid; do
            kill $pid 2>/dev/null || true
            echo "  Killed PID: $pid"
        done
        echo -e "${GREEN}✓ $process_name stopped${NC}"
    else
        echo -e "${YELLOW}ℹ $process_name not running${NC}"
    fi
}

# Stop Celery worker
kill_process "celery.*backend.celery_app"

# Stop Uvicorn (FastAPI backend)
kill_process "uvicorn.*backend.main:app"

# Wait a moment for graceful shutdown
sleep 1

# Force kill if still running
if pgrep -f "uvicorn.*backend.main:app" > /dev/null; then
    echo -e "${RED}Force killing backend...${NC}"
    pkill -9 -f "uvicorn.*backend.main:app"
fi

if pgrep -f "celery.*backend.celery_app" > /dev/null; then
    echo -e "${RED}Force killing Celery...${NC}"
    pkill -9 -f "celery.*backend.celery_app"
fi

echo ""
echo -e "${GREEN}✓ All services stopped${NC}"
echo ""

# Show any remaining webapp processes (exclude Docker)
if pgrep -f "uvicorn.*backend.main|celery.*backend.celery_app" > /dev/null; then
    echo -e "${YELLOW}Warning: Some webapp processes still running:${NC}"
    ps aux | grep -E "uvicorn.*backend.main|celery.*backend.celery_app" | grep -v grep
    echo ""
    echo "Run 'pkill -9 -f \"uvicorn.*backend.main\"' to force kill"
fi

# Ask if user wants to stop Docker services too
echo ""
echo -e "${BLUE}Docker services (PostgreSQL & Redis) are still running${NC}"
echo -e "${YELLOW}To stop them:${NC} docker-compose -f docker-compose.services.yml down"
echo -e "${YELLOW}To stop and remove volumes:${NC} docker-compose -f docker-compose.services.yml down -v"
echo ""

