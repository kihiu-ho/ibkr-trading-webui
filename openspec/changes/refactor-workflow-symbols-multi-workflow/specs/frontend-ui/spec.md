## ADDED Requirements
### Requirement: Workflow Symbol Multi-Workflow Association
The system SHALL let operators associate each workflow symbol with one or more Airflow workflows directly from the Workflow Symbols page.

#### Scenario: Assign symbol to multiple workflows
- **WHEN** the user opens the "Add Symbol" modal
- **THEN** Step 1 SHALL collect the symbol metadata (ticker, display name, priority, enable toggle)
- **AND** Step 2 SHALL present a searchable list of Airflow workflows with multi-select checkboxes
- **AND** the user SHALL be able to select at least one workflow and optionally many workflows before saving
- **AND** the review step SHALL summarize the workflow chips so users can confirm coverage

#### Scenario: Display workflow coverage in catalog
- **WHEN** workflow symbols are listed in the catalog table
- **THEN** each row SHALL render badges for every associated workflow showing the workflow name and status
- **AND** symbols without any workflows SHALL show a red "Unassigned" pill plus tooltip guidance
- **AND** filters SHALL support narrowing by workflow, coverage (has/needs workflow), and workflow state so gaps are easy to find

## REMOVED Requirements
### Requirement: Scheduled Workflows Interface
**Reason**: Cron-based scheduling is no longer managed inside the WebUI; Airflow DAG schedules are configured externally.

### Requirement: Create schedule
**Reason**: The dedicated schedule creation modal/UI is deprecated; users now manage workflow cadence directly in Airflow.

### Requirement: List scheduled workflows
**Reason**: The schedules table and related toggles/actions are removed with the retirement of strategy schedules.

### Requirement: Edit schedule
**Reason**: Editing cron expressions within the WebUI is no longer supported because the scheduling concept has been removed.
