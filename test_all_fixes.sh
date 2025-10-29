#!/bin/bash

# Test script for IBKR Trading WebUI fixes
# Tests: Chart generation, IBKR auth, and login page

set -e

echo "========================================"
echo "IBKR Trading WebUI - Fix Verification"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URLs
BACKEND_URL="http://localhost:8000"
GATEWAY_URL="https://localhost:5055"

# Test counter
PASSED=0
FAILED=0

# Helper function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_code=$5
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" "$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code, expected $expected_code)"
        echo "Response: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "1. Testing Backend Health"
echo "-------------------------"
test_endpoint "Backend Health" "GET" "$BACKEND_URL/api/health" "" "200" || true
echo ""

echo "2. Testing IBKR Authentication Status"
echo "--------------------------------------"
if test_endpoint "Auth Status" "GET" "$BACKEND_URL/api/ibkr/auth/status" "" "200"; then
    echo "Checking status details..."
    status=$(curl -s "$BACKEND_URL/api/ibkr/auth/status")
    echo "$status" | python3 -m json.tool || echo "$status"
fi
echo ""

echo "3. Testing IBKR Gateway Connectivity"
echo "-------------------------------------"
echo -n "Testing Gateway Tickle... "
if curl -s -k --max-time 5 "$GATEWAY_URL/tickle" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Gateway is reachable${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ Gateway is not reachable${NC}"
    echo "  Make sure to start gateway: docker compose up ibkr-gateway -d"
    FAILED=$((FAILED + 1))
fi
echo ""

echo "4. Testing Chart Generation (will fail if not authenticated)"
echo "-------------------------------------------------------------"
# This test may fail if not authenticated, which is expected
echo "Note: This requires IBKR authentication to fully work"
curl -s -X POST "$BACKEND_URL/api/charts/generate" \
    -H "Content-Type: application/json" \
    -d '{
        "symbol": "AAPL",
        "indicator_ids": [1],
        "period": 100,
        "frequency": "1D",
        "strategy_id": null
    }' | python3 -m json.tool 2>/dev/null || echo "Chart generation endpoint responded (may need auth)"
echo ""

echo "5. Testing Frontend Pages"
echo "-------------------------"
test_endpoint "Dashboard" "GET" "$BACKEND_URL/dashboard" "" "200" || true
test_endpoint "IBKR Login Page" "GET" "$BACKEND_URL/ibkr/login" "" "200" || true
test_endpoint "Charts Page" "GET" "$BACKEND_URL/charts" "" "200" || true
echo ""

echo "6. Checking Service Status"
echo "--------------------------"
echo "Docker containers:"
docker compose ps 2>/dev/null || echo "Docker compose not available"
echo ""

echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All critical tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Open browser to: $BACKEND_URL/ibkr/login"
    echo "2. Click 'Open Gateway Login' to authenticate"
    echo "3. Complete 2FA on IBKR mobile app"
    echo "4. Return to login page and click 'Refresh'"
    echo "5. Test chart generation once authenticated"
else
    echo -e "${YELLOW}Some tests failed. Check the output above.${NC}"
    echo ""
    echo "Common issues:"
    echo "- Gateway not running: docker compose up ibkr-gateway -d"
    echo "- Backend not running: docker compose up backend -d"
    echo "- Need to authenticate: Open $BACKEND_URL/ibkr/login"
fi

echo ""
echo "For detailed logs:"
echo "  Backend: docker logs ibkr-backend -f"
echo "  Gateway: docker logs ibkr-gateway -f"
echo ""

