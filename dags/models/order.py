"""
Order Pydantic models
"""
from typing import Optional
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime
from decimal import Decimal


class OrderType(str, Enum):
    """Order type"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(str, Enum):
    """Order side"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """Order status"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Order(BaseModel):
    """Trading order"""
    
    symbol: str = Field(..., description="Stock symbol")
    side: OrderSide = Field(..., description="Order side (BUY/SELL)")
    quantity: int = Field(..., gt=0, description="Number of shares")
    order_type: OrderType = Field(default=OrderType.MARKET, description="Order type")
    
    # Pricing
    limit_price: Optional[Decimal] = Field(None, gt=0, description="Limit price (for LIMIT orders)")
    stop_price: Optional[Decimal] = Field(None, gt=0, description="Stop price (for STOP orders)")
    
    # Status
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")
    order_id: Optional[str] = Field(None, description="Exchange order ID")
    
    # Execution
    filled_quantity: int = Field(default=0, ge=0, description="Filled quantity")
    average_fill_price: Optional[Decimal] = Field(None, description="Average fill price")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Order creation time")
    submitted_at: Optional[datetime] = Field(None, description="Order submission time")
    filled_at: Optional[datetime] = Field(None, description="Order fill time")
    
    # Signal reference
    signal_id: Optional[str] = Field(None, description="Trading signal ID that generated this order")
    
    @validator('filled_quantity')
    def filled_must_not_exceed_quantity(cls, v, values):
        """Ensure filled quantity doesn't exceed order quantity"""
        if 'quantity' in values and v > values['quantity']:
            raise ValueError('filled_quantity cannot exceed quantity')
        return v
    
    @validator('limit_price')
    def limit_price_required_for_limit_orders(cls, v, values):
        """Ensure limit price is set for LIMIT orders"""
        if 'order_type' in values:
            if values['order_type'] in [OrderType.LIMIT, OrderType.STOP_LIMIT] and v is None:
                raise ValueError(f'{values["order_type"]} orders require limit_price')
        return v
    
    @validator('stop_price')
    def stop_price_required_for_stop_orders(cls, v, values):
        """Ensure stop price is set for STOP orders"""
        if 'order_type' in values:
            if values['order_type'] in [OrderType.STOP, OrderType.STOP_LIMIT] and v is None:
                raise ValueError(f'{values["order_type"]} orders require stop_price')
        return v
    
    @property
    def is_filled(self) -> bool:
        """Check if order is fully filled"""
        return self.status == OrderStatus.FILLED and self.filled_quantity == self.quantity
    
    @property
    def is_partially_filled(self) -> bool:
        """Check if order is partially filled"""
        return self.filled_quantity > 0 and self.filled_quantity < self.quantity
    
    @property
    def remaining_quantity(self) -> int:
        """Get remaining unfilled quantity"""
        return self.quantity - self.filled_quantity
    
    @property
    def total_value(self) -> Optional[Decimal]:
        """Get total value of the order (if filled)"""
        if self.average_fill_price and self.filled_quantity > 0:
            return self.average_fill_price * Decimal(self.filled_quantity)
        return None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat(),
        }

