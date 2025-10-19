"""Strategy management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.strategy import Strategy
from backend.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyResponse
from backend.tasks.workflow_tasks import execute_trading_workflow
from typing import List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[StrategyResponse])
async def list_strategies(
    active: bool = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all strategies."""
    query = db.query(Strategy)
    if active is not None:
        query = query.filter(Strategy.active == active)
    strategies = query.offset(skip).limit(limit).all()
    return strategies


@router.post("", response_model=StrategyResponse, status_code=201)
async def create_strategy(strategy_data: StrategyCreate, db: Session = Depends(get_db)):
    """Create a new strategy."""
    # Check if strategy name already exists
    existing = db.query(Strategy).filter(Strategy.name == strategy_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Strategy name already exists")
    
    strategy = Strategy(
        name=strategy_data.name,
        code=strategy_data.code,
        workflow_id=strategy_data.workflow_id,
        param=strategy_data.param or {},
        active=strategy_data.active if strategy_data.active is not None else True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    logger.info(f"Strategy created: {strategy.id} - {strategy.name}")
    return strategy


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Get strategy by ID."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    strategy_data: StrategyUpdate,
    db: Session = Depends(get_db)
):
    """Update a strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Update fields
    update_data = strategy_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(strategy, field, value)
    
    strategy.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(strategy)
    
    logger.info(f"Strategy updated: {strategy.id}")
    return strategy


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Delete a strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    db.delete(strategy)
    db.commit()
    
    logger.info(f"Strategy deleted: {strategy_id}")
    return {"message": "Strategy deleted successfully"}


@router.post("/{strategy_id}/execute")
async def execute_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Execute trading workflow for a strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    if not strategy.active:
        raise HTTPException(status_code=400, detail="Strategy is not active")
    
    # Trigger Celery task
    task = execute_trading_workflow.delay(strategy_id)
    
    logger.info(f"Workflow execution triggered for strategy {strategy_id}, task_id: {task.id}")
    
    return {
        "message": "Workflow execution started",
        "strategy_id": strategy_id,
        "task_id": task.id
    }
