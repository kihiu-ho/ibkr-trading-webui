"""
Workflow API Endpoints
Provides REST APIs for workflow execution management
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.workflow import WorkflowExecution

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.get("/executions")
async def get_workflow_executions(
    strategy_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get workflow executions with optional filtering.
    
    Args:
        strategy_id: Optional strategy filter
        status: Optional status filter (running, completed, failed, stopped)
        limit: Maximum number of executions to return (1-100)
    
    Returns:
        {
            "executions": [...],
            "count": 20,
            "statistics": {
                "running": 2,
                "completed": 15,
                "failed": 3,
                "success_rate": 83.3
            }
        }
    """
    try:
        # Build query
        query = db.query(WorkflowExecution)
        
        if strategy_id:
            query = query.filter(WorkflowExecution.strategy_id == strategy_id)
        
        if status:
            query = query.filter(WorkflowExecution.status == status)
        
        # Order by most recent first
        query = query.order_by(WorkflowExecution.started_at.desc())
        
        # Get executions
        executions = query.limit(limit).all()
        
        # Calculate statistics
        all_executions = db.query(WorkflowExecution)
        if strategy_id:
            all_executions = all_executions.filter(WorkflowExecution.strategy_id == strategy_id)
        
        total_count = all_executions.count()
        running_count = all_executions.filter(WorkflowExecution.status == 'running').count()
        completed_count = all_executions.filter(WorkflowExecution.status == 'completed').count()
        failed_count = all_executions.filter(WorkflowExecution.status == 'failed').count()
        
        success_rate = (completed_count / total_count * 100) if total_count > 0 else 0
        
        return {
            "executions": [execution.to_dict() for execution in executions],
            "count": len(executions),
            "statistics": {
                "running": running_count,
                "completed": completed_count,
                "failed": failed_count,
                "success_rate": success_rate
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching workflow executions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch workflow executions")


@router.get("/executions/{execution_id}")
async def get_workflow_execution(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """
    Get details for a specific workflow execution.
    
    Args:
        execution_id: Unique identifier for the execution
    
    Returns:
        WorkflowExecution as dictionary
    """
    try:
        execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()
        
        if not execution:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow execution not found: {execution_id}"
            )
        
        return execution.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workflow execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch workflow execution")


@router.post("/execute")
async def execute_workflow(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Start a new workflow execution.

    Args:
        request: Dictionary containing strategy_id and optional parameters

    Returns:
        New WorkflowExecution as dictionary
    """
    try:
        strategy_id = request.get('strategy_id')
        if not strategy_id:
            raise HTTPException(status_code=400, detail="strategy_id is required")

        # Create new workflow execution
        execution = WorkflowExecution(
            strategy_id=strategy_id,
            status='running',
            started_at=datetime.now()
        )

        db.add(execution)
        db.commit()
        db.refresh(execution)

        # TODO: Start actual workflow execution in background
        # This would integrate with the workflow orchestration system

        return execution.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting workflow execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start workflow execution")


@router.get("/stats")
async def get_workflow_stats(
    db: Session = Depends(get_db)
):
    """
    Get workflow execution statistics.

    Returns:
        Statistics dictionary with counts and metrics
    """
    try:
        from datetime import datetime, timedelta

        today = datetime.now().date()

        # Get counts
        active_count = db.query(WorkflowExecution).filter(
            WorkflowExecution.status == 'running'
        ).count()

        completed_today = db.query(WorkflowExecution).filter(
            WorkflowExecution.status == 'completed',
            WorkflowExecution.completed_at >= today
        ).count()

        total_executions = db.query(WorkflowExecution).count()
        completed_executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.status == 'completed'
        ).count()

        success_rate = (completed_executions / total_executions * 100) if total_executions > 0 else 0

        # Get total signals (this would come from TradingSignal model)
        from backend.models.trading_signal import TradingSignal
        total_signals = db.query(TradingSignal).count()

        return {
            "activeWorkflows": active_count,
            "completedToday": completed_today,
            "successRate": round(success_rate, 1),
            "totalSignals": total_signals
        }

    except Exception as e:
        logger.error(f"Error getting workflow stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get workflow stats")


@router.post("/executions/{execution_id}/stop")
async def stop_workflow_execution(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """
    Stop a running workflow execution.

    Args:
        execution_id: Unique identifier for the execution

    Returns:
        Updated WorkflowExecution as dictionary
    """
    try:
        execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()

        if not execution:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow execution not found: {execution_id}"
            )

        if execution.status != 'running':
            raise HTTPException(
                status_code=400,
                detail=f"Cannot stop execution with status: {execution.status}"
            )

        # Update status to stopped
        execution.status = 'stopped'
        db.commit()
        db.refresh(execution)

        return execution.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping workflow execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to stop workflow execution")
