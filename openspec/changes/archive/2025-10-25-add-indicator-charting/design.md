# Design: Indicator Charting with MinIO Storage

## Context

Users need to visualize technical indicators on price charts to understand indicator behavior, validate strategies, and make trading decisions. The reference webapp implementation provides proven charting patterns using Plotly.

**Constraints:**
- Must integrate with existing indicator system
- Chart generation should be performant (< 5 seconds)
- Charts must be persisted for later retrieval
- Support multiple indicators per strategy

**Stakeholders:**
- Traders analyzing strategies
- System operators managing storage
- Developers maintaining the system

## Goals / Non-Goals

**Goals:**
- Generate professional trading charts with multiple indicators
- Store charts persistently in MinIO
- Display charts in web UI
- Support historical data retrieval
- Enable chart comparison and analysis

**Non-Goals:**
- Real-time streaming charts
- Interactive chart editing
- Custom indicator formulas
- Chart analytics/statistics

## Decisions

### Decision 1: Chart Generation Library
**Choice:** Plotly (with subplot layout)

**Rationale:**
- Reference webapp uses Plotly successfully
- Professional financial chart appearance
- Multi-row subplots for multiple indicators
- HTML export for web viewing
- Static image export for archival

### Decision 2: Data Storage
**Choice:** MinIO with metadata in PostgreSQL

**Rationale:**
- MinIO provides S3-compatible object storage
- Already used in reference app
- Separates large media from database
- Easy to implement retention policies
- Scalable to large number of charts

### Decision 3: Chart Parameters
**Choice:** Period and Frequency as separate fields

**Rationale:**
- Period = number of historical data points (20, 50, 100, 500)
- Frequency = data granularity (1m, 5m, 1h, 1D, 1W, 1M)
- Allows flexible chart generation
- Easy to adjust analysis scope

### Decision 4: Multiple Indicators
**Choice:** Many-to-many with unique display names

**Rationale:**
- Same indicator type can be used with different parameters
- E.g., "MA20" and "MA50" both use MA type
- Reduces chart complexity (limited indicators per chart)
- User specifies which indicators to include in each chart

## Data Models

### Enhanced Indicator Table
```sql
ALTER TABLE indicators ADD COLUMN (
    period INTEGER DEFAULT 100,
    frequency VARCHAR(10) DEFAULT '1D'
);
```

### Chart Metadata Table
```sql
CREATE TABLE indicator_charts (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    symbol VARCHAR(50) NOT NULL,
    indicator_ids INTEGER[] NOT NULL,
    period INTEGER NOT NULL,
    frequency VARCHAR(10) NOT NULL,
    chart_url VARCHAR(255),
    metadata JSONB,
    generated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
```

## Architecture

### Chart Generation Flow
1. User requests chart for strategy + symbol
2. System fetches market data (period + frequency)
3. Calculate indicator values
4. Generate Plotly figure with all indicators
5. Export as image/HTML
6. Upload to MinIO
7. Store metadata in database
8. Return chart URL to user

## Implementation Steps

1. Database Schema - Add period/frequency to indicators
2. Backend Models - Update Indicator model
3. Chart Service - Implement chart generation
4. MinIO Service - Implement upload/retrieval
5. API Endpoints - Create chart CRUD endpoints
6. Frontend - Build chart gallery
7. Testing - Test all features
