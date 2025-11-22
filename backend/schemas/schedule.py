"""Pydantic schemas for strategy schedules."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ScheduleCreateRequest(BaseModel):
    """Payload for creating a strategy schedule."""

    strategy_id: int = Field(..., description="Strategy ID to schedule")
    cron_expression: str = Field(..., description="Cron expression for execution cadence")
    timezone: str = Field(default="America/New_York", description="IANA timezone name")
    enabled: bool = Field(default=True)
    description: Optional[str] = Field(default=None, description="Optional note for operators")


class ScheduleUpdateRequest(BaseModel):
    """Payload for updating a schedule."""

    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None


class ScheduleResponse(BaseModel):
    """Response returned for schedule endpoints."""

    id: int
    dag_id: str
    strategy_id: int
    workflow_id: Optional[int] = None
    strategy_name: Optional[str] = None
    workflow_name: Optional[str] = None
    cron_expression: str
    timezone: str
    enabled: bool
    description: Optional[str] = None
    next_run_time: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    next_runs_preview: List[datetime] = []
    last_synced_at: Optional[datetime] = None
    pending_airflow_sync: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RunNowRequest(BaseModel):
    """Request payload for triggering on-demand run."""

    strategy_id: int
    dag_id: Optional[str] = Field(default=None, description="Override Airflow DAG id")


class RunNowResponse(BaseModel):
    """Airflow dag run metadata."""

    dag_id: str
    dag_run_id: str
    state: str
    queued_at: Optional[datetime] = None
    conf: dict
