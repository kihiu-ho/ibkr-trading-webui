"""
Workflow Symbols API - Manage trading symbols for workflows
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
import re

from backend.core.database import get_db
from backend.models.workflow_symbol import WorkflowSymbol

router = APIRouter(prefix="/api/workflow-symbols", tags=["workflow-symbols"])


# Pydantic schemas
class WorkflowSymbolCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (uppercase)")
    name: Optional[str] = Field(None, max_length=100, description="Company name")
    enabled: bool = Field(True, description="Enable/disable symbol in workflows")
    priority: int = Field(0, description="Processing priority (higher first)")
    workflow_type: str = Field('trading_signal', description="Workflow type")
    config: Optional[dict] = Field(None, description="Symbol-specific configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "TSLA",
                "name": "Tesla Inc.",
                "enabled": True,
                "priority": 10,
                "workflow_type": "trading_signal",
                "config": {"position_size": 10}
            }
        }


class WorkflowSymbolUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    workflow_type: Optional[str] = None
    config: Optional[dict] = None


class WorkflowSymbolResponse(BaseModel):
    id: int
    symbol: str
    name: Optional[str]
    enabled: bool
    priority: int
    workflow_type: str
    config: Optional[dict]
    created_at: Optional[str]
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


# Validation
def validate_symbol(symbol: str) -> str:
    """Validate and normalize symbol format."""
    symbol = symbol.strip().upper()
    if not re.match(r'^[A-Z]{1,10}$', symbol):
        raise HTTPException(
            status_code=400,
            detail="Symbol must be 1-10 uppercase letters only"
        )
    return symbol


# Endpoints
@router.get("/", response_model=List[WorkflowSymbolResponse])
def list_symbols(
    enabled_only: bool = Query(False, description="Filter by enabled symbols only"),
    workflow_type: Optional[str] = Query(None, description="Filter by workflow type"),
    db: Session = Depends(get_db)
):
    """List all workflow symbols."""
    query = db.query(WorkflowSymbol)
    
    if enabled_only:
        query = query.filter(WorkflowSymbol.enabled == True)
    
    if workflow_type:
        query = query.filter(WorkflowSymbol.workflow_type == workflow_type)
    
    symbols = query.order_by(WorkflowSymbol.priority.desc(), WorkflowSymbol.symbol).all()
    return [WorkflowSymbolResponse(**s.to_dict()) for s in symbols]


@router.post("/", response_model=WorkflowSymbolResponse, status_code=201)
def create_symbol(
    symbol_data: WorkflowSymbolCreate,
    db: Session = Depends(get_db)
):
    """Add a new symbol to workflows."""
    # Validate and normalize symbol
    symbol_data.symbol = validate_symbol(symbol_data.symbol)
    
    # Check if symbol already exists
    existing = db.query(WorkflowSymbol).filter(
        WorkflowSymbol.symbol == symbol_data.symbol
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Symbol {symbol_data.symbol} already exists"
        )
    
    # Create new symbol
    new_symbol = WorkflowSymbol(
        symbol=symbol_data.symbol,
        name=symbol_data.name,
        enabled=symbol_data.enabled,
        priority=symbol_data.priority,
        workflow_type=symbol_data.workflow_type,
        config=symbol_data.config
    )
    
    db.add(new_symbol)
    db.commit()
    db.refresh(new_symbol)
    
    return WorkflowSymbolResponse(**new_symbol.to_dict())


@router.get("/{symbol}", response_model=WorkflowSymbolResponse)
def get_symbol(symbol: str, db: Session = Depends(get_db)):
    """Get details of a specific symbol."""
    symbol = validate_symbol(symbol)
    
    db_symbol = db.query(WorkflowSymbol).filter(
        WorkflowSymbol.symbol == symbol
    ).first()
    
    if not db_symbol:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    return WorkflowSymbolResponse(**db_symbol.to_dict())


@router.patch("/{symbol}", response_model=WorkflowSymbolResponse)
def update_symbol(
    symbol: str,
    updates: WorkflowSymbolUpdate,
    db: Session = Depends(get_db)
):
    """Update symbol configuration (enable/disable, priority, etc)."""
    symbol = validate_symbol(symbol)
    
    db_symbol = db.query(WorkflowSymbol).filter(
        WorkflowSymbol.symbol == symbol
    ).first()
    
    if not db_symbol:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    # Update fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_symbol, field, value)
    
    db.commit()
    db.refresh(db_symbol)
    
    return WorkflowSymbolResponse(**db_symbol.to_dict())


@router.delete("/{symbol}", status_code=204)
def delete_symbol(symbol: str, db: Session = Depends(get_db)):
    """Remove a symbol from workflows."""
    symbol = validate_symbol(symbol)
    
    db_symbol = db.query(WorkflowSymbol).filter(
        WorkflowSymbol.symbol == symbol
    ).first()
    
    if not db_symbol:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    db.delete(db_symbol)
    db.commit()
    
    return None
