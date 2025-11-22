## Context
- Current Airflow DAGs read a single `WORKFLOW_SCHEDULE` env var so all strategies share one cadence and require deploy changes to adjust.
- Strategy metadata already lives in Postgres; schedules should sit alongside to keep UI + backend authoritative.
- Airflow must reflect schedule edits quickly without restarting containers.

## Goals / Non-Goals
- Goals: per-strategy cron configuration, UI editing, backend persistence, Airflow sync, run-now triggers, enable/disable toggle.
- Non-Goals: building a general calendar engine, holiday blacklisting, multi-account routing.

## Decisions
1. **Schedule Storage**: add `strategy_schedules` table referencing strategy_id with cron_expression, enabled, description, run window metadata. Chosen for auditable history + joins.
2. **Airflow Sync Mechanism**: expose REST endpoint `/api/internal/schedules/export` returning active schedules; Airflow DAG factory polls (e.g., every minute) and updates `schedule_interval` via `TriggerDagRunOperator` + DAG paramization. Alternative (Airflow DB direct writes) rejected due to security.
3. **Cron Validation**: backend uses `croniter` to validate + compute next 5 runs, returning preview to UI.
4. **Run-Now**: UI button calls backend `POST /api/workflows/{id}/run-now` which invokes Airflow REST API `/api/v1/dags/{dag_id}/dagRuns` with strategy context.
5. **Toggle Behavior**: disabling schedule pauses DAG via Airflow API and marks backend `enabled=false`; enabling resumes and updates cron.

## Risks / Trade-offs
- **Stale schedules**: polling introduces lag (<=60s). Acceptable vs pushing from backend via webhook because Airflow service is isolated.
- **Airflow API auth**: need service account token; store as env var with limited scope.
- **Cron mistakes**: risk of overlapping runs; mitigate with validation + warnings when cron period shorter than workflow duration.

## Migration Plan
1. Create storage + APIs with feature flag.
2. Deploy backend + Airflow with env var fallback; if no schedule found use manual run.
3. Roll out UI enabling schedule edits.
4. Remove old env var once adoption confirmed.

## Open Questions
- Should schedules respect exchange calendars automatically? (future enhancement)
- Do we need per-strategy timezone overrides beyond UTC? default to America/New_York for now.
