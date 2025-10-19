"""Workflow database models."""
from sqlalchemy import Column, Integer, String, JSON, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base


class Workflow(Base):
    """Workflow definition model."""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)  # two_indicator, autogen_multi_agent, custom
    steps = Column(JSON, nullable=False)  # Array of step definitions
    default_params = Column(JSON)  # Default parameters
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    versions = relationship("WorkflowVersion", back_populates="workflow")
    executions = relationship("WorkflowExecution", back_populates="workflow")
    strategies = relationship("Strategy", back_populates="workflow")


class WorkflowVersion(Base):
    """Workflow version history."""
    __tablename__ = "workflow_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    steps = Column(JSON, nullable=False)
    default_params = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255))
    
    # Relationships
    workflow = relationship("Workflow", back_populates="versions")


class WorkflowExecution(Base):
    """Workflow execution tracking."""
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    task_id = Column(String(255))  # Celery task ID
    status = Column(String(50), nullable=False)  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    results = Column(JSON)  # Execution results
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    strategy = relationship("Strategy", back_populates="executions")
    agent_conversations = relationship("AgentConversation", back_populates="execution")

