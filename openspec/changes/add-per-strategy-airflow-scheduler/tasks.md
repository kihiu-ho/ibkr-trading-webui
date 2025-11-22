## 1. Backend Scheduling APIs
- [x] 1.1 Add schedule persistence model/table per strategy (cron_expression, enabled, description, next_run_cache).
- [x] 1.2 Implement CRUD endpoints (`POST /api/workflows/{id}/schedule`, `GET /api/schedules`, etc.) returning preview of next run times.
- [x] 1.3 Enforce validation (cron parsing, market-hours hints) and unit tests for conversions.

## 2. Airflow & Message Queue Integration
- [x] 2.1 Update DAG loader to read per-strategy schedule from DB or config API instead of env var.
- [x] 2.2 Ensure schedule updates propagate (trigger DAG refresh, update Airflow Variables, or push DagRun via REST) without restart.
- [x] 2.3 Add safeguards: disable schedule -> pause DAG, run-now -> trigger DAG manually; include integration tests where possible.

## 3. Frontend Scheduler UI
- [x] 3.1 Create schedule modal tied to strategies with cron helper sliders + description field.
- [x] 3.2 Display per-strategy schedule table (enabled state, next run, last run, actions) and allow toggles/run-now from UI.
- [x] 3.3 Wire UI to backend endpoints with optimistic updates + error toasts.

## 4. Validation & Ops
- [x] 4.1 Document scheduler workflow in README/QUICK_START (how to enable schedules, market-hours guidance).
- [x] 4.2 E2E test: configure two strategies with different cron expressions, verify Airflow run history reflects both.
