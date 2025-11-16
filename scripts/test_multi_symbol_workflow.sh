#!/bin/bash
# Test Multi-Symbol Workflow Implementation

set -e

BACKEND_URL="http://localhost:8000"
AIRFLOW_URL="http://localhost:8080"

echo "============================================"
echo "Multi-Symbol Workflow Implementation Test"
echo "============================================"
echo ""

# Test 1: Backend Health
echo "✅ Test 1: Backend Health Check"
curl -s "${BACKEND_URL}/health" | grep -q "healthy" && echo "✓ Backend is healthy" || echo "✗ Backend not responding"
echo ""

# Test 2: List Symbols (should be empty or have existing)
echo "✅ Test 2: List Workflow Symbols"
response=$(curl -s "${BACKEND_URL}/api/workflow-symbols/")
echo "Response: $response"
echo ""

# Test 3: Add TSLA
echo "✅ Test 3: Add TSLA Symbol"
curl -s -X POST "${BACKEND_URL}/api/workflow-symbols/" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "TSLA",
    "name": "Tesla Inc.",
    "enabled": true,
    "priority": 10,
    "workflow_type": "trading_signal",
    "config": {"position_size": 10}
  }' && echo "✓ TSLA added" || echo "✗ Failed to add TSLA (may already exist)"
echo ""

# Test 4: Add NVDA
echo "✅ Test 4: Add NVDA Symbol"
curl -s -X POST "${BACKEND_URL}/api/workflow-symbols/" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NVDA",
    "name": "NVIDIA Corporation",
    "enabled": true,
    "priority": 9,
    "workflow_type": "trading_signal",
    "config": {"position_size": 10}
  }' && echo "✓ NVDA added" || echo "✗ Failed to add NVDA (may already exist)"
echo ""

# Test 5: List enabled symbols
echo "✅ Test 5: List Enabled Symbols"
response=$(curl -s "${BACKEND_URL}/api/workflow-symbols/?enabled_only=true")
echo "Enabled symbols: $response"
echo ""

# Test 6: Get TSLA details
echo "✅ Test 6: Get TSLA Details"
response=$(curl -s "${BACKEND_URL}/api/workflow-symbols/TSLA")
echo "TSLA: $response"
echo ""

# Test 7: Disable NVDA
echo "✅ Test 7: Disable NVDA"
curl -s -X PATCH "${BACKEND_URL}/api/workflow-symbols/NVDA" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}' && echo "✓ NVDA disabled" || echo "✗ Failed to disable NVDA"
echo ""

# Test 8: List enabled symbols (should only show TSLA now)
echo "✅ Test 8: List Enabled Symbols (NVDA should be disabled)"
response=$(curl -s "${BACKEND_URL}/api/workflow-symbols/?enabled_only=true")
echo "Enabled symbols: $response"
echo ""

# Test 9: Re-enable NVDA
echo "✅ Test 9: Re-enable NVDA"
curl -s -X PATCH "${BACKEND_URL}/api/workflow-symbols/NVDA" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}' && echo "✓ NVDA enabled" || echo "✗ Failed to enable NVDA"
echo ""

echo "============================================"
echo "✅ All Tests Complete!"
echo "============================================"
echo ""
echo "Next Steps:"
echo "1. Trigger multi-symbol workflow in Airflow UI: ${AIRFLOW_URL}"
echo "2. Monitor DAG execution"
echo "3. Check MLflow for logged runs: http://localhost:5500"
echo "4. Verify artifacts contain market data: ${BACKEND_URL}/api/artifacts/"
echo ""
