"""
Workflow Symbol Model - Manage symbols for trading workflows
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from backend.core.database import Base


class WorkflowSymbol(Base):
    """Model for managing workflow symbols."""
    
    __tablename__ = "workflow_symbols"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, unique=True, index=True)
    name = Column(String(100))  # Company name
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    priority = Column(Integer, default=0)  # Higher priority runs first
    workflow_type = Column(String(50), default='trading_signal')
    config = Column(JSON)  # Symbol-specific configuration
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<WorkflowSymbol(symbol={self.symbol}, enabled={self.enabled})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'enabled': self.enabled,
            'priority': self.priority,
            'workflow_type': self.workflow_type,
            'config': self.config,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
