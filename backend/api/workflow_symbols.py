"""Workflow Symbols API - Manage trading symbols for workflows."""
import re
from datetime import time
from typing import List, Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from pytz import UnknownTimeZoneError, timezone as pytz_timezone
from sqlalchemy.orm import Session, selectinload

from backend.core.database import get_db
from backend.models.workflow import Workflow
from backend.models.workflow_symbol import WorkflowSymbol

router = APIRouter(prefix="/api/workflow-symbols", tags=["workflow-symbols"])


class WorkflowSummary(BaseModel):
    id: int
    name: str
    is_active: bool
    dag_id: Optional[str]


class WorkflowSymbolCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (uppercase)")
    name: Optional[str] = Field(None, max_length=100, description="Company name")
    enabled: bool = Field(True, description="Enable/disable symbol in workflows")
    priority: int = Field(0, description="Processing priority (higher first)")
    workflow_type: str = Field('trading_signal', description="Workflow type")
    workflow_ids: List[int] = Field(..., min_length=1, description="Workflow IDs to associate")
    timezone: str = Field("America/New_York", description="Preferred timezone for this symbol")
    session_start: Optional[time] = Field(None, description="Preferred session start (HH:MM)")
    session_end: Optional[time] = Field(None, description="Preferred session end (HH:MM)")
    allow_weekend: bool = Field(False, description="Allow weekend runs for this symbol")
    config: Optional[dict] = Field(None, description="Symbol-specific configuration")


class WorkflowSymbolUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    workflow_type: Optional[str] = None
    workflow_ids: Optional[List[int]] = Field(None, min_length=1, description="Replace workflow links")
    timezone: Optional[str] = None
    session_start: Optional[time] = None
    session_end: Optional[time] = None
    allow_weekend: Optional[bool] = None
    config: Optional[dict] = None


class WorkflowSymbolResponse(BaseModel):
    id: int
    symbol: str
    name: Optional[str]
    enabled: bool
    priority: int
    workflow_type: str
    workflow_id: Optional[int]
    workflow_name: Optional[str]
    timezone: str
    session_start: Optional[time]
    session_end: Optional[time]
    allow_weekend: bool
    config: Optional[dict]
    created_at: Optional[str]
    updated_at: Optional[str]
    workflows: List[WorkflowSummary] = Field(default_factory=list)

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
    payload = symbol.to_dict()
    payload["workflows"] = [
        WorkflowSummary(
            id=wf.id,
            name=wf.name,
            is_active=bool(wf.is_active),
            dag_id=wf.dag_id,
        ).model_dump()
        for wf in symbol.workflows or []
    ]
    return WorkflowSymbolResponse(**payload)


def _assign_workflows(symbol: WorkflowSymbol, workflows: List[Workflow]) -> None:
    if not workflows:
        raise HTTPException(status_code=400, detail="At least one workflow must be selected")
    symbol.workflows = workflows
    symbol.workflow_id = workflows[0].id


# Endpoints
@router.get("/", response_model=List[WorkflowSymbolResponse])
def list_symbols(
    enabled_only: bool = Query(False, description="Filter by enabled symbols only"),
    workflow_type: Optional[str] = Query(None, description="Filter by workflow type"),
    db: Session = Depends(get_db),
):
    query = db.query(WorkflowSymbol).options(
        selectinload(WorkflowSymbol.workflow),
        selectinload(WorkflowSymbol.workflows),
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

    workflows = _load_workflows(db, symbol_data.workflow_ids)
    _normalize_timezone(symbol_data.timezone)
    _validate_session_window(symbol_data.session_start, symbol_data.session_end)

    new_symbol = WorkflowSymbol(
        symbol=symbol_data.symbol,
        name=symbol_data.name,
        enabled=symbol_data.enabled,
        priority=symbol_data.priority,
        workflow_type=symbol_data.workflow_type,
        timezone=symbol_data.timezone,
        session_start=symbol_data.session_start,
        session_end=symbol_data.session_end,
        allow_weekend=symbol_data.allow_weekend,
        config=symbol_data.config,
    )
    db.add(new_symbol)
    db.flush()
    _assign_workflows(new_symbol, workflows)
    db.commit()
    db.refresh(new_symbol)
    return _serialize_symbol(new_symbol)


@router.get("/{symbol}", response_model=WorkflowSymbolResponse)
def get_symbol(symbol: str, db: Session = Depends(get_db)):
    symbol = validate_symbol(symbol)
    db_symbol = (
        db.query(WorkflowSymbol)
        .options(
            selectinload(WorkflowSymbol.workflow),
            selectinload(WorkflowSymbol.workflows),
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
            selectinload(WorkflowSymbol.workflow),
            selectinload(WorkflowSymbol.workflows),
        )
        .filter(WorkflowSymbol.symbol == symbol)
        .first()
    )
    if not db_symbol:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    update_data = updates.model_dump(exclude_unset=True)
    if "timezone" in update_data:
        update_data["timezone"] = _normalize_timezone(update_data["timezone"])
    if "session_start" in update_data or "session_end" in update_data:
        proposed_start = update_data.get("session_start", db_symbol.session_start)
        proposed_end = update_data.get("session_end", db_symbol.session_end)
        _validate_session_window(proposed_start, proposed_end)

    workflow_ids = update_data.pop("workflow_ids", None)
    for field, value in update_data.items():
        setattr(db_symbol, field, value)

    if workflow_ids is not None:
        workflows = _load_workflows(db, workflow_ids)
        _assign_workflows(db_symbol, workflows)
    elif not db_symbol.workflows:
        raise HTTPException(status_code=400, detail="Workflow symbols must remain linked to at least one workflow")

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
