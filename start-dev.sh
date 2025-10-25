#!/bin/bash

# IBKR Trading WebUI Development Startup Script
# Opens multiple terminal tabs for backend, worker, and logs

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=================================="
echo "IBKR Trading WebUI - Development Mode"
echo "==================================${NC}"
echo ""
echo "This will open 3 terminal tabs:"
echo "  1. FastAPI Backend"
echo "  2. Celery Worker"
echo "  3. Log Viewer"
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo -e "${GREEN}Starting on macOS...${NC}"
    
    # Create AppleScript to open new Terminal tabs
    osascript <<EOF
tell application "Terminal"
    activate
    
    -- Tab 1: Backend
    do script "cd '$PROJECT_ROOT' && source venv/bin/activate && echo '🚀 Starting FastAPI Backend...' && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
    delay 1
    
    -- Tab 2: Celery Worker
    tell application "System Events" to keystroke "t" using {command down}
    delay 0.5
    do script "cd '$PROJECT_ROOT' && source venv/bin/activate && echo '⚙️  Starting Celery Worker...' && celery -A backend.celery_app worker --loglevel=info" in front window
    delay 1
    
    -- Tab 3: Log Viewer
    tell application "System Events" to keystroke "t" using {command down}
    delay 0.5
    do script "cd '$PROJECT_ROOT' && echo '📊 Log Viewer' && echo '' && echo 'Backend logs:' && echo '  tail -f logs/backend.log' && echo '' && echo 'Celery logs:' && echo '  tail -f logs/celery.log' && echo '' && echo 'Web UI: http://localhost:8000' && echo 'API Docs: http://localhost:8000/docs' && echo '' && echo 'Press any key to view logs...' && read && tail -f logs/backend.log logs/celery.log 2>/dev/null || echo 'Logs will appear after services start'" in front window
    
end tell
EOF

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo -e "${GREEN}Starting on Linux...${NC}"
    
    # Check for terminal emulator
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --tab --title="Backend" -- bash -c "cd '$PROJECT_ROOT' && source venv/bin/activate && echo '🚀 Starting FastAPI Backend...' && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000; exec bash" \
                      --tab --title="Celery Worker" -- bash -c "cd '$PROJECT_ROOT' && source venv/bin/activate && echo '⚙️  Starting Celery Worker...' && celery -A backend.celery_app worker --loglevel=info; exec bash" \
                      --tab --title="Logs" -- bash -c "cd '$PROJECT_ROOT' && echo '📊 Log Viewer' && echo 'Web UI: http://localhost:8000' && sleep 3 && tail -f logs/*.log 2>/dev/null || echo 'Waiting for logs...'; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd '$PROJECT_ROOT' && source venv/bin/activate && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000" &
        xterm -e "cd '$PROJECT_ROOT' && source venv/bin/activate && celery -A backend.celery_app worker --loglevel=info" &
    else
        echo -e "${YELLOW}No supported terminal found. Use start-webapp.sh instead.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Unsupported OS. Use start-webapp.sh instead.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Development environment started!${NC}"
echo ""
echo -e "${BLUE}Access points:${NC}"
echo "  Web UI:    http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Workflows: http://localhost:8000/workflows"
echo ""

