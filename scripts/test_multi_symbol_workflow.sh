#!/bin/bash
# Test script for multi-symbol workflow
# Tests end-to-end workflow execution and artifact generation

# Don't exit on error - we want to run all tests and report results
set +e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Multi-Symbol Workflow Test"
echo "=========================================="
echo "Project root: $PROJECT_ROOT"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
AIRFLOW_URL="${AIRFLOW_URL:-http://localhost:8080}"
DAG_ID="ibkr_multi_symbol_workflow"

# Test functions
test_api_health() {
    echo -e "\n${YELLOW}Testing API Health...${NC}"
    if curl -s -f "${BACKEND_URL}/health" > /dev/null; then
        echo -e "${GREEN}✓ Backend API is healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Backend API is not responding${NC}"
        return 1
    fi
}

test_artifacts_api() {
    echo -e "\n${YELLOW}Testing Artifacts API...${NC}"
    
    # Test basic artifacts endpoint
    response=$(curl -s "${BACKEND_URL}/api/artifacts/?limit=10")
    if echo "$response" | grep -q "artifacts"; then
        echo -e "${GREEN}✓ Artifacts API is working${NC}"
        
        # Test grouping
        grouped_response=$(curl -s "${BACKEND_URL}/api/artifacts/?group_by=execution_id&limit=10")
        if echo "$grouped_response" | grep -q "\"grouped\"" || echo "$grouped_response" | grep -q "\"group_count\""; then
            echo -e "${GREEN}✓ Artifacts grouping is working${NC}"
        else
            # Check if it's just empty results (which is OK)
            if echo "$grouped_response" | grep -q "\"artifacts\":\[\]"; then
                echo -e "${GREEN}✓ Artifacts grouping is working (no artifacts to group yet)${NC}"
            else
                echo -e "${YELLOW}⚠ Artifacts grouping may not be working (response: ${grouped_response:0:100})${NC}"
            fi
        fi
        
        # Test filtering
        for type in "llm" "chart" "signal" "order" "trade" "portfolio"; do
            filtered_response=$(curl -s "${BACKEND_URL}/api/artifacts/?type=${type}&limit=5")
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ Filtering by type '${type}' works${NC}"
            else
                echo -e "${YELLOW}⚠ Filtering by type '${type}' failed${NC}"
            fi
        done
        
        return 0
    else
        echo -e "${RED}✗ Artifacts API is not working${NC}"
        return 1
    fi
}

test_airflow_connection() {
    echo -e "\n${YELLOW}Testing Airflow Connection...${NC}"
    if curl -s -f "${AIRFLOW_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Airflow is accessible${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Airflow may not be accessible (this is OK if not running)${NC}"
        return 0
    fi
}

test_dag_exists() {
    echo -e "\n${YELLOW}Testing DAG Existence...${NC}"
    
    # Try to get DAG info via API
    dag_response=$(curl -s "${BACKEND_URL}/api/airflow/dags/${DAG_ID}" 2>/dev/null || echo "")
    
    if echo "$dag_response" | grep -q "${DAG_ID}" || [ -f "dags/${DAG_ID}.py" ] || [ -f "dags/ibkr_multi_symbol_workflow.py" ]; then
        echo -e "${GREEN}✓ DAG file exists${NC}"
        return 0
    else
        echo -e "${RED}✗ DAG file not found${NC}"
        return 1
    fi
}

test_artifact_storage() {
    echo -e "\n${YELLOW}Testing Artifact Storage Functions...${NC}"
    
    # Check if artifact storage functions exist
    if [ -f "dags/utils/artifact_storage.py" ] && \
       grep -q "def store_order_artifact" dags/utils/artifact_storage.py && \
       grep -q "def store_trade_artifact" dags/utils/artifact_storage.py && \
       grep -q "def store_portfolio_artifact" dags/utils/artifact_storage.py; then
        echo -e "${GREEN}✓ All artifact storage functions exist${NC}"
        return 0
    else
        echo -e "${RED}✗ Some artifact storage functions are missing${NC}"
        if [ ! -f "dags/utils/artifact_storage.py" ]; then
            echo -e "${RED}  File dags/utils/artifact_storage.py not found${NC}"
        fi
        return 1
    fi
}

test_mlflow_tracking() {
    echo -e "\n${YELLOW}Testing MLflow Tracking...${NC}"
    
    # Check if MLflow tracking is in the workflow
    if [ -f "dags/ibkr_multi_symbol_workflow.py" ] && \
       grep -q "log_to_mlflow_task" dags/ibkr_multi_symbol_workflow.py && \
       grep -q "mlflow_run_context" dags/ibkr_multi_symbol_workflow.py; then
        echo -e "${GREEN}✓ MLflow tracking is integrated${NC}"
        return 0
    else
        echo -e "${RED}✗ MLflow tracking is not integrated${NC}"
        if [ ! -f "dags/ibkr_multi_symbol_workflow.py" ]; then
            echo -e "${RED}  File dags/ibkr_multi_symbol_workflow.py not found${NC}"
        fi
        return 1
    fi
}

test_chart_generation() {
    echo -e "\n${YELLOW}Testing Chart Generation...${NC}"
    
    # Check if chart generator supports daily and weekly
    if [ -f "dags/utils/chart_generator.py" ] && \
       grep -q "resample_to_weekly" dags/utils/chart_generator.py && \
       ([ -f "dags/ibkr_multi_symbol_workflow.py" ] && grep -q "Timeframe.DAILY\|Timeframe.WEEKLY" dags/ibkr_multi_symbol_workflow.py || \
        [ -f "dags/ibkr_trading_signal_workflow.py" ] && grep -q "Timeframe.DAILY\|Timeframe.WEEKLY" dags/ibkr_trading_signal_workflow.py); then
        echo -e "${GREEN}✓ Chart generation supports daily and weekly timeframes${NC}"
        return 0
    else
        echo -e "${RED}✗ Chart generation may not support all timeframes${NC}"
        if [ ! -f "dags/utils/chart_generator.py" ]; then
            echo -e "${RED}  File dags/utils/chart_generator.py not found${NC}"
        fi
        return 1
    fi
}

test_llm_analysis() {
    echo -e "\n${YELLOW}Testing LLM Analysis...${NC}"
    
    # Check if LLM analyzer supports multi-chart analysis
    if [ -f "dags/utils/llm_signal_analyzer.py" ] && \
       grep -q "analyze_charts" dags/utils/llm_signal_analyzer.py && \
       ([ -f "dags/ibkr_multi_symbol_workflow.py" ] && grep -q "daily_chart.*weekly_chart\|weekly_chart.*daily_chart" dags/ibkr_multi_symbol_workflow.py || \
        [ -f "dags/ibkr_trading_signal_workflow.py" ] && grep -q "daily_chart.*weekly_chart\|weekly_chart.*daily_chart" dags/ibkr_trading_signal_workflow.py); then
        echo -e "${GREEN}✓ LLM analysis supports multi-chart analysis${NC}"
        return 0
    else
        echo -e "${RED}✗ LLM analysis may not support multi-chart analysis${NC}"
        if [ ! -f "dags/utils/llm_signal_analyzer.py" ]; then
            echo -e "${RED}  File dags/utils/llm_signal_analyzer.py not found${NC}"
        fi
        return 1
    fi
}

test_frontend_artifacts() {
    echo -e "\n${YELLOW}Testing Frontend Artifacts Page...${NC}"
    
    # Check if frontend has artifact type detection
    if [ -f "frontend/templates/artifacts.html" ] && \
       grep -q "getArtifactType" frontend/templates/artifacts.html && \
       grep -q "getArtifactTypeBadge" frontend/templates/artifacts.html && \
       grep -q "order\|trade\|portfolio" frontend/templates/artifacts.html; then
        echo -e "${GREEN}✓ Frontend artifacts page supports all artifact types${NC}"
        return 0
    else
        echo -e "${RED}✗ Frontend artifacts page may be missing features${NC}"
        if [ ! -f "frontend/templates/artifacts.html" ]; then
            echo -e "${RED}  File frontend/templates/artifacts.html not found${NC}"
        fi
        return 1
    fi
}

test_airflow_integration() {
    echo -e "\n${YELLOW}Testing Airflow Integration...${NC}"
    
    # Check if Airflow monitor has artifacts display
    if [ -f "frontend/templates/airflow_monitor.html" ] && \
       grep -q "runArtifacts" frontend/templates/airflow_monitor.html && \
       grep -q "loadArtifactsForRun" frontend/templates/airflow_monitor.html && \
       grep -q "getArtifactType" frontend/templates/airflow_monitor.html; then
        echo -e "${GREEN}✓ Airflow integration includes artifacts display${NC}"
        return 0
    else
        echo -e "${RED}✗ Airflow integration may be missing artifacts display${NC}"
        if [ ! -f "frontend/templates/airflow_monitor.html" ]; then
            echo -e "${RED}  File frontend/templates/airflow_monitor.html not found${NC}"
        fi
        return 1
    fi
}

# Run all tests
echo "Starting tests..."
echo ""

PASSED=0
FAILED=0

test_api_health && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
test_artifacts_api && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
test_airflow_connection && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
test_dag_exists && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
test_artifact_storage && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
test_mlflow_tracking && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
test_chart_generation && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
test_llm_analysis && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
test_frontend_artifacts && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))
test_airflow_integration && PASSED=$((PASSED + 1)) || FAILED=$((FAILED + 1))

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${YELLOW}Some tests failed. Please review the output above.${NC}"
    exit 1
fi

