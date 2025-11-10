#!/bin/bash
# Check DAG imports in Airflow container
# This script helps diagnose why DAGs might not appear in Airflow

set -e

DAG_NAME="${1:-ibkr_trading_signal_workflow}"

echo "Checking DAG imports for: $DAG_NAME"
echo "=================================="
echo ""

# Check if Airflow container is running
if ! docker ps | grep -q airflow-webserver; then
    echo "❌ Airflow webserver container is not running"
    exit 1
fi

echo "1. Checking DAG file syntax..."
docker exec airflow-webserver python3 -m py_compile /opt/airflow/dags/${DAG_NAME}.py 2>&1 || {
    echo "❌ Syntax error in DAG file"
    exit 1
}
echo "✅ Syntax OK"

echo ""
echo "2. Checking DAG imports..."
docker exec airflow-webserver python3 -c "
import sys
sys.path.insert(0, '/opt/airflow/dags')
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location('${DAG_NAME}', '/opt/airflow/dags/${DAG_NAME}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print('✅ DAG imports successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" 2>&1

echo ""
echo "3. Checking if DAG is registered in Airflow..."
docker exec airflow-webserver airflow dags list | grep -q "${DAG_NAME}" && {
    echo "✅ DAG is registered"
    docker exec airflow-webserver airflow dags list | grep "${DAG_NAME}"
} || {
    echo "❌ DAG is NOT registered"
    echo ""
    echo "Available DAGs:"
    docker exec airflow-webserver airflow dags list
}

echo ""
echo "4. Checking DAG import errors in Airflow logs..."
docker logs airflow-webserver 2>&1 | grep -i "${DAG_NAME}" | grep -i "error\|import\|traceback" | tail -20 || {
    echo "No recent errors found for ${DAG_NAME}"
}

echo ""
echo "Done!"

