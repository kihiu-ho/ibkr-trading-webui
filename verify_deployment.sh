#!/bin/bash
# Verification Script for Configurable Prompt System Deployment

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "========================================"
echo " Deployment Verification"
echo "========================================"
echo -e "${NC}"

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    set -a
    source .env
    set +a
    echo -e "${GREEN}✓ Environment variables loaded${NC}"
    echo ""
else
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo ""
fi

PASSED=0
FAILED=0

# Test 1: Database tables exist
echo -n "Checking prompt_templates table... "
if psql "$DATABASE_URL" -c "\d prompt_templates" &> /dev/null; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

echo -n "Checking prompt_performance table... "
if psql "$DATABASE_URL" -c "\d prompt_performance" &> /dev/null; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Test 2: Seed data exists
echo -n "Checking seed data... "
PROMPT_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM prompt_templates;" | xargs)
if [ "$PROMPT_COUNT" -ge 3 ]; then
    echo -e "${GREEN}✓ PASS (Found $PROMPT_COUNT prompts)${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL (Found only $PROMPT_COUNT prompts, expected >= 3)${NC}"
    ((FAILED++))
fi

# Test 3: API endpoints accessible
echo -n "Checking API /api/v1/prompts/... "
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/prompts/)
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ PASS (HTTP $HTTP_CODE)${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL (HTTP $HTTP_CODE)${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⊘ SKIP (curl not installed)${NC}"
fi

# Test 4: Frontend accessible
echo -n "Checking frontend /prompts... "
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/prompts)
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ PASS (HTTP $HTTP_CODE)${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL (HTTP $HTTP_CODE)${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⊘ SKIP (curl not installed)${NC}"
fi

# Test 5: Python dependencies
echo -n "Checking jinja2 package... "
if python -c "import jinja2" 2>/dev/null; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Test 6: File integrity
echo -n "Checking prompt_renderer.py... "
if [ -f "backend/services/prompt_renderer.py" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

echo -n "Checking prompt-manager.js... "
if [ -f "frontend/static/js/prompt-manager.js" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

echo -n "Checking prompts.html... "
if [ -f "frontend/templates/prompts.html" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Summary
echo ""
echo "========================================"
echo " Verification Summary"
echo "========================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All checks passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some checks failed. Please review errors above.${NC}"
    exit 1
fi

