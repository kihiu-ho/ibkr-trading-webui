"""Position model."""
from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.sql import func
from backend.core.database import Base


class Position(Base):
    """Open position model."""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    conid = Column(Integer, nullable=False, unique=True, index=True)
    quantity = Column(Integer, nullable=False)
    average_cost = Column('avg_price', Float, nullable=False)  # Map to database column 'avg_price'
    current_price = Column('market_price', Float)  # Map to database column 'market_price'
    unrealized_pnl = Column(Float)
    realized_pnl = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Convert position to dictionary for API responses."""
        return {
            'id': self.id,
            'conid': self.conid,
            'quantity': self.quantity,
            'average_cost': self.average_cost,
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

