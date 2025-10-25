"""
Workflow Lineage Models
Tracks input/output of each step in workflow execution
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSONB
from sqlalchemy.sql import func
from backend.core.database import Base


class LineageRecord(Base):
    """Model for storing workflow execution lineage."""
    __tablename__ = "workflow_lineage"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(255), nullable=False, index=True)
    step_name = Column(String(100), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    input_data = Column(JSONB, nullable=False)
    output_data = Column(JSONB, nullable=False)
    metadata = Column(JSONB)
    error = Column(Text)
    status = Column(String(20), nullable=False, default='success', index=True)  # success, error
    duration_ms = Column(Integer)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "step_name": self.step_name,
            "step_number": self.step_number,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "metadata": self.metadata,
            "error": self.error,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }

    def __repr__(self):
        return f"<LineageRecord(execution_id='{self.execution_id}', step={self.step_number}, name='{self.step_name}', status='{self.status}')>"

