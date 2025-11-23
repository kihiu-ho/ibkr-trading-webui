## 1. Implementation
- [x] 1.1 Extend the workflow symbols API responses to include referenced workflow schedule metadata (schedule id, name, cron, enabled flag) and enforce that create/update payloads specify at least one active schedule association.
- [x] 1.2 Redesign `workflow_symbols.html` to use the new two-panel modal: collect symbol metadata in step one, select schedule coverage in step two, and show a read-only review state that warns when a symbol is not attached to an enabled schedule.
- [x] 1.3 Update the workflow symbol catalog cards/table to surface schedule badges, filter by schedule state, and visually flag unassigned symbols.
- [x] 1.4 Refresh the workflow schedule creation modal with contextual workflow/strategy info, cron helper improvements, inline validation messaging, and a confirmation step that mirrors the new symbol modal patterns.

## 2. Validation
- [x] 2.1 Add backend tests covering the new schedule association validation plus at least one API contract test for the enriched response payload.
- [x] 2.2 Manually exercise the symbol add/edit flow and the schedule creation flow in the browser, capturing screenshots or notes for reviewers.
