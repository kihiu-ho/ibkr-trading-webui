## MODIFIED Requirements

### Requirement: Task Scheduling
The system SHALL support scheduled and periodic task execution with per-strategy cron metadata synced to Airflow/Celery beat.

#### Scenario: Schedule workflow execution
- **WHEN** user schedules workflow to run at specific time
- **THEN** create/update Celery beat or Airflow schedule entry keyed by strategy_id
- **AND** task SHALL be queued at scheduled time using configured timezone and cron expression
- **AND** support cron-like schedules (daily, weekly, custom) plus friendly presets from UI
- **AND** store `trigger_source` (schedule vs manual) on each enqueued task

#### Scenario: Periodic workflows
- **WHEN** workflow is configured as periodic (e.g., every 4 hours)
- **THEN** Celery beat SHALL queue task on schedule only when `enabled=true`
- **AND** previous execution must complete before next starts unless `allow_overlap` flag is explicitly set
- **AND** schedule can be enabled/disabled via API and change SHALL propagate to workers within 60 seconds
- **AND** schedule changes SHALL be logged so SREs can audit cadence adjustments
