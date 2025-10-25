# Database Schema Specification

## ADDED Requirements

### Requirement: PostgreSQL Database Schema
The system SHALL provide a PostgreSQL database schema to persist all trading-related data including strategies, instruments, market data, trading decisions, orders, trades, and positions.

#### Scenario: Database initialization
- **WHEN** the application starts for the first time
- **THEN** all required tables SHALL be created with proper schema
- **AND** foreign key constraints SHALL be established
- **AND** indexes SHALL be created for performance

#### Scenario: Schema validation
- **WHEN** the application connects to the database
- **THEN** the schema version SHALL be validated
- **AND** migrations SHALL be applied if needed

### Requirement: Strategy Table
The system SHALL maintain a `strategy` table to store trading strategy configurations.

#### Scenario: Store strategy configuration
- **WHEN** a new strategy is created
- **THEN** it SHALL be stored with fields: id, name, type, param (JSONB), created_at, updated_at
- **AND** param SHALL contain JSON with configurable timeframe parameters (period_1, bar_1, period_2, bar_2)
- **AND** type SHALL indicate the strategy type (e.g., "two_indicator")

### Requirement: Code Table
The system SHALL maintain a `code` table to store financial instrument information.

#### Scenario: Store instrument details
- **WHEN** a financial instrument is added
- **THEN** it SHALL be stored with fields: id, symbol, conid (IBKR contract ID), exchange, created_at, updated_at
- **AND** conid SHALL be unique
- **AND** symbol SHALL be indexed for fast lookup

### Requirement: Strategy-Code Relationship
The system SHALL maintain a many-to-many relationship between strategies and codes through a junction table.

#### Scenario: Associate codes with strategy
- **WHEN** a strategy is configured with multiple symbols
- **THEN** each symbol SHALL be linked via `strategy_codes` junction table
- **AND** the relationship SHALL support multiple strategies using the same symbol
- **AND** deleting a strategy SHALL remove the associations but not the codes

### Requirement: Market Data Table
The system SHALL maintain a `market_data` table to cache historical price and indicator data.

#### Scenario: Cache market data
- **WHEN** historical data is fetched from IBKR
- **THEN** it SHALL be stored with fields: id, conid, period, bar, data (JSONB), created_at
- **AND** data SHALL contain OHLCV and indicator calculations
- **AND** (conid, period, bar) SHALL be indexed for fast retrieval
- **AND** expired data SHALL be identifiable by created_at timestamp

#### Scenario: Retrieve cached data
- **WHEN** workflow requests historical data
- **THEN** the system SHALL check if recent data exists (< 1 hour old)
- **AND** return cached data if available
- **AND** fetch fresh data from IBKR if cache is stale

### Requirement: Decision Table
The system SHALL maintain a `decision` table to store AI-generated trading recommendations.

#### Scenario: Store trading decision
- **WHEN** AI analysis generates a trading decision
- **THEN** it SHALL be stored with fields: id, code_id, strategy_id, type (buy/sell/hold), current_price, target_price, stop_loss, profit_margin, r_coefficient, analysis_text, created_at
- **AND** type SHALL be one of: 'buy', 'sell', 'hold'
- **AND** r_coefficient SHALL be calculated as (target_price - current_price) / (stop_loss - current_price)
- **AND** profit_margin SHALL be calculated as |target_price - current_price| / current_price
- **AND** analysis_text SHALL contain the full AI-generated analysis

#### Scenario: Link decision to code and strategy
- **WHEN** a decision is stored
- **THEN** it SHALL have a foreign key to the code table
- **AND** it SHALL have a foreign key to the strategy table
- **AND** these relationships SHALL enable querying which strategy generated which decisions

### Requirement: Orders Table
The system SHALL maintain an `orders` table to track all order lifecycle events.

#### Scenario: Store order placement
- **WHEN** an order is placed with IBKR
- **THEN** it SHALL be stored with fields: id, decision_id, ibkr_order_id, conid, side (BUY/SELL), quantity, price, order_type (LMT/MKT), tif (GTC/DAY), status, created_at, updated_at
- **AND** decision_id SHALL link to the decision that triggered the order
- **AND** ibkr_order_id SHALL store IBKR's order identifier
- **AND** status SHALL be one of: 'submitted', 'filled', 'partially_filled', 'cancelled', 'rejected'

#### Scenario: Update order status
- **WHEN** an order status changes
- **THEN** the status field SHALL be updated
- **AND** updated_at SHALL be refreshed
- **AND** if status is 'filled', a trade record SHALL be created

#### Scenario: Track order history
- **WHEN** querying order history
- **THEN** orders SHALL be retrievable by date range, status, or symbol
- **AND** associated decision and strategy SHALL be joinable

### Requirement: Trades Table
The system SHALL maintain a `trades` table to record executed trades and their outcomes.

#### Scenario: Record completed trade
- **WHEN** an order is filled
- **THEN** a trade record SHALL be created with fields: id, order_id, conid, entry_price, entry_quantity, entry_date, exit_price, exit_quantity, exit_date, realized_pnl, created_at, updated_at
- **AND** order_id SHALL link to the orders table
- **AND** realized_pnl SHALL be calculated when exit occurs

#### Scenario: Calculate trade P&L
- **WHEN** a position is closed
- **THEN** realized_pnl SHALL be calculated as (exit_price - entry_price) * quantity
- **AND** the result SHALL account for buy vs sell side

### Requirement: Positions Table
The system SHALL maintain a `positions` table to track current open positions.

#### Scenario: Track open position
- **WHEN** a trade opens a position
- **THEN** it SHALL be stored with fields: id, conid, quantity, average_cost, current_price, unrealized_pnl, updated_at
- **AND** average_cost SHALL be calculated considering all entry trades
- **AND** unrealized_pnl SHALL be (current_price - average_cost) * quantity
- **AND** positions SHALL be updated whenever new trades occur or prices refresh

#### Scenario: Close position
- **WHEN** a position is fully exited
- **THEN** the position record SHALL be removed or marked as closed
- **AND** the final trade SHALL calculate realized P&L

### Requirement: Database Indexes
The system SHALL create indexes for optimal query performance.

#### Scenario: Query performance optimization
- **WHEN** the database is initialized
- **THEN** indexes SHALL be created on:
  - code.conid (unique)
  - code.symbol
  - market_data(conid, period, bar)
  - decision.code_id
  - decision.strategy_id
  - decision.created_at
  - orders.ibkr_order_id
  - orders.status
  - orders.created_at
  - trades.order_id
  - positions.conid

### Requirement: Database Migrations
The system SHALL use Alembic for database schema migrations.

#### Scenario: Apply migrations
- **WHEN** the application starts
- **THEN** pending migrations SHALL be automatically detected
- **AND** migrations SHALL be applied in order
- **AND** migration failures SHALL prevent application startup

#### Scenario: Rollback migrations
- **WHEN** a migration causes issues
- **THEN** migrations SHALL be rollback-able using Alembic
- **AND** data integrity SHALL be preserved during rollback

## ADDED Requirements

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

