"""Workflow Symbol Model - Manage symbols for trading workflows"""
from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Time,
    UniqueConstraint,
    inspect,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.database import Base


class SymbolWorkflowLink(Base):
    """Association model linking symbols to workflows with specific scheduling config."""

    __tablename__ = "symbol_workflow_links"

    id = Column(Integer, primary_key=True, index=True)
    workflow_symbol_id = Column(
        Integer,
        ForeignKey("workflow_symbols.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_id = Column(
        Integer,
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
    )

    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    timezone = Column(String(64), nullable=False, default="America/New_York")
    session_start = Column(Time(timezone=False))
    session_end = Column(Time(timezone=False))
    allow_weekend = Column(Boolean, default=False, nullable=False)
    config = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("workflow_symbol_id", "workflow_id", name="uq_symbol_workflow_link"),
        Index("idx_symbol_workflow_links_symbol_priority", "workflow_symbol_id", "priority"),
    )

    workflow = relationship("Workflow", back_populates="workflow_links")
    symbol = relationship("WorkflowSymbol", back_populates="workflow_links")

    def format_time(self, value):
        return value.strftime("%H:%M") if value else None

    def to_dict(self) -> dict:
        workflow = self.workflow
        return {
            "link_id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_name": workflow.name if workflow else None,
            "workflow_is_active": workflow.is_active if workflow else None,
            "dag_id": workflow.dag_id if workflow else None,
            "is_active": self.is_active,
            "priority": self.priority,
            "timezone": self.timezone,
            "session_start": self.format_time(self.session_start),
            "session_end": self.format_time(self.session_end),
            "allow_weekend": bool(self.allow_weekend),
            "config": self.config,
        }


class WorkflowSymbol(Base):
    """Model for managing workflow symbols."""

    __tablename__ = "workflow_symbols"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, unique=True, index=True)
    name = Column(String(100))  # Company name
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    priority = Column(Integer, default=0)  # Global priority
    
    # Legacy fields (kept for backward compatibility or migration if needed, but effectively deprecated)
    workflow_type = Column(String(50), default="trading_signal")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    workflow_links = relationship(
        "SymbolWorkflowLink",
        back_populates="symbol",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SymbolWorkflowLink.priority",
    )
    workflows = relationship(
        "Workflow",
        secondary="symbol_workflow_links",
        viewonly=True,
        lazy="selectin",
        back_populates="linked_symbols",
    )

    def __repr__(self):
        return f"<WorkflowSymbol(symbol={self.symbol}, enabled={self.enabled})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "workflow_type": self.workflow_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "workflows": [
                link.to_dict()
                for link in self.workflow_links
                if link.workflow
            ],
        }


def ensure_workflow_symbol_schema(engine) -> None:
    """Ensure symbol_workflow_links table exists."""
    try:
        inspector = inspect(engine)
        if "symbol_workflow_links" not in inspector.get_table_names():
            SymbolWorkflowLink.__table__.create(engine)
    except Exception:
        pass
