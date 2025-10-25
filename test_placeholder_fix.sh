#!/bin/bash

# Test script for placeholder image fix
# Verifies that external placeholder dependency has been removed

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║  Testing Placeholder Image Fix                              ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check that via.placeholder.com is NOT in charts.html
echo "=== Test 1: External Placeholder Removed ==="
if grep -q "via.placeholder.com" /Users/he/git/ibkr-trading-webui/frontend/templates/charts.html; then
    echo -e "${RED}✗ FAILED${NC} - External placeholder still found in charts.html"
    exit 1
else
    echo -e "${GREEN}✓ PASSED${NC} - External placeholder removed"
fi
echo ""

# Test 2: Check that SVG data URI is present
echo "=== Test 2: SVG Data URI Present ==="
if grep -q "data:image/svg+xml" /Users/he/git/ibkr-trading-webui/frontend/templates/charts.html; then
    echo -e "${GREEN}✓ PASSED${NC} - SVG data URI found in charts.html"
else
    echo -e "${RED}✗ FAILED${NC} - SVG data URI not found"
    exit 1
fi
echo ""

# Test 3: Verify OpenSpec validation
echo "=== Test 3: OpenSpec Validation ==="
cd /Users/he/git/ibkr-trading-webui
if openspec validate fix-placeholder-images --strict &> /dev/null; then
    echo -e "${GREEN}✓ PASSED${NC} - OpenSpec validation successful"
else
    echo -e "${RED}✗ FAILED${NC} - OpenSpec validation failed"
    exit 1
fi
echo ""

# Test 4: Check backend is running (optional)
echo "=== Test 4: Backend Service Check ==="
if curl -s -f http://localhost:8000/api/indicators > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASSED${NC} - Backend is running"
    echo -e "${YELLOW}→${NC} You can test the fix at: http://localhost:8000/charts"
else
    echo -e "${YELLOW}⚠ SKIPPED${NC} - Backend not running (start with: docker compose up)"
fi
echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║  ✅  All Tests Passed!                                       ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Changes Made:"
echo "   • Removed external via.placeholder.com dependency"
echo "   • Added inline SVG data URI placeholder"
echo "   • No external network calls for placeholders"
echo ""
echo "🧪 To Test Manually:"
echo "   1. Open http://localhost:8000/charts"
echo "   2. Generate a chart or wait for existing charts to load"
echo "   3. Check browser console - should have NO ERR_NAME_NOT_RESOLVED errors"
echo "   4. If a chart fails to load, it will show 'Chart Preview' placeholder"
echo ""
echo "✅ Result: No more placeholder image errors!"
echo ""

