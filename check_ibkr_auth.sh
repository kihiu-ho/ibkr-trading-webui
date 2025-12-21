#!/bin/bash

# IBKR Gateway Authentication Check Script
# This script verifies that the IBKR Gateway is authenticated and ready

echo "🔍 Checking IBKR Gateway Authentication Status..."
echo "================================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if gateway container is running
echo -e "${BLUE}1. Checking if IBKR Gateway container is running...${NC}"
if docker compose ps ibkr-gateway | grep -q "Up"; then
    echo -e "   ${GREEN}✓ Gateway container is running${NC}"
else
    echo -e "   ${RED}✗ Gateway container is NOT running${NC}"
    echo -e "   ${YELLOW}Fix: Run 'docker compose up -d ibkr-gateway'${NC}"
    exit 1
fi
echo ""

# Check if gateway API is responding
echo -e "${BLUE}2. Checking if Gateway API is responding...${NC}"
TICKLE_URL="https://localhost:5055/v1/api/tickle"
TICKLE_RESULT=$(curl -k -s -w "\n%{http_code}" "$TICKLE_URL")
TICKLE_HTTP_CODE=$(echo "$TICKLE_RESULT" | tail -n 1)
TICKLE_BODY=$(echo "$TICKLE_RESULT" | sed '$d')

if [ "$TICKLE_HTTP_CODE" != "000" ]; then
    echo -e "   ${GREEN}✓ Gateway API is responding${NC} (HTTP ${TICKLE_HTTP_CODE})"
    if [ -n "$TICKLE_BODY" ]; then
        echo -e "   Response: ${TICKLE_BODY}"
    fi
    if [ "$TICKLE_HTTP_CODE" = "401" ] || [ "$TICKLE_HTTP_CODE" = "403" ] || echo "$TICKLE_BODY" | grep -qi "access denied"; then
        echo ""
        echo -e "   ${YELLOW}Access denied/unauthorized means the gateway is up but not authenticated.${NC}"
        echo "   Fix: Open https://localhost:5055 in your browser, accept the TLS warning,"
        echo "        and complete the IBKR login (including 2FA). Then rerun this script."
    fi
else
    echo -e "   ${RED}✗ Gateway API is NOT responding${NC}"
    echo -e "   ${YELLOW}Fix: Wait 60 seconds for gateway to initialize${NC}"
    exit 1
fi
echo ""

# Check authentication status
echo -e "${BLUE}3. Checking authentication status...${NC}"
AUTH_URL="https://localhost:5055/v1/api/iserver/auth/status"
AUTH_RESULT=$(curl -k -s -w "\n%{http_code}" "$AUTH_URL")
AUTH_HTTP_CODE=$(echo "$AUTH_RESULT" | tail -n 1)
AUTH_RESPONSE=$(echo "$AUTH_RESULT" | sed '$d')

# Handle "Access Denied" which means not authenticated
if [ "$AUTH_HTTP_CODE" = "401" ] || [ "$AUTH_HTTP_CODE" = "403" ] || echo "$AUTH_RESPONSE" | grep -qi "access denied"; then
    echo -e "   ${RED}✗ NOT AUTHENTICATED${NC}"
    echo -e "   ${YELLOW}The gateway is running but requires authentication.${NC}"
    echo ""
    echo -e "${YELLOW}================================================================${NC}"
    echo -e "${YELLOW}⚠  Action Required: You need to authenticate${NC}"
    echo -e "${YELLOW}================================================================${NC}"
    echo ""
    echo "To authenticate:"
    echo "1. Open https://localhost:5055 in your browser"
    echo "2. Accept the security warning (self-signed certificate)"
    echo "3. Log in with your Interactive Brokers credentials"
    echo "4. Run this script again to verify"
    echo ""
    echo "📖 More details: See IBKR_AUTH_REQUIRED.md"
    exit 1
elif echo "$AUTH_RESPONSE" | grep -q "authenticated.*true"; then
    echo -e "   ${GREEN}✓ ✓ ✓ AUTHENTICATED! ✓ ✓ ✓${NC}"
    echo -e "   ${GREEN}The IBKR Gateway is fully authenticated and ready!${NC}"
    echo ""
    echo -e "   Auth details:"
    echo "$AUTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$AUTH_RESPONSE"
    echo ""
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${GREEN}✓ All checks passed! You can now generate signals.${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Open http://localhost:8000"
    echo "2. Navigate to the signals page"
    echo "3. Enter a symbol (e.g., NVDA)"
    echo "4. Click 'Generate Signal'"
    echo ""
    exit 0
elif echo "$AUTH_RESPONSE" | grep -q "authenticated.*false"; then
    echo -e "   ${RED}✗ NOT AUTHENTICATED${NC}"
    echo -e "   ${YELLOW}The gateway is running but you haven't logged in yet.${NC}"
    echo ""
    echo -e "   Auth details:"
    echo "$AUTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$AUTH_RESPONSE"
    echo ""
    echo -e "${YELLOW}================================================================${NC}"
    echo -e "${YELLOW}⚠  Action Required: You need to authenticate${NC}"
    echo -e "${YELLOW}================================================================${NC}"
    echo ""
    echo "To authenticate:"
    echo "1. Open https://localhost:5055 in your browser"
    echo "2. Accept the security warning (self-signed certificate)"
    echo "3. Log in with your Interactive Brokers credentials"
    echo "4. Run this script again to verify"
    echo ""
    echo "📖 More details: See IBKR_AUTH_REQUIRED.md"
    exit 1
else
    echo -e "   ${YELLOW}⚠ UNEXPECTED RESPONSE${NC}"
    if [ "$AUTH_HTTP_CODE" != "000" ]; then
        echo -e "   HTTP: ${AUTH_HTTP_CODE}"
    fi
    echo -e "   Response: ${AUTH_RESPONSE}"
    echo ""
    echo "The gateway might still be starting up."
    echo "Wait 30 seconds and try again, or check the logs:"
    echo "  docker logs ibkr-gateway --tail 20"
    exit 1
fi
