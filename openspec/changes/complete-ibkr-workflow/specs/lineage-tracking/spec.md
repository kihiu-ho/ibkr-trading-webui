# Lineage Tracking Capability - Spec Deltas

## ADDED Requirements

### Requirement: Workflow Step Lineage Recording
The system SHALL record the input and output of each step in the trading workflow execution for complete traceability.

#### Scenario: Record step execution
- **WHEN** a workflow step is executed
- **THEN** the system SHALL record:
  - Execution ID (unique identifier for the workflow run)
  - Step name (e.g., "fetch_market_data", "llm_analysis")
  - Step number (sequential order: 1, 2, 3, ...)
  - Input data (JSON object with all inputs to the step)
  - Output data (JSON object with all outputs from the step)
  - Metadata (strategy ID, user ID, etc.)
  - Execution duration in milliseconds
  - Status (success or error)
  - Error message (if applicable)
  - Timestamp
- **AND** the record SHALL be stored in the `workflow_lineage` table

#### Scenario: Record step with error
- **WHEN** a workflow step fails with an error
- **THEN** the system SHALL record the step with status "error"
- **AND** the system SHALL capture the full error message and stack trace
- **AND** the system SHALL record partial output data if available
- **AND** the lineage SHALL be queryable for debugging

### Requirement: Lineage Query API
The system SHALL provide APIs to query workflow lineage by execution ID, strategy, or step name.

#### Scenario: Get complete execution lineage
- **WHEN** a user requests lineage for an execution ID
- **THEN** the system SHALL return all steps for that execution
- **AND** steps SHALL be ordered by step number (1, 2, 3, ...)
- **AND** each step SHALL include full input data, output data, and metadata
- **AND** the response SHALL indicate if any steps had errors

#### Scenario: Get lineage for specific step
- **WHEN** a user requests lineage for a specific step in an execution
- **THEN** the system SHALL return the complete record for that step
- **AND** the record SHALL include input data, output data, duration, and status
- **AND** if the step had an error, the error details SHALL be included

#### Scenario: Get recent executions for strategy
- **WHEN** a user requests recent executions for a strategy
- **THEN** the system SHALL return up to 100 most recent execution IDs
- **AND** each execution SHALL include: execution ID, execution time, and status
- **AND** results SHALL be ordered by execution time (newest first)

#### Scenario: Get step statistics
- **WHEN** a user requests statistics for a specific step (e.g., "llm_analysis")
- **THEN** the system SHALL calculate and return:
  - Total executions of that step
  - Success count
  - Error count
  - Success rate
  - Average duration
  - Min and max duration
  - Most common errors
- **AND** statistics SHALL be filterable by strategy and date range

### Requirement: Lineage Visualization Frontend
The system SHALL provide a web UI to visualize workflow execution lineage.

#### Scenario: View execution lineage
- **WHEN** a user navigates to the lineage viewer
- **THEN** the user SHALL be able to select a strategy from a dropdown
- **AND** after selecting a strategy, the user SHALL see a list of recent executions
- **AND** after selecting an execution, the user SHALL see all steps visualized as cards
- **AND** each step card SHALL display:
  - Step number and name
  - Status badge (success or error)
  - Execution duration
  - Input data (formatted JSON)
  - Output data (formatted JSON) or error message
- **AND** steps SHALL be connected with arrow indicators showing flow

#### Scenario: View step details with rich visualization
- **WHEN** a user clicks "View Full Details" on a step card
- **THEN** the system SHALL open a modal with complete step information
- **AND** the system SHALL display a rich visualization based on step type:
  - **Strategy steps**: Configuration table with badges
  - **Market data steps**: Symbol, price, and data range cards
  - **Indicator steps**: Table of all indicator values
  - **Chart steps**: Actual chart images (clickable to open full size)
  - **LLM analysis steps**: Full analysis text in readable format
  - **Signal steps**: Large signal badges (BUY/SELL), price cards, risk/reward calculation
  - **Order steps**: Order status badges, quantity, price, total value
  - **Unknown steps**: Generic input/output JSON display
- **AND** raw JSON data SHALL be available in collapsible sections
- **AND** JSON data SHALL be syntax-highlighted for readability

#### Scenario: View chart images in lineage
- **WHEN** viewing a "generate_charts" step
- **THEN** the system SHALL display the actual chart images
- **AND** each chart SHALL show the timeframe (daily, weekly, etc.)
- **AND** clicking a chart SHALL open it in full size in a new window
- **AND** the chart URLs SHALL be retrieved from the output data

#### Scenario: View LLM analysis text
- **WHEN** viewing an "llm_analysis" step
- **THEN** the system SHALL display the full analysis text
- **AND** the text SHALL be formatted with proper line breaks and spacing
- **AND** the text SHALL be scrollable if it exceeds the viewport
- **AND** the model used SHALL be displayed as a badge
- **AND** the analysis length SHALL be shown

#### Scenario: View trading signal details
- **WHEN** viewing a "parse_signal" step
- **THEN** the system SHALL display:
  - Signal action (BUY/SELL/HOLD) as a large colored badge
  - Entry price, stop loss, and target price in separate cards
  - Confidence percentage
  - Calculated risk/reward ratio
  - Visual color coding (green for BUY, red for SELL, gray for HOLD)
- **AND** if risk/reward data is available, the system SHALL calculate and display:
  - Risk amount (entry - stop loss)
  - Reward amount (target - entry)
  - R:R ratio (e.g., "1:2.5")

#### Scenario: Navigate from strategy to lineage
- **WHEN** a user is viewing a strategy's execution history
- **THEN** each execution SHALL have a "View Lineage" button
- **AND** clicking the button SHALL navigate to the lineage viewer for that execution
- **AND** the lineage viewer SHALL automatically load and display the execution's steps

### Requirement: Lineage Data Retention
The system SHALL retain lineage data for a configurable period for historical analysis and debugging.

#### Scenario: Automatic lineage cleanup
- **WHEN** lineage records exceed the retention period (default: 90 days)
- **THEN** the system SHALL automatically delete old records
- **AND** the cleanup SHALL run as a scheduled task (e.g., weekly)
- **AND** the cleanup SHALL retain lineage for executions with errors for longer (e.g., 180 days)

#### Scenario: Query lineage within retention period
- **WHEN** a user queries lineage
- **THEN** the system SHALL return all records within the retention period
- **AND** records older than the retention period SHALL not be accessible

### Requirement: Performance Impact Minimization
The system SHALL record lineage with minimal impact on workflow execution performance.

#### Scenario: Asynchronous lineage recording
- **WHEN** a workflow step completes
- **THEN** lineage recording SHALL occur asynchronously
- **AND** lineage recording SHALL not block the next step from starting
- **AND** if lineage recording fails, the workflow SHALL continue normally
- **AND** lineage recording failures SHALL be logged but not raise exceptions

#### Scenario: Lineage recording performance
- **WHEN** recording a lineage step
- **THEN** the recording operation SHALL complete in less than 100ms
- **AND** the recording SHALL not cause noticeable delays in workflow execution

---

## MODIFIED Requirements

_None - this is a new capability_

---

## REMOVED Requirements

_None - this is a new capability_


