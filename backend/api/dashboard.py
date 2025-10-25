"""Dashboard API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from backend.core.database import get_db
from backend.models.strategy import Strategy
from backend.models.position import Position
from backend.models.order import Order
from backend.models.workflow import WorkflowExecution
from backend.models.decision import Decision
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get dashboard statistics."""
    
    # Count active strategies (active column is stored as integer: 1=True, 0=False)
    active_strategies = db.query(func.count(Strategy.id)).filter(
        Strategy.active == 1
    ).scalar() or 0
    
    # Count open positions
    open_positions = db.query(func.count(Position.id)).filter(
        Position.quantity != 0
    ).scalar() or 0
    
    # Count pending orders
    pending_orders = db.query(func.count(Order.id)).filter(
        Order.status.in_(['Submitted', 'PreSubmitted', 'PendingSubmit'])
    ).scalar() or 0
    
    # Count running workflow executions
    running_tasks = db.query(func.count(WorkflowExecution.id)).filter(
        WorkflowExecution.status == 'running'
    ).scalar() or 0
    
    # Get total trades count
    total_trades = db.query(func.count(Order.id)).filter(
        Order.status == 'Filled'
    ).scalar() or 0
    
    # Get recent decisions count
    recent_decisions = db.query(func.count(Decision.id)).scalar() or 0
    
    return {
        "active_strategies": active_strategies,
        "open_positions": open_positions,
        "pending_orders": pending_orders,
        "running_tasks": running_tasks,
        "total_trades": total_trades,
        "recent_decisions": recent_decisions
    }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent trading activity."""
    
    # Get recent orders
    recent_orders = db.query(Order).order_by(
        Order.created_at.desc()
    ).limit(limit).all()
    
    # Get recent workflow executions
    recent_executions = db.query(WorkflowExecution).order_by(
        WorkflowExecution.started_at.desc()
    ).limit(limit).all()
    
    return {
        "recent_orders": recent_orders,
        "recent_executions": recent_executions
    }

