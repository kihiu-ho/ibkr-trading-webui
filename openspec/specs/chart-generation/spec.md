# chart-generation Specification

## Purpose
TBD - created by archiving change llm-chart-signals. Update Purpose after archive.
## Requirements
### Requirement: Generate Technical Charts for Multiple Timeframes
The system SHALL generate technical analysis charts for daily, weekly, and monthly timeframes using Plotly.

#### Scenario: Generate daily chart
- **GIVEN** a valid symbol and period
- **WHEN** requesting a daily chart
- **THEN** the system SHALL:
  - Fetch market data for the specified period
  - Calculate all technical indicators (SMA, BB, SuperTrend, MACD, RSI, OBV, ATR)
  - Create a 7-panel Plotly figure
  - Export to JPEG/PNG format
  - Upload to MinIO storage
  - Return public URL

#### Scenario: Generate weekly chart
- **GIVEN** a valid symbol and period
- **WHEN** requesting a weekly chart
- **THEN** the system SHALL:
  - Resample daily data to weekly
  - Calculate weekly indicators
  - Create a 7-panel Plotly figure for weekly timeframe
  - Export and store the chart
  - Return public URL

#### Scenario: Generate monthly chart
- **GIVEN** a valid symbol and period
- **WHEN** requesting a monthly chart
- **THEN** the system SHALL:
  - Resample daily data to monthly
  - Calculate monthly indicators
  - Create a 7-panel Plotly figure for monthly timeframe
  - Export and store the chart
  - Return public URL

### Requirement: 7-Panel Chart Layout
The system SHALL create charts with 7 subplots matching the reference implementation.

####Scenario: Chart panel structure
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
  - Max/Min/Avg/Median annotations
  - Latest value markers (yellow dots)
  - Reference lines for key levels
  - Proper axis labels and legends

### Requirement: Chart Export and Storage
The system SHALL export charts as images and store them accessibly.

#### Scenario: Export chart to image
- **GIVEN** a completed Plotly figure
- **WHEN** exporting the chart
- **THEN** the system SHALL:
  - Use Kaleido to render JPEG/PNG
  - Set image dimensions to 1920x1400 pixels
  - Optimize for LLM vision model consumption
  - Return binary image data

#### Scenario: Store chart in MinIO
- **GIVEN** chart image binary data
- **WHEN** storing the chart
- **THEN** the system SHALL:
  - Generate unique filename: {symbol}_{timeframe}_{timestamp}.jpg
  - Upload to MinIO bucket: trading-charts/signals/
  - Set public read permissions
  - Return public URL using MINIO_PUBLIC_ENDPOINT

### Requirement: Indicator Calculation
The system SHALL calculate all technical indicators required for chart display.

#### Scenario: Calculate moving averages
- **GIVEN** OHLCV data
- **WHEN** calculating indicators
- **THEN** the system SHALL compute:
  - SMA 20, 50, 200
  - Bollinger Bands (20, 2)
  - Handle None values for insufficient data

#### Scenario: Calculate momentum indicators
- **GIVEN** OHLCV data
- **WHEN** calculating indicators
- **THEN** the system SHALL compute:
  - SuperTrend (10, 3)
  - MACD (12, 26, 9)
  - RSI (14)
  - ATR (14)
  - OBV (On-Balance Volume)

