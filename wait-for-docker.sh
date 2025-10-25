#!/bin/bash

# Wait for Docker Desktop to be fully ready

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Waiting for Docker Desktop to be ready...${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker is not installed${NC}"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Wait for Docker daemon to respond (up to 60 seconds)
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker info &> /dev/null 2>&1; then
        echo -e "${GREEN}✓ Docker is ready!${NC}"
        echo ""
        docker --version
        echo ""
        echo -e "${GREEN}You can now run:${NC} ./start-webapp.sh"
        exit 0
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    
    if [ $ATTEMPT -eq 1 ]; then
        echo -e "${YELLOW}Docker Desktop is starting...${NC}"
        echo "This usually takes 10-30 seconds"
        echo ""
    fi
    
    # Show progress indicator
    printf "."
    sleep 2
done

echo ""
echo ""
echo -e "${YELLOW}Docker is taking longer than expected to start${NC}"
echo ""
echo "Please check:"
echo "  1. Docker Desktop is open (check Applications folder)"
echo "  2. Whale icon appears in your menu bar"
echo "  3. Click the whale icon and verify it says 'Docker Desktop is running'"
echo ""
echo "Then run this script again or: ./start-webapp.sh"
exit 1

