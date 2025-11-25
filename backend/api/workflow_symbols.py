"""Workflow Symbols API - Manage trading symbols for workflows."""
import re
from datetime import time
from typing import List, Optional, Sequence, Set

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from pytz import UnknownTimeZoneError, timezone as pytz_timezone
from sqlalchemy.orm import Session, selectinload

from backend.core.database import get_db
from backend.models.workflow import Workflow
from backend.models.workflow_symbol import SymbolWorkflowLink, WorkflowSymbol

router = APIRouter(prefix="/api/workflow-symbols", tags=["workflow-symbols"])


class SymbolWorkflowConfig(BaseModel):
    """Configuration for a specific workflow linked to a symbol."""
    workflow_id: int
    is_active: bool = True
    timezone: str = "America/New_York"
    session_start: Optional[time] = None
    session_end: Optional[time] = None
    allow_weekend: bool = False
    config: Optional[dict] = None


class LinkedWorkflowSummary(BaseModel):
    """Workflow summary with link-specific configuration."""
    link_id: int
    workflow_id: int
    workflow_name: Optional[str]
    workflow_is_active: Optional[bool]
    dag_id: Optional[str]
    is_active: bool
    priority: int
    timezone: str
    session_start: Optional[str]
    session_end: Optional[str]
    allow_weekend: bool
    config: Optional[dict]


class WorkflowSymbolCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (uppercase)")
    name: Optional[str] = Field(None, max_length=100, description="Company name")
    enabled: bool = Field(True, description="Enable/disable symbol globally")
    priority: int = Field(0, description="Global processing priority")
    workflow_type: str = Field('trading_signal', description="Workflow type (legacy)")
    workflows: List[SymbolWorkflowConfig] = Field(..., min_length=1, description="Workflows to associate")


class WorkflowSymbolUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    workflow_type: Optional[str] = None
    workflows: Optional[List[SymbolWorkflowConfig]] = Field(None, description="Replace workflow links")


class WorkflowSymbolResponse(BaseModel):
    id: int
    symbol: str
    name: Optional[str]
    enabled: bool
    priority: int
    workflow_type: str
    created_at: Optional[str]
    updated_at: Optional[str]
    workflows: List[LinkedWorkflowSummary] = Field(default_factory=list)

    class Config:
        from_attributes = True


# Validation helpers

def validate_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if not re.match(r"^[A-Z]{1,10}$", symbol):
        raise HTTPException(status_code=400, detail="Symbol must be 1-10 uppercase letters only")
    return symbol


def _normalize_timezone(tz_name: Optional[str]) -> str:
    tz = (tz_name or "America/New_York").strip()
    try:
        pytz_timezone(tz)
    except UnknownTimeZoneError as exc:  # pragma: no cover - user input
        raise HTTPException(status_code=400, detail=f"Unknown timezone '{tz}'") from exc
    return tz


def _validate_session_window(start: Optional[time], end: Optional[time]) -> None:
    if (start and not end) or (end and not start):
        raise HTTPException(
            status_code=400,
            detail="Session start and end must both be provided or both omitted",
        )
    if start and end and start >= end:
        raise HTTPException(status_code=400, detail="Session end must be after session start")


def _load_workflows(db: Session, workflow_ids: Sequence[int]) -> List[Workflow]:
    ids = sorted({int(wf_id) for wf_id in workflow_ids})
    if not ids:
        return []
    workflows = db.query(Workflow).filter(Workflow.id.in_(ids)).all()
    found = {wf.id for wf in workflows}
    missing = [wf_id for wf_id in ids if wf_id not in found]
    if missing:
        raise HTTPException(status_code=404, detail=f"Workflows not found: {missing}")
    return workflows


def _serialize_symbol(symbol: WorkflowSymbol) -> WorkflowSymbolResponse:
    return WorkflowSymbolResponse(**symbol.to_dict())


def _assign_workflows(db: Session, symbol: WorkflowSymbol, configs: List[SymbolWorkflowConfig]) -> None:
    """Update symbol workflow links based on configurations."""
    if not configs:
        raise HTTPException(status_code=400, detail="At least one workflow must be selected")

    workflow_ids = [c.workflow_id for c in configs]
    seen: Set[int] = set()
    duplicates: Set[int] = set()
    for wf_id in workflow_ids:
        if wf_id in seen:
            duplicates.add(wf_id)
        else:
            seen.add(wf_id)
    if duplicates:
        raise HTTPException(
            status_code=400,
            detail=f"Duplicate workflow_ids detected: {sorted(duplicates)}",
        )

    _load_workflows(db, workflow_ids)

    existing_links = {link.workflow_id: link for link in symbol.workflow_links}
    processed: Set[int] = set()

    for idx, config in enumerate(configs):
        normalized_tz = _normalize_timezone(config.timezone)
        _validate_session_window(config.session_start, config.session_end)

        link = existing_links.get(config.workflow_id)
        if not link:
            link = SymbolWorkflowLink(workflow_id=config.workflow_id)
            symbol.workflow_links.append(link)

        link.is_active = bool(config.is_active)
        link.priority = idx
        link.timezone = normalized_tz
        link.session_start = config.session_start
        link.session_end = config.session_end
        link.allow_weekend = bool(config.allow_weekend)
        link.config = config.config

        processed.add(config.workflow_id)

    # Remove any links that are no longer configured
    for link in list(symbol.workflow_links):
        if link.workflow_id not in processed:
            symbol.workflow_links.remove(link)


# Endpoints
@router.get("/", response_model=List[WorkflowSymbolResponse])
def list_symbols(
    enabled_only: bool = Query(False, description="Filter by enabled symbols only"),
    workflow_type: Optional[str] = Query(None, description="Filter by workflow type"),
    db: Session = Depends(get_db),
):
    query = db.query(WorkflowSymbol).options(
        selectinload(WorkflowSymbol.workflow_links).selectinload(SymbolWorkflowLink.workflow),
    )
    if enabled_only:
        query = query.filter(WorkflowSymbol.enabled.is_(True))
    if workflow_type:
        query = query.filter(WorkflowSymbol.workflow_type == workflow_type)
    symbols = query.order_by(WorkflowSymbol.priority.desc(), WorkflowSymbol.symbol).all()
    return [_serialize_symbol(symbol) for symbol in symbols]


@router.post("/", response_model=WorkflowSymbolResponse, status_code=201)
def create_symbol(symbol_data: WorkflowSymbolCreate, db: Session = Depends(get_db)):
    symbol_data.symbol = validate_symbol(symbol_data.symbol)
    existing = db.query(WorkflowSymbol).filter(WorkflowSymbol.symbol == symbol_data.symbol).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Symbol {symbol_data.symbol} already exists")

    new_symbol = WorkflowSymbol(
        symbol=symbol_data.symbol,
        name=symbol_data.name,
        enabled=symbol_data.enabled,
        priority=symbol_data.priority,
        workflow_type=symbol_data.workflow_type,
    )
    db.add(new_symbol)
    # Assign workflows before flush to ensure relationships are set
    _assign_workflows(db, new_symbol, symbol_data.workflows)
    
    db.commit()
    db.refresh(new_symbol)
    return _serialize_symbol(new_symbol)


@router.get("/{symbol}", response_model=WorkflowSymbolResponse)
def get_symbol(symbol: str, db: Session = Depends(get_db)):
    symbol = validate_symbol(symbol)
    db_symbol = (
        db.query(WorkflowSymbol)
        .options(
            selectinload(WorkflowSymbol.workflow_links).selectinload(SymbolWorkflowLink.workflow),
        )
        .filter(WorkflowSymbol.symbol == symbol)
        .first()
    )
    if not db_symbol:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    return _serialize_symbol(db_symbol)


@router.patch("/{symbol}", response_model=WorkflowSymbolResponse)
def update_symbol(symbol: str, updates: WorkflowSymbolUpdate, db: Session = Depends(get_db)):
    symbol = validate_symbol(symbol)
    db_symbol = (
        db.query(WorkflowSymbol)
        .options(
            selectinload(WorkflowSymbol.workflow_links).selectinload(SymbolWorkflowLink.workflow),
        )
        .filter(WorkflowSymbol.symbol == symbol)
        .first()
    )
    if not db_symbol:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    workflows_config = updates.workflows
    update_data = updates.model_dump(exclude={"workflows"}, exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_symbol, field, value)

    if workflows_config is not None:
        _assign_workflows(db, db_symbol, workflows_config)
    elif not db_symbol.workflow_links:
        # If not updating workflows, ensure we still have some (unless we want to allow 0, but logic says at least 1)
        # Actually, if we are not updating workflows, we don't need to check.
        # But if we updated workflows to empty list, _assign_workflows would raise 400.
        pass

    db.commit()
    db.refresh(db_symbol)
    return _serialize_symbol(db_symbol)


@router.delete("/{symbol}", status_code=204)
def delete_symbol(symbol: str, db: Session = Depends(get_db)):
    symbol = validate_symbol(symbol)
    db_symbol = db.query(WorkflowSymbol).filter(WorkflowSymbol.symbol == symbol).first()
    if not db_symbol:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    db.delete(db_symbol)
    db.commit()
    return None
