## Why
Workflow symbol management currently exposes per-symbol scheduling inputs (window, timezone) even though the execution cadence is controlled solely through workflow schedules tied to strategies. Operators are confused about whether those fields do anything and cannot see which schedules will actually pick up a symbol. Likewise, the schedule creation modal offers limited context when adding a new cadence, making it easy to misconfigure workflows and symbols.

## What Changes
- Rebuild the "Add Workflow Symbol" experience to focus on symbol metadata plus explicit selection of the workflow schedule(s) that will process the symbol, removing the misleading session window inputs.
- Surface live schedule coverage inside the symbol catalog so operators can verify every symbol is attached to at least one enabled schedule.
- Enhance the schedule creation modal with the same visual language as the new symbol flow, including contextual strategy/workflow info, cron helpers, inline validation, and a confirmation step.

## Impact
- Affected specs: `frontend-ui` (symbol catalog UI, scheduled workflows interface)
- Affected code: `frontend/templates/workflow_symbols.html`, `frontend/templates/workflows/schedules.html`, API bindings that hydrate schedule metadata for the modal(s).
