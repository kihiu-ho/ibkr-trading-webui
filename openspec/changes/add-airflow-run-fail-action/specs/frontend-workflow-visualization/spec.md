# frontend-workflow-visualization Specification

## ADDED Requirements

### Requirement: Workflow Run Termination Controls
The Airflow monitor SHALL allow operators to immediately stop an in-flight DAG run by marking it failed without leaving the WebUI.

#### Scenario: Mark running workflow failed from monitor list
- **WHEN** the Airflow monitor lists a DAG run whose state is `running`, `queued`, or `scheduled`
- **THEN** a `Stop & Mark Failed` control SHALL be shown next to that run and inside the run-details modal
- **AND** clicking the control SHALL prompt the operator to confirm and optionally enter a reason
- **AND** after confirmation the system SHALL call the backend API endpoint that sets the DAG run state to `failed`
- **AND** on success the monitor SHALL refresh the DAG/run data within 3 seconds and visually highlight the run as failed

#### Scenario: Handle conflicting or failed termination attempts
- **WHEN** the operator attempts to mark a DAG run failed that already completed or cannot be updated
- **THEN** the backend SHALL return an error response that identifies the conflict reason (e.g., "Run already succeeded at 13:04 UTC")
- **AND** the UI SHALL display this message inline without duplicating the action
- **AND** the action SHALL remain disabled while Airflow health endpoint reports `unavailable`
- **AND** audit logs SHALL include dag_id, dag_run_id, and any operator-provided note whenever the action is executed
