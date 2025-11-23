## 1. Implementation
- [x] 1.1 Remove the strategy schedule data model/service/API (tables, routers, frontend pages) so no endpoints/UI reference cron-based schedules.
- [x] 1.2 Update workflow symbol persistence + API contracts to support an array of workflow IDs per symbol (create/list/update responses, validators, migrations if needed).
- [x] 1.3 Redesign the Workflow Symbols UI to use multi-select workflows, badges, and workflow coverage filters without any schedule elements.
- [x] 1.4 Update strategy/workflow UI pieces that previously linked to schedules so navigation/actions point to the new multi-workflow association flows.

## 2. Validation
- [x] 2.1 Add/refresh backend tests covering multi-workflow association mutations and ensure schedule endpoints are absent.
- [x] 2.2 QA the new Workflow Symbols flow end-to-end (multi-select, filtering, removal) in the browser.
