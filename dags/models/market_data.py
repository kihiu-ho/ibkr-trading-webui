"""
Market data Pydantic models
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class OHLCVBar(BaseModel):
    """Single OHLCV candlestick bar"""
    
    timestamp: datetime = Field(..., description="Bar timestamp")
    open: Decimal = Field(..., gt=0, description="Open price")
    high: Decimal = Field(..., gt=0, description="High price")
    low: Decimal = Field(..., gt=0, description="Low price")
    close: Decimal = Field(..., gt=0, description="Close price")
    volume: int = Field(..., ge=0, description="Trading volume")
    
    @validator('high')
    def high_must_be_highest(cls, v, values):
        """Ensure high is actually the highest price"""
        if 'open' in values and 'low' in values and 'close' in values:
            if v < values['low']:
                raise ValueError('high must be >= low')
        return v
    
    @validator('low')
    def low_must_be_lowest(cls, v, values):
        """Ensure low is actually the lowest price"""
        if 'open' in values:
            if v > values['open']:
                raise ValueError('low must be <= open')
        return v
    
    class Config:
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat(),
        }


class MarketData(BaseModel):
    """Market data for a symbol"""
    
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    exchange: str = Field(default="NASDAQ", description="Exchange (NASDAQ, NYSE, etc.)")
    bars: List[OHLCVBar] = Field(..., min_items=1, description="OHLCV bars")
    timeframe: str = Field(..., description="Timeframe (1D, 1W, etc.)")
    fetched_at: datetime = Field(default_factory=datetime.utcnow, description="Data fetch timestamp")
    
    @validator('symbol')
    def symbol_must_be_uppercase(cls, v):
        """Ensure symbol is uppercase"""
        return v.upper()
    
    @validator('bars')
    def bars_must_be_sorted(cls, v):
        """Ensure bars are sorted by timestamp"""
        if len(v) > 1:
            for i in range(1, len(v)):
                if v[i].timestamp <= v[i-1].timestamp:
                    raise ValueError('bars must be sorted by timestamp (ascending)')
        return v
    
    @property
    def latest_price(self) -> Decimal:
        """Get the latest close price"""
        return self.bars[-1].close if self.bars else Decimal(0)
    
    @property
    def bar_count(self) -> int:
        """Get number of bars"""
        return len(self.bars)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

