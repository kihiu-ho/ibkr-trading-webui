## Overview
Stopping a workflow from the Airflow monitor requires coordinated changes in the FastAPI Airflow proxy and the Alpine.js component that renders `frontend/templates/airflow_monitor.html`. The proxy will expose a dedicated endpoint that marks a DAG run as `failed` through Airflow's REST API, while the UI will surface the control, capture operator intent, and refresh state.

## Backend Approach
1. **Endpoint shape**: `POST /api/airflow/dags/{dag_id}/dagRuns/{dag_run_id}/fail` with body `{ "reason": "optional note" }`.
2. **Airflow call**: Use the existing authenticated `requests.Session` to invoke `PATCH /api/v1/dags/{dag_id}/dagRuns/{dag_run_id}` with `{"state": "failed"}`. Airflow 2.7 treats this as an admin action and will terminate remaining tasks. If Airflow rejects the request (already finished, run missing), pass the error message/status code through.
3. **Validation**: Before forwarding, fetch the run details to ensure it is currently `running`, `queued`, or `scheduled`. Return `409 Conflict` for completed runs so the UI can show a friendly message.
4. **Observability**: Log the operator note alongside dag_id/dag_run_id to create an audit trail. Include previous/new state in the JSON response.

## Frontend Flow
1. Attach a `Stop & Mark Failed` action (button or menu item) to each row in the run list and to the run-details modal header when `selectedRun.state` is `running|queued|scheduled`.
2. Clicking opens a confirmation dialog with optional textarea for "Reason for stopping". Disable submission while the API call is pending and show spinner text.
3. On success, close the dialog, show a toast/snackbar, optimistically update `selectedRun.state` and `taskStats`, and trigger `refreshData()` so the grid and cards align with Airflow's state. On error, keep the dialog open and display the backend-provided message inline.
4. Ensure the action respects RBAC assumptions (monitor already sits behind authenticated FastAPI session); no additional auth is needed beyond backend validation.

## Edge Cases
- API call timeouts should roll back UI state and mark the action as failed.
- Runs that finish between confirmation and request should surface the 409 response and tell the user the run is already finished.
- If Airflow is unreachable, display the health status banner in red and disable the control until `/api/airflow/health` reports healthy again.
