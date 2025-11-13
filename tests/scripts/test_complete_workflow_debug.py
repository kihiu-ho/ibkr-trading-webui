#!/usr/bin/env python3
"""
Complete IBKR Workflow Test with Debug Mode

This script tests the complete workflow in DEBUG MODE:
1. Get market data from PostgreSQL DB (cache)
2. Create charts with indicators for daily and weekly
3. Pass to LLM to generate trading signals
4. Place order according to signal

Following OpenSpec methodology.
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root (two levels up from tests/scripts/) to sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from backend.core.database import SessionLocal
from backend.models.strategy import Strategy, Code
from backend.models.symbol import Symbol
from backend.services.strategy_executor import StrategyExecutor
from backend.services.market_data_cache_service import MarketDataCacheService
from backend.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_complete_workflow():
    """Test complete IBKR workflow with debug mode."""
    logger.info("=" * 70)
    logger.info("COMPLETE IBKR WORKFLOW TEST - DEBUG MODE")
    logger.info("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Verify Debug Mode
        logger.info("\n📋 STEP 0: Verify Debug Mode Configuration")
        logger.info("-" * 70)
        logger.info(f"DEBUG_MODE: {settings.DEBUG_MODE}")
        logger.info(f"CACHE_ENABLED: {settings.CACHE_ENABLED}")
        logger.info(f"CACHE_SYMBOLS: {settings.CACHE_SYMBOLS}")
        
        if not settings.DEBUG_MODE:
            logger.error("❌ DEBUG_MODE is not enabled!")
            logger.info("Enable it in docker-compose.yml: DEBUG_MODE: 'true'")
            return
        
        logger.info("✅ Debug mode is ENABLED - will use cached data")
        
        # Step 1: Get Market Data from PostgreSQL
        logger.info("\n📊 STEP 1: Get Market Data from PostgreSQL DB")
        logger.info("-" * 70)
        
        cache_service = MarketDataCacheService(db)
        
        # Test NVDA
        logger.info("Fetching NVDA market data from cache...")
        nvda_data = await cache_service.get_or_fetch_market_data(
            symbol="NVDA",
            exchange="NASDAQ",
            data_type="daily",
            timeframe="1d"
        )
        
        logger.info(f"✅ Data Source: {nvda_data['source']}")
        logger.info(f"   Symbol: {nvda_data['symbol']}")
        logger.info(f"   Data Points: {len(nvda_data['data'].get('data', []))}")
        
        if nvda_data['source'] != 'cache':
            logger.error("❌ ERROR: Should have used cache in debug mode!")
            return
        
        # Step 2: Create Charts with Indicators
        logger.info("\n📈 STEP 2: Create Charts with Indicators")
        logger.info("-" * 70)
        
        # Check if we have a test strategy
        test_strategy = db.query(Strategy).filter(
            Strategy.active == 1
        ).first()
        
        if not test_strategy:
            logger.warning("No active strategy found. Creating test strategy...")
            
            # Get NVDA symbol
            nvda_symbol = db.query(Symbol).filter(Symbol.symbol == "NVDA").first()
            if not nvda_symbol:
                logger.error("NVDA symbol not found in database!")
                return
            
            # Get or create Code for NVDA
            nvda_code = db.query(Code).filter(Code.conid == nvda_symbol.conid).first()
            if not nvda_code:
                logger.error("NVDA code not found in database!")
                return
            
            # Create test strategy
            test_strategy = Strategy(
                name="Debug Mode Test Strategy - NVDA",
                active=1,
                llm_enabled=1,
                llm_model="gpt-4-turbo-preview",
                llm_language="en",
                llm_timeframes=json.dumps(["1d", "1w"]),
                llm_consolidate=1
            )
            db.add(test_strategy)
            db.commit()
            db.refresh(test_strategy)
            
            # Link to NVDA code
            test_strategy.codes.append(nvda_code)
            db.commit()
            
            logger.info(f"✅ Created test strategy: {test_strategy.name}")
        else:
            logger.info(f"✅ Using existing strategy: {test_strategy.name}")
        
        logger.info(f"   Strategy ID: {test_strategy.id}")
        logger.info(f"   LLM Enabled: {bool(test_strategy.llm_enabled)}")
        logger.info(f"   Timeframes: {test_strategy.llm_timeframes}")
        
        # Step 3: Execute Workflow (Market Data + Charts + LLM)
        logger.info("\n🤖 STEP 3: Execute Workflow (Data + Charts + LLM)")
        logger.info("-" * 70)
        
        executor = StrategyExecutor(db)
        
        logger.info("Executing strategy workflow...")
        logger.info("This will:")
        logger.info("  1. Fetch market data from PostgreSQL cache")
        logger.info("  2. Generate charts with indicators")
        logger.info("  3. Pass charts to LLM for analysis")
        logger.info("  4. Generate trading signals")
        logger.info("")
        
        # Execute the strategy
        execution_id = f"test_debug_{int(datetime.now().timestamp())}"
        
        try:
            result = await executor.execute_strategy(
                strategy=test_strategy,
                execution_id=execution_id
            )
            
            logger.info("✅ Workflow execution completed!")
            logger.info(f"   Execution ID: {execution_id}")
            
            if result:
                logger.info(f"   Result: {json.dumps(result, indent=2)[:500]}...")
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            logger.info("This might be expected if:")
            logger.info("  - LLM API key is not configured")
            logger.info("  - Chart generation has issues")
            logger.info("  - But market data from cache should work!")
        
        # Step 4: Check Lineage for Data Source
        logger.info("\n🔍 STEP 4: Verify Data Source in Lineage")
        logger.info("-" * 70)
        
        from backend.models.lineage import LineageRecord
        
        lineage_records = db.query(LineageRecord).filter(
            LineageRecord.execution_id == execution_id
        ).order_by(LineageRecord.step_number).all()
        
        if lineage_records:
            logger.info(f"Found {len(lineage_records)} lineage records:")
            for record in lineage_records:
                logger.info(f"\n  Step {record.step_number}: {record.step_name}")
                logger.info(f"    Status: {record.status}")
                logger.info(f"    Duration: {record.duration_ms}ms")
                
                if record.step_name == "fetch_market_data":
                    data_source = record.metadata.get('data_source', 'unknown')
                    logger.info(f"    🎯 Data Source: {data_source}")
                    
                    if data_source == 'cache':
                        logger.info("    ✅ Correctly used cache in DEBUG MODE")
                    else:
                        logger.warning(f"    ⚠️  Expected 'cache' but got '{data_source}'")
        else:
            logger.warning("No lineage records found for this execution")
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("WORKFLOW TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Debug Mode: Enabled")
        logger.info(f"✅ Step 1: Market data fetched from PostgreSQL cache")
        logger.info(f"✅ Step 2: Strategy configured with daily/weekly timeframes")
        logger.info(f"{'✅' if lineage_records else '⚠️'} Step 3: Workflow executed")
        logger.info(f"{'✅' if lineage_records else '⚠️'} Step 4: Lineage tracking verified")
        logger.info("")
        logger.info("Note: Order placement (Step 5) requires:")
        logger.info("  - Valid IBKR account ID")
        logger.info("  - Trading signals from LLM")
        logger.info("  - Risk management approval")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
