"""Workflow model to back strategy workflow references."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.database import Base


class Workflow(Base):
    """Represents a logical workflow (Airflow DAG + metadata)."""

    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    dag_id = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    strategies = relationship("Strategy", back_populates="workflow")
    primary_symbols = relationship("WorkflowSymbol", back_populates="workflow")
    linked_symbols = relationship(
        "WorkflowSymbol",
        secondary="workflow_symbol_workflows",
        back_populates="workflows",
        lazy="selectin",
    )

    def to_dict(self) -> dict:
        """Serialize workflow metadata for APIs."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "dag_id": self.dag_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Workflow(id={self.id}, name={self.name})>"
