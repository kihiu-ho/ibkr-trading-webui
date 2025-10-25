# Add Indicator Charting with MinIO Storage

## Why

The current indicator system lacks visualization capabilities:
1. Users cannot see how indicators perform on historical price data
2. No visual representation of indicator signals and overlays
3. Cannot easily compare multiple indicators on the same chart
4. No persistent storage of generated charts
5. No way to analyze indicator behavior across different periods/frequencies

This prevents traders from understanding indicator behavior, validating strategies, and making informed decisions.

## What Changes

### 1. Enhanced Indicator Data Model
- Add `period` parameter (number of data points: 20, 50, 100, 200, 500)
- Add `frequency` parameter (timeframe: 1m, 5m, 15m, 1h, 1D, 1W, 1M)
- Support multiple distinct indicators per strategy with unique names
- Store chart metadata in database

### 2. Chart Generation Service
- Plotly-based chart generation (from reference webapp)
- Support for technical analysis indicators:
  - Price candlesticks with Moving Averages
  - Bollinger Bands with bands and median
  - SuperTrend with direction signals
  - Volume bars with color coding
  - MACD with signal line and histogram
  - RSI with overbought/oversold levels
  - ATR and other indicators
- Multi-row subplot layout
- Annotations with max/min/avg values

### 3. MinIO Storage Integration
- Store generated chart images in MinIO bucket
- Support for multiple formats (JPEG, PNG, HTML)
- Metadata tracking (symbol, strategy, indicator, generated date)
- Automatic cleanup of old charts (retention policy)

### 4. Chart API Endpoints
- Generate chart for symbol with indicators
- List stored charts
- Retrieve chart image URL
- Delete old charts
- Export chart data

### 5. Frontend Chart Display
- Chart gallery page showing all generated charts
- Strategy-specific chart view
- Interactive chart navigation
- Download chart options
- Real-time chart generation with progress indicator

## Impact

### Affected Specs
- `technical-indicators` - Enhanced with period/frequency parameters
- `indicator-charting` - NEW capability for chart generation
- `minio-storage` - NEW capability for chart storage

### Affected Code
- Database: `indicators` table schema updates
- Backend:
  - `backend/models/indicator.py` - Add period/frequency fields
  - `backend/schemas/indicator.py` - Update validation
  - `backend/services/chart_service.py` - NEW chart generation
  - `backend/services/minio_service.py` - NEW MinIO integration
  - `backend/api/charts.py` - NEW chart endpoints
- Frontend:
  - `frontend/templates/charts.html` - NEW chart gallery
  - `frontend/templates/strategies.html` - Chart preview

### Breaking Changes
None - Additive only. Existing indicators continue to work with default period/frequency.

### Dependencies
- plotly
- pandas-ta (technical analysis)
- python-minio
- kaleido (for static chart export)
