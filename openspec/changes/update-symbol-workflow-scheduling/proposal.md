## Why
Workflow symbols currently force every workflow attached to a symbol to inherit the same timezone, session window, and weekend policy. That prevents us from mixing workflows with different trading windows (e.g., a nightly data prep workflow plus an intraday execution workflow) under one ticker without duplicating symbols. Operators also need per-workflow overrides (like JSON config snippets) without bloating the global symbol record.

## What Changes
- Promote the `workflow_symbol_workflows` join table into a first-class `SymbolWorkflowLink` model that stores activation state, execution priority, timezone, session_start/end, weekend toggle, and JSON config per symbol/workflow pair.
- Trim scheduling/config columns from `workflow_symbol` so it only manages identity (`symbol`, `name`, `enabled`, `priority`).
- Expand POST/PATCH `/api/workflow-symbols` to accept a `workflows[]` payload (via `SymbolWorkflowConfig`) and persist the nested link rows atomically.
- Redesign the Workflow Symbols modal (`workflow_symbols.html`) into a three-step wizard: (1) symbol metadata, (2) workflow selection & per-workflow schedule cards, (3) review summary.

## Impact
- Specs touched: `database-schema`, `api-backend`, `frontend-parameter-editor`.
- Code areas: SQLAlchemy models/migrations for workflow symbols, FastAPI schemas & CRUD endpoints for `/api/workflow-symbols`, Jinja2 template + Alpine.js logic for the Workflow Symbols modal.
