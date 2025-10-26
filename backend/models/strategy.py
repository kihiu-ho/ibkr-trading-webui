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
    description = Column(String(500), nullable=True)
    
    # Symbol Configuration
    symbol_conid = Column(Integer, nullable=True, index=True)  # IBKR contract ID
    
    # Strategy Type and Parameters
    type = Column(String(50))  # e.g., "trend_following", "mean_reversion"
    param = Column(JSON)  # Strategy-specific parameters
    risk_params = Column(JSON)  # Risk management: position_size, stop_loss_pct, etc.
    
    # LLM Configuration
    llm_enabled = Column(Integer, default=1)  # 0 = disabled, 1 = enabled
    llm_model = Column(String(50), default="gpt-4-vision-preview")
    llm_language = Column(String(5), default="en")  # en or zh
    llm_timeframes = Column(JSON)  # List of timeframes: ["1d", "1w"]
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=True)
    
    # Scheduling
    schedule = Column(String(100), nullable=True)  # Cron expression: "0 9 * * *"
    last_executed_at = Column(DateTime(timezone=True), nullable=True)
    next_execution_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    codes = relationship("Code", secondary=StrategyCode, back_populates="strategies")
    indicators = relationship("Indicator", secondary="strategy_indicators", back_populates="strategies")
    signals = relationship("TradingSignal", back_populates="strategy")
    prompt_templates = relationship("PromptTemplate", back_populates="strategy")
    prompt_performances = relationship("PromptPerformance", back_populates="strategy")
    decisions = relationship("Decision", back_populates="strategy")
    workflow_executions = relationship("WorkflowExecution", back_populates="strategy")
    
    def to_dict(self):
        """Convert strategy to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "symbol_conid": self.symbol_conid,
            "type": self.type,
            "param": self.param,
            "risk_params": self.risk_params,
            "llm_enabled": bool(self.llm_enabled),
            "llm_model": self.llm_model,
            "llm_language": self.llm_language,
            "llm_timeframes": self.llm_timeframes,
            "prompt_template_id": self.prompt_template_id,
            "schedule": self.schedule,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None,
            "next_execution_at": self.next_execution_at.isoformat() if self.next_execution_at else None,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Strategy(id={self.id}, name='{self.name}', active={bool(self.is_active)})>"


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

