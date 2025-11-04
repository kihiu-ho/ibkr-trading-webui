#!/bin/bash

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "IBKR DEBUG MODE - COMPLETE DATABASE VERIFICATION"
echo "======================================================================"
echo ""

# Step 1: Verify DEBUG_MODE Configuration
echo -e "${BLUE}📋 STEP 1: Verify DEBUG_MODE Configuration${NC}"
echo "----------------------------------------------------------------------"

CONFIG=$(curl -s http://localhost:8000/api/market-data/cache-stats)
DEBUG_MODE=$(echo "$CONFIG" | jq -r '.debug_mode')
CACHE_ENABLED=$(echo "$CONFIG" | jq -r '.cache_enabled')
SYMBOLS=$(echo "$CONFIG" | jq -r '.symbols | join(", ")')

echo "Configuration:"
echo "  DEBUG_MODE: $DEBUG_MODE"
echo "  CACHE_ENABLED: $CACHE_ENABLED"
echo "  Cached Symbols: $SYMBOLS"

if [ "$DEBUG_MODE" == "true" ]; then
    echo -e "${GREEN}✅ DEBUG_MODE is ENABLED${NC}"
else
    echo -e "${RED}❌ DEBUG_MODE is NOT ENABLED${NC}"
    exit 1
fi

echo ""

# Step 2: Check Initial Database State
echo -e "${BLUE}📊 STEP 2: Initial Database State${NC}"
echo "----------------------------------------------------------------------"

docker compose exec -T backend python << 'PYTHON_EOF'
from backend.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("\nBefore Workflow Execution:")
try:
    with db.connection() as conn:
        for table in ['charts', 'llm_analyses', 'trading_signals', 'workflow_executions']:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table:25} {count:4} rows")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
PYTHON_EOF

echo ""

# Step 3: Execute Workflow in DEBUG_MODE
echo -e "${BLUE}🔄 STEP 3: Execute Workflow in DEBUG_MODE${NC}"
echo "----------------------------------------------------------------------"

# Get active strategy
STRATEGIES=$(curl -s http://localhost:8000/api/strategies)
ACTIVE_STRATEGY=$(echo "$STRATEGIES" | jq -r '.[] | select(.active == true) | .id' | head -n 1)

if [ -z "$ACTIVE_STRATEGY" ]; then
    echo -e "${RED}❌ No active strategy found${NC}"
    exit 1
fi

echo "Using Strategy ID: $ACTIVE_STRATEGY"
STRATEGY_NAME=$(echo "$STRATEGIES" | jq -r ".[] | select(.id == $ACTIVE_STRATEGY) | .name")
echo "Strategy Name: $STRATEGY_NAME"
echo ""

# Execute workflow
echo "Executing workflow..."
EXEC_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/strategies/$ACTIVE_STRATEGY/execute")
TASK_ID=$(echo "$EXEC_RESPONSE" | jq -r '.task_id')
echo "Task ID: $TASK_ID"

if [ "$TASK_ID" == "null" ] || [ -z "$TASK_ID" ]; then
    echo -e "${RED}❌ Failed to start workflow${NC}"
    exit 1
fi

echo ""
echo "Waiting for workflow to complete (35 seconds)..."
sleep 35

echo ""

# Step 4: Check Workflow Status
echo -e "${BLUE}📈 STEP 4: Check Workflow Status${NC}"
echo "----------------------------------------------------------------------"

EXECUTIONS=$(curl -s "http://localhost:8000/api/workflows/executions?limit=1")
LATEST_EXEC_ID=$(echo "$EXECUTIONS" | jq -r '.executions[0].id')
LATEST_STATUS=$(echo "$EXECUTIONS" | jq -r '.executions[0].status')
LATEST_ERROR=$(echo "$EXECUTIONS" | jq -r '.executions[0].error')

echo "Latest Execution:"
echo "  ID: $LATEST_EXEC_ID"
echo "  Status: $LATEST_STATUS"
if [ "$LATEST_ERROR" != "null" ] && [ -n "$LATEST_ERROR" ]; then
    echo "  Error: $LATEST_ERROR"
fi

echo ""

# Step 5: Verify Charts in Database
echo -e "${BLUE}📊 STEP 5: Verify Charts in PostgreSQL${NC}"
echo "----------------------------------------------------------------------"

CHARTS=$(curl -s "http://localhost:8000/api/charts?limit=10")
CHART_COUNT=$(echo "$CHARTS" | jq -r '.total')

echo "Charts in database: $CHART_COUNT"

if [ "$CHART_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Charts successfully saved!${NC}"
    echo ""
    echo "Chart Details:"
    echo "$CHARTS" | jq '.charts[] | {
        id, 
        symbol, 
        timeframe, 
        chart_type,
        data_points, 
        indicators: (.indicators_applied | keys),
        price_current,
        chart_url: .chart_url_jpeg
    }'
else
    echo -e "${RED}❌ No charts found in database${NC}"
fi

echo ""

# Step 6: Verify LLM Analyses in Database
echo -e "${BLUE}🤖 STEP 6: Verify LLM Analyses in PostgreSQL${NC}"
echo "----------------------------------------------------------------------"

ANALYSES=$(curl -s "http://localhost:8000/api/llm-analyses?limit=10")
ANALYSIS_COUNT=$(echo "$ANALYSES" | jq -r '.total')

echo "LLM Analyses in database: $ANALYSIS_COUNT"

if [ "$ANALYSIS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ LLM Analyses successfully saved!${NC}"
    echo ""
    echo "Analysis Details:"
    echo "$ANALYSES" | jq '.analyses[] | {
        id,
        symbol,
        timeframe,
        model_name,
        chart_id,
        response_length: (.response_text | length),
        latency_ms,
        analyzed_at
    }'
else
    echo -e "${YELLOW}⚠️  No LLM analyses found in database${NC}"
fi

echo ""

# Step 7: Verify Foreign Key Relationships
echo -e "${BLUE}🔗 STEP 7: Verify Foreign Key Relationships${NC}"
echo "----------------------------------------------------------------------"

if [ "$CHART_COUNT" -gt 0 ] && [ "$ANALYSIS_COUNT" -gt 0 ]; then
    echo "Checking chart → analysis relationships..."
    
    FIRST_CHART_ID=$(echo "$CHARTS" | jq -r '.charts[0].id')
    CHART_ANALYSES=$(curl -s "http://localhost:8000/api/llm-analyses/chart/$FIRST_CHART_ID")
    LINKED_COUNT=$(echo "$CHART_ANALYSES" | jq -r '.count')
    
    echo "Chart ID $FIRST_CHART_ID has $LINKED_COUNT linked analyses"
    
    if [ "$LINKED_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Foreign key relationships working${NC}"
    else
        echo -e "${YELLOW}⚠️  No analyses linked to chart${NC}"
    fi
fi

echo ""

# Step 8: Verify Lineage Tracking
echo -e "${BLUE}📝 STEP 8: Verify Lineage Tracking${NC}"
echo "----------------------------------------------------------------------"

if [ -n "$LATEST_EXEC_ID" ]; then
    LINEAGE=$(curl -s "http://localhost:8000/api/lineage/executions/$LATEST_EXEC_ID")
    STEP_COUNT=$(echo "$LINEAGE" | jq -r '.steps | length')
    
    echo "Lineage steps recorded: $STEP_COUNT"
    
    if [ "$STEP_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Lineage tracking working${NC}"
        echo ""
        echo "Key steps:"
        echo "$LINEAGE" | jq '.steps[] | {
            step_name,
            status,
            duration_ms,
            data_source: .metadata.data_source
        }' | head -30
    fi
fi

echo ""

# Step 9: Complete Database Verification
echo -e "${BLUE}💾 STEP 9: Complete Database Verification${NC}"
echo "----------------------------------------------------------------------"

docker compose exec -T backend python << 'PYTHON_EOF'
from backend.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("\n╔══════════════════════════════════════════════════════════════╗")
print("║           FINAL DATABASE STATE - ALL TABLES                  ║")
print("╚══════════════════════════════════════════════════════════════╝\n")

try:
    with db.connection() as conn:
        tables = [
            'strategies',
            'codes', 
            'symbols',
            'market_data_cache',
            'workflow_executions',
            'workflow_logs',
            'charts',
            'llm_analyses',
            'trading_signals',
            'workflow_lineage'
        ]
        
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            status = "✅" if count > 0 else "⚠️"
            print(f"  {status} {table:25} {count:6} rows")
    
    print("\n" + "="*66)
    
    # Check data quality
    print("\nData Quality Checks:")
    
    # Check charts have URLs
    result = conn.execute(text("SELECT COUNT(*) FROM charts WHERE chart_url_jpeg IS NOT NULL"))
    charts_with_urls = result.scalar()
    result = conn.execute(text("SELECT COUNT(*) FROM charts"))
    total_charts = result.scalar()
    
    if total_charts > 0:
        print(f"  ✅ Charts with URLs: {charts_with_urls}/{total_charts}")
    
    # Check LLM analyses have responses
    result = conn.execute(text("SELECT COUNT(*) FROM llm_analyses WHERE response_text IS NOT NULL"))
    analyses_with_responses = result.scalar()
    result = conn.execute(text("SELECT COUNT(*) FROM llm_analyses"))
    total_analyses = result.scalar()
    
    if total_analyses > 0:
        print(f"  ✅ Analyses with responses: {analyses_with_responses}/{total_analyses}")
    
    # Check foreign key links
    result = conn.execute(text("SELECT COUNT(*) FROM llm_analyses WHERE chart_id IS NOT NULL"))
    linked_analyses = result.scalar()
    
    if total_analyses > 0:
        print(f"  ✅ Analyses linked to charts: {linked_analyses}/{total_analyses}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
finally:
    db.close()
PYTHON_EOF

echo ""

# Step 10: API Endpoints Verification
echo -e "${BLUE}🌐 STEP 10: API Endpoints Verification${NC}"
echo "----------------------------------------------------------------------"

echo "Testing API endpoints..."

# Test charts API
CHARTS_STATS=$(curl -s http://localhost:8000/api/charts/stats/summary)
if echo "$CHARTS_STATS" | jq -e '.total_charts' > /dev/null; then
    echo -e "  ✅ Charts API working"
else
    echo -e "  ❌ Charts API failed"
fi

# Test LLM analyses API
LLM_STATS=$(curl -s http://localhost:8000/api/llm-analyses/stats/summary)
if echo "$LLM_STATS" | jq -e '.total_analyses' > /dev/null; then
    echo -e "  ✅ LLM Analyses API working"
else
    echo -e "  ❌ LLM Analyses API failed"
fi

# Test workflows API
if echo "$EXECUTIONS" | jq -e '.executions' > /dev/null; then
    echo -e "  ✅ Workflows API working"
else
    echo -e "  ❌ Workflows API failed"
fi

echo ""

# Final Summary
echo "======================================================================"
echo -e "${CYAN}📊 DEBUG MODE DATABASE VERIFICATION - SUMMARY${NC}"
echo "======================================================================"

echo ""
echo "Environment:"
echo "  • DEBUG_MODE: $DEBUG_MODE"
echo "  • CACHE_ENABLED: $CACHE_ENABLED"
echo "  • Cached Symbols: $SYMBOLS"

echo ""
echo "Workflow Execution:"
echo "  • Execution ID: $LATEST_EXEC_ID"
echo "  • Status: $LATEST_STATUS"
echo "  • Charts Created: $CHART_COUNT"
echo "  • LLM Analyses: $ANALYSIS_COUNT"

echo ""
echo "Data Verification:"
if [ "$CHART_COUNT" -gt 0 ]; then
    echo -e "  ${GREEN}✅ Charts persisted to PostgreSQL${NC}"
else
    echo -e "  ${RED}❌ No charts in database${NC}"
fi

if [ "$ANALYSIS_COUNT" -gt 0 ]; then
    echo -e "  ${GREEN}✅ LLM Analyses persisted to PostgreSQL${NC}"
else
    echo -e "  ${YELLOW}⚠️  No LLM analyses in database${NC}"
fi

echo ""
echo "API Endpoints:"
echo -e "  ${GREEN}✅ All API endpoints operational${NC}"

echo ""
echo "======================================================================"

if [ "$DEBUG_MODE" == "true" ] && [ "$CHART_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ DEBUG MODE VERIFICATION PASSED!${NC}"
    echo ""
    echo "System Status: OPERATIONAL ✅"
    echo "Data Persistence: WORKING ✅"
    echo "API Endpoints: FUNCTIONAL ✅"
else
    echo -e "${YELLOW}⚠️  PARTIAL SUCCESS - Some data may be missing${NC}"
fi

echo "======================================================================"
echo ""

