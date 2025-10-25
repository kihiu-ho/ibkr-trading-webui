"""Technical analysis API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.schemas.analysis import (
    AnalysisRequest,
    ComprehensiveAnalysis
)
from backend.services.analysis_service import AnalysisService
from backend.services.ibkr_service import IBKRService
from backend.services.chart_service import ChartService
from backend.services.minio_service import MinIOService
from backend.models.strategy import Code
from backend.models.market import MarketData
from backend.models.indicator import Indicator
import pandas as pd
import logging
from sqlalchemy import desc
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=ComprehensiveAnalysis, status_code=201)
async def generate_analysis(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive technical analysis for a symbol.
    
    This endpoint:
    - Fetches market data from IBKR or cache
    - Calculates all technical indicators
    - Performs 3/4 signal confirmation
    - Generates trade recommendations with R-multiples
    - Returns detailed Chinese analysis report
    """
    try:
        logger.info(f"Generating analysis for {request.symbol}")
        
        # Get or fetch the symbol's Code
        code = db.query(Code).filter(Code.symbol == request.symbol.upper()).first()
        
        if not code:
            # Try to fetch from IBKR
            logger.info(f"Symbol {request.symbol} not found in database, fetching from IBKR")
            ibkr = IBKRService()
            contracts = await ibkr.search_contracts(request.symbol)
            if contracts and len(contracts) > 0:
                contract = next((c for c in contracts if c.get('assetClass') == 'STK'), contracts[0])
                code = Code(
                    symbol=request.symbol.upper(),
                    conid=contract.get('conid'),
                    exchange=contract.get('exchange', ''),
                    name=contract.get('description', request.symbol)
                )
                db.add(code)
                db.commit()
                db.refresh(code)
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Symbol {request.symbol} not found in IBKR"
                )
        
        # Get market data
        market_data_query = db.query(MarketData).filter(
            MarketData.conid == code.conid
        ).order_by(desc(MarketData.created_at)).limit(request.period)
        
        cached_data = market_data_query.all()
        
        # Convert to DataFrame
        if len(cached_data) > 0:
            logger.info(f"Using cached market data for {request.symbol}")
            all_bars = []
            for item in cached_data:
                if item.data and 'data' in item.data:
                    for bar in item.data['data']:
                        all_bars.append({
                            'date': pd.to_datetime(bar.get('t', 0), unit='ms'),
                            'open': float(bar.get('o', 0)),
                            'high': float(bar.get('h', 0)),
                            'low': float(bar.get('l', 0)),
                            'close': float(bar.get('c', 0)),
                            'volume': int(bar.get('v', 0))
                        })
            
            if len(all_bars) < 50:
                # Not enough data, fetch from IBKR
                logger.info(f"Insufficient cached data for {request.symbol}, fetching from IBKR")
                df = await fetch_ibkr_data(code, request, db)
            else:
                df = pd.DataFrame(all_bars).sort_values('date').tail(request.period)
        else:
            # Fetch from IBKR
            logger.info(f"No cached data for {request.symbol}, fetching from IBKR")
            df = await fetch_ibkr_data(code, request, db)
        
        if df.empty or len(df) < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient market data for {request.symbol}. Need at least 50 data points."
            )
        
        # Generate comprehensive analysis
        analysis_service = AnalysisService()
        analysis = await analysis_service.generate_comprehensive_analysis(
            symbol=request.symbol.upper(),
            market_data=df,
            period=request.period,
            timeframe=request.timeframe,
            language=request.language
        )
        
        # Generate chart visualization (reference: reference/webapp/services/chart_service.py)
        try:
            chart_service = ChartService()
            minio_service = MinIOService()
            
            # Get indicators used in analysis (matching the 7-panel reference layout)
            indicators_list = _get_analysis_indicators(db)
            
            # Generate chart with same indicators as analysis
            jpeg_bytes, html_string = await chart_service.generate_chart(
                symbol=request.symbol.upper(),
                market_data=df,
                indicators_list=indicators_list,
                period=request.period,
                frequency=request.timeframe
            )
            
            # Upload chart to MinIO
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            
            # Upload JPEG
            jpeg_key = f"charts/{request.symbol.upper()}/{timestamp}_{unique_id}_analysis.jpg"
            chart_url_jpeg = minio_service.upload_file(
                file_content=jpeg_bytes,
                object_name=jpeg_key,
                content_type="image/jpeg"
            )
            
            # Upload HTML
            html_key = f"charts/{request.symbol.upper()}/{timestamp}_{unique_id}_analysis.html"
            chart_url_html = minio_service.upload_file(
                file_content=html_string.encode('utf-8'),
                object_name=html_key,
                content_type="text/html"
            )
            
            # Add chart URLs to analysis
            analysis.chart_url_jpeg = chart_url_jpeg
            analysis.chart_url_html = chart_url_html
            
            logger.info(f"Generated and uploaded chart for {request.symbol}")
            
        except Exception as e:
            # Chart generation failure shouldn't break analysis
            logger.warning(f"Failed to generate chart for {request.symbol}: {e}")
            analysis.chart_url_jpeg = None
            analysis.chart_url_html = None
        
        logger.info(f"Successfully generated analysis for {request.symbol}")
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating analysis for {request.symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analysis: {str(e)}"
        )


async def fetch_ibkr_data(code: Code, request: AnalysisRequest, db: Session) -> pd.DataFrame:
    """Fetch historical data from IBKR and cache it."""
    ibkr = IBKRService()
    
    # Map timeframe
    period_map = {
        "1d": "1y",
        "1w": "5y",
        "1m": "10y"
    }
    period = period_map.get(request.timeframe, "1y")
    
    try:
        history = await ibkr.get_historical_data(
            conid=code.conid,
            period=period,
            bar=request.timeframe
        )
        
        if not history or 'data' not in history:
            raise Exception("No historical data returned from IBKR")
        
        # Cache the data
        market_data = MarketData(
            conid=code.conid,
            period=period,
            bar=request.timeframe,
            data=history
        )
        db.add(market_data)
        db.commit()
        
        # Convert to DataFrame
        bars = []
        for bar in history['data']:
            bars.append({
                'date': pd.to_datetime(bar.get('t', 0), unit='ms'),
                'open': float(bar.get('o', 0)),
                'high': float(bar.get('h', 0)),
                'low': float(bar.get('l', 0)),
                'close': float(bar.get('c', 0)),
                'volume': int(bar.get('v', 0))
            })
        
        df = pd.DataFrame(bars).sort_values('date')
        logger.info(f"Fetched and cached {len(df)} bars for {code.symbol}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching IBKR data: {e}")
        raise


def _get_analysis_indicators(db: Session):
    """Get or create standard indicators for analysis charts.
    
    Creates indicators matching the 7-panel layout from:
    reference/webapp/services/chart_service.py
    """
    # Define standard indicators for analysis
    standard_indicators = [
        ("SuperTrend (10,3)", "SuperTrend", {"period": 10, "multiplier": 3}),
        ("SMA 20", "MA", {"period": 20, "ma_type": "SMA", "source": "close"}),
        ("SMA 50", "MA", {"period": 50, "ma_type": "SMA", "source": "close"}),
        ("SMA 200", "MA", {"period": 200, "ma_type": "SMA", "source": "close"}),
        ("Bollinger Bands (20,2)", "BB", {"period": 20, "std_dev": 2, "source": "close"}),
        ("MACD (12,26,9)", "MACD", {"fast_period": 12, "slow_period": 26, "signal_period": 9}),
        ("RSI (14)", "RSI", {"period": 14, "overbought": 70, "oversold": 30}),
        ("ATR (14)", "ATR", {"period": 14}),
    ]
    
    indicators_list = []
    for name, ind_type, params in standard_indicators:
        # Check if indicator exists
        indicator = db.query(Indicator).filter(
            Indicator.name == name,
            Indicator.type == ind_type
        ).first()
        
        if not indicator:
            # Create indicator
            indicator = Indicator(
                name=name,
                type=ind_type,
                parameters=params
            )
            db.add(indicator)
            db.commit()
            db.refresh(indicator)
        
        indicators_list.append(indicator)
    
    return indicators_list


@router.get("/health")
async def health_check():
    """Health check endpoint for analysis service."""
    return {
        "status": "healthy",
        "service": "technical-analysis",
        "version": "1.0.0",
        "chart_reference": "reference/webapp/services/chart_service.py"
    }

