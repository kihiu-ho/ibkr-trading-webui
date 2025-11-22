"""Dynamic DAG factory binding strategies to their cron schedules."""
from __future__ import annotations

import logging
import os
from datetime import timedelta
from typing import Any, Dict, List

import pendulum
import requests
from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

logger = logging.getLogger(__name__)

BACKEND_BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://backend:8000")
SCHEDULES_ENDPOINT = f"{BACKEND_BASE_URL}/api/schedules"
SYNC_ENDPOINT_TEMPLATE = f"{BACKEND_BASE_URL}/api/schedules/{{schedule_id}}/sync"
WORKFLOW_DAG_ID = os.getenv("IBKR_TRADING_DAG_ID", "ibkr_trading_strategy")
TRIGGER_TIMEOUT = int(os.getenv("SCHEDULE_TRIGGER_TIMEOUT", "30"))


def _fetch_schedules() -> List[Dict[str, Any]]:
    try:
        response = requests.get(SCHEDULES_ENDPOINT, timeout=TRIGGER_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        logger.warning("Unexpected schedule payload type: %s", type(data))
    except Exception as exc:  # pragma: no cover - Airflow runtime
        logger.error("Failed to load strategy schedules: %s", exc)
    return []


def _mark_synced(schedule_id: int) -> None:
    try:
        requests.post(
            SYNC_ENDPOINT_TEMPLATE.format(schedule_id=schedule_id),
            timeout=TRIGGER_TIMEOUT,
        )
    except Exception as exc:  # pragma: no cover - Airflow runtime
        logger.warning("Unable to mark schedule %s as synced: %s", schedule_id, exc)


DEFAULT_ARGS = {
    "owner": "ibkr-trading",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


for schedule in _fetch_schedules():
    try:
        dag_id = schedule.get("dag_id") or f"strategy_{schedule['strategy_id']}_schedule"
        cron_expression = schedule["cron_expression"]
        tz_name = schedule.get("timezone") or "UTC"
        enabled = schedule.get("enabled", True)

        try:
            dag_timezone = pendulum.timezone(tz_name)
        except Exception:  # pragma: no cover - fallback to UTC
            logger.warning("Unknown timezone '%s' for schedule %s, defaulting to UTC", tz_name, dag_id)
            dag_timezone = pendulum.UTC

        dag = DAG(
            dag_id=dag_id,
            default_args=DEFAULT_ARGS,
            schedule_interval=cron_expression,
            catchup=False,
            max_active_runs=1,
            tags=["ibkr", "strategy-schedule"],
            description=f"Auto-trigger for strategy {schedule.get('strategy_id')}",
            timezone=dag_timezone,
        )
        dag.is_paused_upon_creation = not enabled

        with dag:
            TriggerDagRunOperator(
                task_id="trigger_ibkr_strategy",
                trigger_dag_id=WORKFLOW_DAG_ID,
                conf={
                    "strategy_id": schedule.get("strategy_id"),
                    "workflow_id": schedule.get("workflow_id"),
                    "schedule_id": schedule.get("id"),
                    "trigger_source": "schedule",
                },
                reset_dag_run=True,
                wait_for_completion=False,
            )

        globals()[dag_id] = dag

        if schedule.get("pending_airflow_sync"):
            _mark_synced(schedule["id"])

    except KeyError as exc:  # pragma: no cover - safe guard
        logger.error("Skipping schedule due to missing field: %s", exc)
