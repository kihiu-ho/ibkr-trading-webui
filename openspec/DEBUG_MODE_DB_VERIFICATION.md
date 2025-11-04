# OpenSpec: Debug Mode Database Verification

**Status**: 🔄 Testing  
**Created**: 2025-10-29  
**Author**: AI Agent  
**Category**: System Verification

## Objective

Run IBKR workflow in DEBUG_MODE and verify complete data persistence to PostgreSQL database.

## Verification Plan

### Step 1: Verify Environment Configuration
- Check DEBUG_MODE=true in environment
- Verify CACHE_ENABLED=true
- Confirm cached symbols (NVDA, TSLA, AAPL)

### Step 2: Execute Workflow
- Run strategy execution
- Monitor workflow progress
- Check for errors

### Step 3: Verify Database Persistence

#### Charts Table
- Chart records created
- MinIO URLs stored
- Indicators metadata persisted
- Price/volume data saved

#### LLM Analyses Table
- Analysis records created
- Prompts and responses saved
- Model metadata stored
- Performance metrics tracked

#### Trading Signals Table
- Signals created
- Linked to charts (chart_id FK)
- Linked to analyses (llm_analysis_id FK)
- Strategy metadata included

#### Workflow Executions Table
- Execution records
- Status tracking
- Timing information

#### Lineage Table
- Step-by-step tracking
- Data source verification
- Performance metrics

### Step 4: API Verification
- Test all CRUD endpoints
- Verify data retrieval
- Check statistics endpoints

## Success Criteria

- ✅ DEBUG_MODE active
- ✅ Data fetched from cache (not live IBKR)
- ✅ Charts saved to PostgreSQL
- ✅ LLM analyses saved to PostgreSQL
- ✅ All foreign keys properly linked
- ✅ API endpoints return correct data
- ✅ Complete audit trail available

## Expected Results

### Database Tables (Expected Rows)
- `strategies`: >= 1 active strategy
- `symbols`: 3 symbols (NVDA, TSLA, AAPL)
- `codes`: 3 codes
- `market_data_cache`: 3 cached entries
- `workflow_executions`: >= 1 execution
- `charts`: >= 1 chart per symbol
- `llm_analyses`: >= 1 analysis per chart
- `trading_signals`: >= 1 signal (if LLM generates signals)
- `workflow_logs`: Multiple step logs

### Data Quality Checks
- Chart URLs valid (MinIO accessible)
- Indicators metadata complete
- Datetime fields properly formatted
- Foreign key relationships intact
- No NULL values in required fields

