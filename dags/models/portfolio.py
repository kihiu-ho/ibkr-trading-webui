"""
Portfolio Pydantic models
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class Position(BaseModel):
    """Single portfolio position"""
    
    symbol: str = Field(..., description="Stock symbol")
    quantity: int = Field(..., description="Position size (negative for short)")
    average_cost: Decimal = Field(..., gt=0, description="Average cost basis per share")
    current_price: Decimal = Field(..., gt=0, description="Current market price")
    
    # Calculated fields
    market_value: Decimal = Field(..., description="Current market value")
    unrealized_pnl: Decimal = Field(..., description="Unrealized profit/loss")
    unrealized_pnl_percent: Decimal = Field(..., description="Unrealized P&L percentage")
    
    # Metadata
    first_acquired: Optional[datetime] = Field(None, description="First acquisition date")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    @property
    def is_long(self) -> bool:
        """Check if this is a long position"""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if this is a short position"""
        return self.quantity < 0
    
    @property
    def cost_basis(self) -> Decimal:
        """Get total cost basis"""
        return self.average_cost * Decimal(abs(self.quantity))
    
    @property
    def is_profitable(self) -> bool:
        """Check if position is currently profitable"""
        return self.unrealized_pnl > 0
    
    class Config:
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat(),
        }


class Portfolio(BaseModel):
    """Complete portfolio snapshot"""
    
    account_id: str = Field(..., description="Account ID")
    positions: List[Position] = Field(default_factory=list, description="Current positions")
    
    # Cash and totals
    cash_balance: Decimal = Field(..., ge=0, description="Cash balance")
    total_market_value: Decimal = Field(..., ge=0, description="Total market value of positions")
    total_value: Decimal = Field(..., ge=0, description="Total account value (cash + positions)")
    
    # Performance
    total_unrealized_pnl: Decimal = Field(default=Decimal(0), description="Total unrealized P&L")
    total_realized_pnl: Optional[Decimal] = Field(None, description="Total realized P&L (if tracked)")
    
    # Metadata
    snapshot_time: datetime = Field(default_factory=datetime.utcnow, description="Portfolio snapshot time")
    currency: str = Field(default="USD", description="Account currency")
    
    @property
    def position_count(self) -> int:
        """Get number of positions"""
        return len(self.positions)
    
    @property
    def positions_by_symbol(self) -> Dict[str, Position]:
        """Get positions indexed by symbol"""
        return {pos.symbol: pos for pos in self.positions}
    
    @property
    def long_positions(self) -> List[Position]:
        """Get all long positions"""
        return [pos for pos in self.positions if pos.is_long]
    
    @property
    def short_positions(self) -> List[Position]:
        """Get all short positions"""
        return [pos for pos in self.positions if pos.is_short]
    
    @property
    def largest_position(self) -> Optional[Position]:
        """Get largest position by market value"""
        if not self.positions:
            return None
        return max(self.positions, key=lambda p: abs(p.market_value))
    
    @property
    def cash_percentage(self) -> Decimal:
        """Get percentage of portfolio in cash"""
        if self.total_value > 0:
            return (self.cash_balance / self.total_value) * Decimal(100)
        return Decimal(100)
    
    @property
    def is_profitable(self) -> bool:
        """Check if portfolio has net profit"""
        return self.total_unrealized_pnl > 0
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol"""
        return self.positions_by_symbol.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """Check if portfolio has a position in symbol"""
        return symbol in self.positions_by_symbol
    
    class Config:
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat(),
        }

