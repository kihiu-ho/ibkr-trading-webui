## ADDED Requirements

### Requirement: Workflow Trigger UI Feedback
The system SHALL provide immediate and clear feedback when users trigger workflows.

#### Scenario: Trigger button state management
- **WHEN** user views workflow card
- **THEN** trigger button SHALL be enabled if:
  - DAG is not paused
  - DAG has no import errors
  - Active runs count is less than max_active_runs limit
- **AND** trigger button SHALL be disabled with tooltip if:
  - DAG is paused (tooltip: "DAG is paused")
  - DAG has import errors (tooltip: "DAG has import errors")
  - Maximum active runs reached (tooltip: "Maximum active runs reached. Cancel active run to trigger new one.")
- **AND** button state SHALL update automatically when conditions change

#### Scenario: Trigger confirmation with context
- **WHEN** user clicks trigger button
- **THEN** confirmation dialog SHALL display:
  - DAG name and description
  - Current active runs count
  - Estimated wait time if run will be queued
  - Option to cancel active run before triggering
  - DAG configuration summary if available
- **AND** user SHALL be able to proceed with trigger or cancel
- **AND** if active run exists, user SHALL see option to cancel it first

#### Scenario: Trigger loading and success feedback
- **WHEN** user confirms trigger
- **THEN** trigger button SHALL show loading state
- **AND** loading spinner SHALL be displayed
- **AND** after successful trigger, SHALL display:
  - Success message with run ID
  - Run status (running or queued)
  - Link to view run details
  - Estimated start time if queued
- **AND** DAG list SHALL auto-refresh to show new run
- **AND** newly triggered run SHALL be highlighted in runs table

#### Scenario: Trigger error feedback
- **WHEN** trigger request fails
- **THEN** error message SHALL be displayed
- **AND** error message SHALL be user-friendly and actionable
- **AND** error message SHALL explain:
  - What went wrong
  - Why it happened
  - How to fix it
- **AND** error SHALL be logged to console for debugging
- **AND** user SHALL be able to retry trigger after fixing issue

#### Scenario: Active run detection and display
- **WHEN** workflow has active runs
- **THEN** active run information SHALL be displayed on workflow card
- **AND** information SHALL include:
  - Run ID
  - Start time
  - Duration
  - Current status
  - Link to view run details
- **AND** if max_active_runs limit reached, warning SHALL be displayed
- **AND** user SHALL see option to cancel active run
- **AND** trigger button SHALL show why it's disabled if applicable

#### Scenario: Queued run status display
- **WHEN** workflow run is queued due to max_active_runs
- **THEN** queued status SHALL be clearly displayed
- **AND** queued run SHALL show:
  - Queued timestamp
  - Active run blocking it (run ID, start time, duration)
  - Estimated wait time
  - Auto-refresh to show when it starts
- **AND** status SHALL update automatically when run starts
- **AND** user SHALL understand why run is queued

## MODIFIED Requirements

### Requirement: Workflow Execution Visualization
The system SHALL provide real-time visualization of workflow execution with lineage tracking and step-by-step progress.

#### Scenario: View workflow execution graph
- **WHEN** user navigates to workflow execution page
- **THEN** a directed acyclic graph (DAG) SHALL be displayed
- **AND** each node SHALL represent a workflow step
- **AND** edges SHALL show data flow between steps
- **AND** nodes SHALL be color-coded by status (pending/running/completed/failed)
- **AND** trigger status SHALL be clearly indicated
- **AND** queued runs SHALL be displayed with queued status

#### Scenario: Real-time execution updates
- **WHEN** workflow is executing
- **THEN** the visualization SHALL update in real-time
- **AND** currently executing step SHALL be highlighted
- **AND** completed steps SHALL show success/failure indicators
- **AND** timing information SHALL be displayed for each step
- **AND** trigger events SHALL be reflected immediately
- **AND** queued runs SHALL be monitored and updated when they start

