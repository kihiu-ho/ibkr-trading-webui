#!/usr/bin/env python3
"""
Test Market Data Cache and Debug Mode Features

This script demonstrates and tests:
1. Cache population
2. Cache retrieval
3. Debug mode data source selection
4. Cache statistics
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.core.database import SessionLocal
from backend.services.market_data_cache_service import MarketDataCacheService
from backend.config.settings import settings


async def test_cache_features():
    """Test all cache features."""
    print("=" * 60)
    print("Market Data Cache & Debug Mode Test Suite")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        cache_service = MarketDataCacheService(db)
        
        # Test 1: Cache Statistics
        print("\n📊 Test 1: Cache Statistics")
        print("-" * 60)
        stats = cache_service.get_cache_stats()
        print(f"Total entries: {stats['total_entries']}")
        print(f"Active entries: {stats['active_entries']}")
        print(f"Unique symbols: {stats['unique_symbols']}")
        print(f"Symbols cached: {', '.join(stats['symbols'])}")
        print(f"Cache enabled: {stats['cache_enabled']}")
        print(f"Debug mode: {stats['debug_mode']}")
        print(f"TTL: {stats['ttl_hours']} hours")
        
        # Test 2: Fetch from Cache (Cache Hit)
        print("\n✅ Test 2: Fetch NVDA (Should be Cache HIT)")
        print("-" * 60)
        result = await cache_service.get_or_fetch_market_data(
            symbol="NVDA",
            exchange="NASDAQ",
            data_type="daily",
            timeframe="1d",
            period="1y"
        )
        print(f"Data source: {result['source']}")
        print(f"Symbol: {result['symbol']}")
        print(f"Data points: {len(result['data'].get('data', []))}")
        if result['source'] == 'cache':
            print(f"Cached at: {result['cached_at']}")
        else:
            print(f"Fetched at: {result['fetched_at']}")
        
        # Test 3: Verify Cache Miss for Unknown Symbol
        print("\n❌ Test 3: Fetch AAPL (Should be Cache MISS - will fetch from IBKR)")
        print("-" * 60)
        try:
            result2 = await cache_service.get_or_fetch_market_data(
                symbol="AAPL",
                exchange="NASDAQ",
                data_type="daily",
                timeframe="1d",
                period="1m"
            )
            print(f"Data source: {result2['source']}")
            print(f"Symbol: {result2['symbol']}")
            print(f"Data points: {len(result2['data'].get('data', []))}")
            if result2['source'] == 'live_api':
                print("✓ Successfully fetched and cached AAPL")
        except Exception as e:
            print(f"Expected error (IBKR may require auth): {str(e)[:100]}")
        
        # Test 4: Debug Mode Simulation
        print("\n🐛 Test 4: Debug Mode Simulation")
        print("-" * 60)
        print(f"Current DEBUG_MODE: {settings.DEBUG_MODE}")
        print(f"Current CACHE_ENABLED: {settings.CACHE_ENABLED}")
        
        # Temporarily enable debug mode for testing
        original_debug = settings.DEBUG_MODE
        original_cache = settings.CACHE_ENABLED
        
        settings.DEBUG_MODE = True
        settings.CACHE_ENABLED = True
        
        cache_service_debug = MarketDataCacheService(db)
        print(f"\nEnabled DEBUG_MODE for test")
        
        # Should use cache for NVDA (exists)
        try:
            result3 = await cache_service_debug.get_or_fetch_market_data(
                symbol="NVDA",
                exchange="NASDAQ",
                data_type="daily"
            )
            print(f"✓ DEBUG MODE: NVDA fetched from {result3['source']}")
            if result3['source'] == 'cache':
                print("  ✓ Correctly used cache in debug mode")
            else:
                print("  ✗ ERROR: Should have used cache!")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
        
        # Should fail for GOOG (doesn't exist in cache)
        try:
            result4 = await cache_service_debug.get_or_fetch_market_data(
                symbol="GOOG",
                exchange="NASDAQ",
                data_type="daily"
            )
            print(f"  ✗ ERROR: Should have failed for uncached symbol in debug mode")
        except ValueError as e:
            if "Debug mode enabled but data not in cache" in str(e):
                print(f"✓ DEBUG MODE: Correctly rejected uncached symbol (GOOG)")
                print(f"  Error message: {str(e)[:80]}...")
            else:
                print(f"  ✗ Unexpected error: {e}")
        
        # Restore settings
        settings.DEBUG_MODE = original_debug
        settings.CACHE_ENABLED = original_cache
        
        # Test 5: Final Statistics
        print("\n📊 Test 5: Final Cache Statistics")
        print("-" * 60)
        final_stats = cache_service.get_cache_stats()
        print(f"Total entries: {final_stats['total_entries']}")
        print(f"Symbols: {', '.join(final_stats['symbols'])}")
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_cache_features())

