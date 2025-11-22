#!/usr/bin/env python3
"""
E2E verifier for per-strategy Airflow schedules.

Usage:
    E2E_STRATEGY_IDS="1,2" BACKEND_URL=http://localhost:8000 AIRFLOW_API_URL=http://localhost:8080/api/v1 \
        python tests/scripts/test_airflow_schedule_e2e.py

The script:
1. Ensures each supplied strategy has a schedule with a unique cron expression.
2. For each strategy, triggers `POST /api/workflows/{workflow_id}/run-now`.
3. Polls the Airflow REST API for dagRuns on `IBKR_TRADING_DAG_ID` and verifies each run captured the strategy_id.

Set env vars:
    BACKEND_URL (default http://localhost:8000)
    AIRFLOW_API_URL (default http://airflow-webserver:8080/api/v1)
    AIRFLOW_USERNAME / AIRFLOW_PASSWORD
    E2E_STRATEGY_IDS (comma list or pass as CLI args)
    E2E_WORKFLOW_ID (defaults to 1)
    IBKR_TRADING_DAG_ID (defaults to ibkr_trading_strategy)
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Dict, List

import requests
from requests.auth import HTTPBasicAuth


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
AIRFLOW_API_URL = os.getenv("AIRFLOW_API_URL", "http://localhost:8080/api/v1")
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "airflow")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "airflow")
WORKFLOW_ID = int(os.getenv("E2E_WORKFLOW_ID", "1"))
IBKR_DAG_ID = os.getenv("IBKR_TRADING_DAG_ID", "ibkr_trading_strategy")
RUN_TIMEOUT = int(os.getenv("E2E_RUN_TIMEOUT_SECONDS", "180"))
REQUEST_TIMEOUT = int(os.getenv("E2E_REQUEST_TIMEOUT_SECONDS", "30"))


def _strategy_ids_from_env(argv: List[str]) -> List[int]:
    if len(argv) > 1:
        ids_src = argv[1]
    else:
        ids_src = os.getenv("E2E_STRATEGY_IDS")
    if not ids_src:
        print("Provide strategy IDs via E2E_STRATEGY_IDS env or CLI argument, e.g. '1,2'.", file=sys.stderr)
        sys.exit(1)
    try:
        return [int(part.strip()) for part in ids_src.split(",") if part.strip()]
    except ValueError as exc:
        print(f"Invalid strategy id list: {exc}", file=sys.stderr)
        sys.exit(1)


def _cron_for_index(index: int) -> str:
    presets = ["0 9 * * 1-5", "30 9 * * 1-5", "0 10 * * 1-5"]
    return presets[index % len(presets)]


def list_schedules() -> List[Dict]:
    resp = requests.get(f"{BACKEND_URL}/api/schedules", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, list) else []


def ensure_schedule(strategy_id: int, cron_expression: str) -> Dict:
    schedules = list_schedules()
    schedule = next((s for s in schedules if s["strategy_id"] == strategy_id), None)
    payload = {
        "cron_expression": cron_expression,
        "timezone": "America/New_York",
        "enabled": True,
        "description": f"E2E test schedule ({cron_expression})"
    }

    if schedule:
        resp = requests.put(
            f"{BACKEND_URL}/api/schedules/{schedule['id']}",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    resp = requests.post(
        f"{BACKEND_URL}/api/workflows/{WORKFLOW_ID}/schedule",
        json={"strategy_id": strategy_id, **payload},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def trigger_run(strategy_id: int):
    resp = requests.post(
        f"{BACKEND_URL}/api/workflows/{WORKFLOW_ID}/run-now",
        json={"strategy_id": strategy_id},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def poll_airflow_for_runs(strategy_ids: List[int]):
    auth = HTTPBasicAuth(AIRFLOW_USERNAME, AIRFLOW_PASSWORD)
    deadline = time.time() + RUN_TIMEOUT
    found = {sid: False for sid in strategy_ids}

    while time.time() < deadline:
        resp = requests.get(
            f"{AIRFLOW_API_URL}/dags/{IBKR_DAG_ID}/dagRuns?limit=25&order_by=-start_date",
            timeout=REQUEST_TIMEOUT,
            auth=auth,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Failed to fetch Airflow dagRuns: {resp.status_code} {resp.text}")
        payload = resp.json()
        dag_runs = payload.get("dag_runs", [])
        for run in dag_runs:
            conf = run.get("conf") or {}
            sid = conf.get("strategy_id")
            if sid in found:
                found[sid] = True
        if all(found.values()):
            print("Airflow dagRuns detected for all strategies.")
            return
        time.sleep(5)

    missing = [sid for sid, seen in found.items() if not seen]
    raise TimeoutError(f"Did not observe dagRuns for strategy ids: {missing}")


def main(argv: List[str]):
    strategy_ids = _strategy_ids_from_env(argv)
    print(f"Preparing schedules for strategies: {strategy_ids}")
    for idx, sid in enumerate(strategy_ids):
        cron = _cron_for_index(idx)
        schedule = ensure_schedule(sid, cron)
        print(f"Schedule ready for strategy {sid}: dag_id={schedule.get('dag_id')} cron={schedule.get('cron_expression')}")

    for sid in strategy_ids:
        result = trigger_run(sid)
        print(f"Triggered run for strategy {sid}: dag_run_id={result.get('dag_run_id')}")

    poll_airflow_for_runs(strategy_ids)
    print("E2E schedule verification successful.")


if __name__ == "__main__":
    try:
        main(sys.argv)
    except Exception as exc:  # pragma: no cover - CLI reporting
        print(f"E2E schedule test failed: {exc}", file=sys.stderr)
        sys.exit(1)
