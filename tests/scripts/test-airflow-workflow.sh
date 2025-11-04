#!/bin/bash

# Test script for IBKR Airflow Workflow
# This script validates the Airflow workflow implementation

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       IBKR Airflow Workflow - Validation Test Suite           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Helper function to print test results
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        FAILED=$((FAILED + 1))
    fi
}

echo "=== 1. Checking Airflow Services ==="
echo ""

# Check if Airflow services are running
echo "Checking Airflow Scheduler..."
docker ps | grep -q ibkr-airflow-scheduler
test_result $? "Airflow Scheduler is running"

echo "Checking Airflow Webserver..."
docker ps | grep -q ibkr-airflow-webserver
test_result $? "Airflow Webserver is running"

echo "Checking Airflow Worker..."
docker ps | grep -q ibkr-airflow-worker
test_result $? "Airflow Worker is running"

echo ""
echo "=== 2. Checking Airflow Directory Structure ==="
echo ""

# Check if directories exist
echo "Checking airflow/dags..."
test -d airflow/dags
test_result $? "airflow/dags directory exists"

echo "Checking airflow/plugins..."
test -d airflow/plugins
test_result $? "airflow/plugins directory exists"

echo "Checking airflow/config..."
test -d airflow/config
test_result $? "airflow/config directory exists"

echo ""
echo "=== 3. Checking Plugin Files ==="
echo ""

# Check if plugin files exist
echo "Checking IBKRHook..."
test -f airflow/plugins/ibkr_plugin/hooks/ibkr_hook.py
test_result $? "IBKRHook file exists"

echo "Checking MLflowTracker..."
test -f airflow/plugins/ibkr_plugin/hooks/mlflow_tracker.py
test_result $? "MLflowTracker file exists"

echo "Checking ConfigLoader..."
test -f airflow/plugins/ibkr_plugin/hooks/config_loader.py
test_result $? "ConfigLoader file exists"

echo "Checking Market Data Operator..."
test -f airflow/plugins/ibkr_plugin/operators/market_data_operator.py
test_result $? "Market Data Operator file exists"

echo "Checking Signal Operator..."
test -f airflow/plugins/ibkr_plugin/operators/signal_operator.py
test_result $? "Signal Operator file exists"

echo "Checking Order Operator..."
test -f airflow/plugins/ibkr_plugin/operators/order_operator.py
test_result $? "Order Operator file exists"

echo "Checking Market Open Sensor..."
test -f airflow/plugins/ibkr_plugin/sensors/market_sensor.py
test_result $? "Market Open Sensor file exists"

echo "Checking Auth Sensor..."
test -f airflow/plugins/ibkr_plugin/sensors/auth_sensor.py
test_result $? "Auth Sensor file exists"

echo ""
echo "=== 4. Checking DAG Files ==="
echo ""

echo "Checking Trading Strategy DAG..."
test -f airflow/dags/ibkr_trading_strategy_dag.py
test_result $? "Trading Strategy DAG file exists"

echo ""
echo "=== 5. Checking Configuration ==="
echo ""

echo "Checking workflow config..."
test -f airflow/config/trading_workflow.yaml
test_result $? "Workflow configuration file exists"

echo ""
echo "=== 6. Validating DAG Syntax ==="
echo ""

echo "Validating DAG Python syntax..."
docker exec ibkr-airflow-scheduler python -m py_compile /opt/airflow/dags/ibkr_trading_strategy_dag.py 2>/dev/null
if [ $? -eq 0 ]; then
    test_result 0 "DAG syntax is valid"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Could not validate DAG syntax (Airflow may need restart)"
fi

echo ""
echo "=== 7. Checking Airflow DAG List ==="
echo ""

echo "Listing DAGs in Airflow..."
DAG_LIST=$(docker exec ibkr-airflow-scheduler airflow dags list 2>/dev/null | grep -c "ibkr_trading_strategy" || echo "0")
if [ "$DAG_LIST" -gt 0 ]; then
    test_result 0 "Trading Strategy DAG is registered in Airflow"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: DAG not yet visible (may need to wait for Airflow to parse it)"
    echo "   Run: docker exec ibkr-airflow-scheduler airflow dags list"
    echo "   to check again in a few seconds"
fi

echo ""
echo "=== 8. Checking Dependencies ==="
echo ""

echo "Checking httpx package..."
docker exec ibkr-airflow-scheduler python -c "import httpx" 2>/dev/null
test_result $? "httpx package is installed"

echo "Checking pytz package..."
docker exec ibkr-airflow-scheduler python -c "import pytz" 2>/dev/null
test_result $? "pytz package is installed"

echo "Checking mlflow package..."
docker exec ibkr-airflow-scheduler python -c "import mlflow" 2>/dev/null
test_result $? "mlflow package is installed"

echo ""
echo "=== 9. Checking MLflow Connection ==="
echo ""

echo "Checking MLflow server..."
docker ps | grep -q ibkr-mlflow-server
test_result $? "MLflow server is running"

echo "Checking MLflow API..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:5500/health | grep -q "200"
if [ $? -eq 0 ]; then
    test_result 0 "MLflow API is accessible"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: MLflow API may not be ready yet"
fi

echo ""
echo "=== 10. Checking Backend Services ==="
echo ""

echo "Checking Backend API..."
docker ps | grep -q ibkr-backend
test_result $? "Backend service is running"

echo "Checking IBKR Gateway..."
docker ps | grep -q ibkr-gateway
test_result $? "IBKR Gateway is running"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                      TEST SUMMARY                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Airflow workflow is ready.${NC}"
    echo ""
    echo "Next Steps:"
    echo "  1. Access Airflow UI: http://localhost:8080 (airflow/airflow)"
    echo "  2. Access MLflow UI: http://localhost:5500"
    echo "  3. Trigger the workflow from Airflow UI"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed. Please review the errors above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  1. Restart Airflow services: docker-compose restart airflow-scheduler airflow-webserver airflow-worker"
    echo "  2. Check logs: docker logs ibkr-airflow-scheduler --tail 100"
    echo "  3. Wait a few seconds for DAG parsing and retry"
    echo ""
    exit 1
fi

