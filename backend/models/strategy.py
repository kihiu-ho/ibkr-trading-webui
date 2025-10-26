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
    """
    Trading strategy model.
    
    Represents a complete automated trading strategy with:
    - Symbol selection (conid)
    - Indicator configuration
    - Prompt template for LLM analysis
    - Execution schedule (cron expression)
    - Risk parameters
    """
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    workflow_id = Column(Integer, nullable=True)
    type = Column(String(50))
    param = Column(JSON)
    active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    llm_enabled = Column(Integer, default=1)
    llm_model = Column(String(50), default="gpt-4-vision-preview")
    llm_language = Column(String(5), default="en")
    llm_timeframes = Column(JSON)
    llm_consolidate = Column(Integer, default=1)
    llm_prompt_custom = Column(String(500), nullable=True)
    
    # Relationships
    codes = relationship("Code", secondary=StrategyCode, back_populates="strategies")
    decisions = relationship("Decision", back_populates="strategy")
    workflow_executions = relationship("WorkflowExecution", back_populates="strategy")
    
    def to_dict(self):
        """Convert strategy to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "workflow_id": self.workflow_id,
            "type": self.type,
            "param": self.param,
            "active": bool(self.active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "llm_enabled": bool(self.llm_enabled),
            "llm_model": self.llm_model,
            "llm_language": self.llm_language,
            "llm_timeframes": self.llm_timeframes,
            "llm_consolidate": bool(self.llm_consolidate),
            "llm_prompt_custom": self.llm_prompt_custom,
        }
    
    def __repr__(self):
        return f"<Strategy(id={self.id}, name='{self.name}', active={bool(self.active)})>"


class Code(Base):
    """
    Financial instrument code model.
    
    Stores IBKR contract information for instruments used in strategies.
    This is the legacy model - new code should use the Symbol model.
    """
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

