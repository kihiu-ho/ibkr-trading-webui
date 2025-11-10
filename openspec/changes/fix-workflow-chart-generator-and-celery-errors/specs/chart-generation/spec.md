## MODIFIED Requirements

### Requirement: 7-Panel Chart Layout
The system SHALL create charts with 7 subplots matching the reference implementation.

#### Scenario: Chart panel structure
- **GIVEN** market data and indicators
- **WHEN** creating the chart figure
- **THEN** the system SHALL include these panels in order:
  1. Price with MA (20, 50, 200) & Bollinger Bands
  2. SuperTrend indicator
  3. Volume (in millions)
  4. MACD with histogram
  5. RSI with 30/70 levels
  6. OBV (On-Balance Volume)
  7. ATR (Average True Range)

#### Scenario: Chart annotations
- **GIVEN** indicator data
- **WHEN** rendering each panel
- **THEN** the system SHALL add:
  - Max/Min/Avg/Median annotations with correct Plotly yref format (y, y1, y3, y5, etc.)
  - Latest value markers (yellow dots)
  - Reference lines for key levels
  - Proper axis labels and legends
- **AND** annotations SHALL use valid Plotly yref values that match the subplot y-axis references
- **AND** yref values SHALL be calculated based on subplot row index using the format: "y" for row 1, "y{axis_index}" for subsequent rows

