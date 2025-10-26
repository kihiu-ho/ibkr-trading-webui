"""
Lineage Tracker Service
Tracks input/output of each step in workflow execution for complete traceability
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.models.lineage import LineageRecord

logger = logging.getLogger(__name__)


class LineageTracker:
    """
    Tracks input/output lineage for each step in the trading workflow.
    
    Usage:
        tracker = LineageTracker()
        await tracker.record_step(
            execution_id="strategy_123_2025-10-25T10:30:00",
            step_name="fetch_market_data",
            step_number=2,
            input_data={"symbol": "AAPL", "conid": 265598},
            output_data={"rows": 500, "latest_price": 175.23},
            duration_ms=1234
        )
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize LineageTracker.
        
        Args:
            db_session: SQLAlchemy session (if None, will use get_db())
        """
        self.db_session = db_session
    
    async def record_step(
        self,
        execution_id: str,
        step_name: str,
        step_number: int,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> LineageRecord:
        """
        Record a single workflow step with its input/output.
        
        Args:
            execution_id: Unique identifier for this workflow execution
            step_name: Name of the step (e.g., "chart_generation", "llm_analysis")
            step_number: Sequential order of this step (1, 2, 3...)
            input_data: Dictionary of input data for this step
            output_data: Dictionary of output data from this step
            metadata: Additional context (strategy_id, user_id, etc.)
            error: Error message if step failed
            duration_ms: Execution time in milliseconds
        
        Returns:
            LineageRecord object
        """
        try:
            # Get database session
            db = self.db_session or next(get_db())
            
            # Create lineage record
            record = LineageRecord(
                execution_id=execution_id,
                step_name=step_name,
                step_number=step_number,
                input_data=input_data,
                output_data=output_data,
                metadata=metadata or {},
                error=error,
                duration_ms=duration_ms,
                status="error" if error else "success",
                recorded_at=datetime.now()
            )
            
            # Save to database
            db.add(record)
            db.commit()
            db.refresh(record)
            
            logger.debug(
                f"Lineage recorded: execution_id={execution_id}, "
                f"step={step_number}:{step_name}, status={record.status}, "
                f"duration={duration_ms}ms"
            )
            
            return record
            
        except Exception as e:
            logger.error(f"Failed to record lineage: {e}", exc_info=True)
            # Don't raise - lineage recording should not block workflow
            return None
    
    async def get_execution_lineage(
        self,
        execution_id: str
    ) -> List[LineageRecord]:
        """
        Get complete lineage for a workflow execution.
        
        Args:
            execution_id: Unique identifier for the execution
        
        Returns:
            List of LineageRecord objects ordered by step_number
        """
        db = self.db_session or next(get_db())
        
        records = db.query(LineageRecord).filter(
            LineageRecord.execution_id == execution_id
        ).order_by(LineageRecord.step_number).all()
        
        return records
    
    async def get_step_lineage(
        self,
        execution_id: str,
        step_name: str
    ) -> Optional[LineageRecord]:
        """
        Get lineage for a specific step in an execution.
        
        Args:
            execution_id: Unique identifier for the execution
            step_name: Name of the step
        
        Returns:
            LineageRecord object or None
        """
        db = self.db_session or next(get_db())
        
        record = db.query(LineageRecord).filter(
            LineageRecord.execution_id == execution_id,
            LineageRecord.step_name == step_name
        ).first()
        
        return record
    
    async def get_recent_executions(
        self,
        strategy_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent execution IDs, optionally filtered by strategy.
        
        Args:
            strategy_id: Filter by strategy ID (from metadata)
            limit: Maximum number of executions to return
        
        Returns:
            List of execution info dictionaries
        """
        db = self.db_session or next(get_db())
        
        # Get unique execution IDs with their metadata
        query = db.query(LineageRecord).distinct(LineageRecord.execution_id)
        
        if strategy_id:
            # Filter by strategy_id in step_metadata
            query = query.filter(
                LineageRecord.step_metadata['strategy_id'].astext == str(strategy_id)
            )
        
        # Order by most recent first
        query = query.order_by(desc(LineageRecord.recorded_at)).limit(limit)
        
        records = query.all()
        
        # Build execution info
        executions = []
        for record in records:
            # Get execution summary
            exec_records = await self.get_execution_lineage(record.execution_id)
            
            has_errors = any(r.error is not None for r in exec_records)
            status = "error" if has_errors else "completed"
            
            executions.append({
                "execution_id": record.execution_id,
                "strategy_id": record.step_metadata.get("strategy_id") if record.step_metadata else None,
                "executed_at": record.recorded_at.isoformat(),
                "status": status,
                "step_count": len(exec_records)
            })
        
        return executions
    
    async def get_step_statistics(
        self,
        step_name: str,
        strategy_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get statistics for a specific step across executions.
        
        Args:
            step_name: Name of the step
            strategy_id: Optional strategy filter
            days: Number of days to include
        
        Returns:
            Dictionary with statistics (avg duration, success rate, etc.)
        """
        from datetime import timedelta
        from sqlalchemy import func
        
        db = self.db_session or next(get_db())
        
        # Calculate date threshold
        since = datetime.now() - timedelta(days=days)
        
        # Build query
        query = db.query(LineageRecord).filter(
            LineageRecord.step_name == step_name,
            LineageRecord.recorded_at >= since
        )
        
        if strategy_id:
            query = query.filter(
                LineageRecord.step_metadata['strategy_id'].astext == str(strategy_id)
            )
        
        records = query.all()
        
        if not records:
            return {
                "step_name": step_name,
                "total_executions": 0,
                "success_count": 0,
                "error_count": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0
            }
        
        # Calculate statistics
        success_count = sum(1 for r in records if r.status == "success")
        error_count = sum(1 for r in records if r.status == "error")
        durations = [r.duration_ms for r in records if r.duration_ms is not None]
        
        return {
            "step_name": step_name,
            "total_executions": len(records),
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": success_count / len(records) if records else 0.0,
            "avg_duration_ms": int(sum(durations) / len(durations)) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "common_errors": self._get_common_errors(records)
        }
    
    def _get_common_errors(self, records: List[LineageRecord], limit: int = 5) -> List[Dict[str, Any]]:
        """Get most common error messages from records."""
        from collections import Counter
        
        errors = [r.error for r in records if r.error]
        error_counts = Counter(errors)
        
        return [
            {"error": error, "count": count}
            for error, count in error_counts.most_common(limit)
        ]


# Singleton instance
_lineage_tracker = None


def get_lineage_tracker(db_session: Optional[Session] = None) -> LineageTracker:
    """
    Get singleton instance of LineageTracker.
    
    Args:
        db_session: Optional database session
    
    Returns:
        LineageTracker instance
    """
    global _lineage_tracker
    if _lineage_tracker is None or db_session is not None:
        _lineage_tracker = LineageTracker(db_session)
    return _lineage_tracker

