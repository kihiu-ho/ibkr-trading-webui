#!/bin/bash
# Test script for Airflow task instance logs endpoint

set +e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

echo "=========================================="
echo "Airflow Task Instance Logs Test"
echo "=========================================="
echo ""

# Test 1: Check if endpoint exists
echo -e "${BLUE}Test 1: Checking if logs endpoint is accessible...${NC}"
TEST_URL="${BACKEND_URL}/api/airflow/dags/ibkr_stock_data_workflow/dagRuns/manual__2025-11-09T04:20:51.002466+00:00/taskInstances/extract_stock_data/logs/1"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$TEST_URL")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

if [ "$HTTP_STATUS" = "404" ]; then
    echo -e "${RED}✗ Endpoint returned 404 - route may not be registered${NC}"
    echo -e "${YELLOW}  The server may need to be restarted to pick up the new route${NC}"
    echo -e "${YELLOW}  Response: ${BODY}${NC}"
elif [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Endpoint is accessible (HTTP 200)${NC}"
    echo "$BODY" | python3 -m json.tool 2>/dev/null | head -20 || echo "$BODY" | head -20
else
    echo -e "${YELLOW}⚠ Endpoint returned HTTP ${HTTP_STATUS}${NC}"
    echo "$BODY" | head -20
fi
echo ""

# Test 2: Check Airflow health
echo -e "${BLUE}Test 2: Checking Airflow connection...${NC}"
HEALTH_RESPONSE=$(curl -s "${BACKEND_URL}/api/airflow/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Airflow is accessible${NC}"
else
    echo -e "${YELLOW}⚠ Airflow health check: ${HEALTH_RESPONSE}${NC}"
fi
echo ""

# Test 3: Test with URL-encoded dag_run_id
echo -e "${BLUE}Test 3: Testing with URL-encoded dag_run_id...${NC}"
ENCODED_DAG_RUN_ID="manual__2025-11-09T04%3A20%3A51.002466%2B00%3A00"
TEST_URL2="${BACKEND_URL}/api/airflow/dags/ibkr_stock_data_workflow/dagRuns/${ENCODED_DAG_RUN_ID}/taskInstances/extract_stock_data/logs/1"
RESPONSE2=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$TEST_URL2")
HTTP_STATUS2=$(echo "$RESPONSE2" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY2=$(echo "$RESPONSE2" | sed '/HTTP_STATUS:/d')

if [ "$HTTP_STATUS2" = "200" ]; then
    echo -e "${GREEN}✓ URL-encoded endpoint works${NC}"
    echo "$BODY2" | python3 -m json.tool 2>/dev/null | head -20 || echo "$BODY2" | head -20
else
    echo -e "${YELLOW}⚠ URL-encoded endpoint returned HTTP ${HTTP_STATUS2}${NC}"
    echo "$BODY2" | head -20
fi
echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo -e "${BLUE}If endpoints return 404:${NC}"
echo "  1. Restart the backend server to load the new route"
echo "  2. Check backend logs for route registration"
echo "  3. Verify the route is included in main.py"
echo ""
echo -e "${BLUE}If endpoints return 200 but logs are empty:${NC}"
echo "  1. Check if the task instance actually has logs in Airflow"
echo "  2. Verify the task ran successfully"
echo "  3. Check Airflow logs directory"
echo ""

