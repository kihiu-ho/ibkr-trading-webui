# api-backend Specification

## Purpose
TBD - created by archiving change add-fastapi-trading-webapp. Update Purpose after archive.
## Requirements
### Requirement: Workflow Management Endpoints
The system SHALL provide CRUD endpoints for managing workflow definitions.

#### Scenario: List workflows
- **WHEN** GET /api/workflows is called
- **THEN** return list of workflows with: id, name, type, created_at, executions_count
- **AND** support filtering by type
- **AND** support pagination

#### Scenario: Create workflow
- **WHEN** POST /api/workflows is called with {name, type, steps[], default_params}
- **THEN** validate workflow structure
- **AND** create workflow record
- **AND** return 201 Created with workflow details

#### Scenario: Get workflow details
- **WHEN** GET /api/workflows/{id} is called
- **THEN** return workflow with: id, name, type, steps, default_params, version, created_at, updated_at
- **AND** include list of strategies using this workflow
- **AND** include recent execution statistics

#### Scenario: Update workflow
- **WHEN** PUT /api/workflows/{id} is called
- **THEN** validate updated workflow
- **AND** create new version in workflow_versions table
- **AND** update workflow record
- **AND** return updated workflow

#### Scenario: Delete workflow
- **WHEN** DELETE /api/workflows/{id} is called
- **THEN** check if workflow is in use by active strategies
- **AND** if in use, return 409 Conflict with list of strategies
- **AND** if not in use, soft delete workflow
- **AND** return 204 No Content

#### Scenario: Clone workflow
- **WHEN** POST /api/workflows/{id}/clone is called
- **THEN** create copy of workflow with new ID
- **AND** append " (Copy)" to name
- **AND** return 201 Created with new workflow

### Requirement: Task Queue Management Endpoints
The system SHALL provide endpoints for managing Celery tasks and workflow executions.

#### Scenario: Get task status
- **WHEN** GET /api/tasks/{task_id} is called
- **THEN** query Celery result backend for task state
- **AND** return {task_id, status, progress, result, error}
- **AND** status SHALL be: PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED

#### Scenario: Cancel task
- **WHEN** DELETE /api/tasks/{task_id} is called
- **THEN** send revoke signal to Celery
- **AND** update workflow_execution status to 'cancelled'
- **AND** return 200 OK with confirmation

#### Scenario: List active tasks
- **WHEN** GET /api/tasks is called
- **THEN** query Celery for active tasks
- **AND** return list with: task_id, task_name, strategy_id, status, started_at, progress
- **AND** support filtering by status, strategy_id

#### Scenario: Get task queue metrics
- **WHEN** GET /api/tasks/metrics is called
- **THEN** return: tasks_queued, tasks_active, tasks_completed_today, tasks_failed_today, average_duration, worker_count
- **AND** fetch metrics from Celery inspect and Redis

### Requirement: Workflow Execution Endpoints
The system SHALL provide endpoints for executing and monitoring workflows.

#### Scenario: Execute workflow asynchronously
- **WHEN** POST /api/workflows/{id}/execute is called with {strategy_id, symbols[], priority}
- **THEN** validate workflow and strategy exist
- **AND** create Celery task for workflow execution
- **AND** create workflow_execution record with task_id
- **AND** return 202 Accepted with {workflow_execution_id, task_id}

#### Scenario: Execute multiple workflows
- **WHEN** POST /api/workflows/execute-batch is called with [{workflow_id, strategy_id, priority}]
- **THEN** submit each workflow as separate Celery task
- **AND** return list of {workflow_execution_id, task_id} for each
- **AND** tasks SHALL execute concurrently

#### Scenario: Get workflow execution status
- **WHEN** GET /api/workflow-executions/{id} is called
- **THEN** return workflow_execution record
- **AND** include: id, workflow_id, strategy_id, status, started_at, completed_at, progress, results
- **AND** if running, fetch real-time progress from Celery task

#### Scenario: List workflow executions
- **WHEN** GET /api/workflow-executions is called
- **THEN** return list of executions with filters: workflow_id, strategy_id, status, date_range
- **AND** support pagination and sorting
- **AND** include: id, workflow_name, strategy_name, status, started_at, duration, decisions_made

### Requirement: AutoGen Configuration Endpoints
The system SHALL provide endpoints for configuring AutoGen agents.

#### Scenario: Get AutoGen agent templates
- **WHEN** GET /api/autogen/agent-templates is called
- **THEN** return list of predefined agent templates:
  - TechnicalAnalystAgent
  - RiskManagerAgent
  - FundamentalAgent
  - SentimentAgent
  - ExecutorAgent
- **AND** each template includes: name, description, default_prompt, recommended_model, required_tools

#### Scenario: Configure strategy AutoGen agents
- **WHEN** PUT /api/strategies/{id}/autogen-config is called with {agents[]}
- **THEN** validate agent configurations
- **AND** each agent SHALL have: agent_name, enabled, system_prompt, llm_config, max_iterations
- **AND** update strategy.param.autogen_config
- **AND** return updated configuration

#### Scenario: Get agent conversation history
- **WHEN** GET /api/workflow-executions/{id}/agent-conversation is called
- **THEN** fetch agent_conversations records for this execution
- **AND** return list of messages ordered by timestamp
- **AND** include: agent_name, message_type, message_content, timestamp, tokens_used

### Requirement: Workflow Analytics Endpoints
The system SHALL provide endpoints for workflow performance analytics.

#### Scenario: Get workflow performance metrics
- **WHEN** GET /api/workflows/{id}/metrics is called
- **THEN** calculate and return:
  - total_executions
  - success_rate
  - average_duration
  - decisions_breakdown (BUY/SELL/HOLD counts)
  - orders_placed
  - average_r_coefficient
  - win_rate (if trades completed)
- **AND** support date_range filter

#### Scenario: Compare workflows
- **WHEN** GET /api/workflows/compare is called with workflow_ids[]
- **THEN** return side-by-side metrics for selected workflows
- **AND** include same metrics as single workflow
- **AND** highlight best-performing workflow for each metric

### Requirement: Scheduled Workflow Endpoints
The system SHALL provide endpoints for scheduling periodic workflow executions.

#### Scenario: Create scheduled workflow
- **WHEN** POST /api/workflows/{id}/schedule is called with {cron_expression, strategy_id, enabled}
- **THEN** create Celery Beat schedule entry
- **AND** store schedule in database
- **AND** return 201 Created with schedule details

#### Scenario: List scheduled workflows
- **WHEN** GET /api/schedules is called
- **THEN** return list of scheduled workflows
- **AND** include: id, workflow_name, strategy_name, cron_expression, enabled, next_run_time, last_run_time

#### Scenario: Update schedule
- **WHEN** PUT /api/schedules/{id} is called
- **THEN** update cron_expression, enabled status
- **AND** update Celery Beat schedule
- **AND** return updated schedule

#### Scenario: Delete schedule
- **WHEN** DELETE /api/schedules/{id} is called
- **THEN** remove from Celery Beat
- **AND** delete schedule record
- **AND** return 204 No Content

