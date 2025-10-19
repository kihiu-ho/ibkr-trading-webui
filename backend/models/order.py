"""Order model."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base


class Order(Base):
    """Order tracking model."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Integer, ForeignKey("decisions.id"))
    ibkr_order_id = Column(String(100), index=True)
    conid = Column(Integer, nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Integer, nullable=False)
    price = Column(Float)
    order_type = Column(String(10), nullable=False)  # LMT, MKT
    tif = Column(String(10), nullable=False)  # GTC, DAY
    status = Column(String(50), nullable=False, index=True)  # submitted, filled, cancelled, rejected
    filled_price = Column(Float)
    filled_quantity = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    decision = relationship("Decision", back_populates="orders")
    trades = relationship("Trade", back_populates="order")

