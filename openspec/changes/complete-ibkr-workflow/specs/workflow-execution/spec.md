# Workflow Execution Capability - Spec Deltas

## ADDED Requirements

### Requirement: Complete Trading Workflow Execution
The system SHALL execute a complete end-to-end automated trading workflow from market data fetching to order placement.

#### Scenario: Successful workflow execution
- **WHEN** a strategy is triggered by Celery Beat schedule
- **THEN** the system SHALL execute all steps in sequence:
  1. Load strategy configuration
  2. Fetch market data from IBKR
  3. Calculate technical indicators
  4. Generate charts
  5. Analyze charts with LLM
  6. Parse trading signal
  7. Place orders (if signal present)
  8. Record execution results
- **AND** the entire workflow SHALL complete in less than 5 minutes
- **AND** all steps SHALL be recorded in the lineage tracker

#### Scenario: Workflow execution with error recovery
- **WHEN** a step in the workflow fails
- **THEN** the system SHALL record the error in the lineage tracker
- **AND** the system SHALL attempt to gracefully handle the error
- **AND** the system SHALL not proceed to subsequent steps if a critical error occurs
- **AND** the system SHALL notify administrators of the failure

### Requirement: Strategy Scheduling
The system SHALL support cron-based scheduling of strategy executions.

#### Scenario: Create scheduled strategy
- **WHEN** a user creates a strategy with a cron schedule (e.g., "0 9 * * MON-FRI")
- **THEN** the system SHALL register the schedule with Celery Beat
- **AND** the strategy SHALL execute automatically at the specified times
- **AND** the user SHALL be able to view the next execution time

#### Scenario: Update strategy schedule
- **WHEN** a user updates a strategy's schedule
- **THEN** the system SHALL update the Celery Beat schedule
- **AND** the next execution time SHALL reflect the new schedule
- **AND** the change SHALL take effect immediately

#### Scenario: Disable strategy execution
- **WHEN** a user deactivates a strategy
- **THEN** the system SHALL skip execution of that strategy
- **AND** the Celery Beat schedule SHALL remain in place for future reactivation

### Requirement: Symbol Search and Contract Management
The system SHALL provide symbol search functionality using IBKR's API.

#### Scenario: Search for symbol
- **WHEN** a user searches for a symbol (e.g., "AAPL")
- **THEN** the system SHALL query IBKR's API for matching symbols
- **AND** the system SHALL return results including symbol name, contract ID (conid), exchange, and asset type
- **AND** the system SHALL cache results for 1 hour to improve performance

#### Scenario: Get contract details
- **WHEN** a user selects a symbol
- **THEN** the system SHALL retrieve detailed contract information from IBKR
- **AND** the system SHALL store the contract details in the database
- **AND** the system SHALL display currency, expiry (if applicable), and multiplier

### Requirement: Strategy Execution History
The system SHALL maintain a complete history of all strategy executions.

#### Scenario: View execution history
- **WHEN** a user views a strategy's execution history
- **THEN** the system SHALL display all past executions
- **AND** each execution SHALL show: execution time, signal generated, orders placed, and execution status
- **AND** the user SHALL be able to view the full lineage of any execution

#### Scenario: Query recent executions
- **WHEN** a user requests recent executions for a strategy
- **THEN** the system SHALL return up to 100 most recent executions
- **AND** results SHALL be ordered by execution time (newest first)
- **AND** each execution SHALL include a summary of outcomes

---

## MODIFIED Requirements

### Requirement: Strategy Configuration
The system SHALL support comprehensive strategy configuration including symbol, indicators, prompts, schedule, and risk parameters.

#### Scenario: Create complete strategy
- **WHEN** a user creates a new strategy
- **THEN** the user SHALL select:
  - A trading symbol (via IBKR search)
  - One or more technical indicators with parameters
  - An LLM prompt template (global or strategy-specific)
  - A cron schedule for automatic execution
  - Risk management parameters (risk per trade, stop loss type, position sizing)
- **AND** the system SHALL validate all configurations before saving
- **AND** the system SHALL create a Celery Beat schedule for the strategy

#### Scenario: Strategy validation
- **WHEN** a user submits a strategy configuration
- **THEN** the system SHALL validate:
  - Symbol exists and is tradable
  - Indicator parameters are within valid ranges
  - Prompt template is active and accessible
  - Cron schedule is valid
  - Risk parameters are reasonable (e.g., risk per trade ≤ 5%)
- **AND** the system SHALL return clear error messages for invalid configurations

---

## REMOVED Requirements

_None - this is a new capability_


