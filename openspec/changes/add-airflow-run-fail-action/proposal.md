## Why
Operators currently have no way to stop a misbehaving workflow from the Airflow monitor embedded in the WebUI. When a DAG run stalls or behaves unexpectedly, the only option is to open the standalone Airflow UI, find the run, and mark it failed there. This slows incident response, keeps bad tasks running longer than necessary, and makes it impossible to triage runs from the consolidated trading console.

## What Changes
- Add a "Stop & Mark Failed" control everywhere runs are listed in the Airflow monitor (cards, tables, and run-details modal) so operators can terminate a run without leaving the WebUI.
- Capture an optional operator note when the action is triggered, call the Airflow REST API to update the DAG run state to `failed`, and surface any backend errors inline.
- Refresh the monitor state after the action so the stopped run is highlighted as failed, task statistics update, and future triggers honor the new status.

## Impact
- Affected specs: `frontend-workflow-visualization`
- Affected code: `frontend/templates/airflow_monitor.html` (controls + UX), `backend/app/routes/airflow_proxy.py` (new mark-failed endpoint + Airflow call), any shared JS helpers for notifications.
