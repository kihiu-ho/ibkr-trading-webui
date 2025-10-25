#!/bin/bash

# Frontend Features Comprehensive Test Script
# Tests all implemented LLM trading frontend features

set -e  # Exit on error

BACKEND_URL="http://localhost:8000"
TEST_RESULTS_DIR="tests/results"
mkdir -p "$TEST_RESULTS_DIR"

echo "=================================="
echo "Frontend Features Test Suite"
echo "=================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
test_passed() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓ PASSED${NC}: $1"
}

test_failed() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗ FAILED${NC}: $1"
    echo "  Error: $2"
}

test_info() {
    echo -e "${YELLOW}ℹ INFO${NC}: $1"
}

run_test() {
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Check if backend is running
echo "Step 1: Checking backend availability..."
if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    test_passed "Backend is running at $BACKEND_URL"
else
    test_failed "Backend check" "Backend not running at $BACKEND_URL"
    echo ""
    echo "Please start the backend first:"
    echo "  uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi
echo ""

# Test 1: API Endpoints - Workflows
echo "Step 2: Testing Workflow API Endpoints..."
run_test

# 2.1 List workflows
echo "  2.1 GET /api/workflows"
if curl -s "$BACKEND_URL/api/workflows" | jq . > "$TEST_RESULTS_DIR/workflows_list.json" 2>&1; then
    test_passed "List workflows endpoint"
else
    test_failed "List workflows endpoint" "API call failed"
fi

# 2.2 List workflow executions
echo "  2.2 GET /api/workflows/executions"
if curl -s "$BACKEND_URL/api/workflows/executions" | jq . > "$TEST_RESULTS_DIR/executions_list.json" 2>&1; then
    test_passed "List workflow executions endpoint"
    EXECUTION_COUNT=$(jq 'length' "$TEST_RESULTS_DIR/executions_list.json")
    test_info "Found $EXECUTION_COUNT workflow execution(s)"
else
    test_failed "List workflow executions endpoint" "API call failed"
fi

# Get first execution ID if available
EXECUTION_ID=$(jq -r '.[0].id // empty' "$TEST_RESULTS_DIR/executions_list.json")

if [ -n "$EXECUTION_ID" ]; then
    # 2.3 Get execution details
    echo "  2.3 GET /api/workflows/executions/$EXECUTION_ID"
    if curl -s "$BACKEND_URL/api/workflows/executions/$EXECUTION_ID" | jq . > "$TEST_RESULTS_DIR/execution_details.json" 2>&1; then
        test_passed "Get execution details endpoint"
        
        # Check for statistics
        if jq -e '.statistics' "$TEST_RESULTS_DIR/execution_details.json" > /dev/null; then
            TOTAL_STEPS=$(jq -r '.statistics.total_steps' "$TEST_RESULTS_DIR/execution_details.json")
            SUCCESS_RATE=$(jq -r '.statistics.success_rate' "$TEST_RESULTS_DIR/execution_details.json")
            test_info "Execution stats: $TOTAL_STEPS steps, $SUCCESS_RATE% success rate"
        fi
    else
        test_failed "Get execution details endpoint" "API call failed"
    fi
    
    # 2.4 Get execution logs
    echo "  2.4 GET /api/workflows/executions/$EXECUTION_ID/logs"
    if curl -s "$BACKEND_URL/api/workflows/executions/$EXECUTION_ID/logs" | jq . > "$TEST_RESULTS_DIR/execution_logs.json" 2>&1; then
        test_passed "Get execution logs endpoint"
        LOG_COUNT=$(jq 'length' "$TEST_RESULTS_DIR/execution_logs.json")
        test_info "Found $LOG_COUNT log entries"
    else
        test_failed "Get execution logs endpoint" "API call failed"
    fi
    
    # 2.5 Get execution lineage
    echo "  2.5 GET /api/workflows/executions/$EXECUTION_ID/lineage"
    if curl -s "$BACKEND_URL/api/workflows/executions/$EXECUTION_ID/lineage" | jq . > "$TEST_RESULTS_DIR/execution_lineage.json" 2>&1; then
        test_passed "Get execution lineage endpoint"
        NODE_COUNT=$(jq '.nodes | length' "$TEST_RESULTS_DIR/execution_lineage.json")
        EDGE_COUNT=$(jq '.edges | length' "$TEST_RESULTS_DIR/execution_lineage.json")
        test_info "Lineage: $NODE_COUNT nodes, $EDGE_COUNT edges"
    else
        test_failed "Get execution lineage endpoint" "API call failed"
    fi
else
    test_info "No existing executions found - skipping execution detail tests"
fi

echo ""

# Test 2: API Endpoints - Logs
echo "Step 3: Testing Logs API Endpoints..."
run_test

# 3.1 Query logs
echo "  3.1 GET /api/logs"
if curl -s "$BACKEND_URL/api/logs?limit=10" | jq . > "$TEST_RESULTS_DIR/logs_query.json" 2>&1; then
    test_passed "Query logs endpoint"
    TOTAL_LOGS=$(jq '.total' "$TEST_RESULTS_DIR/logs_query.json")
    test_info "Total logs in system: $TOTAL_LOGS"
else
    test_failed "Query logs endpoint" "API call failed"
fi

# 3.2 Log statistics
echo "  3.2 GET /api/logs/statistics"
if curl -s "$BACKEND_URL/api/logs/statistics" | jq . > "$TEST_RESULTS_DIR/logs_statistics.json" 2>&1; then
    test_passed "Log statistics endpoint"
    if jq -e '.total_logs' "$TEST_RESULTS_DIR/logs_statistics.json" > /dev/null; then
        TOTAL=$(jq -r '.total_logs' "$TEST_RESULTS_DIR/logs_statistics.json")
        FAILED=$(jq -r '.failed_logs' "$TEST_RESULTS_DIR/logs_statistics.json")
        RATE=$(jq -r '.success_rate' "$TEST_RESULTS_DIR/logs_statistics.json")
        test_info "Log stats: $TOTAL total, $FAILED failed, $RATE% success"
    fi
else
    test_failed "Log statistics endpoint" "API call failed"
fi

echo ""

# Test 3: API Endpoints - Strategies
echo "Step 4: Testing Strategy API Endpoints..."
run_test

# 4.1 List strategies
echo "  4.1 GET /api/strategies"
if curl -s "$BACKEND_URL/api/strategies" | jq . > "$TEST_RESULTS_DIR/strategies_list.json" 2>&1; then
    test_passed "List strategies endpoint"
    STRATEGY_COUNT=$(jq 'length' "$TEST_RESULTS_DIR/strategies_list.json")
    test_info "Found $STRATEGY_COUNT strategy(ies)"
else
    test_failed "List strategies endpoint" "API call failed"
fi

# Get first strategy ID if available
STRATEGY_ID=$(jq -r '.[0].id // empty' "$TEST_RESULTS_DIR/strategies_list.json")

if [ -n "$STRATEGY_ID" ]; then
    # 4.2 Get strategy details
    echo "  4.2 GET /api/strategies/$STRATEGY_ID"
    if curl -s "$BACKEND_URL/api/strategies/$STRATEGY_ID" | jq . > "$TEST_RESULTS_DIR/strategy_details.json" 2>&1; then
        test_passed "Get strategy details endpoint"
    else
        test_failed "Get strategy details endpoint" "API call failed"
    fi
    
    # 4.3 Validate strategy parameters
    echo "  4.3 POST /api/strategies/$STRATEGY_ID/validate-params"
    if curl -s -X POST "$BACKEND_URL/api/strategies/$STRATEGY_ID/validate-params" | jq . > "$TEST_RESULTS_DIR/strategy_validation.json" 2>&1; then
        test_passed "Validate strategy parameters endpoint"
        IS_VALID=$(jq -r '.valid' "$TEST_RESULTS_DIR/strategy_validation.json")
        if [ "$IS_VALID" = "true" ]; then
            test_info "Strategy parameters are valid"
        else
            ERROR_COUNT=$(jq '.errors | length' "$TEST_RESULTS_DIR/strategy_validation.json")
            test_info "Strategy has $ERROR_COUNT validation error(s)"
        fi
    else
        test_failed "Validate strategy parameters endpoint" "API call failed"
    fi
else
    test_info "No strategies found - skipping strategy detail tests"
fi

echo ""

# Test 4: Frontend Pages
echo "Step 5: Testing Frontend Pages Availability..."
run_test

# 5.1 Dashboard
echo "  5.1 GET /dashboard"
if curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/dashboard" | grep -q "200"; then
    test_passed "Dashboard page loads"
else
    test_failed "Dashboard page" "Page did not return 200"
fi

# 5.2 Strategies page
echo "  5.2 GET /strategies"
if curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/strategies" | grep -q "200"; then
    test_passed "Strategies page loads"
else
    test_failed "Strategies page" "Page did not return 200"
fi

# 5.3 Workflows list page
echo "  5.3 GET /workflows"
if curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/workflows" | grep -q "200"; then
    test_passed "Workflows list page loads"
else
    test_failed "Workflows list page" "Page did not return 200"
fi

# 5.4 Workflow execution page (if execution exists)
if [ -n "$EXECUTION_ID" ]; then
    echo "  5.4 GET /workflows/executions/$EXECUTION_ID"
    if curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/workflows/executions/$EXECUTION_ID" | grep -q "200"; then
        test_passed "Workflow execution page loads"
    else
        test_failed "Workflow execution page" "Page did not return 200"
    fi
else
    test_info "No execution ID - skipping execution page test"
fi

echo ""

# Test 5: Static Assets
echo "Step 6: Testing Static Assets..."
run_test

# 6.1 JavaScript files
echo "  6.1 Checking JavaScript files"
if [ -f "frontend/static/js/workflows-list.js" ]; then
    test_passed "workflows-list.js exists"
else
    test_failed "workflows-list.js" "File not found"
fi

if [ -f "frontend/static/js/workflow-execution.js" ]; then
    test_passed "workflow-execution.js exists"
else
    test_failed "workflow-execution.js" "File not found"
fi

echo ""

# Test 6: WebSocket Endpoint
echo "Step 7: Testing WebSocket Endpoint..."
run_test

echo "  7.1 WebSocket /ws/logs endpoint"
test_info "WebSocket testing requires browser or wscat tool"
test_info "Manual test: wscat -c ws://localhost:8000/ws/logs"

echo ""

# Test Summary
echo "=================================="
echo "Test Summary"
echo "=================================="
echo "Total Tests Run:    $TESTS_RUN"
echo -e "Tests Passed:       ${GREEN}$TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "Tests Failed:       ${RED}$TESTS_FAILED${NC}"
else
    echo -e "Tests Failed:       ${GREEN}$TESTS_FAILED${NC}"
fi
echo ""

# Output test results location
echo "Detailed test results saved to: $TEST_RESULTS_DIR/"
echo ""

# Test result files
echo "Generated test result files:"
ls -1 "$TEST_RESULTS_DIR"/ 2>/dev/null | sed 's/^/  - /'
echo ""

# Final verdict
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo ""
    echo "Frontend is ready to use!"
    echo "Open: http://localhost:8000/workflows"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please review the errors above and check:"
    echo "  - Backend is running: uvicorn backend.main:app --reload"
    echo "  - Database is accessible"
    echo "  - All dependencies are installed"
    exit 1
fi

