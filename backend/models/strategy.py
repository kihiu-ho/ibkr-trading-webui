"""Strategy and Code database models."""
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base


# Association table for many-to-many relationship
StrategyCode = Table(
    'strategy_codes',
    Base.metadata,
    Column('strategy_id', Integer, ForeignKey('strategies.id'), primary_key=True),
    Column('code_id', Integer, ForeignKey('codes.id'), primary_key=True)
)


class Strategy(Base):
    """Trading strategy model."""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    type = Column(String(50))  # Legacy: two_indicator, etc.
    param = Column(JSON)  # Strategy-specific parameters (overrides workflow defaults)
    active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    workflow = relationship("Workflow", back_populates="strategies")
    codes = relationship("Code", secondary=StrategyCode, back_populates="strategies")
    executions = relationship("WorkflowExecution", back_populates="strategy")
    decisions = relationship("Decision", back_populates="strategy")


class Code(Base):
    """Financial instrument code model."""
    __tablename__ = "codes"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    conid = Column(Integer, nullable=False, unique=True, index=True)
    exchange = Column(String(50))
    name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    strategies = relationship("Strategy", secondary=StrategyCode, back_populates="codes")
    market_data = relationship("MarketData", back_populates="code")
    decisions = relationship("Decision", back_populates="code")

