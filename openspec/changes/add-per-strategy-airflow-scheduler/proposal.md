## Why
Airflow DAGs for IBKR workflows currently share a single `WORKFLOW_SCHEDULE` env var, so every strategy either runs manually or on the same cadence. Traders need per-strategy control from the UI to align signals with market sessions without touching deployment config.

## What Changes
- Persist per-strategy cron expressions, enable/disable flags, and descriptions via backend schedule endpoints.
- Sync saved schedules into Airflow so each strategy’s DAG uses its own cron cadence and can be toggled without redeploying.
- Extend frontend workflow/strategy screens with schedule editor (cron helper + preview) and quick "Run now" + enable toggles.
- Update message-queue/Airflow integration to regenerate schedules safely when users update cron details.

## Impact
- Specs affected: `trading-workflow`, `api-backend`, `frontend-ui`, `message-queue`.
- Code areas: FastAPI schedule APIs, schedule persistence (DB + ORM), Airflow DAG factory/config loader, frontend schedule modal, Celery/Airflow sync utilities.
- Requires coordination with Airflow deployment (scheduler must reload DAGs after schedule updates).
