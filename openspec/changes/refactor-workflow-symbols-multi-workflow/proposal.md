## Why
Workflow symbol management still assumes a single workflow per symbol plus an auxiliary "strategy schedule" concept that duplicates Airflow orchestration logic. Operators now need to bind a single symbol to multiple Airflow workflows (e.g., research + trading) while the existing schedule UI/API adds confusion and maintenance debt. Removing the bespoke scheduling stack and focusing on explicit symbol→workflow mappings simplifies both UX and backend responsibilities.

## What Changes
- Replace the current Workflow Symbols form/table with a multi-select workflow experience that shows badges per associated workflow and removes all schedule selection/filters.
- Deprecate and remove the strategy schedule API/UI entirely (no `/api/schedules`, no schedule tables/modals) in favor of directly associating workflows to symbols and strategies.
- Update backend contracts so workflow symbol endpoints accept/return an array of workflow IDs, eliminating the `strategy_schedules` table usage and all cron metadata.

## Impact
- Affected specs: `frontend-ui` (Workflow Symbols experience & removal of Scheduled Workflows interface), `api-backend` (deprecate schedule endpoints, define new multi-workflow payload contract).
- Affected code: `backend/api/workflow_symbols.py`, `backend/models/workflow_symbol*.py`, `backend/api/schedules.py` + related services/models, and `frontend/templates/workflow_symbols.html` with full schedule UI removal.
