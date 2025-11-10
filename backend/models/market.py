"""Market data model."""
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base


class MarketData(Base):
    """Market data cache model."""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    conid = Column(Integer, ForeignKey("codes.conid"), nullable=False, index=True)
    period = Column(String(20), nullable=False)  # 1d, 1w, 1m, 1y
    bar = Column(String(20), nullable=False)  # 1min, 5min, 1h, 1d, 1w
    data = Column(JSON, nullable=False)  # OHLCV and indicators
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Note: Code model removed - relationship disabled
    # code = relationship("Code", back_populates="market_data")

