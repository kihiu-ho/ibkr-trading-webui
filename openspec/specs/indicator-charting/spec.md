# indicator-charting Specification

## Purpose
TBD - created by archiving change add-indicator-charting. Update Purpose after archive.
## Requirements
### Requirement: Period and Frequency Parameters
The system SHALL support configurable analysis periods and data frequencies for indicators.

#### Scenario: Create indicator with period
- **WHEN** creating indicator with period=100 and frequency='1D'
- **THEN** indicator stores period and frequency for chart generation

#### Scenario: Generate chart with custom period
- **WHEN** generating chart with period=200 and frequency='1W'
- **THEN** system fetches 200 weekly candles and calculates indicators

#### Scenario: Supported frequencies
- **WHEN** requesting chart generation
- **THEN** system supports: 1m, 5m, 15m, 1h, 1D, 1W, 1M

### Requirement: Multiple Distinct Indicators
The system SHALL support multiple indicators with unique names on the same strategy.

#### Scenario: Create strategy with multiple MA indicators
- **WHEN** adding "MA 20" and "MA 50" to strategy
- **THEN** both indicators stored with distinct names and parameters

#### Scenario: Generate chart with multiple indicators
- **WHEN** generating chart for strategy with 3 indicators
- **THEN** chart displays all 3 with unique colors/styles

### Requirement: Chart Generation
The system SHALL generate professional technical analysis charts.

#### Scenario: Generate price chart
- **WHEN** POST /api/charts/generate with symbol and period
- **THEN** candlestick chart generated and stored in MinIO

#### Scenario: Chart with indicators
- **WHEN** chart includes RSI, MA, MACD
- **THEN** each displays in appropriate subplot

#### Scenario: Chart annotations
- **WHEN** chart is generated
- **THEN** includes max/min/average annotations for each indicator

#### Scenario: Chart performance
- **WHEN** generating chart with 100 points and 3 indicators
- **THEN** completes in < 5 seconds

