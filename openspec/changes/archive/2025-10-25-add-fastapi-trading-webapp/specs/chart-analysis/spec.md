# Chart Analysis Specification

## ADDED Requirements

### Requirement: Technical Chart Generation
The system SHALL generate technical analysis charts with multiple indicators.

#### Scenario: Generate candlestick chart
- **WHEN** historical data is fetched for a symbol
- **THEN** generate candlestick chart using Plotly with OHLC data
- **AND** apply timeframe-appropriate styling
- **AND** include volume bars as subplot

#### Scenario: Add SuperTrend indicator
- **WHEN** generating chart
- **THEN** calculate SuperTrend (10, 3) indicator
- **AND** overlay on price chart with green (uptrend) and red (downtrend) colors
- **AND** show trend changes as signal points

#### Scenario: Add moving averages
- **WHEN** generating chart
- **THEN** calculate and overlay:
  - 20-period SMA (short-term)
  - 50-period SMA (medium-term)
  - 200-period SMA (long-term)
- **AND** use distinct colors and line styles
- **AND** show crossovers (golden cross, death cross)

#### Scenario: Add MACD indicator
- **WHEN** generating chart
- **THEN** calculate MACD (12, 26, 9)
- **AND** display in subplot below price chart
- **AND** show MACD line, signal line, and histogram
- **AND** highlight zero-line crosses and signal crossovers

#### Scenario: Add RSI indicator
- **WHEN** generating chart
- **THEN** calculate RSI (14-period)
- **AND** display in subplot
- **AND** mark overbought (>70) and oversold (<30) zones
- **AND** highlight divergences if detected

#### Scenario: Add Bollinger Bands
- **WHEN** generating chart
- **THEN** calculate Bollinger Bands (20, 2)
- **AND** overlay upper band, middle (SMA), and lower band
- **AND** fill area between bands with transparency
- **AND** highlight price touches/breaks of bands

### Requirement: Chart Image Export
The system SHALL export charts as images for AI analysis.

#### Scenario: Export chart as PNG
- **WHEN** chart is generated
- **THEN** export as high-resolution PNG (1920x1080 or configurable)
- **AND** ensure all indicators are visible and labeled
- **AND** include title with: symbol, timeframe, date range

#### Scenario: Upload chart to storage
- **WHEN** chart image is exported
- **THEN** upload to MinIO bucket with filename: {symbol}_{timeframe}_{timestamp}.png
- **AND** return storage URL for retrieval
- **AND** set appropriate content type and permissions

### Requirement: Chart Data Caching
The system SHALL cache historical data to reduce API calls.

#### Scenario: Check cache before fetching
- **WHEN** chart generation is requested
- **THEN** check market_data table for existing data
- **AND** if data exists and is fresh (< 1 hour for intraday, < 1 day for daily), use cached data
- **AND** if stale or missing, fetch from IBKR and cache

#### Scenario: Cache historical data
- **WHEN** data is fetched from IBKR
- **THEN** store in market_data table with: conid, period, bar, data (JSONB), created_at
- **AND** include OHLCV and calculated indicators in data
- **AND** index by (conid, period, bar) for fast lookup

### Requirement: Interactive Chart Display
The system SHALL provide interactive charts in the web UI.

#### Scenario: Display interactive chart
- **WHEN** user views a symbol's chart page
- **THEN** render Plotly chart embedded in HTML
- **AND** enable zoom, pan, hover tooltips
- **AND** show indicator values on hover

#### Scenario: Toggle indicators
- **WHEN** user interacts with chart controls
- **THEN** allow toggling visibility of: moving averages, SuperTrend, MACD, RSI, Bollinger Bands
- **AND** persist preferences for session
- **AND** update chart dynamically

### Requirement: Multi-Timeframe Chart Comparison
The system SHALL support viewing multiple timeframes side-by-side.

#### Scenario: Display daily and weekly charts
- **WHEN** user requests multi-timeframe view
- **THEN** display daily chart and weekly chart in adjacent panels or stacked
- **AND** synchronize time ranges when possible
- **AND** highlight trend agreement or divergence between timeframes

### Requirement: Indicator Calculation
The system SHALL accurately calculate all technical indicators.

#### Scenario: Calculate SuperTrend
- **WHEN** calculating SuperTrend
- **THEN** use formula with period=10, multiplier=3
- **AND** use ATR (Average True Range) for volatility
- **AND** determine trend direction based on price vs bands

#### Scenario: Calculate ATR
- **WHEN** calculating ATR for stop-loss or indicators
- **THEN** use 14-period ATR by default
- **AND** ATR = average of True Range over period
- **AND** True Range = max(high - low, |high - prev_close|, |low - prev_close|)

### Requirement: Chart Error Handling
The system SHALL handle chart generation errors gracefully.

#### Scenario: Insufficient data
- **WHEN** historical data is insufficient (< 200 bars for 200 SMA)
- **THEN** log warning "Insufficient data for indicator: 200 SMA"
- **AND** omit unavailable indicators
- **AND** generate chart with available data

#### Scenario: Storage upload failure
- **WHEN** chart upload to MinIO fails
- **THEN** retry up to 3 times with exponential backoff
- **AND** if still fails, store chart data locally and log error
- **AND** return local path instead of storage URL

