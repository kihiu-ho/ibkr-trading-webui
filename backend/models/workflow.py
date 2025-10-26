"""Workflow execution model for tracking strategy workflow runs."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from backend.models import Base
from datetime import datetime, timezone


class WorkflowExecution(Base):
    """
    Workflow execution tracking model.
    
    Tracks the execution of trading workflows/strategies, including:
    - Execution status (running, completed, failed)
    - Start and end times
    - Any errors that occurred
    - Associated strategy
    """
    __tablename__ = "workflow_executions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    workflow_id = Column(Integer, nullable=True, index=True)  # Optional workflow ID
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    
    # Execution status
    status = Column(String(50), nullable=False, index=True)  # 'running', 'completed', 'failed'
    
    # Timestamps
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error information
    error = Column(Text, nullable=True)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="workflow_executions")
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, strategy_id={self.strategy_id}, status={self.status})>"
    
    def to_dict(self):
        """Convert workflow execution to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "strategy_id": self.strategy_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }


# Create indexes for common queries
Index('idx_workflow_executions_strategy_status', WorkflowExecution.strategy_id, WorkflowExecution.status)
Index('idx_workflow_executions_started', WorkflowExecution.started_at.desc())

