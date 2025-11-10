## ADDED Requirements
### Requirement: Task Instance Logs Display
The system SHALL display Airflow task instance logs in a readable, formatted view.

#### Scenario: View logs for completed task
- **WHEN** user clicks "View Logs" button for a task instance
- **THEN** fetch logs from Airflow API
- **AND** display logs in a modal with formatted text
- **AND** show line numbers and proper formatting
- **AND** display task metadata (task_id, dag_run_id, try_number)

#### Scenario: View logs for running task
- **WHEN** user clicks "View Logs" for a task that is currently running
- **THEN** fetch current logs from Airflow API
- **AND** display logs with auto-refresh option
- **AND** show "Logs are updating..." indicator

#### Scenario: Empty logs handling
- **WHEN** task instance has no logs available
- **THEN** display clear message: "No logs available for this task instance"
- **AND** suggest possible reasons (task not executed, logs cleared, etc.)

#### Scenario: Log formatting
- **WHEN** logs are displayed
- **THEN** format with monospace font
- **AND** show line numbers
- **AND** preserve log structure (timestamps, log levels)
- **AND** enable text selection and copying

#### Scenario: Error handling
- **WHEN** log fetch fails (404, 500, timeout)
- **THEN** display appropriate error message
- **AND** provide retry option
- **AND** log error details for debugging

