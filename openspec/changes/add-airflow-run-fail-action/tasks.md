## 1. Backend Controls
- [ ] 1.1 Add a FastAPI route under `/api/airflow/dags/{dag_id}/dagRuns/{dag_run_id}/fail` (or equivalent) that validates run status, forwards a PATCH/POST to the Airflow REST API to set the run state to `failed`, and records the optional operator note in logs.
- [ ] 1.2 Return structured success/error payloads (run id, previous/new state, message) and unit-test the helper that calls Airflow so API failures bubble up with actionable detail.

## 2. Frontend UX
- [ ] 2.1 Surface a `Stop & Mark Failed` control for every running/queued DAG run in the Airflow monitor tables and detail modal; disable it for completed runs.
- [ ] 2.2 Implement a confirmation dialog that captures an optional operator note, invokes the new backend endpoint, shows success/error toasts, and refreshes the DAG/run lists plus modal task stats after completion.
- [ ] 2.3 Update Alpine component state handling so local run/task lists immediately reflect the failure without waiting for the auto-refresh interval.

## 3. Validation
- [ ] 3.1 Add/extend API tests (or mocks) to cover successful fail requests, invalid run states, and downstream Airflow errors (Auth failure, network timeout).
- [ ] 3.2 Document manual verification steps: start a sample DAG, trigger the button, confirm Airflow UI now shows the run as failed and tasks stop executing.
