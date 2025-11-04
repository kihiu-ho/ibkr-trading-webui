#!/usr/bin/env python3
"""
Populate Symbols and Codes Tables from Market Data Cache

This script reads cached market data and populates the symbols and codes tables
with the contract information, ensuring all cached symbols are also available
in the symbol/code lookup tables.

Usage:
    python scripts/populate_symbols_from_cache.py
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.database import SessionLocal
from backend.models.symbol import Symbol
from backend.models.strategy import Code
from backend.models.market_data_cache import MarketDataCache
from backend.services.ibkr_service import IBKRService
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def populate_symbols_and_codes():
    """Populate symbols and codes tables from market data cache."""
    logger.info("=" * 60)
    logger.info("Populating Symbols and Codes from Market Data Cache")
    logger.info("=" * 60)
    
    db = SessionLocal()
    ibkr = IBKRService()
    
    try:
        # Get all unique symbols from cache
        cached_data = db.query(MarketDataCache).filter(
            MarketDataCache.is_active == True
        ).all()
        
        if not cached_data:
            logger.warning("No data found in market_data_cache table")
            return
        
        logger.info(f"Found {len(cached_data)} entries in cache")
        
        # Group by symbol
        symbols_map = {}
        for entry in cached_data:
            if entry.symbol not in symbols_map:
                symbols_map[entry.symbol] = entry
        
        logger.info(f"Processing {len(symbols_map)} unique symbols")
        logger.info("")
        
        symbols_added = 0
        symbols_updated = 0
        codes_added = 0
        codes_updated = 0
        
        for symbol_name, cache_entry in symbols_map.items():
            logger.info(f"Processing {symbol_name}...")
            
            # Get additional details from IBKR if needed
            company_name = None
            currency = None
            asset_type = "STK"  # Default to stock
            
            if cache_entry.conid:
                try:
                    # Fetch contract details for complete information
                    contracts = await ibkr.search_contracts(symbol_name)
                    if contracts:
                        contract = contracts[0]
                        company_name = contract.get('companyName') or contract.get('name')
                        currency = contract.get('currency', 'USD')
                        asset_type = contract.get('assetClass') or contract.get('secType', 'STK')
                        
                        # Update conid if it was missing or different
                        if not cache_entry.conid or cache_entry.conid != contract.get('conid'):
                            cache_entry.conid = contract.get('conid')
                            db.commit()
                            logger.info(f"  Updated cache conid: {cache_entry.conid}")
                except Exception as e:
                    logger.warning(f"  Could not fetch contract details: {e}")
                    currency = "USD"  # Default
            
            # 1. Populate/Update symbols table
            existing_symbol = db.query(Symbol).filter(
                Symbol.conid == cache_entry.conid
            ).first() if cache_entry.conid else None
            
            if existing_symbol:
                existing_symbol.symbol = symbol_name
                existing_symbol.exchange = cache_entry.exchange
                existing_symbol.name = company_name or existing_symbol.name
                existing_symbol.currency = currency or existing_symbol.currency
                existing_symbol.asset_type = asset_type or existing_symbol.asset_type
                existing_symbol.last_updated = datetime.now()
                symbols_updated += 1
                logger.info(f"  ✓ Updated symbol: {symbol_name} (conid: {cache_entry.conid})")
            else:
                new_symbol = Symbol(
                    conid=cache_entry.conid or 0,  # Use 0 if conid not available
                    symbol=symbol_name,
                    name=company_name,
                    exchange=cache_entry.exchange,
                    currency=currency,
                    asset_type=asset_type,
                    last_updated=datetime.now()
                )
                db.add(new_symbol)
                symbols_added += 1
                logger.info(f"  ✓ Added symbol: {symbol_name} (conid: {cache_entry.conid})")
            
            # 2. Populate/Update codes table (legacy support)
            if cache_entry.conid:
                existing_code = db.query(Code).filter(
                    Code.conid == cache_entry.conid
                ).first()
                
                if existing_code:
                    existing_code.symbol = symbol_name
                    existing_code.exchange = cache_entry.exchange
                    existing_code.name = company_name or existing_code.name
                    codes_updated += 1
                    logger.info(f"  ✓ Updated code: {symbol_name}")
                else:
                    new_code = Code(
                        symbol=symbol_name,
                        conid=cache_entry.conid,
                        exchange=cache_entry.exchange,
                        name=company_name
                    )
                    db.add(new_code)
                    codes_added += 1
                    logger.info(f"  ✓ Added code: {symbol_name}")
        
        # Commit all changes
        db.commit()
        
        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("Summary")
        logger.info("=" * 60)
        logger.info(f"Symbols added: {symbols_added}")
        logger.info(f"Symbols updated: {symbols_updated}")
        logger.info(f"Codes added: {codes_added}")
        logger.info(f"Codes updated: {codes_updated}")
        
        # Verify
        total_symbols = db.query(Symbol).count()
        total_codes = db.query(Code).count()
        logger.info(f"\nTotal symbols in DB: {total_symbols}")
        logger.info(f"Total codes in DB: {total_codes}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(populate_symbols_and_codes())

