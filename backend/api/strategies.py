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
        workflow_id=strategy_data.workflow_id,
        param=strategy_data.param or {},
        active=1 if strategy_data.active else 0
    )
    
    # Associate symbols if provided
    if strategy_data.symbol_ids:
        from backend.models.strategy import Code
        codes = db.query(Code).filter(Code.id.in_(strategy_data.symbol_ids)).all()
        if len(codes) != len(strategy_data.symbol_ids):
            raise HTTPException(status_code=400, detail="One or more symbol IDs not found")
        strategy.codes = codes
    
    # Associate indicators if provided
    if strategy_data.indicator_ids:
        from backend.models.indicator import Indicator
        indicators = db.query(Indicator).filter(Indicator.id.in_(strategy_data.indicator_ids)).all()
        if len(indicators) != len(strategy_data.indicator_ids):
            raise HTTPException(status_code=400, detail="One or more indicator IDs not found")
        strategy.indicators = indicators
    
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    logger.info(f"Strategy created: {strategy.id} - {strategy.name} with {len(strategy.codes)} symbols and {len(strategy.indicators)} indicators")
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
    
    # Update basic fields
    update_data = strategy_data.dict(exclude_unset=True, exclude={'symbol_ids'})
    for field, value in update_data.items():
        if field == 'active':
            setattr(strategy, field, 1 if value else 0)
        else:
            setattr(strategy, field, value)
    
    # Update symbols if provided
    if strategy_data.symbol_ids is not None:
        from backend.models.strategy import Code
        codes = db.query(Code).filter(Code.id.in_(strategy_data.symbol_ids)).all()
        if len(codes) != len(strategy_data.symbol_ids):
            raise HTTPException(status_code=400, detail="One or more symbol IDs not found")
        strategy.codes = codes
    
    # Update indicators if provided
    if strategy_data.indicator_ids is not None:
        from backend.models.indicator import Indicator
        indicators = db.query(Indicator).filter(Indicator.id.in_(strategy_data.indicator_ids)).all()
        if len(indicators) != len(strategy_data.indicator_ids):
            raise HTTPException(status_code=400, detail="One or more indicator IDs not found")
        strategy.indicators = indicators
    
    db.commit()
    db.refresh(strategy)
    
    logger.info(f"Strategy updated: {strategy.id} - {strategy.name}")
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


@router.get("/{strategy_id}/executions")
async def get_strategy_executions(strategy_id: int, db: Session = Depends(get_db)):
    """Get workflow executions for a specific strategy."""
    try:
        from backend.models.workflow import WorkflowExecution

        executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.strategy_id == strategy_id
        ).order_by(WorkflowExecution.started_at.desc()).all()

        return [execution.to_dict() for execution in executions]

    except Exception as e:
        logger.error(f"Error fetching strategy executions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch strategy executions")


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


@router.post("/{strategy_id}/validate-params")
async def validate_strategy_parameters(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """Validate strategy parameters against business rules."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    errors = []
    warnings = []
    
    param = strategy.param or {}
    
    # Validate account_size
    account_size = param.get('account_size', 0)
    if account_size <= 0:
        errors.append("account_size must be greater than 0")
    elif account_size < 10000:
        warnings.append("account_size is very small, consider increasing for realistic trading")
    
    # Validate risk_per_trade
    risk_per_trade = param.get('risk_per_trade', 0)
    if not (0 < risk_per_trade <= 1):
        errors.append("risk_per_trade must be between 0 and 1 (0-100%)")
    elif risk_per_trade > 0.05:
        warnings.append("risk_per_trade is high (>5%), consider reducing for safer trading")
    
    # Validate min_r_coefficient
    min_r = param.get('min_r_coefficient', 0)
    if min_r <= 0:
        errors.append("min_r_coefficient must be greater than 0")
    elif min_r < 1.0:
        warnings.append("min_r_coefficient < 1.0 may result in poor risk/reward trades")
    
    # Validate min_profit_margin
    min_profit = param.get('min_profit_margin', 0)
    if min_profit < 0:
        errors.append("min_profit_margin must be >= 0")
    elif min_profit < 3:
        warnings.append("min_profit_margin < 3% may be too conservative")
    
    # Validate delay_between_symbols
    delay = param.get('delay_between_symbols', 60)
    if delay < 0:
        errors.append("delay_between_symbols must be >= 0")
    elif delay < 10:
        warnings.append("delay_between_symbols < 10s may trigger rate limits")
    
    # Validate AI/LLM parameters
    temperature = param.get('temperature', 0.7)
    if not (0 <= temperature <= 2):
        errors.append("temperature must be between 0 and 2")
    
    max_tokens = param.get('max_tokens', 4000)
    if not (1 <= max_tokens <= 32000):
        errors.append("max_tokens must be between 1 and 32000")
    
    # Check if codes/symbols are configured
    from backend.models.strategy import Code
    codes = db.query(Code).join(Code.strategies).filter(Strategy.id == strategy_id).all()
    if not codes:
        errors.append("No symbols/codes configured for this strategy")
    
    is_valid = len(errors) == 0
    
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "parameters": param,
        "symbols_count": len(codes) if codes else 0
    }
