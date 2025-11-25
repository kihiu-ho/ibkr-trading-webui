## 1. Database & Models
- [x] 1.1 Create Alembic migration that adds `symbol_workflow_links` table (association object) and drops scheduling columns from `workflow_symbols`.
- [x] 1.2 Update SQLAlchemy models + relationships to expose `SymbolWorkflowLink` with priority/order helpers.
- [x] 1.3 Backfill existing workflow-symbol associations into the new table and migrate scheduling data into per-link records.

## 2. Backend API
- [x] 2.1 Add `SymbolWorkflowConfig` Pydantic schema plus nested validation (timezone, session windows, JSON config).
- [x] 2.2 Update POST `/api/workflow-symbols` to accept `workflows[]`, create links transactionally, and return expanded link payloads.
- [x] 2.3 Update PATCH `/api/workflow-symbols/{symbol}` to diff/add/remove links, toggle `is_active`, and persist per-workflow schedule overrides.
- [x] 2.4 Extend backend tests to cover validation errors (overlapping windows, missing workflows) and success payload structure.

## 3. Frontend Workflow Symbols Modal
- [x] 3.1 Redesign `workflow_symbols.html` modal into three steps (symbol details, workflow configuration, review) with drag/drop or click-to-activate interactions.
- [x] 3.2 Implement scheduling cards (timezone dropdown, session start/end pickers, weekend toggle, JSON editor) for each active workflow.
- [x] 3.3 Serialize modal state into the new nested payload expected by the API and update inline validation/review summary.
- [x] 3.4 Add frontend smoke tests (e.g., Alpine component tests) covering multi-workflow configuration and JSON validation messaging.
