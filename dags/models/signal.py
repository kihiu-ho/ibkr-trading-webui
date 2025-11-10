"""
Trading signal Pydantic models
"""
from typing import Optional
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime
from decimal import Decimal


class SignalAction(str, Enum):
    """Trading signal action"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalConfidence(str, Enum):
    """Signal confidence level"""
    HIGH = "HIGH"      # 80-100%
    MEDIUM = "MEDIUM"  # 50-79%
    LOW = "LOW"        # 0-49%


class TradingSignal(BaseModel):
    """LLM-generated trading signal"""
    
    symbol: str = Field(..., description="Stock symbol")
    action: SignalAction = Field(..., description="Trading action (BUY/SELL/HOLD)")
    confidence: SignalConfidence = Field(..., description="Confidence level")
    confidence_score: Decimal = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    
    # Reasoning
    reasoning: str = Field(..., min_length=10, description="LLM reasoning for the signal")
    key_factors: list[str] = Field(default_factory=list, description="Key factors influencing the decision")
    
    # Technical analysis
    trend: Optional[str] = Field(None, description="Identified trend (bullish/bearish/neutral)")
    support_level: Optional[Decimal] = Field(None, description="Identified support level")
    resistance_level: Optional[Decimal] = Field(None, description="Identified resistance level")
    
    # Risk management
    suggested_entry_price: Optional[Decimal] = Field(None, description="Suggested entry price")
    suggested_stop_loss: Optional[Decimal] = Field(None, description="Suggested stop loss")
    suggested_take_profit: Optional[Decimal] = Field(None, description="Suggested take profit")
    r_multiple: Optional[Decimal] = Field(None, description="R-multiple (risk/reward ratio)")
    position_size_percent: Optional[Decimal] = Field(None, description="Suggested position size as percentage")
    
    # Metadata
    timeframe_analyzed: str = Field(..., description="Timeframe analyzed (daily/weekly/both)")
    model_used: str = Field(..., description="LLM model used (gpt-4o/claude-3.5-sonnet)")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Signal generation timestamp")
    
    @validator('confidence_score')
    def validate_confidence_matches_level(cls, v, values):
        """Ensure confidence score matches confidence level"""
        if 'confidence' in values:
            conf = values['confidence']
            if conf == SignalConfidence.HIGH and v < 80:
                raise ValueError('HIGH confidence requires score >= 80')
            if conf == SignalConfidence.MEDIUM and (v < 50 or v >= 80):
                raise ValueError('MEDIUM confidence requires score 50-79')
            if conf == SignalConfidence.LOW and v >= 50:
                raise ValueError('LOW confidence requires score < 50')
        return v
    
    @property
    def is_actionable(self) -> bool:
        """Check if signal is actionable (not HOLD and confidence >= MEDIUM)"""
        return (
            self.action != SignalAction.HOLD
            and self.confidence in [SignalConfidence.HIGH, SignalConfidence.MEDIUM]
        )
    
    @property
    def risk_reward_ratio(self) -> Optional[Decimal]:
        """Calculate risk/reward ratio (returns r_multiple if available, otherwise calculates)"""
        if self.r_multiple is not None:
            return self.r_multiple
        if all([self.suggested_entry_price, self.suggested_stop_loss, self.suggested_take_profit]):
            risk = abs(self.suggested_entry_price - self.suggested_stop_loss)
            reward = abs(self.suggested_take_profit - self.suggested_entry_price)
            if risk > 0:
                return reward / risk
        return None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat(),
        }

