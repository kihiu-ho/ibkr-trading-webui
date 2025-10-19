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
    average_cost = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

