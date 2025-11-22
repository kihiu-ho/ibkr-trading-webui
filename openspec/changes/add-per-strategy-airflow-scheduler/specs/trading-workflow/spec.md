## ADDED Requirements

### Requirement: Strategy-Specific Airflow Schedule Binding
Trading workflows SHALL bind each Airflow DAG instance to the cron expression saved for the owning strategy so cadences diverge per strategy without container redeploys.

#### Scenario: Load schedule from schedule service
- **WHEN** Airflow generates DAGs for strategies
- **THEN** fetch cron expression, timezone, and enabled flag from backend schedule service
- **AND** set DAG `schedule_interval` to that cron
- **AND** if schedule is disabled, pause the DAG and require manual triggers

#### Scenario: Apply schedule updates dynamically
- **WHEN** a strategy schedule is updated via API
- **THEN** Airflow SHALL pick up the change within 60 seconds without restarting scheduler
- **AND** next DagRun SHALL reflect the new cron expression
- **AND** previous DagRuns SHALL remain in history for traceability

### Requirement: UI-Controlled Run Overrides
Trading workflows SHALL support ad-hoc execution requests independent of the cron cadence so users can run strategies immediately from the UI.

#### Scenario: Trigger run-now outside cron
- **WHEN** user clicks "Run now" for a strategy with or without an active schedule
- **THEN** backend SHALL call Airflow REST API to create a DagRun with strategy context
- **AND** DAG SHALL execute once immediately in addition to any future scheduled runs
- **AND** execution SHALL be logged with source="manual"
