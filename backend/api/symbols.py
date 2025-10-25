"""Symbol lookup and management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.strategy import Code
from backend.models.symbol import Symbol
from backend.services.symbol_service import SymbolService, get_symbol_service
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search")
async def search_symbols(
    query: str = Query(..., min_length=1, description="Symbol or company name to search"),
    limit: int = Query(default=10, le=50, description="Maximum results to return"),
    use_cache: bool = Query(default=True, description="Use cached results if available"),
    db: Session = Depends(get_db)
):
    """
    Search for symbols in IBKR with automatic caching.
    
    Results are cached for 7 days to reduce API calls.
    """
    try:
        service = get_symbol_service(db)
        results = await service.search_symbols(query, limit, use_cache)
        
        logger.info(f"Symbol search for '{query}' returned {len(results)} results")
        return {
            "query": query,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Symbol search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Symbol search failed: {str(e)}")


@router.get("/saved")
async def list_saved_symbols(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all saved symbols (Code entities)."""
    codes = db.query(Code).offset(skip).limit(limit).all()
    return codes


@router.get("/conid/{conid}")
async def get_symbol_by_conid(
    conid: int,
    refresh_if_stale: bool = Query(default=True, description="Refresh from IBKR if cache is stale"),
    db: Session = Depends(get_db)
):
    """
    Get symbol information by IBKR contract ID (conid).
    
    Uses cached data if available and fresh (< 7 days old).
    """
    try:
        service = get_symbol_service(db)
        symbol = await service.get_by_conid(conid, refresh_if_stale)
        
        if not symbol:
            raise HTTPException(status_code=404, detail=f"Symbol not found for conid {conid}")
        
        return symbol.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get symbol by conid {conid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get symbol: {str(e)}")


from pydantic import BaseModel

class SymbolSaveRequest(BaseModel):
    """Request model for saving a symbol."""
    symbol: str
    conid: int
    exchange: Optional[str] = None
    name: Optional[str] = None


@router.post("/save")
async def save_symbol(
    request: SymbolSaveRequest,
    db: Session = Depends(get_db)
):
    """Save a symbol to the database for future use."""
    # Check if already exists
    existing = db.query(Code).filter(Code.conid == request.conid).first()
    if existing:
        return existing
    
    code = Code(
        symbol=request.symbol,
        conid=request.conid,
        exchange=request.exchange,
        name=request.name
    )
    
    db.add(code)
    db.commit()
    db.refresh(code)
    
    logger.info(f"Saved symbol: {request.symbol} (conid: {request.conid})")
    return code


@router.delete("/{code_id}")
async def delete_symbol(code_id: int, db: Session = Depends(get_db)):
    """Delete a saved symbol."""
    code = db.query(Code).filter(Code.id == code_id).first()
    
    if not code:
        raise HTTPException(status_code=404, detail="Symbol not found")
    
    # Check if symbol is used by any strategies
    if code.strategies:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete symbol - it is used by {len(code.strategies)} strategy/strategies"
        )
    
    db.delete(code)
    db.commit()
    
    logger.info(f"Deleted symbol: {code.symbol} (ID: {code_id})")
    return {"message": "Symbol deleted successfully"}


@router.get("/symbol/{symbol_str}")
async def get_by_symbol(
    symbol_str: str,
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    db: Session = Depends(get_db)
):
    """
    Get symbol(s) by symbol string (e.g., "AAPL").
    
    May return multiple results if symbol trades on different exchanges.
    """
    try:
        service = get_symbol_service(db)
        symbols = await service.get_by_symbol(symbol_str, exchange)
        
        if not symbols:
            return {
                "symbol": symbol_str,
                "exchange": exchange,
                "count": 0,
                "results": []
            }
        
        return {
            "symbol": symbol_str,
            "exchange": exchange,
            "count": len(symbols),
            "results": [s.to_dict() for s in symbols]
        }
        
    except Exception as e:
        logger.error(f"Failed to get symbol '{symbol_str}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get symbol: {str(e)}")


class BatchCacheRequest(BaseModel):
    """Request model for batch caching symbols."""
    conids: List[int]


@router.post("/batch-cache")
async def batch_cache_symbols(
    request: BatchCacheRequest,
    db: Session = Depends(get_db)
):
    """
    Cache multiple symbols by conid in a single request.
    
    Useful for pre-loading symbols before strategy execution.
    """
    try:
        service = get_symbol_service(db)
        results = await service.batch_cache_symbols(request.conids)
        
        return {
            "requested": len(request.conids),
            "cached": len(results),
            "results": {conid: symbol.to_dict() for conid, symbol in results.items()}
        }
        
    except Exception as e:
        logger.error(f"Batch cache failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch cache failed: {str(e)}")


@router.post("/refresh-cache")
async def refresh_stale_cache(
    max_symbols: int = Query(default=100, le=1000, description="Max symbols to refresh"),
    db: Session = Depends(get_db)
):
    """
    Refresh stale cached symbols (> 7 days old).
    
    Run this periodically as a maintenance task.
    """
    try:
        service = get_symbol_service(db)
        refreshed = await service.refresh_stale_cache(max_symbols)
        
        return {
            "refreshed": refreshed,
            "max_requested": max_symbols
        }
        
    except Exception as e:
        logger.error(f"Cache refresh failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cache refresh failed: {str(e)}")


@router.get("/cache/stats")
async def get_cache_stats(db: Session = Depends(get_db)):
    """Get statistics about the symbol cache."""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    try:
        total = db.query(func.count(Symbol.id)).scalar()
        
        # Count by asset type
        by_asset_type = db.query(
            Symbol.asset_type,
            func.count(Symbol.id)
        ).group_by(Symbol.asset_type).all()
        
        # Count stale symbols (> 7 days)
        cutoff_date = datetime.now() - timedelta(days=7)
        stale = db.query(func.count(Symbol.id)).filter(
            Symbol.last_updated < cutoff_date
        ).scalar()
        
        # Count by exchange (top 10)
        by_exchange = db.query(
            Symbol.exchange,
            func.count(Symbol.id)
        ).group_by(Symbol.exchange).order_by(
            func.count(Symbol.id).desc()
        ).limit(10).all()
        
        return {
            "total_cached": total,
            "stale_count": stale,
            "by_asset_type": {asset_type: count for asset_type, count in by_asset_type if asset_type},
            "top_exchanges": {exchange: count for exchange, count in by_exchange if exchange}
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

