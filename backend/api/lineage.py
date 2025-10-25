"""
Lineage API Endpoints
Provides REST APIs for querying workflow execution lineage
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.services.lineage_tracker import get_lineage_tracker
from backend.models.lineage import LineageRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/lineage", tags=["lineage"])


@router.get("/execution/{execution_id}")
async def get_execution_lineage(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete lineage for a workflow execution.
    
    Returns list of all steps with input/output data ordered by step number.
    
    Args:
        execution_id: Unique identifier for the execution
    
    Returns:
        {
            "execution_id": "strategy_123_2025-10-25T10:30:00",
            "steps": [...],
            "total_steps": 8,
            "has_errors": false
        }
    """
    tracker = get_lineage_tracker(db)
    
    try:
        lineage = await tracker.get_execution_lineage(execution_id)
        
        if not lineage:
            raise HTTPException(
                status_code=404,
                detail=f"No lineage found for execution_id: {execution_id}"
            )
        
        return {
            "execution_id": execution_id,
            "steps": [record.to_dict() for record in lineage],
            "total_steps": len(lineage),
            "has_errors": any(r.error is not None for r in lineage)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching execution lineage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch execution lineage")


@router.get("/execution/{execution_id}/step/{step_name}")
async def get_step_lineage(
    execution_id: str,
    step_name: str,
    db: Session = Depends(get_db)
):
    """
    Get lineage for a specific step in an execution.
    
    Args:
        execution_id: Unique identifier for the execution
        step_name: Name of the step (e.g., "llm_analysis")
    
    Returns:
        LineageRecord as dictionary
    """
    tracker = get_lineage_tracker(db)
    
    try:
        record = await tracker.get_step_lineage(execution_id, step_name)
        
        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"Step '{step_name}' not found in execution '{execution_id}'"
            )
        
        return record.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching step lineage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch step lineage")


@router.get("/strategy/{strategy_id}/recent")
async def get_recent_executions(
    strategy_id: int,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get recent execution IDs for a strategy.
    
    Args:
        strategy_id: Strategy ID
        limit: Maximum number of executions to return (1-100)
    
    Returns:
        {
            "strategy_id": 123,
            "executions": [
                {
                    "execution_id": "strategy_123_2025-10-25T10:30:00",
                    "executed_at": "2025-10-25T10:30:00",
                    "status": "completed",
                    "step_count": 8
                },
                ...
            ],
            "count": 10
        }
    """
    tracker = get_lineage_tracker(db)
    
    try:
        executions = await tracker.get_recent_executions(
            strategy_id=strategy_id,
            limit=limit
        )
        
        return {
            "strategy_id": strategy_id,
            "executions": executions,
            "count": len(executions)
        }
        
    except Exception as e:
        logger.error(f"Error fetching recent executions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch recent executions")


@router.get("/step/{step_name}/statistics")
async def get_step_statistics(
    step_name: str,
    strategy_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific step across executions.
    
    Args:
        step_name: Name of the step
        strategy_id: Optional strategy filter
        days: Number of days to include (1-365)
    
    Returns:
        {
            "step_name": "llm_analysis",
            "total_executions": 150,
            "success_count": 145,
            "error_count": 5,
            "success_rate": 0.967,
            "avg_duration_ms": 8932,
            "min_duration_ms": 5234,
            "max_duration_ms": 15678,
            "common_errors": [...]
        }
    """
    tracker = get_lineage_tracker(db)
    
    try:
        stats = await tracker.get_step_statistics(
            step_name=step_name,
            strategy_id=strategy_id,
            days=days
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching step statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch step statistics")


@router.get("/recent")
async def get_all_recent_executions(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get recent executions across all strategies.
    
    Args:
        limit: Maximum number of executions to return (1-100)
    
    Returns:
        List of recent execution info dictionaries
    """
    tracker = get_lineage_tracker(db)
    
    try:
        executions = await tracker.get_recent_executions(
            strategy_id=None,
            limit=limit
        )
        
        return {
            "executions": executions,
            "count": len(executions)
        }
        
    except Exception as e:
        logger.error(f"Error fetching recent executions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch recent executions")

