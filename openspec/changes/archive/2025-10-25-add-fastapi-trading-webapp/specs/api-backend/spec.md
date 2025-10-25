# API Backend Specification

## ADDED Requirements

### Requirement: FastAPI Application Setup
The system SHALL provide a RESTful API using FastAPI framework with automatic OpenAPI documentation.

#### Scenario: Application initialization
- **WHEN** the backend starts
- **THEN** FastAPI app SHALL be initialized with proper configuration
- **AND** CORS middleware SHALL be configured for frontend access
- **AND** database connection pool SHALL be established
- **AND** OpenAPI documentation SHALL be available at /docs

#### Scenario: Health check endpoint
- **WHEN** GET /api/health is called
- **THEN** return 200 OK with system status
- **AND** include: database connection status, IBKR API status, MinIO status
- **AND** return 503 if any critical service is unavailable

### Requirement: Authentication Endpoints
The system SHALL provide endpoints to check IBKR authentication status.

#### Scenario: Check IBKR authentication
- **WHEN** GET /api/authenticate is called
- **THEN** call IBKR API status endpoint
- **AND** return {authenticated: true/false, account_id: string}
- **AND** cache result for 30 seconds to avoid excessive checks

### Requirement: Strategy Management Endpoints
The system SHALL provide CRUD endpoints for trading strategies.

#### Scenario: List strategies
- **WHEN** GET /api/strategies is called
- **THEN** return list of all strategies with: id, name, type, param, created_at
- **AND** support pagination with query params: limit, offset
- **AND** support filtering by type

#### Scenario: Create strategy
- **WHEN** POST /api/strategies is called with valid payload
- **THEN** validate: name is unique, type is valid, param is valid JSON
- **AND** create strategy record in database
- **AND** return 201 Created with strategy details

#### Scenario: Get strategy details
- **WHEN** GET /api/strategies/{id} is called
- **THEN** return strategy with associated codes
- **AND** return 404 if strategy not found

#### Scenario: Update strategy
- **WHEN** PUT /api/strategies/{id} is called
- **THEN** validate updated fields
- **AND** update strategy record
- **AND** return updated strategy
- **AND** return 404 if not found

#### Scenario: Delete strategy
- **WHEN** DELETE /api/strategies/{id} is called
- **THEN** remove strategy and associations from database
- **AND** return 204 No Content
- **AND** return 404 if not found

### Requirement: Workflow Execution Endpoints
The system SHALL provide endpoints to execute and monitor trading workflows.

#### Scenario: Execute workflow
- **WHEN** POST /api/workflow/execute is called with {strategy_id, symbols[]}
- **THEN** validate strategy exists
- **AND** start workflow execution asynchronously
- **AND** return 202 Accepted with workflow_id
- **AND** workflow status SHALL be 'running'

#### Scenario: Get workflow status
- **WHEN** GET /api/workflow/status/{id} is called
- **THEN** return workflow status: {id, status, progress, current_symbol, completed_symbols, total_symbols, started_at, completed_at}
- **AND** return 404 if workflow_id not found

### Requirement: Chart Endpoints
The system SHALL provide endpoints for chart generation and retrieval.

#### Scenario: Generate chart
- **WHEN** GET /api/charts/{conid} is called with query params: period, bar, mode
- **THEN** fetch historical data (cached or fresh)
- **AND** generate chart with indicators
- **AND** upload to MinIO
- **AND** return {chart_url, generated_at}

#### Scenario: Get chart history
- **WHEN** GET /api/charts/history/{conid} is called
- **THEN** return list of previously generated charts
- **AND** include: chart_url, period, bar, generated_at
- **AND** sort by generated_at descending

### Requirement: Order Management Endpoints
The system SHALL provide endpoints for order lifecycle management.

#### Scenario: Place order
- **WHEN** POST /api/orders is called with {conid, side, price, quantity, order_type, tif}
- **THEN** validate order parameters
- **AND** submit order to IBKR
- **AND** store order in database
- **AND** return 201 Created with order details and IBKR order_id

#### Scenario: List orders
- **WHEN** GET /api/orders is called
- **THEN** return list of orders with filters: status, symbol, date_range
- **AND** support pagination
- **AND** include associated decision and strategy

#### Scenario: Get order details
- **WHEN** GET /api/orders/{id} is called
- **THEN** return complete order details
- **AND** include current status from IBKR if order is active
- **AND** return 404 if not found

#### Scenario: Cancel order
- **WHEN** DELETE /api/orders/{id} is called
- **THEN** cancel order via IBKR API
- **AND** update order status to 'cancelled'
- **AND** return 200 OK with cancellation confirmation

### Requirement: Portfolio Endpoints
The system SHALL provide endpoints for portfolio and position management.

#### Scenario: Get portfolio summary
- **WHEN** GET /api/portfolio is called
- **THEN** return: total_value, realized_pnl, unrealized_pnl, open_positions_count, win_rate, trade_count

#### Scenario: Get positions
- **WHEN** GET /api/portfolio/positions is called
- **THEN** return list of open positions with: symbol, conid, quantity, average_cost, current_price, unrealized_pnl
- **AND** sync with IBKR positions if requested

#### Scenario: Get trade history
- **WHEN** GET /api/portfolio/trades is called
- **THEN** return closed trades with filters: date_range, symbol, strategy
- **AND** include: entry/exit dates, prices, realized_pnl
- **AND** support pagination

### Requirement: Decision Endpoints
The system SHALL provide endpoints for viewing trading decisions.

#### Scenario: List decisions
- **WHEN** GET /api/decisions is called
- **THEN** return list of decisions with filters: type, strategy, symbol, date_range
- **AND** include: code, type, current_price, target_price, r_coefficient, profit_margin, created_at
- **AND** support pagination

#### Scenario: Get decision details
- **WHEN** GET /api/decisions/{id} is called
- **THEN** return complete decision with full analysis_text
- **AND** include associated order if placed
- **AND** return 404 if not found

### Requirement: Request Validation
The system SHALL validate all API requests using Pydantic schemas.

#### Scenario: Invalid request payload
- **WHEN** API receives invalid request body
- **THEN** return 422 Unprocessable Entity
- **AND** include detailed validation errors with field names
- **AND** log validation error

#### Scenario: Missing required fields
- **WHEN** required fields are missing from request
- **THEN** return 422 with "field required" errors
- **AND** specify which fields are missing

### Requirement: Error Handling
The system SHALL handle errors consistently and provide meaningful responses.

#### Scenario: Internal server error
- **WHEN** an unexpected error occurs
- **THEN** return 500 Internal Server Error
- **AND** log error with full stack trace
- **AND** return generic error message to client (no sensitive details)

#### Scenario: External API error
- **WHEN** IBKR API call fails
- **THEN** return 502 Bad Gateway
- **AND** include error message from IBKR if available
- **AND** log error for debugging

### Requirement: API Documentation
The system SHALL provide comprehensive API documentation.

#### Scenario: OpenAPI schema
- **WHEN** user accesses /docs
- **THEN** display interactive Swagger UI with all endpoints
- **AND** include request/response schemas
- **AND** provide example payloads
- **AND** allow testing endpoints directly from UI

#### Scenario: ReDoc documentation
- **WHEN** user accesses /redoc
- **THEN** display ReDoc alternative documentation view
- **AND** provide searchable, well-organized API reference

## ADDED Requirements

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

