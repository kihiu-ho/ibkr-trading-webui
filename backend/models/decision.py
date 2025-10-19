"""Trading decision model."""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base


class Decision(Base):
    """Trading decision model."""
    __tablename__ = "decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    code_id = Column(Integer, ForeignKey("codes.id"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    type = Column(String(20), nullable=False)  # buy, sell, hold
    current_price = Column(Float, nullable=False)
    target_price = Column(Float)
    stop_loss = Column(Float)
    profit_margin = Column(Float)
    r_coefficient = Column(Float)
    analysis_text = Column(Text)  # AI-generated analysis
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    code = relationship("Code", back_populates="decisions")
    strategy = relationship("Strategy", back_populates="decisions")
    orders = relationship("Order", back_populates="decision")

