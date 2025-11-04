"""
Chart configuration and result Pydantic models
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class Timeframe(str, Enum):
    """Chart timeframe"""
    DAILY = "1D"
    WEEKLY = "1W"
    MONTHLY = "1M"


class ChartConfig(BaseModel):
    """Configuration for chart generation"""
    
    symbol: str = Field(..., description="Stock symbol")
    timeframe: Timeframe = Field(default=Timeframe.DAILY, description="Chart timeframe")
    lookback_periods: int = Field(default=60, gt=0, description="Number of periods to show")
    
    # Indicator flags
    include_sma: bool = Field(default=True, description="Include moving averages")
    include_rsi: bool = Field(default=True, description="Include RSI")
    include_macd: bool = Field(default=True, description="Include MACD")
    include_bollinger: bool = Field(default=True, description="Include Bollinger Bands")
    include_volume: bool = Field(default=True, description="Include volume subplot")
    
    # Chart styling
    width: int = Field(default=1920, gt=0, description="Chart width in pixels")
    height: int = Field(default=1080, gt=0, description="Chart height in pixels")
    style: str = Field(default="seaborn", description="Matplotlib style")
    
    # Colors
    up_color: str = Field(default="green", description="Up candle color")
    down_color: str = Field(default="red", description="Down candle color")
    
    class Config:
        use_enum_values = True


class ChartResult(BaseModel):
    """Result of chart generation"""
    
    symbol: str = Field(..., description="Stock symbol")
    timeframe: Timeframe = Field(..., description="Chart timeframe")
    file_path: str = Field(..., description="Path to generated PNG file")
    width: int = Field(..., description="Chart width")
    height: int = Field(..., description="Chart height")
    periods_shown: int = Field(..., description="Number of periods in the chart")
    indicators_included: List[str] = Field(default_factory=list, description="List of indicators included")
    
    @property
    def file_size_mb(self) -> float:
        """Get approximate file size in MB (estimate)"""
        # Rough estimate: PNG at 1920x1080 is ~0.5-2MB
        return (self.width * self.height) / (1920 * 1080) * 1.5
    
    class Config:
        use_enum_values = True

