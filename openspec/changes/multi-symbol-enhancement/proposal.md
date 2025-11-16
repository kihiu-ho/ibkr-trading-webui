# Change Proposal: Multi-Symbol Workflow Enhancement

**Status:** PROPOSED  
**Created:** 2025-11-15  
**Author:** AI Assistant  
**Type:** Feature Enhancement

## Summary

Enhance the IBKR trading workflow to:
1. Fix MLflow logging timeout issues
2. Add raw market data (OHLCV, indicators) to artifacts
3. Enable multi-symbol support with configurable symbol lists
4. Integrate symbol management in backend and frontend

## Problem Statement

### Issue 1: MLflow Task Hangs
The `log_to_mlflow` task gets stuck during execution, causing workflows to hang indefinitely. Logs show it reaches MLflow setup but doesn't complete.

### Issue 2: Missing Market Data in Artifacts
Current artifacts lack raw market data:
- No OHLCV data (Open, High, Low, Close, Volume)
- No indicator values (RSI, MACD, SMA, etc.)
- Only LLM analysis text is stored

### Issue 3: Single Symbol Limitation
Current workflow only supports one symbol (TSLA). Need to:
- Support multiple symbols (TSLA, NVDA, etc.)
- Enable/disable symbols dynamically
- Process symbols in parallel for efficiency

## Proposed Solution

### 1. Fix MLflow Timeout

**Root Cause:** Backend API calls during MLflow logging have short timeouts (2-3s) and may be causing deadlocks.

**Solution:**
- Remove synchronous backend API calls from MLflow task
- Use async updates or separate task for artifact updates
- Increase timeout from 5 minutes to 10 minutes
- Add better error handling and logging

### 2. Add Raw Market Data to Artifacts

**Enhancement:** Extend artifact storage to include:

```python
{
  "market_data": {
    "ohlcv": [
      {"date": "2025-11-15", "open": 250.5, "high": 252.8, 
       "low": 249.2, "close": 252.5, "volume": 1234567},
      ...
    ],
    "indicators": {
      "rsi": {"current": 54.2, "values": [...]},
      "macd": {"macd": 1.23, "signal": 0.98, "histogram": 0.25},
      "sma_20": 248.5,
      "sma_50": 245.2,
      "sma_200": 230.1,
      "bollinger_bands": {
        "upper": 255.0, "middle": 250.0, "lower": 245.0
      }
    }
  }
}
```

### 3. Multi-Symbol Support

**Architecture:**

```
Backend:
- New table: workflow_symbols
  - id, symbol, enabled, priority, created_at
- New API endpoints:
  - GET /api/workflow-symbols/
  - POST /api/workflow-symbols/
  - PATCH /api/workflow-symbols/{symbol}
  - DELETE /api/workflow-symbols/{symbol}

Frontend:
- New page: Symbol Management
  - List symbols with enable/disable toggles
  - Add/remove symbols
  - Set processing priority
- Workflow Dashboard:
  - Show status per symbol
  - Filter by symbol
  - Display multi-symbol charts

DAG:
- Dynamic symbol list from backend API
- Parallel task groups per symbol
- Consolidated reporting
```

## Implementation Plan

### Phase 1: Fix MLflow Timeout (Critical)
1. Remove backend API calls from `log_to_mlflow_task`
2. Add timeout parameters and error handling
3. Create separate task for artifact updates
4. Test with current single-symbol workflow

### Phase 2: Add Market Data to Artifacts
1. Extend `Artifact.chart_data` to include OHLCV
2. Add `indicator_values` JSON column
3. Update chart generation to store raw data
4. Enhance artifact API to return market data
5. Update frontend to display data tables

### Phase 3: Multi-Symbol Backend
1. Create `workflow_symbols` table and model
2. Implement CRUD API endpoints
3. Add symbol validation
4. Create migration script

### Phase 4: Multi-Symbol DAG
1. Modify DAG to read symbol list from backend
2. Create dynamic task groups per symbol
3. Add parallel processing with proper dependencies
4. Update MLflow logging for multi-symbol

### Phase 5: Frontend Integration
1. Create Symbol Management page
2. Add symbol enable/disable UI
3. Update Dashboard for multi-symbol view
4. Add symbol filtering to charts/artifacts

## Database Schema Changes

```sql
-- New table for workflow symbols
CREATE TABLE workflow_symbols (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100),
    enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    workflow_type VARCHAR(50) DEFAULT 'trading_signal',
    config JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Add index for enabled symbols
CREATE INDEX idx_workflow_symbols_enabled ON workflow_symbols(enabled);

-- Extend artifacts table
ALTER TABLE artifacts 
    ADD COLUMN IF NOT EXISTS market_data JSON,
    ADD COLUMN IF NOT EXISTS indicator_values JSON;
```

## API Changes

### New Endpoints

```python
# Workflow Symbols
GET    /api/workflow-symbols/              # List all symbols
POST   /api/workflow-symbols/              # Add symbol
GET    /api/workflow-symbols/{symbol}      # Get symbol details
PATCH  /api/workflow-symbols/{symbol}      # Update (enable/disable)
DELETE /api/workflow-symbols/{symbol}      # Remove symbol

# Enhanced Artifact Endpoint
GET    /api/artifacts/{id}/market-data     # Get market data for artifact
```

## Configuration Changes

```yaml
# conf.yaml additions
workflow:
  symbols:
    default: ['TSLA', 'NVDA']
    max_parallel: 5
    retry_failed: true
  
  mlflow:
    timeout_minutes: 10
    artifact_update_async: true
```

## Testing Strategy

1. **Unit Tests:**
   - Symbol CRUD operations
   - Market data serialization
   - Artifact storage with new fields

2. **Integration Tests:**
   - MLflow logging completion
   - Multi-symbol DAG execution
   - Frontend symbol management

3. **Performance Tests:**
   - Parallel symbol processing
   - Large OHLCV data storage
   - API response times

## Rollback Plan

1. Keep existing single-symbol workflow as backup
2. Feature flags for multi-symbol mode
3. Database migrations are reversible
4. Frontend can fall back to single symbol view

## Success Criteria

- [ ] MLflow task completes without timeout
- [ ] Market data (OHLCV + indicators) stored in artifacts
- [ ] Backend API supports symbol CRUD operations
- [ ] DAG processes multiple symbols in parallel
- [ ] Frontend displays symbol management UI
- [ ] All existing tests pass
- [ ] New tests achieve >80% coverage

## Dependencies

- SQLAlchemy migrations
- Frontend React components
- Airflow dynamic task groups
- MLflow artifact storage

## Security Considerations

- Validate symbol format (uppercase, 1-10 chars)
- Rate limit API endpoints
- Prevent SQL injection in dynamic queries
- Sanitize user inputs for symbols

## Performance Impact

- **Positive:** Parallel processing of multiple symbols
- **Negative:** Increased database storage for market data
- **Mitigation:** Data retention policies, pagination

## Documentation Updates

- Add symbol management guide
- Update API documentation
- Create workflow diagrams
- Add troubleshooting section for timeouts

## Open Questions

1. Should we support real-time symbol updates during DAG runs?
2. Maximum number of symbols to support?
3. Priority-based execution order?
4. Historical data retention period?

## References

- Current workflow: `dags/ibkr_trading_signal_workflow.py`
- Multi-symbol example: `dags/ibkr_multi_symbol_workflow.py`
- Artifact model: `backend/models/artifact.py`
