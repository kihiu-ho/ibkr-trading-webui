"""
Technical indicators Pydantic models
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal


class TechnicalIndicators(BaseModel):
    """Technical indicators calculated from market data"""
    
    # Moving Averages
    sma_20: Optional[List[Optional[Decimal]]] = Field(None, description="20-period Simple Moving Average")
    sma_50: Optional[List[Optional[Decimal]]] = Field(None, description="50-period Simple Moving Average")
    sma_200: Optional[List[Optional[Decimal]]] = Field(None, description="200-period Simple Moving Average")
    
    # RSI
    rsi_14: Optional[List[Optional[Decimal]]] = Field(None, description="14-period Relative Strength Index")
    
    # MACD
    macd_line: Optional[List[Optional[Decimal]]] = Field(None, description="MACD line")
    macd_signal: Optional[List[Optional[Decimal]]] = Field(None, description="MACD signal line")
    macd_histogram: Optional[List[Optional[Decimal]]] = Field(None, description="MACD histogram")
    
    # Bollinger Bands
    bb_upper: Optional[List[Optional[Decimal]]] = Field(None, description="Bollinger Bands upper band")
    bb_middle: Optional[List[Optional[Decimal]]] = Field(None, description="Bollinger Bands middle band (SMA 20)")
    bb_lower: Optional[List[Optional[Decimal]]] = Field(None, description="Bollinger Bands lower band")
    
    @property
    def has_sma(self) -> bool:
        """Check if SMAs are calculated"""
        return self.sma_20 is not None or self.sma_50 is not None or self.sma_200 is not None
    
    @property
    def has_rsi(self) -> bool:
        """Check if RSI is calculated"""
        return self.rsi_14 is not None
    
    @property
    def has_macd(self) -> bool:
        """Check if MACD is calculated"""
        return self.macd_line is not None
    
    @property
    def has_bollinger(self) -> bool:
        """Check if Bollinger Bands are calculated"""
        return self.bb_upper is not None
    
    @property
    def latest_rsi(self) -> Optional[Decimal]:
        """Get latest RSI value"""
        if self.rsi_14 and len(self.rsi_14) > 0:
            return self.rsi_14[-1]
        return None
    
    @property
    def is_rsi_overbought(self) -> bool:
        """Check if latest RSI indicates overbought (>70)"""
        rsi = self.latest_rsi
        return rsi is not None and rsi > Decimal('70')
    
    @property
    def is_rsi_oversold(self) -> bool:
        """Check if latest RSI indicates oversold (<30)"""
        rsi = self.latest_rsi
        return rsi is not None and rsi < Decimal('30')
    
    class Config:
        json_encoders = {
            Decimal: float,
        }

