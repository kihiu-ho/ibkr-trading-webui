"""API endpoints for managing strategy schedules and run-now triggers."""
from __future__ import annotations

import logging
import time
from typing import List, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, status
from requests.auth import HTTPBasicAuth
from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.core.database import get_db
from backend.schemas.schedule import (
    RunNowRequest,
    RunNowResponse,
    ScheduleCreateRequest,
    ScheduleResponse,
    ScheduleUpdateRequest,
)
from backend.services.strategy_service import StrategyService, StrategySchedule

router = APIRouter(tags=["schedules"])
logger = logging.getLogger(__name__)


def _serialize_schedule(service: StrategyService, schedule) -> ScheduleResponse:
    preview: List = []
    if schedule.enabled:
        preview = service.preview_next_runs(
            schedule.cron_expression,
            timezone_name=schedule.timezone,
            count=5,
        )
    dag_id = schedule.strategy_dag_id if hasattr(schedule, "strategy_dag_id") else f"strategy_{schedule.strategy_id}_schedule"
    strategy_name = schedule.strategy.name if getattr(schedule, "strategy", None) else None
    return ScheduleResponse(
        id=schedule.id,
        dag_id=dag_id,
        strategy_id=schedule.strategy_id,
        workflow_id=schedule.workflow_id,
        strategy_name=strategy_name,
        cron_expression=schedule.cron_expression,
        timezone=schedule.timezone,
        enabled=schedule.enabled,
        description=schedule.description,
        next_run_time=schedule.next_run_time,
        last_run_time=schedule.last_run_time,
        next_runs_preview=preview,
        last_synced_at=schedule.last_synced_at,
        pending_airflow_sync=schedule.pending_airflow_sync,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


def _airflow_auth():
    return HTTPBasicAuth(settings.AIRFLOW_USERNAME, settings.AIRFLOW_PASSWORD)


def _apply_airflow_state(schedule: StrategySchedule) -> None:
    """Pause/unpause schedule DAG to match enabled flag."""
    dag_id = schedule.strategy_dag_id
    payload = {"is_paused": not schedule.enabled}
    try:
        response = requests.patch(
            f"{settings.AIRFLOW_API_URL}/dags/{dag_id}",
            json=payload,
            auth=_airflow_auth(),
            timeout=settings.AIRFLOW_RUN_TIMEOUT_SECONDS,
        )
        if response.status_code >= 400 and response.status_code != 404:
            logger.warning("Airflow dag patch failed for %s: %s", dag_id, response.text)
    except requests.RequestException as exc:
        logger.warning("Failed to sync Airflow DAG %s: %s", dag_id, exc)


def _pause_airflow_dag(dag_id: str) -> None:
    try:
        requests.patch(
            f"{settings.AIRFLOW_API_URL}/dags/{dag_id}",
            json={"is_paused": True},
            auth=_airflow_auth(),
            timeout=settings.AIRFLOW_RUN_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.warning("Unable to pause Airflow DAG %s: %s", dag_id, exc)


@router.post(
    "/api/workflows/{workflow_id}/schedule",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_schedule(
    workflow_id: int,
    payload: ScheduleCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a per-strategy schedule."""
    service = StrategyService(db)
    strategy = service.get_strategy(payload.strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    if strategy.workflow_id != workflow_id:
        raise HTTPException(
            status_code=400,
            detail="Strategy is not associated with specified workflow",
        )
    try:
        schedule = service.create_schedule(
            strategy_id=payload.strategy_id,
            cron_expression=payload.cron_expression,
            timezone_name=payload.timezone,
            enabled=payload.enabled,
            description=payload.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _apply_airflow_state(schedule)
    return _serialize_schedule(service, schedule)


@router.get("/api/schedules", response_model=List[ScheduleResponse])
def list_schedules(
    strategy_id: Optional[int] = Query(default=None),
    workflow_id: Optional[int] = Query(default=None),
    enabled: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
):
    """List stored schedules."""
    service = StrategyService(db)
    schedules = service.list_schedules(strategy_id=strategy_id, workflow_id=workflow_id, enabled=enabled)
    return [_serialize_schedule(service, schedule) for schedule in schedules]


@router.put("/api/schedules/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int,
    payload: ScheduleUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update cron/timezone/description for a schedule."""
    service = StrategyService(db)
    try:
        schedule = service.update_schedule(
            schedule_id,
            cron_expression=payload.cron_expression,
            timezone_name=payload.timezone,
            enabled=payload.enabled,
            description=payload.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _apply_airflow_state(schedule)
    return _serialize_schedule(service, schedule)


@router.delete("/api/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    service = StrategyService(db)
    try:
        schedule = service.get_schedule_by_id(schedule_id)
        dag_id = schedule.strategy_dag_id if schedule else None
        service.delete_schedule(schedule_id)
        if dag_id:
            _pause_airflow_dag(dag_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return None


@router.post("/api/workflows/{workflow_id}/run-now", response_model=RunNowResponse)
def run_strategy_now(
    workflow_id: int,
    payload: RunNowRequest,
    db: Session = Depends(get_db),
):
    """Trigger an immediate Airflow DAG run for a given strategy."""
    service = StrategyService(db)
    strategy = service.get_strategy(payload.strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    if strategy.workflow_id != workflow_id:
        raise HTTPException(status_code=400, detail="Strategy is not associated with workflow")

    result = _trigger_airflow_dag(
        strategy_id=strategy.id,
        workflow_id=workflow_id,
        dag_id=payload.dag_id or settings.AIRFLOW_DEFAULT_DAG_ID,
    )
    return RunNowResponse(
        dag_id=result["dag_id"],
        dag_run_id=result["dag_run_id"],
        state=result.get("state", "queued"),
        queued_at=result.get("queued_at"),
        conf=result.get("conf", {}),
    )


def _trigger_airflow_dag(*, strategy_id: int, workflow_id: int, dag_id: str) -> dict:
    url = f"{settings.AIRFLOW_API_URL}/dags/{dag_id}/dagRuns"
    run_id = f"manual__strategy_{strategy_id}__{int(time.time())}"
    payload = {
        "dag_run_id": run_id,
        "conf": {
            "strategy_id": strategy_id,
            "workflow_id": workflow_id,
            "trigger_source": "manual",
        },
    }
    try:
        response = requests.post(
            url,
            json=payload,
            auth=HTTPBasicAuth(settings.AIRFLOW_USERNAME, settings.AIRFLOW_PASSWORD),
            timeout=settings.AIRFLOW_RUN_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Failed to contact Airflow: {exc}") from exc

    if response.status_code >= 400:
        detail = response.text or "Airflow rejected request"
        raise HTTPException(status_code=response.status_code, detail=detail)

    data = response.json()
    data.setdefault("dag_id", dag_id)
    data.setdefault("dag_run_id", run_id)
    data.setdefault("conf", payload["conf"])
    return data


@router.post("/api/schedules/{schedule_id}/sync", response_model=ScheduleResponse)
def mark_schedule_synced(schedule_id: int, db: Session = Depends(get_db)):
    """Mark schedule as synced by Airflow (called from Airflow side)."""
    service = StrategyService(db)
    try:
        schedule = service.mark_schedule_synced(schedule_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _serialize_schedule(service, schedule)
