# database-schema Specification

## Purpose
TBD - created by archiving change add-fastapi-trading-webapp. Update Purpose after archive.
## Requirements
### Requirement: Workflow Table
The system SHALL maintain a `workflow` table to store reusable workflow definitions.

#### Scenario: Store workflow definition
- **WHEN** a workflow is created
- **THEN** it SHALL be stored with fields: id, name, type (template type), steps (JSONB), default_params (JSONB), created_at, updated_at
- **AND** steps SHALL contain array of step definitions with type and configuration
- **AND** type SHALL indicate template: 'two_indicator', 'three_indicator', 'autogen_multi_agent', 'custom'

#### Scenario: Workflow versioning
- **WHEN** workflow is modified
- **THEN** a new version record SHALL be created in workflow_versions table
- **AND** version record SHALL contain: workflow_id, version_number, steps (JSONB), created_at, created_by
- **AND** active workflow SHALL reference current version

### Requirement: Workflow Execution Table
The system SHALL maintain a `workflow_execution` table to track all workflow runs.

#### Scenario: Record workflow execution
- **WHEN** workflow executes
- **THEN** create record with: id, workflow_id, strategy_id, task_id (Celery task ID), status, started_at, completed_at, results (JSONB), error_message
- **AND** status SHALL be one of: 'pending', 'running', 'completed', 'failed', 'cancelled'
- **AND** results SHALL contain: symbols_processed, decisions_made, orders_placed, execution_logs

#### Scenario: Link executions to strategies
- **WHEN** querying workflow executions
- **THEN** executions SHALL be joinable with strategy and workflow tables
- **AND** support filtering by workflow_id, strategy_id, status, date_range

### Requirement: Agent Conversations Table
The system SHALL maintain an `agent_conversations` table to log AutoGen agent interactions.

#### Scenario: Log agent message
- **WHEN** AutoGen agents exchange messages
- **THEN** create record with: id, workflow_execution_id, agent_name, message_type (request/response), message_content, timestamp, tokens_used
- **AND** messages SHALL be ordered by timestamp
- **AND** full conversation SHALL be retrievable by workflow_execution_id

#### Scenario: Track agent performance
- **WHEN** analyzing agent contribution
- **THEN** aggregate messages by agent_name
- **AND** calculate: total messages, average tokens, decisions influenced
- **AND** support querying agent performance metrics

### Requirement: Strategy-Workflow Relationship
The system SHALL update strategy table to reference workflows instead of storing workflow logic inline.

#### Scenario: Strategy with workflow reference
- **WHEN** strategy is created or updated
- **THEN** strategy SHALL have workflow_id foreign key
- **AND** param field SHALL contain strategy-specific overrides only
- **AND** workflow definition SHALL come from workflow table
- **AND** if workflow_id is NULL, use legacy inline workflow (backward compatibility)

### Requirement: Celery Task Tracking
The system SHALL track Celery task information for workflow executions.

#### Scenario: Store task metadata
- **WHEN** workflow is submitted to Celery
- **THEN** workflow_execution.task_id SHALL store Celery task UUID
- **AND** task status SHALL be queryable from Redis result backend
- **AND** task progress SHALL be stored and retrievable

### Requirement: Workflow Analytics Tables
The system SHALL maintain tables for workflow performance analytics.

#### Scenario: Aggregate workflow metrics
- **WHEN** workflows execute over time
- **THEN** aggregate metrics SHALL be calculated: total_executions, success_rate, avg_duration, decisions_by_type, orders_placed
- **AND** metrics SHALL be stored in workflow_metrics table with: workflow_id, date, metrics (JSONB)
- **AND** enable fast querying of workflow performance trends

