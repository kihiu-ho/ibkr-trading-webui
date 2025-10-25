# Indicator Visualization Capability

## ADDED Requirements

### Requirement: Indicator Management Page
The system SHALL provide a web interface for managing indicators at `/indicators`.

#### Scenario: View indicators list
- **WHEN** user navigates to `/indicators`
- **THEN** display table of all indicators with name, type, parameters summary, and actions

#### Scenario: Create indicator via UI
- **WHEN** user clicks "Add Indicator" button
- **THEN** show modal with indicator type selector and parameter form

#### Scenario: Edit indicator via UI
- **WHEN** user clicks edit icon on indicator
- **THEN** show modal pre-filled with current parameters for editing

#### Scenario: Delete indicator via UI
- **WHEN** user clicks delete icon and confirms
- **THEN** remove indicator and refresh the list

### Requirement: Visual Indicator Builder
The system SHALL provide an interactive form for configuring indicator parameters.

#### Scenario: Select indicator type
- **WHEN** user selects indicator type from dropdown
- **THEN** dynamically render parameter form based on selected type

#### Scenario: Configure MA indicator
- **WHEN** user selects "Moving Average" type
- **THEN** show form fields: `period` (number), `type` (SMA/EMA/WMA selector), `source` (close/open/high/low)

#### Scenario: Configure Bollinger Bands
- **WHEN** user selects "Bollinger Bands" type
- **THEN** show form fields: `period` (number), `std_dev` (number), `source` (selector)

#### Scenario: Real-time parameter validation
- **WHEN** user enters parameter values
- **THEN** validate in real-time and show error messages for invalid values

#### Scenario: Save indicator configuration
- **WHEN** user submits valid indicator form
- **THEN** create indicator via API and show success notification

### Requirement: Chart Visualization
The system SHALL display price charts with indicator overlays.

#### Scenario: Render price chart
- **WHEN** user views strategy or symbol chart page
- **THEN** display candlestick or line chart with price data

#### Scenario: Overlay indicator on chart
- **WHEN** strategy has associated indicators
- **THEN** render each indicator as overlay (line, band, or signal markers)

#### Scenario: Moving Average visualization
- **WHEN** strategy includes MA indicator
- **THEN** draw MA line on chart in distinct color with legend entry

#### Scenario: Bollinger Bands visualization
- **WHEN** strategy includes Bollinger Bands
- **THEN** draw upper band, middle band, lower band as three lines with shaded area between bands

#### Scenario: RSI visualization
- **WHEN** strategy includes RSI indicator
- **THEN** draw RSI in separate panel below price chart with overbought/oversold threshold lines

#### Scenario: Multiple indicators display
- **WHEN** strategy has 3+ indicators
- **THEN** render all indicators with unique colors and legend showing name and parameters

### Requirement: Interactive Chart Features
The system SHALL provide interactive chart controls for better analysis.

#### Scenario: Zoom chart
- **WHEN** user scrolls mouse wheel on chart
- **THEN** zoom in/out centered on cursor position

#### Scenario: Pan chart
- **WHEN** user drags chart
- **THEN** pan horizontally to view different time periods

#### Scenario: Toggle indicator visibility
- **WHEN** user clicks indicator name in legend
- **THEN** toggle indicator visibility on chart

#### Scenario: Show indicator values on hover
- **WHEN** user hovers over chart
- **THEN** display tooltip with date, price, and all indicator values at that point

#### Scenario: Change timeframe
- **WHEN** user selects different timeframe (1D, 1W, 1M)
- **THEN** reload chart data and recalculate indicator values for new timeframe

### Requirement: Real-time Indicator Updates
The system SHALL update chart when indicators are modified.

#### Scenario: Indicator parameter changed
- **WHEN** user updates indicator parameters and saves
- **THEN** immediately recalculate and redraw indicator on all relevant charts

#### Scenario: Indicator added to strategy
- **WHEN** new indicator is associated with strategy
- **THEN** strategy chart automatically adds new indicator overlay

#### Scenario: Indicator removed from strategy
- **WHEN** indicator is removed from strategy
- **THEN** strategy chart removes indicator overlay without full page reload

### Requirement: Multi-Symbol Visualization
The system SHALL support viewing indicators across multiple symbols.

#### Scenario: Symbol selector
- **WHEN** viewing indicator visualization page
- **THEN** display dropdown to select symbol from strategy's associated symbols

#### Scenario: Switch symbol
- **WHEN** user selects different symbol
- **THEN** reload chart with selected symbol data and apply same indicators

#### Scenario: Compare symbols
- **WHEN** user enables comparison mode
- **THEN** display multiple symbols on same chart with normalized scales

### Requirement: Indicator Preview
The system SHALL show preview before saving indicator configuration.

#### Scenario: Preview indicator
- **WHEN** user clicks "Preview" in indicator form
- **THEN** show sample chart with indicator applied using current parameters

#### Scenario: Adjust parameters in preview
- **WHEN** user modifies parameters in preview mode
- **THEN** update preview chart in real-time

#### Scenario: Save from preview
- **WHEN** user clicks "Save" from preview
- **THEN** create indicator and close preview modal

