## Context
Workflow symbols currently map a ticker to exactly one workflow plus a single strategy schedule. Operators manage cron windows in-app even though Airflow already owns orchestration. We want symbols to declare which Airflow workflows they belong to (one symbol can power multiple DAGs), and let Airflow/strategies decide cadence externally. This implies dropping the bespoke `strategy_schedules` table, UI, and API endpoints.

## Goals / Non-Goals
- Goals: simplify symbol configuration, allow n: n symbol↔workflow mapping, remove cron/schedule complexity from UI/API.
- Non-Goals: redesign of strategy parameter editing, Airflow DAG authoring, or new orchestration features.

## Decisions
1. **Symbol-centric associations**: extend the workflow symbol model with a join table `workflow_symbol_workflows` (or reuse existing relationship) so API payloads accept `workflow_ids[]` instead of schedule IDs.
2. **Retire schedule concept**: delete `/api/schedules` endpoints, the `strategy_schedules` table/service, and the frontend schedules page. All cron management will happen directly in Airflow or automation scripts.
3. **UI flow**: convert the Workflow Symbols modal into a multi-step experience focused on selecting workflows (with search/filter/badges) instead of cron windows.

## Risks / Trade-offs
- Removing schedules means users must manage cadence elsewhere; document that expectation to avoid confusion.
- Migrating existing data requires a one-time script to translate schedule-linked workflows back to symbol associations.

## Migration Plan
1. Ship DB migration to drop schedule tables/columns once symbol-workflow associations exist.
2. Remove frontend routes and menu items pointing to schedules.
3. Coordinate release communication so operators know to configure Airflow DAG schedules outside the UI.

## Open Questions
- Do we need historical audit of old schedules? (Assume no, but archive exported JSON before dropping.)
- Should workflows track which symbols they serve for analytics? (Potential follow-up capability.)
