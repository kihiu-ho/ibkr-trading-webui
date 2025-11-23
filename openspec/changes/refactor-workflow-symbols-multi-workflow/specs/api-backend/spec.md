## ADDED Requirements
### Requirement: Workflow Symbol Multi-Workflow API
The backend SHALL expose workflow symbol endpoints that accept and return multiple workflow associations per symbol.

#### Scenario: Create workflow symbol with multiple workflows
- **WHEN** POST /api/workflow-symbols is called with {symbol, workflow_ids[]}
- **THEN** validate that workflow_ids is a non-empty array of existing workflows
- **AND** persist the symbol plus its workflow links inside a join table
- **AND** respond with 201 Created including `workflows: [{id, name}]`

#### Scenario: Update workflow symbol workflows
- **WHEN** PATCH /api/workflow-symbols/{symbol} is called with workflow_ids[]
- **THEN** replace the existing associations with the provided set atomically
- **AND** return 400 if the array is empty or references invalid workflows
- **AND** respond with the updated symbol payload showing the workflow list

## REMOVED Requirements
### Requirement: Scheduled Workflow Endpoints
**Reason**: The platform no longer manages cron schedules; `/api/workflows/{id}/schedule`, `/api/schedules`, and related endpoints are removed.

### Requirement: Create scheduled workflow
**Reason**: Schedule creation logic has been deprecated in favor of managing cadence directly in Airflow.

### Requirement: List scheduled workflows
**Reason**: Listing cron schedules inside the WebUI backend is obsolete once scheduling moves out of scope.

### Requirement: Update schedule
**Reason**: Updating cron expressions via API is no longer supported.

### Requirement: Delete schedule
**Reason**: Deleting schedules via the backend API is no longer required after removing the feature entirely.
