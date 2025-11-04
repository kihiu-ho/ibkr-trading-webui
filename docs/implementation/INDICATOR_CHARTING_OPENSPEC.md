# Indicator Charting OpenSpec Change - Complete Documentation

## Overview

**Change ID**: `add-indicator-charting`  
**Status**: ✅ **OpenSpec Proposal Created & Validated**  
**Validation**: Passed strict mode

This OpenSpec change adds professional chart generation capabilities to the indicator system, enabling traders to visualize technical analysis across multiple indicators with flexible period and frequency parameters.

## What's Being Built

### 1. **Period & Frequency Parameters**
- **Period**: Configurable data point count (20, 50, 100, 200, 500)
- **Frequency**: Configurable timeframe (1m, 5m, 15m, 1h, 1D, 1W, 1M)
- Allows traders to analyze indicators at any granularity

### 2. **Multiple Distinct Indicators**
- Same strategy can have "MA 20" and "MA 50" (different names, different parameters)
- Unique display names for each indicator instance
- Flexible parameter combinations per indicator
- All indicators display together on same chart

### 3. **Professional Chart Generation**
- **Plotly-based charts** (proven from reference webapp)
- **Multi-indicator support**:
  - Price candlesticks (OHLC)
  - Moving Averages (multiple on same chart)
  - Bollinger Bands (upper/middle/lower with fill)
  - SuperTrend (with direction signals)
  - Volume (color-coded bars)
  - MACD (histogram + signal line)
  - RSI (with overbought/oversold zones)
  - ATR (volatility measure)
- **Annotations**: Max/min/average values per indicator
- **Export formats**: JPEG and interactive HTML

### 4. **MinIO Storage**
- Charts stored in S3-compatible MinIO bucket
- Persistent retrieval by chart ID
- Metadata tracking (symbol, strategy, indicators, timestamp)
- 30-day retention with automatic cleanup
- Optimized compression for storage efficiency

### 5. **Chart Gallery & Display**
- Chart gallery page showing all generated charts
- Strategy-specific chart view
- Quick generation from strategy page
- Download in JPEG or HTML format
- Real-time generation progress indicator

## Architecture Decisions

### Why Plotly?
- Proven by reference webapp implementation
- Professional financial chart appearance
- Multi-row subplot support for multiple indicators
- HTML export for web viewing
- Static image export for archival
- Extensive annotation support

### Why MinIO?
- S3-compatible object storage
- Already used in reference application
- Separates large media from database
- Scalable and easy retention policies
- No external dependencies

### Why Separate Period/Frequency?
- **Period** = number of data points (analysis scope)
- **Frequency** = granularity level (intraday/daily/weekly)
- Flexible chart generation across timeframes
- Easy parameter adjustment

## Database Schema Changes

```sql
-- Add to indicators table
ALTER TABLE indicators ADD COLUMN (
    period INTEGER DEFAULT 100,        -- Number of data points
    frequency VARCHAR(10) DEFAULT '1D' -- 1m, 5m, 1h, 1D, 1W, 1M
);

-- New metadata table
CREATE TABLE indicator_charts (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    symbol VARCHAR(50) NOT NULL,
    indicator_ids INTEGER[] NOT NULL,  -- Array of indicators on chart
    period INTEGER NOT NULL,
    frequency VARCHAR(10) NOT NULL,
    chart_url VARCHAR(255),            -- MinIO storage location
    metadata JSONB,                    -- Additional tracking
    generated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP               -- For retention policy
);
```

## API Endpoints

### Generate Chart
```
POST /api/charts/generate
{
    "strategy_id": 1,
    "symbol": "AAPL",
    "indicator_ids": [1, 2, 3],
    "period": 100,
    "frequency": "1D"
}

Response: {
    "chart_id": 123,
    "status": "ready",
    "url": "https://minio:9000/trading-charts/...",
    "generated_at": "2025-10-21T..."
}
```

### List Charts
```
GET /api/charts?strategy_id=1&symbol=AAPL

Response: [
    {
        "id": 123,
        "symbol": "AAPL",
        "strategy_id": 1,
        "indicators": [1, 2, 3],
        "url": "...",
        "created": "2025-10-21T..."
    }
]
```

### Retrieve Chart
```
GET /api/charts/123

Response: {
    "id": 123,
    "url": "https://minio:9000/trading-charts/...",
    "symbol": "AAPL",
    "indicators": [
        {id: 1, name: "MA 20", type: "MA"},
        {id: 2, name: "RSI 14", type: "RSI"}
    ],
    "metadata": {...}
}
```

### Delete Chart
```
DELETE /api/charts/123

Response: {"success": true}
```

## Implementation Phases

### Phase 1: Database & Models (3 tasks)
- Add period/frequency columns to indicators
- Create indicator_charts metadata table
- Update Indicator model and schemas

### Phase 2: Chart Service (8 tasks)
- Implement chart_service.py
- Price candlestick generation
- All indicator overlays (MA, BB, SuperTrend, etc.)
- Volume, MACD, RSI, ATR subplots
- Annotations and styling
- JPEG and HTML export

### Phase 3: Storage (4 tasks)
- Implement minio_service.py
- Chart upload functionality
- Chart retrieval functionality
- Retention policy enforcement

### Phase 4: API & Frontend (8 tasks)
- Create charts.py API routes
- Build charts.html gallery page
- Add chart generation modal
- Add controls to strategy page
- Implement download functionality

### Phase 5: Testing (5 tasks)
- Chart generation testing
- MinIO operations testing
- API endpoint testing
- Retention policy testing
- Frontend UI testing

## Files to Create/Modify

### Create:
- `backend/models/chart.py` - Chart metadata model
- `backend/schemas/chart.py` - Chart validation schemas
- `backend/services/chart_service.py` - Plotly chart generation
- `backend/services/minio_service.py` - MinIO operations
- `backend/api/charts.py` - Chart API endpoints
- `frontend/templates/charts.html` - Chart gallery page

### Modify:
- `database/init.sql` - Add new tables
- `backend/models/indicator.py` - Add period/frequency
- `backend/schemas/indicator.py` - Update schemas
- `backend/main.py` - Register new routes
- `frontend/templates/strategies.html` - Add chart links

## Example Usage

### Creating Indicators with Distinct Names
```bash
# MA 20 (short term)
curl -X POST /api/indicators \
  -d '{
    "name": "MA 20",
    "type": "MA",
    "period": 100,
    "frequency": "1D",
    "parameters": {"period": 20, "ma_type": "SMA"}
  }'

# MA 50 (medium term) 
curl -X POST /api/indicators \
  -d '{
    "name": "MA 50",
    "type": "MA",
    "period": 100,
    "frequency": "1D",
    "parameters": {"period": 50, "ma_type": "SMA"}
  }'
```

### Generating Charts
```bash
# Generate chart with both MAs + RSI
curl -X POST /api/charts/generate \
  -d '{
    "strategy_id": 1,
    "symbol": "AAPL",
    "indicator_ids": [1, 2, 3],  # MA 20, MA 50, RSI 14
    "period": 100,
    "frequency": "1D"
  }'
```

## Performance Targets

- Chart generation: < 5 seconds for 100 points + 3 indicators
- JPEG export: Optimized compression (< 500KB)
- MinIO upload: < 1 second
- Chart retrieval: < 100ms

## OpenSpec Location

```
openspec/changes/add-indicator-charting/
├── proposal.md              # Why and what
├── design.md                # Architecture decisions
├── tasks.md                 # 25+ implementation tasks
└── specs/
    ├── indicator-charting/spec.md    # Chart requirements
    └── minio-storage/spec.md         # Storage requirements
```

## Reference Implementation

Based on proven patterns from:
- `reference/webapp/app.py:218` - `create_plotly_figure()` function
- `reference/webapp/app.py:378` - `generate_technical_chart()` function
- MinIO integration patterns from reference app

## Next Steps

1. **Review**: Read `design.md` for architecture details
2. **Plan**: Create sprint tasks from `tasks.md`
3. **Implement**: Follow phases 1-5 sequentially
4. **Test**: Comprehensive testing per phase
5. **Deploy**: Follow deployment checklist

## Status Summary

✅ OpenSpec proposal created  
✅ Documentation complete  
✅ Architecture designed  
✅ Technical decisions recorded  
✅ Task breakdown prepared  
✅ Reference implementation identified  
🔄 **Ready for implementation phase**

---

**Created**: October 21, 2025  
**Change ID**: `add-indicator-charting`  
**Validation**: ✅ Passed OpenSpec strict validation
