# Frontend Dashboard Specification

## ADDED Requirements

### Requirement: Real-Time Workflow Monitoring
The system SHALL display real-time status of all workflow executions on the dashboard.

#### Scenario: Display workflow execution cards
- **WHEN** user views dashboard
- **THEN** active workflow executions SHALL be displayed as cards
- **AND** each card SHALL show: strategy name, symbols, status, progress %
- **AND** cards SHALL update in real-time via WebSocket
- **AND** completed workflows SHALL remain visible for 5 minutes

#### Scenario: Workflow status indicators
- **WHEN** workflow is executing
- **THEN** status SHALL be displayed with color coding:
  - Running: blue with spinner
  - Completed: green with checkmark
  - Failed: red with error icon
  - Paused: yellow with pause icon
- **AND** progress bar SHALL show completion percentage
- **AND** estimated time remaining SHALL be displayed

### Requirement: Key Performance Metrics
The system SHALL display key trading performance metrics prominently.

#### Scenario: Display metric cards
- **WHEN** user views dashboard
- **THEN** metric cards SHALL be displayed showing:
  - Active Strategies count
  - Running Workflows count
  - Today's Decisions count (BUY/SELL breakdown)
  - Success Rate percentage
  - Total P&L (if available from positions)
- **AND** metrics SHALL update in real-time
- **AND** clicking metric SHALL navigate to detailed view

#### Scenario: Metric trends
- **WHEN** viewing metrics
- **THEN** trend indicators SHALL show change from previous period
- **AND** upward trends SHALL be green with up arrow
- **AND** downward trends SHALL be red with down arrow
- **AND** hover SHALL show detailed breakdown

### Requirement: Quick Action Buttons
The system SHALL provide quick access to common actions from dashboard.

#### Scenario: Display quick actions
- **WHEN** user views dashboard
- **THEN** quick action buttons SHALL be displayed:
  - "New Strategy" → navigates to strategy creation
  - "Execute Workflow" → opens execution dialog
  - "View Logs" → opens log viewer
  - "Refresh Data" → reloads all dashboard data
- **AND** buttons SHALL have appropriate icons
- **AND** keyboard shortcuts SHALL be supported

#### Scenario: Execute workflow from dashboard
- **WHEN** user clicks "Execute Workflow"
- **THEN** modal SHALL open with strategy selection
- **AND** user SHALL select one or more strategies
- **AND** execution SHALL start on confirmation
- **AND** workflow card SHALL appear immediately

### Requirement: Recent Trading Decisions
The system SHALL display recent trading decisions with key information.

#### Scenario: Display recent decisions list
- **WHEN** user views dashboard
- **THEN** list of last 10 decisions SHALL be displayed
- **AND** each decision SHALL show: type (BUY/SELL), symbol, price, R-coeff, profit margin
- **AND** BUY decisions SHALL have green badge
- **AND** SELL decisions SHALL have red badge
- **AND** clicking decision SHALL show full details

#### Scenario: Filter decisions
- **WHEN** user applies decision filters
- **THEN** decisions SHALL be filtered by type (BUY/SELL/HOLD)
- **AND** decisions SHALL be filtered by symbol
- **AND** decisions SHALL be filtered by date range
- **AND** filter state SHALL persist in URL

### Requirement: Performance Chart
The system SHALL display performance chart showing trading activity over time.

#### Scenario: Display performance chart
- **WHEN** user views dashboard
- **THEN** Chart.js line chart SHALL be displayed
- **AND** chart SHALL show last 30 days by default
- **AND** chart SHALL plot: number of decisions per day
- **AND** chart SHALL allow hovering for exact values
- **AND** timeframe selector SHALL allow 7d/30d/90d/1y

#### Scenario: Chart interactivity
- **WHEN** user hovers over chart point
- **THEN** tooltip SHALL show: date, decision count, success rate
- **AND** clicking point SHALL filter decisions for that day
- **AND** chart SHALL support zoom in/out
- **AND** chart SHALL be responsive to screen size

### Requirement: System Health Indicators
The system SHALL display system health and connectivity status.

#### Scenario: Display health indicators
- **WHEN** user views dashboard
- **THEN** health indicators SHALL show:
  - IBKR Gateway connection status
  - Database connection status
  - AI/LLM API status
  - Celery worker status
- **AND** indicators SHALL be green/red for healthy/unhealthy
- **AND** clicking indicator SHALL show detailed diagnostics

#### Scenario: Alert notifications
- **WHEN** system health issue detected
- **THEN** alert SHALL be displayed on dashboard
- **AND** alert SHALL show error message and suggested action
- **AND** alert SHALL be dismissible but persist in notification center
- **AND** critical alerts SHALL require acknowledgment

### Requirement: Customizable Dashboard Layout
The system SHALL allow users to customize dashboard layout and widgets.

#### Scenario: Rearrange dashboard widgets
- **WHEN** user enters edit mode
- **THEN** all widgets SHALL become draggable
- **AND** widgets SHALL be drag-and-drop reorderable
- **AND** layout SHALL save automatically
- **AND** layout SHALL persist across sessions

#### Scenario: Show/hide widgets
- **WHEN** user clicks customize button
- **THEN** widget selector modal SHALL open
- **AND** user SHALL be able to toggle widgets on/off
- **AND** hidden widgets SHALL not be displayed
- **AND** user can reset to default layout

### Requirement: Mobile Responsive Dashboard
The system SHALL provide optimized dashboard experience on mobile devices.

#### Scenario: Mobile layout adaptation
- **WHEN** viewed on mobile device
- **THEN** dashboard SHALL use single-column layout
- **AND** metric cards SHALL stack vertically
- **AND** charts SHALL be touch-optimized
- **AND** navigation SHALL use mobile-friendly menu

#### Scenario: Mobile gestures
- **WHEN** using touch interface
- **THEN** swipe gestures SHALL navigate between sections
- **AND** pull-to-refresh SHALL reload data
- **AND** tap-and-hold SHALL show context menus
- **AND** all interactive elements SHALL be touch-friendly sized

### Requirement: Dashboard Auto-Refresh
The system SHALL automatically refresh dashboard data at configurable intervals.

#### Scenario: Auto-refresh behavior
- **WHEN** dashboard is active
- **THEN** data SHALL auto-refresh every 30 seconds by default
- **AND** refresh interval SHALL be configurable (10s/30s/60s/off)
- **AND** refresh SHALL not interrupt user interactions
- **AND** last refresh time SHALL be displayed

#### Scenario: Background refresh
- **WHEN** dashboard tab is not active
- **THEN** refresh interval SHALL increase to conserve resources
- **AND** refresh SHALL resume normal interval when tab becomes active
- **AND** WebSocket connection SHALL remain active
- **AND** critical updates SHALL still push in background

### Requirement: Dashboard Search and Filter
The system SHALL provide global search and filter across dashboard data.

#### Scenario: Global search
- **WHEN** user enters search query
- **THEN** search SHALL scan:
  - Strategy names
  - Symbol codes
  - Workflow names
  - Decision details
- **AND** matching results SHALL be highlighted
- **AND** search SHALL support fuzzy matching
- **AND** recent searches SHALL be saved

#### Scenario: Time-based filtering
- **WHEN** user selects time range filter
- **THEN** all dashboard data SHALL filter to range
- **AND** charts SHALL adjust to time range
- **AND** decisions SHALL filter to time range
- **AND** workflows SHALL filter to time range
- **AND** preset ranges SHALL be available (Today/This Week/This Month)

