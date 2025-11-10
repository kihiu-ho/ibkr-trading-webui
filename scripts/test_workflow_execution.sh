#!/bin/bash
# Test script to trigger and monitor the IBKR multi-symbol workflow

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
AIRFLOW_URL="${AIRFLOW_URL:-http://localhost:8080}"
DAG_ID="ibkr_multi_symbol_workflow"

echo "=========================================="
echo "IBKR Workflow Execution Test"
echo "=========================================="
echo ""

# Check if Airflow is accessible
echo -e "${BLUE}Checking Airflow connection...${NC}"
if ! curl -s -f "${AIRFLOW_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ Airflow is not accessible at ${AIRFLOW_URL}${NC}"
    echo -e "${YELLOW}Please ensure Airflow is running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Airflow is accessible${NC}"
echo ""

# Check if DAG exists
echo -e "${BLUE}Checking if DAG exists...${NC}"
DAG_INFO=$(curl -s "${AIRFLOW_URL}/api/v1/dags/${DAG_ID}" 2>/dev/null || echo "")
if echo "$DAG_INFO" | grep -q "${DAG_ID}"; then
    echo -e "${GREEN}✓ DAG '${DAG_ID}' exists${NC}"
else
    echo -e "${RED}✗ DAG '${DAG_ID}' not found${NC}"
    echo -e "${YELLOW}Please ensure the DAG is loaded in Airflow${NC}"
    exit 1
fi
echo ""

# Trigger the DAG
echo -e "${BLUE}Triggering DAG execution...${NC}"
TRIGGER_RESPONSE=$(curl -s -X POST \
    "${AIRFLOW_URL}/api/v1/dags/${DAG_ID}/dagRuns" \
    -H "Content-Type: application/json" \
    -H "Authorization: Basic YWlyZmxvdzphaXJmbG93" \
    -d '{"conf": {}}' 2>/dev/null || echo "")

if echo "$TRIGGER_RESPONSE" | grep -q "dag_run_id\|state"; then
    DAG_RUN_ID=$(echo "$TRIGGER_RESPONSE" | grep -o '"dag_run_id":"[^"]*"' | cut -d'"' -f4 || echo "")
    echo -e "${GREEN}✓ DAG triggered successfully${NC}"
    if [ -n "$DAG_RUN_ID" ]; then
        echo -e "${GREEN}  DAG Run ID: ${DAG_RUN_ID}${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Could not trigger DAG via API (may need authentication)${NC}"
    echo -e "${YELLOW}  Response: ${TRIGGER_RESPONSE:0:200}${NC}"
    echo ""
    echo -e "${BLUE}Alternative: Use Airflow UI to trigger the DAG manually${NC}"
    echo -e "${BLUE}  URL: ${AIRFLOW_URL}/dags/${DAG_ID}/graph${NC}"
    exit 0
fi
echo ""

# Monitor execution
echo -e "${BLUE}Monitoring DAG execution...${NC}"
echo -e "${YELLOW}(This may take several minutes)${NC}"
echo ""

MAX_WAIT=300  # 5 minutes
WAIT_INTERVAL=10
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
    
    if [ -n "$DAG_RUN_ID" ]; then
        DAG_RUN_STATUS=$(curl -s "${AIRFLOW_URL}/api/v1/dags/${DAG_ID}/dagRuns/${DAG_RUN_ID}" \
            -H "Authorization: Basic YWlyZmxvdzphaXJmbG93" 2>/dev/null || echo "")
        STATE=$(echo "$DAG_RUN_STATUS" | grep -o '"state":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        
        echo -e "${BLUE}[${ELAPSED}s] DAG Run State: ${STATE}${NC}"
        
        if [ "$STATE" = "success" ]; then
            echo -e "${GREEN}✓ DAG execution completed successfully!${NC}"
            break
        elif [ "$STATE" = "failed" ]; then
            echo -e "${RED}✗ DAG execution failed${NC}"
            exit 1
        fi
    else
        echo -e "${BLUE}[${ELAPSED}s] Waiting for DAG to complete...${NC}"
    fi
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${YELLOW}⚠ Timeout waiting for DAG to complete${NC}"
    echo -e "${YELLOW}  Check Airflow UI for status: ${AIRFLOW_URL}/dags/${DAG_ID}${NC}"
fi
echo ""

# Check for artifacts
echo -e "${BLUE}Checking for generated artifacts...${NC}"
if [ -n "$DAG_RUN_ID" ]; then
    ARTIFACTS_RESPONSE=$(curl -s "${BACKEND_URL}/api/artifacts/?execution_id=${DAG_RUN_ID}&limit=100")
    ARTIFACT_COUNT=$(echo "$ARTIFACTS_RESPONSE" | grep -o '"total":[0-9]*' | cut -d':' -f2 || echo "0")
    
    if [ "$ARTIFACT_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Found ${ARTIFACT_COUNT} artifacts for this execution${NC}"
        
        # Count by type
        for type in "chart" "llm" "signal" "order" "trade" "portfolio"; do
            TYPE_COUNT=$(echo "$ARTIFACTS_RESPONSE" | grep -o "\"type\":\"${type}\"" | wc -l | tr -d ' ' || echo "0")
            if [ "$TYPE_COUNT" -gt 0 ]; then
                echo -e "${GREEN}  - ${type}: ${TYPE_COUNT}${NC}"
            fi
        done
    else
        echo -e "${YELLOW}⚠ No artifacts found for execution ${DAG_RUN_ID}${NC}"
        echo -e "${YELLOW}  This may be normal if the workflow is still running or failed early${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Cannot check artifacts without DAG run ID${NC}"
fi
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo -e "${BLUE}View artifacts at: ${BACKEND_URL}/artifacts${NC}"
echo -e "${BLUE}View Airflow DAG at: ${AIRFLOW_URL}/dags/${DAG_ID}${NC}"
echo ""

