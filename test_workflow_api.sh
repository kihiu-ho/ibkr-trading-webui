#!/bin/bash
# Test Complete IBKR Workflow via API
# This tests the actual workflow execution to verify debug mode is working

echo "======================================================================"
echo "IBKR WORKFLOW API TEST - DEBUG MODE"
echo "======================================================================"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get first active strategy
echo -e "${BLUE}Getting active strategy...${NC}"
STRATEGY=$(curl -s http://localhost:8000/api/strategies | jq '.[] | select(.active == true) | {id, name}' | head -20)
STRATEGY_ID=$(echo "$STRATEGY" | jq -r '.id // empty' | head -1)

if [ -z "$STRATEGY_ID" ]; then
    echo -e "${YELLOW}No active strategy found. Creating one...${NC}"
    
    # Get NVDA code
    CODES=$(curl -s "http://localhost:8000/api/codes?symbol=NVDA" | jq '.[0]')
    CODE_ID=$(echo "$CODES" | jq -r '.id // empty')
    
    if [ -z "$CODE_ID" ]; then
        echo -e "${YELLOW}NVDA code not found. Workflow test requires symbol data.${NC}"
        exit 0
    fi
    
    # Create strategy
    NEW_STRATEGY=$(curl -s -X POST http://localhost:8000/api/strategies \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Debug Mode Test Strategy",
            "active": true,
            "llm_enabled": true,
            "llm_model": "gpt-4-turbo-preview",
            "llm_language": "en",
            "llm_timeframes": ["1d", "1w"],
            "llm_consolidate": true,
            "code_ids": ['$CODE_ID']
        }')
    
    STRATEGY_ID=$(echo "$NEW_STRATEGY" | jq -r '.id')
    echo -e "${GREEN}Created strategy ID: $STRATEGY_ID${NC}"
else
    echo -e "${GREEN}Using strategy ID: $STRATEGY_ID${NC}"
    echo "$STRATEGY" | jq '.'
fi

echo ""
echo -e "${BLUE}Executing strategy workflow...${NC}"
EXEC_ID="debug_test_$(date +%s)"

RESULT=$(curl -s -X POST "http://localhost:8000/api/strategies/$STRATEGY_ID/execute" \
    -H "Content-Type: application/json" \
    -d '{"execution_id": "'$EXEC_ID'"}' 2>&1)

echo ""
echo "Execution Result:"
echo "$RESULT" | jq '.' | head -30

echo ""
echo -e "${BLUE}Checking lineage for data source...${NC}"
sleep 3

LINEAGE=$(curl -s "http://localhost:8000/api/lineage?execution_id=$EXEC_ID")
echo "$LINEAGE" | jq '[.[] | {step: .step_name, status, data_source: .metadata.data_source, debug_mode: .metadata.debug_mode}]'

echo ""
DATA_SOURCE=$(echo "$LINEAGE" | jq -r '.[] | select(.step_name == "fetch_market_data") | .metadata.data_source')

if [ "$DATA_SOURCE" == "cache" ]; then
    echo -e "${GREEN}✅ SUCCESS: Workflow used CACHE (PostgreSQL) for data${NC}"
else
    echo -e "${YELLOW}⚠️  Data source: $DATA_SOURCE (expected: cache)${NC}"
fi

echo ""
echo "======================================================================"

