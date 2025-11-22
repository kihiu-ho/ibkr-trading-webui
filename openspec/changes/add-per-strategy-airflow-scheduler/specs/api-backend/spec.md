## MODIFIED Requirements

### Requirement: Scheduled Workflow Endpoints
The system SHALL provide endpoints for scheduling periodic workflow executions with per-strategy cron settings that drive Airflow DAG cadences and manual overrides.

#### Scenario: Create scheduled workflow
- **WHEN** POST /api/workflows/{id}/schedule is called with {cron_expression, timezone, strategy_id, enabled, description}
- **THEN** validate cron expression via croniter and reject invalid input
- **AND** create database record linked to the strategy (one active schedule per strategy)
- **AND** calculate and return next 5 run timestamps plus metadata {next_run_time, last_run_time}
- **AND** publish schedule payload for Airflow to consume (e.g., via internal export endpoint or message)

#### Scenario: List scheduled workflows
- **WHEN** GET /api/schedules is called (optionally filtered by workflow_id or strategy_id)
- **THEN** return list of schedules including id, workflow_name, strategy_name, cron_expression, timezone, enabled, next_run_time, last_run_time, description, created/updated timestamps
- **AND** include `source` field (auto/manual) and `last_synced_at` to show when Airflow picked it up

#### Scenario: Update schedule
- **WHEN** PUT /api/schedules/{id} is called with new cron expression or enabled flag
- **THEN** revalidate cron, store change history, and recompute next runs
- **AND** notify Airflow scheduler (REST hook or queue message) so DAG schedule_interval updates without restart
- **AND** return updated schedule including `pending_airflow_sync` boolean until Airflow acknowledges

#### Scenario: Delete schedule
- **WHEN** DELETE /api/schedules/{id} is called
- **THEN** remove schedule and mark associated Airflow DAG paused with `schedule_interval=None`
- **AND** delete record or mark soft-deleted per retention policy
- **AND** return 204 No Content

#### Scenario: Trigger immediate execution
- **WHEN** POST /api/workflows/{id}/run-now is called with {strategy_id}
- **THEN** call Airflow REST API to create dagRun tagged `trigger_source=manual`
- **AND** response SHALL include dag_run_id, queued_at, strategy context
- **AND** request SHALL be accepted even if schedule is disabled (single run only)
