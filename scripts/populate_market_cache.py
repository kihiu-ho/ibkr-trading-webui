#!/usr/bin/env python3
"""
Populate Market Data Cache Script

Fetches historical market data from IBKR and stores it in the PostgreSQL database
for use in debug mode and to reduce API calls.

Usage:
    # Populate default symbols (NVDA, TSLA) with 1 year of data
    python scripts/populate_market_cache.py
    
    # Populate custom symbols
    python scripts/populate_market_cache.py --symbols AAPL MSFT GOOGL
    
    # Specify time period
    python scripts/populate_market_cache.py --symbols NVDA --days 90
    
    # Force refresh even if cached
    python scripts/populate_market_cache.py --refresh
"""
import argparse
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.database import SessionLocal
from backend.services.market_data_cache_service import MarketDataCacheService
from backend.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def populate_cache_for_symbol(
    cache_service: MarketDataCacheService,
    symbol: str,
    exchange: str,
    days: int,
    force_refresh: bool
):
    """Populate cache for a single symbol."""
    try:
        # Calculate period based on days
        if days <= 30:
            period = "1m"
        elif days <= 90:
            period = "3m"
        elif days <= 180:
            period = "6m"
        else:
            period = "1y"
        
        logger.info(f"📥 Fetching {symbol} ({exchange}) - {days} days (period: {period})")
        
        result = await cache_service.get_or_fetch_market_data(
            symbol=symbol,
            exchange=exchange,
            data_type="daily",
            timeframe="1d",
            period=period,
            force_refresh=force_refresh
        )
        
        data_points = len(result.get("data", {}).get("data", []))
        source = result.get("source", "unknown")
        
        logger.info(f"✅ {symbol}: Cached {data_points} data points (source: {source})")
        return {"symbol": symbol, "success": True, "data_points": data_points, "source": source}
        
    except Exception as e:
        logger.error(f"❌ {symbol}: Failed - {str(e)}")
        return {"symbol": symbol, "success": False, "error": str(e)}


async def main():
    parser = argparse.ArgumentParser(
        description="Populate market data cache from IBKR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Default symbols (NVDA, TSLA)
  %(prog)s --symbols AAPL MSFT                # Custom symbols
  %(prog)s --days 90                          # Last 90 days
  %(prog)s --exchange NYSE --symbols IBM      # Specify exchange
  %(prog)s --refresh                          # Force refresh cache
        """
    )
    
    parser.add_argument(
        '--symbols',
        nargs='+',
        help=f'Symbols to cache (default: {settings.CACHE_SYMBOLS})'
    )
    parser.add_argument(
        '--exchange',
        default=settings.CACHE_EXCHANGE,
        help=f'Exchange name (default: {settings.CACHE_EXCHANGE})'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days of historical data (default: 365)'
    )
    parser.add_argument(
        '--refresh',
        action='store_true',
        help='Force refresh even if cached'
    )
    
    args = parser.parse_args()
    
    # Use provided symbols or default from settings
    symbols = args.symbols if args.symbols else settings.CACHE_SYMBOLS
    
    logger.info("=" * 60)
    logger.info("Market Data Cache Population")
    logger.info("=" * 60)
    logger.info(f"Symbols: {', '.join(symbols)}")
    logger.info(f"Exchange: {args.exchange}")
    logger.info(f"Days: {args.days}")
    logger.info(f"Force Refresh: {args.refresh}")
    logger.info(f"Cache TTL: {settings.CACHE_TTL_HOURS} hours")
    logger.info("=" * 60)
    
    # Create database session
    db = SessionLocal()
    try:
        cache_service = MarketDataCacheService(db)
        
        # Show current cache stats
        stats = cache_service.get_cache_stats()
        logger.info(f"Current cache: {stats['active_entries']} entries, {stats['unique_symbols']} symbols")
        logger.info("")
        
        # Populate cache for each symbol
        results = []
        for symbol in symbols:
            result = await populate_cache_for_symbol(
                cache_service=cache_service,
                symbol=symbol,
                exchange=args.exchange,
                days=args.days,
                force_refresh=args.refresh
            )
            results.append(result)
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("Summary")
        logger.info("=" * 60)
        
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        logger.info(f"✅ Successful: {len(successful)}/{len(results)}")
        for r in successful:
            logger.info(f"   {r['symbol']}: {r['data_points']} points ({r['source']})")
        
        if failed:
            logger.info(f"❌ Failed: {len(failed)}/{len(results)}")
            for r in failed:
                logger.info(f"   {r['symbol']}: {r['error']}")
        
        # Updated cache stats
        stats = cache_service.get_cache_stats()
        logger.info("")
        logger.info(f"Cache now has: {stats['active_entries']} entries, {stats['unique_symbols']} symbols")
        logger.info("=" * 60)
        
        # Exit code based on results
        sys.exit(0 if len(failed) == 0 else 1)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

