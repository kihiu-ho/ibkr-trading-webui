#!/bin/bash
# Test DAG imports and trigger via API
# This script validates that all IBKR DAGs can be imported and triggered

set -e

BASE_URL="${1:-http://localhost:8000}"
AIRFLOW_USER="${2:-airflow}"
AIRFLOW_PASS="${3:-airflow}"

echo "Testing DAG imports and API triggering"
echo "======================================"
echo ""

# Test DAG import in container
echo "1. Testing DAG imports in Airflow container..."
for dag in ibkr_trading_signal_workflow ibkr_stock_data_workflow ibkr_multi_symbol_workflow; do
    echo -n "  Testing $dag... "
    if docker exec ibkr-airflow-scheduler python3 -c "
import sys
sys.path.insert(0, '/opt/airflow/dags')
import importlib.util
spec = importlib.util.spec_from_file_location('test', '/opt/airflow/dags/${dag}.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print('OK')
" 2>&1 | grep -q "OK"; then
        echo "✅ OK"
    else
        echo "❌ FAILED"
        docker exec ibkr-airflow-scheduler python3 -c "
import sys
sys.path.insert(0, '/opt/airflow/dags')
import importlib.util
spec = importlib.util.spec_from_file_location('test', '/opt/airflow/dags/${dag}.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
" 2>&1 | tail -10
        exit 1
    fi
done

echo ""
echo "2. Checking DAG status via API..."
response=$(curl -s -u "${AIRFLOW_USER}:${AIRFLOW_PASS}" "${BASE_URL}/api/airflow/dags?limit=100")
ibkr_dags=$(echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
ibkr = [d for d in data.get('dags', []) if d['dag_id'].startswith('ibkr_')]
for d in ibkr:
    status = '✅ Active' if not d.get('has_import_errors') else '❌ Import Errors'
    paused = ' (PAUSED)' if d.get('is_paused') else ''
    print(f\"  - {d['dag_id']}: {status}{paused}\")
")

if [ -z "$ibkr_dags" ]; then
    echo "  ⚠️  No IBKR DAGs found in API response"
    echo "  Waiting 30 seconds for Airflow to refresh DAG bag..."
    sleep 30
    response=$(curl -s -u "${AIRFLOW_USER}:${AIRFLOW_PASS}" "${BASE_URL}/api/airflow/dags?limit=100")
    ibkr_dags=$(echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
ibkr = [d for d in data.get('dags', []) if d['dag_id'].startswith('ibkr_')]
for d in ibkr:
    status = '✅ Active' if not d.get('has_import_errors') else '❌ Import Errors'
    paused = ' (PAUSED)' if d.get('is_paused') else ''
    print(f\"  - {d['dag_id']}: {status}{paused}\")
")
fi

echo "$ibkr_dags"

echo ""
echo "3. Testing DAG trigger via API..."
for dag in ibkr_trading_signal_workflow; do
    echo -n "  Triggering $dag... "
    response=$(curl -s -X POST \
        -u "${AIRFLOW_USER}:${AIRFLOW_PASS}" \
        -H "Content-Type: application/json" \
        "${BASE_URL}/api/airflow/dags/${dag}/dagRuns" \
        -d '{}')
    
    if echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if 'dag_run_id' in data else 1)" 2>/dev/null; then
        run_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['dag_run_id'])" 2>/dev/null)
        echo "✅ Triggered (run_id: $run_id)"
    else
        error=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('detail', 'Unknown error'))" 2>/dev/null || echo "Unknown error")
        echo "❌ Failed: $error"
    fi
done

echo ""
echo "Done!"

