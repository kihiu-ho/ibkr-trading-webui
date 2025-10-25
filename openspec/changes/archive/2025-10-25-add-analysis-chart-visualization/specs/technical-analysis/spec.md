# Technical Analysis Chart Visualization - Spec Delta

## ADDED Requirements

### Requirement: Interactive Chart Visualization
The system SHALL generate and display interactive technical analysis charts alongside text reports.

#### Scenario: Generate chart with analysis
- **GIVEN** a comprehensive analysis is requested for a symbol
- **WHEN** the analysis service calculates indicators
- **THEN** the system SHALL generate a multi-panel Plotly chart
- **AND** SHALL upload the chart to MinIO storage
- **AND** SHALL include chart URLs (JPEG and HTML) in the analysis response

#### Scenario: Display 7-panel chart layout
- **GIVEN** a chart is generated for analysis
- **WHEN** the chart is rendered
- **THEN** the system SHALL display 7 subplots in this order:
  1. Price chart with candlesticks, SMA (20, 50, 200), and Bollinger Bands
  2. SuperTrend indicator (green=bullish, red=bearish)
  3. Volume bars (green=up day, red=down day)
  4. MACD with histogram and signal line
  5. RSI with overbought/oversold zones
  6. OBV (On-Balance Volume)
  7. ATR (Average True Range)
- **AND** SHALL use row heights proportional to importance: [0.35, 0.15, 0.1, 0.15, 0.15, 0.1, 0.1]

#### Scenario: Chart annotations and markers
- **GIVEN** a chart with indicator subplots
- **WHEN** the chart is displayed
- **THEN** each subplot SHALL show max/min/avg annotations
- **AND** SHALL highlight latest values with yellow markers
- **AND** SHALL include proper color coding (green=bullish, red=bearish)
- **AND** SHALL show shared X-axis with date

#### Scenario: Interactive chart features
- **GIVEN** a rendered Plotly chart
- **WHEN** user interacts with the chart
- **THEN** the system SHALL support zooming into specific date ranges
- **AND** SHALL support panning across time periods
- **AND** SHALL show unified hover tooltips with all indicator values
- **AND** SHALL allow toggling legend items on/off

#### Scenario: Chart download capability
- **GIVEN** a displayed chart
- **WHEN** user clicks download button
- **THEN** the system SHALL provide chart in JPEG format
- **AND** MAY provide chart in PNG format with transparency
- **AND** SHALL maintain chart quality at minimum 1920x1400 resolution

### Requirement: Chart-Analysis Consistency
The system SHALL ensure that charts display the exact same indicators analyzed in the text report.

#### Scenario: Indicator values match between chart and report
- **GIVEN** an analysis with both chart and text report
- **WHEN** comparing indicator values
- **THEN** the chart SHALL display the same SuperTrend, MACD, RSI, ATR, OBV values as the report
- **AND** SHALL use the same parameters (e.g., SuperTrend 10,3, RSI 14, MACD 12,26,9)
- **AND** SHALL show the same latest indicator values

#### Scenario: Visual confirmation of signals
- **GIVEN** a 3/4 signal confirmation in the report
- **WHEN** viewing the chart
- **THEN** the chart SHALL visually confirm the signals:
  - SuperTrend color matches trend direction
  - Price position relative to SMA 20 is visible
  - MACD crossover is visible
  - RSI level supports the signal
- **AND** SHALL make signal confirmation visually obvious

### Requirement: Reference Implementation Compatibility
The system SHALL reference the proven chart layout from `reference/webapp/services/chart_service.py`.

#### Scenario: Use reference chart structure
- **GIVEN** the reference implementation at `reference/webapp/services/chart_service.py`
- **WHEN** designing the chart layout
- **THEN** the system SHOULD use similar subplot organization
- **AND** SHOULD use similar color schemes for indicators
- **AND** SHOULD use similar annotation patterns (max/min/avg)
- **AND** SHALL maintain the 7-panel layout for consistency

#### Scenario: Document chart reference
- **GIVEN** the chart implementation
- **WHEN** documenting the system
- **THEN** the system SHALL include comments referencing `reference/webapp/services/chart_service.py`
- **AND** SHALL document any deviations from the reference
- **AND** SHALL explain the rationale for layout choices

## ADDED Requirements

### Requirement: Comprehensive Analysis Response with Charts
The system SHALL generate comprehensive analysis reports **with integrated chart visualization**.

#### Scenario: Analysis includes chart URLs
- **GIVEN** a comprehensive analysis is generated
- **WHEN** the analysis response is returned
- **THEN** the response SHALL include:
  - `chart_url_jpeg`: Public URL to chart image (JPEG)
  - `chart_url_html`: Public URL to interactive HTML chart
  - All existing analysis fields (unchanged)
- **AND** SHALL ensure chart URLs are publicly accessible

#### Scenario: Frontend displays chart
- **GIVEN** an analysis response with chart URLs
- **WHEN** the analysis page is rendered
- **THEN** the page SHALL display the interactive HTML chart
- **AND** SHALL provide a download link for the JPEG chart
- **AND** SHALL show the chart above or alongside the text report
- **AND** SHALL allow toggling chart visibility

