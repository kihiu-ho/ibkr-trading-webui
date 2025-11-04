"""
Trade execution Pydantic models
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class TradeExecution(BaseModel):
    """Single trade execution"""
    
    execution_id: str = Field(..., description="Execution ID from broker")
    order_id: str = Field(..., description="Related order ID")
    symbol: str = Field(..., description="Stock symbol")
    side: str = Field(..., description="Trade side (BUY/SELL)")
    
    # Execution details
    quantity: int = Field(..., gt=0, description="Executed quantity")
    price: Decimal = Field(..., gt=0, description="Execution price")
    commission: Decimal = Field(default=Decimal(0), ge=0, description="Commission paid")
    
    # Timing
    executed_at: datetime = Field(..., description="Execution timestamp")
    
    # Metadata
    exchange: Optional[str] = Field(None, description="Exchange where executed")
    liquidity: Optional[str] = Field(None, description="Liquidity (added/removed)")
    
    @property
    def total_cost(self) -> Decimal:
        """Get total cost including commission"""
        return (self.price * Decimal(self.quantity)) + self.commission
    
    @property
    def cost_per_share(self) -> Decimal:
        """Get cost per share including commission"""
        if self.quantity > 0:
            return self.total_cost / Decimal(self.quantity)
        return Decimal(0)
    
    class Config:
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat(),
        }


class Trade(BaseModel):
    """Aggregated trade (one or more executions)"""
    
    order_id: str = Field(..., description="Related order ID")
    symbol: str = Field(..., description="Stock symbol")
    side: str = Field(..., description="Trade side (BUY/SELL)")
    
    # Aggregated execution details
    total_quantity: int = Field(..., gt=0, description="Total executed quantity")
    average_price: Decimal = Field(..., gt=0, description="Average execution price")
    total_commission: Decimal = Field(default=Decimal(0), ge=0, description="Total commission")
    
    # Executions
    executions: list[TradeExecution] = Field(default_factory=list, description="Individual executions")
    
    # Timing
    first_execution_at: datetime = Field(..., description="First execution timestamp")
    last_execution_at: datetime = Field(..., description="Last execution timestamp")
    
    @property
    def total_value(self) -> Decimal:
        """Get total trade value (excluding commission)"""
        return self.average_price * Decimal(self.total_quantity)
    
    @property
    def total_cost(self) -> Decimal:
        """Get total cost (including commission)"""
        return self.total_value + self.total_commission
    
    @property
    def execution_count(self) -> int:
        """Get number of executions"""
        return len(self.executions)
    
    class Config:
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat(),
        }

