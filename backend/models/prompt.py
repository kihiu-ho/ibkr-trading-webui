"""
Prompt Template and Performance Models
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, ARRAY, Date, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base


class PromptTemplate(Base):
    """Model for storing configurable Jinja2 prompt templates."""
    
    __tablename__ = "prompt_templates"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template content
    prompt_text = Column(Text, nullable=False)  # Full Jinja2 template
    template_version = Column(Integer, nullable=False, default=1)
    
    # Categorization
    template_type = Column(String(50), nullable=False, default="analysis")  # analysis, consolidation, decision
    language = Column(String(5), nullable=False, default="en")  # en, zh
    
    # Strategy association (NULL = global default)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)
    
    # Metadata
    created_by = Column(String(100), nullable=True)
    tags = Column(ARRAY(String(255)), nullable=True)  # Array for categorization
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    strategy = relationship("Strategy", foreign_keys=[strategy_id])
    performance_records = relationship("PromptPerformance", back_populates="prompt_template", cascade="all, delete-orphan")
    signals = relationship("TradingSignal")
    
    # Table constraints
    __table_args__ = (
        # Ensure only one default per type+language+strategy combination
        # This is handled at the database level with DEFERRABLE constraint
    )
    
    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name='{self.name}', type='{self.template_type}', strategy_id={self.strategy_id})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "prompt_text": self.prompt_text,
            "template_version": self.template_version,
            "template_type": self.template_type,
            "language": self.language,
            "strategy_id": self.strategy_id,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "created_by": self.created_by,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_global(self):
        """Check if this is a global template (not strategy-specific)."""
        return self.strategy_id is None
    
    @property
    def scope(self):
        """Return scope description."""
        return "global" if self.is_global else f"strategy-{self.strategy_id}"


class PromptPerformance(Base):
    """Model for tracking prompt template performance metrics."""
    
    __tablename__ = "prompt_performance"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Prompt identification
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id", ondelete="CASCADE"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=True)
    
    # Time period
    date = Column(Date, nullable=False)
    
    # Signal counts
    signals_generated = Column(Integer, nullable=False, default=0)
    signals_executed = Column(Integer, nullable=False, default=0)
    
    # Financial metrics
    total_profit_loss = Column(DECIMAL(15, 2), nullable=True)
    
    # Win/Loss tracking
    win_count = Column(Integer, nullable=False, default=0)
    loss_count = Column(Integer, nullable=False, default=0)
    
    # R-Multiple statistics
    avg_r_multiple = Column(DECIMAL(10, 4), nullable=True)
    best_r_multiple = Column(DECIMAL(10, 4), nullable=True)
    worst_r_multiple = Column(DECIMAL(10, 4), nullable=True)
    
    # Percentage returns
    avg_profit_pct = Column(DECIMAL(10, 4), nullable=True)
    avg_loss_pct = Column(DECIMAL(10, 4), nullable=True)
    
    # Confidence metrics
    avg_confidence = Column(DECIMAL(5, 4), nullable=True)
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    prompt_template = relationship("PromptTemplate", back_populates="performance_records")
    strategy = relationship("Strategy")
    
    # Table constraints
    __table_args__ = (
        # Ensure one record per prompt+strategy+date
        # This is handled at the database level with UNIQUE constraint
    )
    
    def __repr__(self):
        return f"<PromptPerformance(id={self.id}, prompt={self.prompt_template_id}, date={self.date}, win_rate={self.win_rate:.2%})>"
    
    @property
    def win_rate(self):
        """Calculate win rate."""
        total = self.win_count + self.loss_count
        return self.win_count / total if total > 0 else 0.0
    
    @property
    def total_signals(self):
        """Total win + loss signals."""
        return self.win_count + self.loss_count
    
    @property
    def execution_rate(self):
        """Calculate execution rate."""
        return self.signals_executed / self.signals_generated if self.signals_generated > 0 else 0.0
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "prompt_template_id": self.prompt_template_id,
            "strategy_id": self.strategy_id,
            "date": self.date.isoformat() if self.date else None,
            "signals_generated": self.signals_generated,
            "signals_executed": self.signals_executed,
            "total_profit_loss": float(self.total_profit_loss) if self.total_profit_loss else None,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "win_rate": self.win_rate,
            "avg_r_multiple": float(self.avg_r_multiple) if self.avg_r_multiple else None,
            "best_r_multiple": float(self.best_r_multiple) if self.best_r_multiple else None,
            "worst_r_multiple": float(self.worst_r_multiple) if self.worst_r_multiple else None,
            "avg_profit_pct": float(self.avg_profit_pct) if self.avg_profit_pct else None,
            "avg_loss_pct": float(self.avg_loss_pct) if self.avg_loss_pct else None,
            "avg_confidence": float(self.avg_confidence) if self.avg_confidence else None,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

