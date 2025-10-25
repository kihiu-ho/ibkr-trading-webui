"""Workflow logging model."""
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base


class WorkflowLog(Base):
    """Workflow step logging model."""
    __tablename__ = "workflow_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False, index=True)
    step_name = Column(String(100), nullable=False)
    step_type = Column(String(50), nullable=False)  # fetch_data, ai_analysis, decision, order, etc.
    code = Column(String(50))
    conid = Column(Integer)
    input_data = Column(JSON, default={})
    output_data = Column(JSON, default={})
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    duration_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

