## MODIFIED Requirements

### Requirement: Scheduled Workflows Interface
The system SHALL provide interface for scheduling periodic workflow executions with per-strategy cron helpers, enable/disable switches, and run-now controls.

#### Scenario: Create schedule
- **WHEN** user clicks "Schedule" on a workflow or strategy card
- **THEN** display schedule creation modal
- **AND** show fields: workflow (pre-selected), strategy (dropdown), cron expression input with helper presets, timezone selector (default America/New_York), enabled toggle, description, and preview of next 5 run times
- **AND** validate cron in the UI (highlight errors) before allowing submission
- **AND** submit to backend and, on success, show toast "Schedule saved"

#### Scenario: List scheduled workflows
- **WHEN** user views schedules page or strategy detail panel
- **THEN** display table of schedules
- **AND** each row shows: workflow name, strategy, friendly cron summary, timezone, enabled status, next run, last run, airflow sync status, actions (Run now, Edit, Delete)
- **AND** provide enable/disable toggle that updates backend immediately
- **AND** provide "Run now" button per row even if schedule disabled (executes once)

#### Scenario: Edit schedule
- **WHEN** user edits schedule
- **THEN** display same form as create with pre-filled values, plus read-only metadata (created_at, updated_at, last_run)
- **AND** allow changing cron expression, timezone, strategy, enabled status, description
- **AND** update next run preview live as cron changes and warn if cron interval < workflow duration threshold (configurable hint)
