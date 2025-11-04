#!/bin/bash

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "DATA PERSISTENCE DIAGNOSTIC & FIX"
echo "======================================================================"
echo ""

# Step 1: Check if database tables exist
echo -e "${BLUE}📋 STEP 1: Verify Database Tables${NC}"
echo "----------------------------------------------------------------------"

echo "Checking database tables..."
docker compose exec -T backend python << 'PYTHON_EOF'
from backend.core.database import engine
from sqlalchemy import inspect, text

inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"\n✅ Total tables in database: {len(tables)}")
print("\nTables found:")
for table in sorted(tables):
    print(f"  - {table}")

# Check specific tables
required_tables = ['charts', 'llm_analyses', 'strategies', 'symbols', 'codes', 'trading_signals']
missing = [t for t in required_tables if t not in tables]

if missing:
    print(f"\n❌ Missing tables: {', '.join(missing)}")
else:
    print(f"\n✅ All required tables exist")

# Check row counts
with engine.connect() as conn:
    for table in ['strategies', 'symbols', 'codes', 'charts', 'llm_analyses']:
        if table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table}: {count} rows")
PYTHON_EOF

echo ""

# Step 2: Check for strategies
echo -e "${BLUE}📊 STEP 2: Check Strategies${NC}"
echo "----------------------------------------------------------------------"

STRATEGIES=$(curl -s http://localhost:8000/api/strategies)
STRATEGY_COUNT=$(echo "$STRATEGIES" | jq '. | length')

echo "Strategies in database: $STRATEGY_COUNT"

if [ "$STRATEGY_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ No strategies found - creating test strategy${NC}"
    
    # Create a test strategy
    docker compose exec -T backend python << 'PYTHON_EOF'
from backend.core.database import SessionLocal
from backend.models.strategy import Strategy, Code
from sqlalchemy import text

db = SessionLocal()

try:
    # Check if strategy already exists
    existing = db.query(Strategy).filter(Strategy.name == "Test Workflow Strategy").first()
    
    if not existing:
        # Create strategy
        strategy = Strategy(
            name="Test Workflow Strategy",
            type="llm_analysis",
            param={"risk_level": "medium"},
            active=1,
            llm_enabled=1,
            llm_model="gpt-4-turbo-preview",
            llm_language="en",
            llm_timeframes=["1d", "1w"],
            llm_consolidate=1
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        print(f"✅ Created strategy: {strategy.name} (ID: {strategy.id})")
        
        # Add codes to strategy
        codes = db.query(Code).filter(Code.code.in_(["NVDA", "TSLA", "AAPL"])).all()
        if codes:
            strategy.codes = codes
            db.commit()
            print(f"✅ Added {len(codes)} codes to strategy")
        else:
            print("⚠️ No codes found to add to strategy")
    else:
        print(f"✅ Strategy already exists: {existing.name} (ID: {existing.id})")
        
except Exception as e:
    print(f"❌ Error creating strategy: {e}")
    db.rollback()
finally:
    db.close()
PYTHON_EOF
else
    echo -e "${GREEN}✅ Strategies found${NC}"
    echo "$STRATEGIES" | jq '.[] | {id, name, active}'
fi

echo ""

# Step 3: Check symbols and codes
echo -e "${BLUE}🔤 STEP 3: Check Symbols & Codes${NC}"
echo "----------------------------------------------------------------------"

docker compose exec -T backend python << 'PYTHON_EOF'
from backend.core.database import SessionLocal
from backend.models.symbol import Symbol
from backend.models.strategy import Code

db = SessionLocal()

try:
    symbols = db.query(Symbol).all()
    codes = db.query(Code).all()
    
    print(f"Symbols in database: {len(symbols)}")
    print(f"Codes in database: {len(codes)}")
    
    if len(symbols) > 0:
        print("\nSymbols:")
        for sym in symbols[:5]:
            print(f"  - {sym.symbol} (conid: {sym.conid})")
    
    if len(codes) > 0:
        print("\nCodes:")
        for code in codes[:5]:
            print(f"  - {code.code} (conid: {code.conid})")
    
    if len(symbols) == 0 or len(codes) == 0:
        print("\n⚠️ Running population scripts...")
        
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    db.close()
PYTHON_EOF

echo ""

# Step 4: Populate from cache if needed
echo -e "${BLUE}💾 STEP 4: Populate Data from Cache${NC}"
echo "----------------------------------------------------------------------"

echo "Running population scripts..."
docker compose exec -T backend python /app/scripts/populate_symbols_from_cache.py 2>&1 | tail -20

echo ""

# Step 5: Check cache data
echo -e "${BLUE}📦 STEP 5: Verify Market Data Cache${NC}"
echo "----------------------------------------------------------------------"

CACHE_STATS=$(curl -s http://localhost:8000/api/market-data/cache-stats)
echo "$CACHE_STATS" | jq '.'

echo ""

# Step 6: Test workflow execution
echo -e "${BLUE}🔄 STEP 6: Execute Test Workflow${NC}"
echo "----------------------------------------------------------------------"

# Get an active strategy
ACTIVE_STRATEGY=$(curl -s http://localhost:8000/api/strategies | jq -r '.[] | select(.active == 1) | .id' | head -n 1)

if [ -n "$ACTIVE_STRATEGY" ]; then
    echo "Executing strategy ID: $ACTIVE_STRATEGY"
    
    EXEC_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/strategies/$ACTIVE_STRATEGY/execute")
    echo "$EXEC_RESPONSE" | jq '.'
    
    TASK_ID=$(echo "$EXEC_RESPONSE" | jq -r '.task_id')
    
    if [ "$TASK_ID" != "null" ]; then
        echo ""
        echo "Waiting for workflow to complete (35 seconds)..."
        sleep 35
        
        # Check celery logs for errors
        echo ""
        echo "Checking celery worker logs..."
        docker logs ibkr-celery-worker --tail 50 | grep -E "ERROR|Failed|Saved chart|Saved LLM|chart_id|analysis_id" | tail -20
    fi
else
    echo -e "${RED}❌ No active strategy found${NC}"
fi

echo ""

# Step 7: Verify data was saved
echo -e "${BLUE}✅ STEP 7: Verify Data Persistence${NC}"
echo "----------------------------------------------------------------------"

echo "Checking charts..."
CHARTS=$(curl -s "http://localhost:8000/api/charts?limit=5")
CHART_COUNT=$(echo "$CHARTS" | jq -r '.total')
echo "Charts in database: $CHART_COUNT"

if [ "$CHART_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Charts successfully saved!${NC}"
    echo "$CHARTS" | jq '.charts[] | {id, symbol, timeframe, generated_at}'
else
    echo -e "${YELLOW}⚠️ No charts found yet${NC}"
fi

echo ""
echo "Checking LLM analyses..."
ANALYSES=$(curl -s "http://localhost:8000/api/llm-analyses?limit=5")
ANALYSIS_COUNT=$(echo "$ANALYSES" | jq -r '.total')
echo "LLM Analyses in database: $ANALYSIS_COUNT"

if [ "$ANALYSIS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ LLM Analyses successfully saved!${NC}"
    echo "$ANALYSES" | jq '.analyses[] | {id, symbol, timeframe, analyzed_at}'
else
    echo -e "${YELLOW}⚠️ No analyses found yet${NC}"
fi

echo ""

# Step 8: Summary
echo "======================================================================"
echo -e "${BLUE}📊 DIAGNOSTIC SUMMARY${NC}"
echo "======================================================================"

docker compose exec -T backend python << 'PYTHON_EOF'
from backend.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    with db.connection() as conn:
        print("\nFinal Row Counts:")
        for table in ['strategies', 'codes', 'symbols', 'charts', 'llm_analyses', 'trading_signals', 'workflow_executions']:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {table}: {count} rows")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
PYTHON_EOF

echo ""
echo "======================================================================"
echo -e "${GREEN}DIAGNOSTIC COMPLETE${NC}"
echo "======================================================================"
echo ""

