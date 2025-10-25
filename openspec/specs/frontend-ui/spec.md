# frontend-ui Specification

## Purpose
TBD - created by archiving change add-fastapi-trading-webapp. Update Purpose after archive.
## Requirements
### Requirement: Workflow Builder Interface
The system SHALL provide a visual workflow builder for creating and editing workflows.

#### Scenario: Display workflow builder
- **WHEN** user accesses workflow builder page
- **THEN** display visual canvas with workflow steps as connected nodes
- **AND** show toolbar with available step types
- **AND** show workflow properties panel (name, type, description)

#### Scenario: Add workflow step
- **WHEN** user clicks "Add Step" button
- **THEN** display step type selector dropdown
- **AND** available types: fetch_data, generate_chart, ai_analyze, consolidate, decide, validate_risk, place_order, wait
- **AND** on selection, add step node to canvas
- **AND** open step configuration panel

#### Scenario: Configure workflow step
- **WHEN** user clicks on workflow step
- **THEN** display step configuration form in side panel
- **AND** show step-specific fields (e.g., for fetch_data: period, bar, indicators[])
- **AND** allow editing configuration
- **AND** validate inputs on change
- **AND** save configuration to step

#### Scenario: Reorder workflow steps
- **WHEN** user drags a step to new position
- **THEN** update step order
- **AND** update connections between steps
- **AND** re-validate workflow after reorder

#### Scenario: Delete workflow step
- **WHEN** user clicks delete button on step
- **THEN** show confirmation dialog
- **AND** if confirmed, remove step from workflow
- **AND** update connections
- **AND** re-validate workflow

#### Scenario: Save workflow
- **WHEN** user clicks "Save" button
- **THEN** validate workflow structure (at least one data fetch, one decision step)
- **AND** if valid, submit POST /api/workflows or PUT /api/workflows/{id}
- **AND** show success message
- **AND** if invalid, display errors and prevent save

### Requirement: Workflow Template Selection
The system SHALL provide pre-built workflow templates for quick setup.

#### Scenario: Select workflow template
- **WHEN** user creates new workflow
- **THEN** display template gallery with:
  - "2-Indicator Multi-Timeframe" (default from original design)
  - "3-Indicator Multi-Timeframe"
  - "AutoGen Multi-Agent"
  - "Single Timeframe"
  - "Custom" (blank)
- **AND** each template shows preview diagram and description

#### Scenario: Load template
- **WHEN** user selects template
- **THEN** populate workflow canvas with template steps
- **AND** user CAN modify steps
- **AND** user CAN add/remove steps

### Requirement: AutoGen Agent Configuration UI
The system SHALL provide interface for configuring AutoGen agents for strategies.

#### Scenario: Access AutoGen configuration
- **WHEN** user edits strategy and selects workflow type "autogen_multi_agent"
- **THEN** display "Configure AutoGen Agents" section
- **AND** show list of agent types with enable/disable toggles

#### Scenario: Configure individual agent
- **WHEN** user clicks "Configure" on an agent
- **THEN** display agent configuration modal with:
  - Agent name (readonly)
  - Enabled toggle
  - System prompt (textarea, customizable)
  - LLM model selection (dropdown)
  - Temperature slider (0-2)
  - Max iterations (number input)
- **AND** pre-fill with template defaults
- **AND** allow editing

#### Scenario: Save AutoGen configuration
- **WHEN** user saves strategy with AutoGen config
- **THEN** validate at least TechnicalAnalyst, RiskManager, Executor are enabled
- **AND** validate prompts are not empty
- **AND** save to strategy.param.autogen_config
- **AND** show confirmation

### Requirement: Workflow Execution Monitoring
The system SHALL provide real-time monitoring of workflow executions.

#### Scenario: View active workflows
- **WHEN** user accesses workflow execution monitor page
- **THEN** display list of running workflows
- **AND** each entry shows: workflow name, strategy name, status, progress, current step, elapsed time
- **AND** auto-refresh every 5 seconds

#### Scenario: View workflow progress
- **WHEN** viewing running workflow
- **THEN** display progress bar showing percentage complete
- **AND** show current step being executed
- **AND** show completed steps (green checkmark)
- **AND** show pending steps (grey)

#### Scenario: Cancel running workflow
- **WHEN** user clicks "Cancel" on running workflow
- **THEN** show confirmation dialog
- **AND** if confirmed, submit DELETE /api/tasks/{task_id}
- **AND** update status to "Cancelling..."
- **AND** refresh to show "Cancelled" when complete

#### Scenario: View workflow results
- **WHEN** workflow completes
- **THEN** display summary: symbols processed, decisions made, orders placed, errors
- **AND** show link to view detailed logs
- **AND** show link to view decisions generated

### Requirement: Workflow Analytics Dashboard
The system SHALL provide analytics dashboard for workflow performance.

#### Scenario: Display workflow metrics
- **WHEN** user views workflow analytics page
- **THEN** display metrics cards: total executions, success rate, avg duration, total decisions, total orders
- **AND** show charts: executions over time (line), decisions breakdown (pie: BUY/SELL/HOLD), success rate trend

#### Scenario: Compare workflows
- **WHEN** user selects multiple workflows
- **THEN** display side-by-side comparison table
- **AND** highlight best performer for each metric (green)
- **AND** allow filtering by date range

### Requirement: Task Queue Dashboard
The system SHALL provide dashboard for monitoring Celery task queue.

#### Scenario: Display task queue status
- **WHEN** user accesses task queue dashboard
- **THEN** display real-time metrics:
  - Active workers count
  - Tasks queued (by priority: high/normal/low)
  - Tasks active (currently executing)
  - Tasks completed today
  - Tasks failed today
  - Average task duration
- **AND** update metrics every 10 seconds

#### Scenario: View active tasks
- **WHEN** user views active tasks section
- **THEN** display table of currently executing tasks
- **AND** each row shows: task_id, task_name (workflow), strategy, started_at, elapsed_time, progress
- **AND** provide "Cancel" button for each task

### Requirement: Scheduled Workflows Interface
The system SHALL provide interface for scheduling periodic workflow executions.

#### Scenario: Create schedule
- **WHEN** user clicks "Schedule" on workflow
- **THEN** display schedule creation modal
- **AND** show fields: workflow (pre-selected), strategy (dropdown), cron expression (with helper), enabled (toggle), description
- **AND** provide cron helper: "Every X hours/days/weeks" selector
- **AND** show preview of next 5 run times

#### Scenario: List scheduled workflows
- **WHEN** user views schedules page
- **THEN** display table of schedules
- **AND** each row shows: workflow name, strategy, schedule (cron or friendly), enabled, next run, last run, actions
- **AND** provide enable/disable toggle
- **AND** provide edit and delete buttons

#### Scenario: Edit schedule
- **WHEN** user edits schedule
- **THEN** display same form as create with pre-filled values
- **AND** allow changing cron expression, strategy, enabled status
- **AND** update next run time preview when cron changes

### Requirement: Strategy-Workflow Association UI
The system SHALL update strategy management UI to support workflow selection.

#### Scenario: Select workflow for strategy
- **WHEN** user creates or edits strategy
- **THEN** display "Workflow" dropdown with available workflows
- **AND** show workflow type badge next to name (e.g., "AutoGen", "Multi-TF")
- **AND** when workflow is selected, load and display workflow parameters

#### Scenario: Override workflow parameters
- **WHEN** workflow is selected
- **THEN** display workflow default parameters
- **AND** allow overriding parameters at strategy level
- **AND** mark overridden parameters with indicator
- **AND** show reset button to revert to workflow default

### Requirement: Agent Conversation Viewer
The system SHALL provide interface to view AutoGen agent conversations.

#### Scenario: View agent conversation
- **WHEN** user views workflow execution with AutoGen
- **THEN** display "Agent Conversation" tab
- **AND** show conversation thread with messages in chat-like format
- **AND** each message shows: agent avatar/icon, agent name, message content, timestamp

#### Scenario: Conversation formatting
- **WHEN** displaying conversation
- **THEN** use different colors for each agent type
- **AND** highlight final decision message from ExecutorAgent
- **AND** allow expanding/collapsing messages for readability
- **AND** show token count per message

### Requirement: Workflow Version History UI
The system SHALL provide interface for viewing and managing workflow versions.

#### Scenario: View workflow versions
- **WHEN** user views workflow details
- **THEN** display "Version History" section
- **AND** list all versions with: version number, created date, creator, changes summary
- **AND** show "Current" badge on active version

#### Scenario: Compare workflow versions
- **WHEN** user selects two versions to compare
- **THEN** display side-by-side diff of workflow steps
- **AND** highlight added steps (green), removed steps (red), modified steps (yellow)

#### Scenario: Revert to previous version
- **WHEN** user clicks "Revert" on old version
- **THEN** show confirmation dialog
- **AND** if confirmed, create new version with old version's content
- **AND** mark as "Reverted from v{X}"
- **AND** refresh to show new version as current

