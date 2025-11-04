# OpenSpec: Chart, LLM, and Signal Persistence System

**Status**: 🚧 In Progress  
**Created**: 2025-10-29  
**Author**: AI Agent  
**Category**: Data Persistence & Storage

## Overview

This specification defines a comprehensive data persistence layer for storing:
1. Generated charts (daily/weekly) in MinIO with URLs in PostgreSQL
2. Strategy metadata with indicators for LLM prompts
3. LLM analysis responses
4. Trading signals

## Motivation

### Current State
- Charts are generated but not persistently stored with metadata
- LLM responses are not saved for historical analysis
- Trading signals lack full audit trail
- Strategy indicator configurations not tracked per execution

### Goals
1. **Audit Trail**: Complete history of all charts, analyses, and signals
2. **Reproducibility**: Replay past decisions with full context
3. **Performance**: Query historical patterns without regeneration
4. **Compliance**: Meet regulatory requirements for trade justification

## Design

### Database Schema

#### 1. Charts Table

```sql
CREATE TABLE charts (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER REFERENCES workflow_executions(id),
    symbol VARCHAR(20) NOT NULL,
    conid INTEGER,
    timeframe VARCHAR(10) NOT NULL,  -- '1d', '1w', '1mo'
    chart_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly'
    
    -- MinIO Storage
    chart_url_jpeg VARCHAR(500) NOT NULL,
    chart_url_html VARCHAR(500),
    minio_bucket VARCHAR(100),
    minio_object_key VARCHAR(500),
    
    -- Chart Metadata
    indicators_applied JSONB,  -- {RSI: {period: 14}, MACD: {...}}
    data_points INTEGER,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    
    -- Technical Analysis Summary
    price_current DECIMAL(12, 2),
    price_change_pct DECIMAL(8, 4),
    volume_avg BIGINT,
    
    -- Status
    generated_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active',  -- active, archived, deleted
    
    UNIQUE(execution_id, symbol, timeframe)
);

CREATE INDEX idx_charts_execution ON charts(execution_id);
CREATE INDEX idx_charts_symbol_timeframe ON charts(symbol, timeframe, generated_at DESC);
```

#### 2. LLM Analyses Table

```sql
CREATE TABLE llm_analyses (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER REFERENCES workflow_executions(id),
    chart_id INTEGER REFERENCES charts(id),
    symbol VARCHAR(20) NOT NULL,
    
    -- LLM Request
    prompt_text TEXT NOT NULL,
    prompt_template_id INTEGER,
    model_name VARCHAR(100),  -- 'gpt-4-turbo-preview'
    timeframe VARCHAR(10),
    
    -- Strategy Context
    strategy_id INTEGER REFERENCES strategies(id),
    indicators_metadata JSONB,  -- Full indicator config used
    
    -- LLM Response
    response_text TEXT,
    response_json JSONB,  -- Structured response if applicable
    confidence_score DECIMAL(5, 4),
    
    -- Technical Insights Extracted
    trend_direction VARCHAR(20),  -- bullish, bearish, neutral
    support_levels JSONB,  -- [150.20, 148.50]
    resistance_levels JSONB,  -- [155.00, 158.30]
    key_patterns JSONB,  -- ['double_bottom', 'breakout']
    
    -- Metadata
    tokens_used INTEGER,
    latency_ms INTEGER,
    analyzed_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'completed',
    error_message TEXT,
    
    UNIQUE(execution_id, chart_id)
);

CREATE INDEX idx_llm_analyses_execution ON llm_analyses(execution_id);
CREATE INDEX idx_llm_analyses_symbol ON llm_analyses(symbol, analyzed_at DESC);
CREATE INDEX idx_llm_analyses_chart ON llm_analyses(chart_id);
```

#### 3. Enhanced Trading Signals Table

```sql
-- Extend existing trading_signals table
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS chart_id INTEGER REFERENCES charts(id);
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS llm_analysis_id INTEGER REFERENCES llm_analyses(id);
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS execution_id INTEGER REFERENCES workflow_executions(id);
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS strategy_metadata JSONB;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_signals_chart ON trading_signals(chart_id);
CREATE INDEX IF NOT EXISTS idx_signals_llm_analysis ON trading_signals(llm_analysis_id);
CREATE INDEX IF NOT EXISTS idx_signals_execution ON trading_signals(execution_id);
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Execution Start                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Fetch Market Data   │
              │  (from cache/IBKR)   │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Generate Chart      │
              │  (Daily + Weekly)    │
              └──────────┬───────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Upload to MinIO                   │
        │  - JPEG: charts/NVDA/20251029.jpg │
        │  - HTML: charts/NVDA/20251029.html│
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │  Save Chart Record to PostgreSQL   │
        │  - chart_url_jpeg                  │
        │  - chart_url_html                  │
        │  - indicators_applied: {RSI, MACD} │
        │  - execution_id, symbol, timeframe │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │  Prepare LLM Prompt                │
        │  - Include strategy indicators     │
        │  - Chart URL for vision models     │
        │  - Context: timeframe, symbol      │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │  Call LLM API                      │
        │  - Send chart image + prompt       │
        │  - Get analysis response           │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │  Save LLM Analysis to PostgreSQL   │
        │  - prompt_text                     │
        │  - response_text                   │
        │  - indicators_metadata             │
        │  - chart_id (FK)                   │
        │  - confidence_score, patterns      │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │  Extract Trading Signal            │
        │  - Action: BUY/SELL/HOLD           │
        │  - Confidence, entry/exit prices   │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │  Save Trading Signal to PostgreSQL │
        │  - signal, action, confidence      │
        │  - chart_id, llm_analysis_id (FKs) │
        │  - strategy_metadata               │
        │  - execution_id (FK)               │
        └────────────────────────────────────┘
```

### API Endpoints

#### Charts
- `POST /api/charts` - Create chart record
- `GET /api/charts/{id}` - Get chart details
- `GET /api/charts?execution_id=X` - Get charts by execution
- `GET /api/charts?symbol=NVDA&timeframe=1d` - Get charts by symbol/timeframe

#### LLM Analyses
- `POST /api/llm-analyses` - Create analysis record
- `GET /api/llm-analyses/{id}` - Get analysis details
- `GET /api/llm-analyses?execution_id=X` - Get analyses by execution
- `GET /api/llm-analyses?chart_id=Y` - Get analysis for specific chart

#### Trading Signals (Enhanced)
- `POST /api/signals` - Create signal (with chart_id, llm_analysis_id)
- `GET /api/signals?execution_id=X` - Get signals by execution
- `GET /api/signals?chart_id=Y` - Get signal for specific chart

## Implementation Plan

### Phase 1: Database Schema ✅
1. Create migration for `charts` table
2. Create migration for `llm_analyses` table
3. Alter `trading_signals` table with new foreign keys
4. Add indexes for performance

### Phase 2: Models & Services 🚧
1. Create `Chart` SQLAlchemy model
2. Create `LLMAnalysis` SQLAlchemy model
3. Update `TradingSignal` model
4. Create `ChartPersistenceService`
5. Create `LLMAnalysisService`
6. Update `TradingSignalService`

### Phase 3: Workflow Integration 🚧
1. Update `workflow_tasks.py` to save charts
2. Update workflow to save LLM analyses
3. Update workflow to link signals with charts/analyses
4. Add lineage tracking for all persistence operations

### Phase 4: API Endpoints 📝
1. Implement chart CRUD endpoints
2. Implement LLM analysis CRUD endpoints
3. Update signal endpoints with new filters
4. Add swagger documentation

### Phase 5: Testing ✅
1. Unit tests for models and services
2. Integration tests for workflow
3. API endpoint tests
4. Performance tests for queries

## Example Usage

### Chart Record
```json
{
  "id": 123,
  "execution_id": 12,
  "symbol": "NVDA",
  "conid": 4815747,
  "timeframe": "1d",
  "chart_type": "daily",
  "chart_url_jpeg": "http://minio:9000/trading-charts/charts/NVDA/20251029_123456_abc123.jpg",
  "chart_url_html": "http://minio:9000/trading-charts/charts/NVDA/20251029_123456_abc123.html",
  "indicators_applied": {
    "RSI": {"period": 14, "overbought": 70, "oversold": 30},
    "MACD": {"fast": 12, "slow": 26, "signal": 9},
    "SMA": {"periods": [20, 50, 200]}
  },
  "data_points": 62,
  "start_date": "2024-10-29T00:00:00Z",
  "end_date": "2025-10-29T00:00:00Z",
  "price_current": 189.45,
  "price_change_pct": 2.35,
  "volume_avg": 45000000,
  "generated_at": "2025-10-29T12:18:48Z"
}
```

### LLM Analysis Record
```json
{
  "id": 456,
  "execution_id": 12,
  "chart_id": 123,
  "symbol": "NVDA",
  "prompt_text": "Analyze this NVIDIA daily chart with RSI, MACD...",
  "model_name": "gpt-4-turbo-preview",
  "timeframe": "1d",
  "strategy_id": 2,
  "indicators_metadata": {
    "RSI": {"current": 58.3, "trend": "neutral"},
    "MACD": {"histogram": 0.45, "signal": "bullish_crossover"}
  },
  "response_text": "Technical analysis shows bullish momentum...",
  "confidence_score": 0.78,
  "trend_direction": "bullish",
  "support_levels": [185.00, 182.50],
  "resistance_levels": [192.00, 195.50],
  "key_patterns": ["ascending_triangle", "higher_lows"],
  "tokens_used": 1250,
  "latency_ms": 4823,
  "analyzed_at": "2025-10-29T12:18:54Z"
}
```

### Trading Signal Record (Enhanced)
```json
{
  "id": 789,
  "execution_id": 12,
  "chart_id": 123,
  "llm_analysis_id": 456,
  "symbol": "NVDA",
  "signal": "BUY",
  "action": "OPEN_LONG",
  "confidence": 0.78,
  "entry_price": 189.50,
  "stop_loss": 185.00,
  "take_profit": 195.00,
  "strategy_metadata": {
    "timeframes": ["1d", "1w"],
    "indicators": ["RSI", "MACD", "SMA"],
    "risk_reward_ratio": 2.2
  },
  "generated_at": "2025-10-29T12:18:55Z"
}
```

## Benefits

1. **Complete Audit Trail**: Every decision has full context
2. **Regulatory Compliance**: Prove reasoning for all trades
3. **Performance Analysis**: Backtest LLM accuracy over time
4. **Cost Optimization**: Reuse charts instead of regenerating
5. **Debugging**: Replay exact conditions of any trade
6. **ML Training**: Build dataset for model improvement

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Storage Growth | High | Implement archival policy (90 days active) |
| Query Performance | Medium | Proper indexing, pagination |
| MinIO Availability | High | Backup URLs, redundancy |
| Data Consistency | Medium | Database transactions, FK constraints |

## Success Metrics

- ✅ 100% of charts stored with URLs
- ✅ 100% of LLM responses persisted
- ✅ 100% of signals linked to charts and analyses
- ✅ Query response time < 100ms for recent data
- ✅ Zero data loss in persistence layer

## Timeline

- Day 1: Database schema and migrations ✅
- Day 2: Models and services 🚧
- Day 3: Workflow integration 🚧
- Day 4: API endpoints 📝
- Day 5: Testing and documentation ✅

---

**Status**: Implementation Started  
**Next**: Create database migrations and models

