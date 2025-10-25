"""
API endpoints for LLM-based trading signal generation.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from backend.core.database import get_db
from backend.models.trading_signal import TradingSignal
from backend.models.strategy import Strategy
from backend.services.signal_generator import SignalGenerator
from pydantic import BaseModel

router = APIRouter()


# Pydantic schemas for API
class SignalGenerateRequest(BaseModel):
    """Request to generate a trading signal."""
    symbol: str
    strategy_id: Optional[int] = None
    timeframes: Optional[List[str]] = None
    force_regenerate: bool = False


class SignalBatchRequest(BaseModel):
    """Request to batch generate signals."""
    symbols: List[str]
    strategy_id: Optional[int] = None
    timeframes: Optional[List[str]] = None


class SignalResponse(BaseModel):
    """Trading signal response."""
    id: Optional[int] = None
    symbol: str
    signal_type: str
    trend: Optional[str] = None
    confidence: Optional[float] = None
    entry_price_low: Optional[float] = None
    entry_price_high: Optional[float] = None
    stop_loss: Optional[float] = None
    target_conservative: Optional[float] = None
    target_aggressive: Optional[float] = None
    r_multiple_conservative: Optional[float] = None
    r_multiple_aggressive: Optional[float] = None
    position_size_percent: Optional[float] = None
    confirmation_signals: Optional[dict] = None
    chart_url_daily: Optional[str] = None
    chart_url_weekly: Optional[str] = None
    generated_at: datetime
    status: str = "active"
    
    class Config:
        from_attributes = True


@router.post("/generate", response_model=SignalResponse)
async def generate_signal(
    request: SignalGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a trading signal for a symbol.
    
    - **symbol**: Stock symbol (e.g., TSLA)
    - **strategy_id**: Optional strategy ID to use settings from
    - **timeframes**: List of timeframes (default: ["1d", "1w"])
    - **force_regenerate**: Force new signal even if recent one exists
    """
    try:
        # Check if recent signal exists
        if not request.force_regenerate:
            recent_signal = db.query(TradingSignal).filter(
                TradingSignal.symbol == request.symbol,
                TradingSignal.status == "active",
                TradingSignal.generated_at > datetime.now() - timedelta(hours=24)
            ).order_by(TradingSignal.generated_at.desc()).first()
            
            if recent_signal:
                return SignalResponse.from_orm(recent_signal)
        
        # Get strategy settings if provided
        timeframes = request.timeframes
        
        if request.strategy_id:
            strategy = db.query(Strategy).filter(Strategy.id == request.strategy_id).first()
            if strategy and strategy.llm_enabled:
                timeframes = timeframes or strategy.llm_timeframes or ["1d", "1w"]
        
        # Generate signal
        generator = SignalGenerator()
        signal_data = await generator.generate_signal(
            symbol=request.symbol,
            timeframes=timeframes
        )
        
        # Save to database
        db_signal = TradingSignal(
            symbol=signal_data["symbol"],
            strategy_id=request.strategy_id,
            signal_type=signal_data["signal_type"],
            trend=signal_data.get("trend"),
            confidence=signal_data.get("confidence"),
            timeframe_primary=signal_data.get("timeframes", ["1d"])[0],
            timeframe_confirmation=signal_data.get("timeframes", ["1d", "1w"])[1] if len(signal_data.get("timeframes", [])) > 1 else None,
            entry_price_low=signal_data.get("entry_price_low"),
            entry_price_high=signal_data.get("entry_price_high"),
            stop_loss=signal_data.get("stop_loss"),
            target_conservative=signal_data.get("target_conservative"),
            target_aggressive=signal_data.get("target_aggressive"),
            r_multiple_conservative=signal_data.get("r_multiple_conservative"),
            r_multiple_aggressive=signal_data.get("r_multiple_aggressive"),
            position_size_percent=signal_data.get("position_size_percent"),
            confirmation_signals=signal_data.get("confirmation"),
            analysis_daily=signal_data.get("analysis_daily"),
            analysis_weekly=signal_data.get("analysis_weekly"),
            analysis_consolidated=signal_data.get("analysis_consolidated"),
            chart_url_daily=signal_data.get("chart_url_daily"),
            chart_url_weekly=signal_data.get("chart_url_weekly"),
            chart_html_daily=signal_data.get("chart_html_daily"),
            chart_html_weekly=signal_data.get("chart_html_weekly"),
            language="en",  # Always English
            model_used=signal_data.get("model_used"),
            provider=signal_data.get("provider"),
            generated_at=signal_data.get("generated_at"),
            expires_at=signal_data.get("expires_at"),
            status="active"
        )
        
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)
        
        return SignalResponse.from_orm(db_signal)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate signal: {str(e)}")


@router.post("/batch", response_model=dict)
async def batch_generate_signals(
    request: SignalBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Generate signals for multiple symbols in batch.
    
    - **symbols**: List of stock symbols
    - **strategy_id**: Optional strategy ID to use settings from
    - **timeframes**: List of timeframes (default: ["1d", "1w"])
    """
    try:
        # Get strategy settings if provided
        timeframes = request.timeframes
        
        if request.strategy_id:
            strategy = db.query(Strategy).filter(Strategy.id == request.strategy_id).first()
            if strategy and strategy.llm_enabled:
                timeframes = timeframes or strategy.llm_timeframes or ["1d", "1w"]
        
        # Generate signals
        generator = SignalGenerator()
        batch_result = await generator.batch_generate(
            symbols=request.symbols,
            timeframes=timeframes
        )
        
        # Save successful signals to database
        saved_signals = []
        for signal_data in batch_result["signals"]:
            db_signal = TradingSignal(
                symbol=signal_data["symbol"],
                strategy_id=request.strategy_id,
                signal_type=signal_data["signal_type"],
                trend=signal_data.get("trend"),
                confidence=signal_data.get("confidence"),
                # ... (same fields as above)
                status="active"
            )
            db.add(db_signal)
            saved_signals.append(signal_data["symbol"])
        
        db.commit()
        
        return {
            "total": batch_result["total"],
            "successful": batch_result["successful"],
            "failed": batch_result["failed"],
            "saved_signals": saved_signals,
            "errors": batch_result["errors"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {str(e)}")


@router.get("/{symbol}", response_model=SignalResponse)
async def get_latest_signal(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Get the latest active signal for a symbol.
    
    - **symbol**: Stock symbol
    """
    signal = db.query(TradingSignal).filter(
        TradingSignal.symbol == symbol.upper(),
        TradingSignal.status == "active"
    ).order_by(TradingSignal.generated_at.desc()).first()
    
    if not signal:
        raise HTTPException(status_code=404, detail=f"No active signal found for {symbol}")
    
    return SignalResponse.from_orm(signal)


@router.get("/history/all", response_model=List[SignalResponse])
async def get_signal_history(
    symbol: Optional[str] = Query(None),
    strategy_id: Optional[int] = Query(None),
    status: Optional[str] = Query("active"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """
    Get signal history with filters.
    
    - **symbol**: Filter by symbol (optional)
    - **strategy_id**: Filter by strategy (optional)
    - **status**: Filter by status (default: active)
    - **limit**: Maximum results (default: 100)
    - **offset**: Pagination offset (default: 0)
    """
    query = db.query(TradingSignal)
    
    if symbol:
        query = query.filter(TradingSignal.symbol == symbol.upper())
    if strategy_id:
        query = query.filter(TradingSignal.strategy_id == strategy_id)
    if status:
        query = query.filter(TradingSignal.status == status)
    
    signals = query.order_by(TradingSignal.generated_at.desc()).offset(offset).limit(limit).all()
    
    return [SignalResponse.from_orm(signal) for signal in signals]


@router.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint for signal service."""
    from backend.config.settings import settings
    
    return {
        "status": "healthy",
        "service": "trading-signals",
        "llm_provider": settings.LLM_VISION_PROVIDER,
        "llm_model": settings.LLM_VISION_MODEL,
        "api_key_configured": bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_key_here")
    }

