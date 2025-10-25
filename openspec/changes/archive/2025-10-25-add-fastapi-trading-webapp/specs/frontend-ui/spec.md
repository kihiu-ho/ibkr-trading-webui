# Frontend UI Specification

## ADDED Requirements

### Requirement: Base Layout with Tailwind CSS
The system SHALL provide a responsive base layout using Tailwind CSS utility classes.

#### Scenario: Base layout rendering
- **WHEN** any page loads
- **THEN** render base layout with: navigation header, main content area, footer
- **AND** apply Tailwind CSS for responsive design
- **AND** include dark mode support (optional)
- **AND** ensure mobile-friendly breakpoints

#### Scenario: Navigation menu
- **WHEN** base layout renders
- **THEN** display navigation menu with links: Dashboard, Strategies, Orders, Portfolio, Charts, Workflow
- **AND** highlight active page
- **AND** collapse to hamburger menu on mobile

### Requirement: Dashboard Page
The system SHALL provide a comprehensive dashboard with key metrics and recent activity.

#### Scenario: Display account summary
- **WHEN** dashboard loads
- **THEN** fetch and display: total portfolio value, realized P&L, unrealized P&L, cash balance
- **AND** show percentage change from previous day
- **AND** use color coding: green for gains, red for losses

#### Scenario: Display active positions
- **WHEN** dashboard loads
- **THEN** fetch and display top 5 positions by value
- **AND** show: symbol, quantity, current price, unrealized P&L, % gain/loss
- **AND** provide link to full portfolio page

#### Scenario: Display recent trades
- **WHEN** dashboard loads
- **THEN** fetch and display last 10 closed trades
- **AND** show: symbol, entry/exit dates, realized P&L
- **AND** provide link to full trade history

#### Scenario: Display recent decisions
- **WHEN** dashboard loads
- **THEN** fetch and display last 5 trading decisions
- **AND** show: symbol, type (buy/sell), current_price, target_price, decision timestamp
- **AND** indicate if order was placed

### Requirement: Strategy Management Page
The system SHALL provide UI for creating and managing trading strategies.

#### Scenario: List strategies
- **WHEN** strategies page loads
- **THEN** display table of all strategies with: name, type, associated symbols count, created date
- **AND** provide actions: View, Edit, Delete
- **AND** include "Create New Strategy" button

#### Scenario: Create strategy form
- **WHEN** user clicks "Create New Strategy"
- **THEN** display form with fields: name, type (dropdown), parameters (JSON editor or form fields for period_1, bar_1, period_2, bar_2)
- **AND** include symbol selection (multi-select or comma-separated input)
- **AND** validate inputs client-side before submission
- **AND** submit via POST /api/strategies

#### Scenario: Edit strategy form
- **WHEN** user clicks Edit on a strategy
- **THEN** pre-populate form with existing strategy data
- **AND** allow updating all fields
- **AND** submit via PUT /api/strategies/{id}

#### Scenario: Delete strategy confirmation
- **WHEN** user clicks Delete on a strategy
- **THEN** show confirmation dialog "Are you sure you want to delete this strategy?"
- **AND** if confirmed, submit DELETE /api/strategies/{id}
- **AND** refresh strategy list on success

### Requirement: Workflow Execution Page
The system SHALL provide UI for executing and monitoring trading workflows.

#### Scenario: Workflow trigger interface
- **WHEN** workflow page loads
- **THEN** display list of strategies with "Execute Workflow" button for each
- **AND** include optional settings: specific symbols to process, delay between symbols

#### Scenario: Execute workflow
- **WHEN** user clicks "Execute Workflow" for a strategy
- **THEN** submit POST /api/workflow/execute with strategy_id
- **AND** display "Workflow started" notification
- **AND** redirect to workflow status view

#### Scenario: Workflow status display
- **WHEN** viewing workflow status
- **THEN** display: workflow ID, status (running/completed/failed), progress bar, current symbol being processed, completed symbols list, estimated time remaining
- **AND** auto-refresh status every 5 seconds while running
- **AND** show completion summary when done

#### Scenario: View workflow results
- **WHEN** workflow completes
- **THEN** display summary: total symbols processed, decisions made, orders placed, errors encountered
- **AND** provide links to view decisions and orders
- **AND** show detailed logs (collapsible sections)

### Requirement: Order Management Page
The system SHALL provide UI for viewing and managing orders.

#### Scenario: Display active orders
- **WHEN** orders page loads
- **THEN** display table of active orders (status: submitted, partially_filled)
- **AND** show: symbol, side, quantity, price, status, submitted time
- **AND** provide "Cancel" button for each active order

#### Scenario: Display order history
- **WHEN** user clicks "Order History" tab
- **THEN** display all historical orders with filters: date range, status, symbol
- **AND** support pagination
- **AND** show: symbol, side, quantity, fill price, status, submitted/filled times

#### Scenario: Cancel order
- **WHEN** user clicks "Cancel" on an order
- **THEN** submit DELETE /api/orders/{id}
- **AND** show confirmation "Order cancelled"
- **AND** update order list

#### Scenario: Place manual order form
- **WHEN** user clicks "Place Order" button
- **THEN** display form with: symbol lookup, side (buy/sell), quantity, price, order type (limit/market), TIF
- **AND** validate inputs
- **AND** submit via POST /api/orders
- **AND** show confirmation with order details

### Requirement: Portfolio Page
The system SHALL provide detailed portfolio views and metrics.

#### Scenario: Display positions
- **WHEN** portfolio page loads
- **THEN** display table of all open positions
- **AND** show: symbol, quantity, average cost, current price, market value, unrealized P&L, % gain/loss
- **AND** calculate and display totals

#### Scenario: Display P&L breakdown
- **WHEN** user views P&L section
- **THEN** display: realized P&L (today, this week, this month, all time), unrealized P&L (total)
- **AND** show charts: P&L over time (line chart), P&L by strategy (pie chart)

#### Scenario: Display performance metrics
- **WHEN** user views performance section
- **THEN** display: win rate, average R achieved, profit factor, total trades, average gain per trade
- **AND** show comparison to benchmarks if available

#### Scenario: Display trade history
- **WHEN** user views trade history section
- **THEN** display table of closed trades with pagination
- **AND** show: symbol, entry/exit dates, entry/exit prices, quantity, realized P&L, holding period
- **AND** allow filtering by date range, symbol, strategy

### Requirement: Chart Viewer Page
The system SHALL provide interactive chart viewing.

#### Scenario: Display interactive chart
- **WHEN** chart page loads for a symbol
- **THEN** render Plotly chart with candlesticks and indicators
- **AND** enable zoom, pan, hover tooltips
- **AND** display controls to toggle indicators
- **AND** allow timeframe selection (dropdown: 1d, 1w, 1m, 3m, 1y)

#### Scenario: Toggle indicators
- **WHEN** user clicks indicator toggle (checkbox or button)
- **THEN** show/hide indicator on chart dynamically
- **AND** available toggles: SuperTrend, MA20, MA50, MA200, MACD, RSI, Bollinger Bands, Volume

#### Scenario: View AI analysis
- **WHEN** user clicks "View Analysis" on chart page
- **THEN** display latest AI-generated analysis for this symbol
- **AND** show: daily analysis, weekly analysis, consolidated analysis, trading decision
- **AND** format analysis text with proper paragraphs and sections

### Requirement: Responsive Design
The system SHALL be fully responsive across desktop, tablet, and mobile devices.

#### Scenario: Desktop view
- **WHEN** accessed on desktop (>1024px width)
- **THEN** display full layout with sidebar navigation and wide content area
- **AND** tables SHALL show all columns

#### Scenario: Tablet view
- **WHEN** accessed on tablet (768px - 1024px width)
- **THEN** adjust layout with collapsible navigation
- **AND** tables SHALL adapt with horizontal scroll if needed

#### Scenario: Mobile view
- **WHEN** accessed on mobile (<768px width)
- **THEN** collapse navigation to hamburger menu
- **AND** stack content vertically
- **AND** tables SHALL display in card layout
- **AND** ensure touch targets are appropriately sized

### Requirement: Loading States and Feedback
The system SHALL provide clear feedback during asynchronous operations.

#### Scenario: Loading indicator
- **WHEN** data is being fetched
- **THEN** display loading spinner or skeleton screens
- **AND** disable interaction with loading elements

#### Scenario: Success notification
- **WHEN** operation succeeds (e.g., strategy created, order placed)
- **THEN** display success toast notification
- **AND** auto-dismiss after 3 seconds

#### Scenario: Error notification
- **WHEN** operation fails
- **THEN** display error toast notification with error message
- **AND** provide dismiss button
- **AND** log error to console for debugging

### Requirement: Form Validation
The system SHALL validate user inputs on frontend before submission.

#### Scenario: Client-side validation
- **WHEN** user submits a form
- **THEN** validate required fields are filled
- **AND** validate data types (e.g., price is numeric, quantity is integer)
- **AND** validate ranges (e.g., quantity > 0, profit_margin >= 0)
- **AND** display inline validation errors
- **AND** prevent submission if validation fails

## ADDED Requirements

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

