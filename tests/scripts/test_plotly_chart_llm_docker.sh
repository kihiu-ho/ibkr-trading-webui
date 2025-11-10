#!/bin/bash
# Test script for Plotly chart generation and LLM analysis
# This script should be run inside the Airflow Docker container where dependencies are available

set -e

echo "======================================================================"
echo "🧪 PLOTLY CHART GENERATION & LLM ANALYSIS TEST (Docker)"
echo "======================================================================"
echo ""

# Check if we're in the right environment
if ! python3 -c "import stock_indicators" 2>/dev/null; then
    echo "❌ stock_indicators not found. This test must run in Docker container."
    echo "   Run: docker-compose exec airflow-webserver bash"
    echo "   Then: python3 /path/to/test_plotly_chart_llm.py"
    exit 1
fi

if ! python3 -c "import plotly" 2>/dev/null; then
    echo "❌ plotly not found. This test must run in Docker container."
    exit 1
fi

echo "✅ Dependencies found"
echo ""

# Run the test
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$PROJECT_ROOT"

python3 tests/scripts/test_plotly_chart_llm.py

echo ""
echo "======================================================================"
echo "✅ TEST COMPLETE"
echo "======================================================================"

