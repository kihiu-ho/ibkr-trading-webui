"""Workflow Symbol Model - Manage symbols for trading workflows"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Time,
    inspect,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.database import Base


WorkflowSymbolWorkflow = Table(
    "workflow_symbol_workflows",
    Base.metadata,
    Column(
        "workflow_symbol_id",
        Integer,
        ForeignKey("workflow_symbols.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "workflow_id",
        Integer,
        ForeignKey("workflows.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)


class WorkflowSymbol(Base):
    """Model for managing workflow symbols."""

    __tablename__ = "workflow_symbols"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, unique=True, index=True)
    name = Column(String(100))  # Company name
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    priority = Column(Integer, default=0)  # Higher priority runs first
    workflow_type = Column(String(50), default="trading_signal")
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="SET NULL"), index=True)
    timezone = Column(String(64), nullable=False, default="America/New_York")
    session_start = Column(Time(timezone=False))
    session_end = Column(Time(timezone=False))
    allow_weekend = Column(Boolean, default=False, nullable=False)
    config = Column(JSON)  # Symbol-specific configuration
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    workflow = relationship("Workflow", back_populates="primary_symbols")
    workflows = relationship(
        "Workflow",
        secondary="workflow_symbol_workflows",
        back_populates="linked_symbols",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<WorkflowSymbol(symbol={self.symbol}, enabled={self.enabled}, workflow_id={self.workflow_id})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "workflow_type": self.workflow_type,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow.name if self.workflow else None,
            "timezone": self.timezone,
            "session_start": self.session_start.isoformat() if self.session_start else None,
            "session_end": self.session_end.isoformat() if self.session_end else None,
            "allow_weekend": bool(self.allow_weekend),
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "workflows": [
                {
                    "id": workflow.id,
                    "name": workflow.name,
                    "is_active": bool(workflow.is_active),
                    "dag_id": workflow.dag_id,
                }
                for workflow in self.workflows or []
            ],
        }


def ensure_workflow_symbol_schema(engine) -> None:
    """Backfill workflow_symbols table with new scheduling columns if missing."""
    try:
        inspector = inspect(engine)
    except Exception:
        return

    if "workflow_symbols" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("workflow_symbols")}
    dialect = (engine.dialect.name or "").lower()
    statements = []

    def add_column(name: str, ddl: str) -> None:
        statements.append(f"ALTER TABLE workflow_symbols ADD COLUMN {name} {ddl}")

    if "workflow_id" not in existing:
        if dialect == "postgresql":
            add_column("workflow_id", "INTEGER REFERENCES workflows(id) ON DELETE SET NULL")
        else:
            add_column("workflow_id", "INTEGER")

    if "timezone" not in existing:
        default_clause = "DEFAULT 'America/New_York'"
        if dialect == "postgresql":
            add_column("timezone", f"VARCHAR(64) NOT NULL {default_clause}")
        else:
            add_column("timezone", f"TEXT NOT NULL {default_clause}")

    if "session_start" not in existing:
        add_column("session_start", "TIME")

    if "session_end" not in existing:
        add_column("session_end", "TIME")

    if "allow_weekend" not in existing:
        if dialect == "postgresql":
            add_column("allow_weekend", "BOOLEAN NOT NULL DEFAULT FALSE")
        else:
            add_column("allow_weekend", "BOOLEAN NOT NULL DEFAULT 0")

    if not statements:
        return

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
