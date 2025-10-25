"""Charts API endpoints for technical analysis visualization."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.models.indicator import Indicator, IndicatorChart
from backend.models.strategy import Code
from backend.models.market import MarketData
from backend.schemas.indicator import ChartGenerateRequest, ChartResponse
from backend.services.chart_service import ChartService
from backend.services.minio_service import MinIOService
from backend.services.ibkr_service import IBKRService
import pandas as pd

logger = logging.getLogger(__name__)

router = APIRouter()


async def fetch_ibkr_data(code: Code, request: ChartGenerateRequest, db: Session) -> pd.DataFrame:
    """
    Fetch historical market data from IBKR and cache it.
    
    Args:
        code: Code object with conid
        request: Chart generation request with period and frequency
        db: Database session
        
    Returns:
        DataFrame with OHLCV data
    """
    ibkr = IBKRService()
    
    # Map frequency to IBKR period and bar
    period_map = {
        '1D': ('1w', '1d'),
        '1W': ('1m', '1w'),
        '1M': ('3m', '1d'),
        '3M': ('6m', '1d'),
        '1Y': ('1y', '1d'),
    }
    
    period, bar = period_map.get(request.frequency, ('1y', '1d'))
    
    try:
        # Fetch from IBKR
        logger.info(f"Fetching {period}/{bar} data for conid {code.conid}")
        historical_data = await ibkr.get_historical_data(
            conid=code.conid,
            period=period,
            bar=bar
        )
        
        if not historical_data or 'data' not in historical_data:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data available for {code.symbol} from IBKR"
            )
        
        # Cache the data
        market_data = MarketData(
            conid=code.conid,
            period=period,
            bar=bar,
            data=historical_data
        )
        db.add(market_data)
        db.commit()
        
        # Convert to DataFrame
        bars = []
        for bar_data in historical_data['data']:
            bars.append({
                'date': pd.to_datetime(bar_data.get('t', 0), unit='ms'),
                'open': float(bar_data.get('o', 0)),
                'high': float(bar_data.get('h', 0)),
                'low': float(bar_data.get('l', 0)),
                'close': float(bar_data.get('c', 0)),
                'volume': int(bar_data.get('v', 0))
            })
        
        df = pd.DataFrame(bars).sort_values('date').tail(request.period)
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No valid bars received for {code.symbol}"
            )
        
        return df
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch IBKR data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch market data from IBKR: {str(e)}"
        )


@router.post("/generate", response_model=ChartResponse, status_code=201)
async def generate_chart(
    request: ChartGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a technical analysis chart with specified indicators.
    
    - **symbol**: Stock symbol (e.g., AAPL)
    - **indicator_ids**: List of indicator IDs to include
    - **period**: Number of data points (20-500)
    - **frequency**: Data frequency (1D, 1W, 1M, etc.)
    - **strategy_id**: Optional strategy ID to associate with
    """
    try:
        # Validate indicators exist
        indicators = db.query(Indicator).filter(
            Indicator.id.in_(request.indicator_ids)
        ).all()
        
        if len(indicators) != len(request.indicator_ids):
            raise HTTPException(
                status_code=404,
                detail="One or more indicators not found"
            )
        
        # Fetch market data
        # First check local database cache
        # Get the Code object for the symbol
        code = db.query(Code).filter(Code.symbol == request.symbol.upper()).first()
        
        if not code:
            # Try to fetch from IBKR
            logger.info(f"Symbol {request.symbol} not found in database, fetching from IBKR")
            try:
                ibkr = IBKRService()
                contracts = await ibkr.search_contracts(request.symbol)
                if contracts and len(contracts) > 0:
                    # Take the first stock contract
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
            except Exception as e:
                logger.error(f"Failed to fetch symbol from IBKR: {e}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Symbol {request.symbol} not found and could not be fetched from IBKR: {str(e)}"
                )
        
        # Now query market data using the conid
        market_data_query = db.query(MarketData).filter(
            MarketData.conid == code.conid
        ).order_by(desc(MarketData.created_at)).limit(request.period)
        
        cached_data = market_data_query.all()
        
        if len(cached_data) > 0:
            # Use cached data - data is stored in JSON field
            logger.info(f"Using cached market data for {request.symbol}")
            # Extract OHLCV data from JSON
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
            
            if len(all_bars) >= min(request.period, 20):
                df = pd.DataFrame(all_bars).sort_values('date').tail(request.period)
            else:
                # Not enough data, fetch from IBKR
                logger.info(f"Insufficient cached bars for {request.symbol}, fetching from IBKR")
                df = await fetch_ibkr_data(code, request, db)
        else:
            # Fetch from IBKR
            logger.info(f"No cached data for {request.symbol}, fetching from IBKR")
            df = await fetch_ibkr_data(code, request, db)
        
        # Generate chart
        chart_service = ChartService()
        jpeg_bytes, html_string = await chart_service.generate_chart(
            symbol=request.symbol,
            market_data=df,
            indicators_list=indicators,
            period=request.period,
            frequency=request.frequency
        )
        
        # Create database record first to get ID
        chart_record = IndicatorChart(
            strategy_id=request.strategy_id,
            symbol=request.symbol,
            indicator_ids=request.indicator_ids,
            period=request.period,
            frequency=request.frequency,
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            chart_metadata={
                'jpeg_size_kb': len(jpeg_bytes) / 1024,
                'html_size_kb': len(html_string.encode()) / 1024,
                'num_indicators': len(indicators),
                'indicator_names': [ind.name for ind in indicators]
            }
        )
        db.add(chart_record)
        db.commit()
        db.refresh(chart_record)
        
        # Upload to MinIO
        minio_service = MinIOService()
        jpeg_url, html_url = await minio_service.upload_chart(
            chart_jpeg=jpeg_bytes,
            chart_html=html_string,
            symbol=request.symbol,
            chart_id=chart_record.id
        )
        
        # Update URLs in database
        chart_record.chart_url_jpeg = jpeg_url
        chart_record.chart_url_html = html_url
        db.commit()
        db.refresh(chart_record)
        
        logger.info(f"Generated chart {chart_record.id} for {request.symbol}")
        
        return ChartResponse(
            id=chart_record.id,
            strategy_id=chart_record.strategy_id,
            symbol=chart_record.symbol,
            indicator_ids=chart_record.indicator_ids,
            period=chart_record.period,
            frequency=chart_record.frequency,
            chart_url_jpeg=chart_record.chart_url_jpeg,
            chart_url_html=chart_record.chart_url_html,
            metadata=chart_record.chart_metadata or {},
            generated_at=chart_record.generated_at,
            expires_at=chart_record.expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating chart: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating chart: {str(e)}"
        )


@router.get("", response_model=List[ChartResponse])
async def list_charts(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    strategy_id: Optional[int] = Query(None, description="Filter by strategy"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of charts to return"),
    db: Session = Depends(get_db)
):
    """
    List generated charts with optional filters.
    
    - **symbol**: Filter by stock symbol
    - **strategy_id**: Filter by strategy ID
    - **limit**: Maximum number of results (default 50)
    """
    try:
        query = db.query(IndicatorChart).order_by(desc(IndicatorChart.generated_at))
        
        if symbol:
            query = query.filter(IndicatorChart.symbol == symbol.upper())
        
        if strategy_id:
            query = query.filter(IndicatorChart.strategy_id == strategy_id)
        
        charts = query.limit(limit).all()
        
        return [
            ChartResponse(
                id=chart.id,
                strategy_id=chart.strategy_id,
                symbol=chart.symbol,
                indicator_ids=chart.indicator_ids,
                period=chart.period,
                frequency=chart.frequency,
                chart_url_jpeg=chart.chart_url_jpeg,
                chart_url_html=chart.chart_url_html,
                metadata=chart.chart_metadata or {},
                generated_at=chart.generated_at,
                expires_at=chart.expires_at
            )
            for chart in charts
        ]
        
    except Exception as e:
        logger.error(f"Error listing charts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing charts: {str(e)}"
        )


@router.get("/{chart_id}", response_model=ChartResponse)
async def get_chart(
    chart_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific chart by ID.
    
    - **chart_id**: Chart database ID
    """
    try:
        chart = db.query(IndicatorChart).filter(IndicatorChart.id == chart_id).first()
        
        if not chart:
            raise HTTPException(
                status_code=404,
                detail=f"Chart {chart_id} not found"
            )
        
        return ChartResponse(
            id=chart.id,
            strategy_id=chart.strategy_id,
            symbol=chart.symbol,
            indicator_ids=chart.indicator_ids,
            period=chart.period,
            frequency=chart.frequency,
            chart_url_jpeg=chart.chart_url_jpeg,
            chart_url_html=chart.chart_url_html,
            metadata=chart.chart_metadata or {},
            generated_at=chart.generated_at,
            expires_at=chart.expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chart {chart_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting chart: {str(e)}"
        )


@router.delete("/{chart_id}", status_code=204)
async def delete_chart(
    chart_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a chart and its associated files.
    
    - **chart_id**: Chart database ID
    """
    try:
        chart = db.query(IndicatorChart).filter(IndicatorChart.id == chart_id).first()
        
        if not chart:
            raise HTTPException(
                status_code=404,
                detail=f"Chart {chart_id} not found"
            )
        
        # Delete from MinIO
        if chart.chart_url_jpeg or chart.chart_url_html:
            minio_service = MinIOService()
            await minio_service.delete_chart(
                jpeg_url=chart.chart_url_jpeg or "",
                html_url=chart.chart_url_html or ""
            )
        
        # Delete from database
        db.delete(chart)
        db.commit()
        
        logger.info(f"Deleted chart {chart_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chart {chart_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting chart: {str(e)}"
        )


@router.post("/cleanup-expired", status_code=200)
async def cleanup_expired_charts(
    expiry_days: int = Query(30, ge=1, le=365, description="Delete charts older than this many days"),
    db: Session = Depends(get_db)
):
    """
    Clean up expired charts from database and MinIO.
    
    - **expiry_days**: Number of days to keep charts (default 30)
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=expiry_days)
        
        # Find expired charts
        expired_charts = db.query(IndicatorChart).filter(
            IndicatorChart.generated_at < cutoff_date
        ).all()
        
        # Delete from MinIO
        minio_service = MinIOService()
        for chart in expired_charts:
            if chart.chart_url_jpeg or chart.chart_url_html:
                await minio_service.delete_chart(
                    jpeg_url=chart.chart_url_jpeg or "",
                    html_url=chart.chart_url_html or ""
                )
        
        # Delete from database
        deleted_count = db.query(IndicatorChart).filter(
            IndicatorChart.generated_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} expired charts")
        
        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up expired charts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cleaning up expired charts: {str(e)}"
        )

