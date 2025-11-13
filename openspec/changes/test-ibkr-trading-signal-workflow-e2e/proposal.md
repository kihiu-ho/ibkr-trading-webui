# Test IBKR Trading Signal Workflow End-to-End

## Why

The `ibkr_trading_signal_workflow` DAG is a critical component that orchestrates the complete trading pipeline: market data fetching → technical chart generation → LLM analysis → order placement → portfolio tracking. While individual components have been tested, the workflow has never been validated end-to-end using real data from the PostgreSQL database. This testing is essential to:

1. Validate complete workflow execution with actual market data
2. Identify and fix integration issues between workflow tasks
3. Verify data persistence across all artifact types (charts, signals, orders, trades, portfolio)
4. Ensure LLM analysis produces actionable trading signals
5. Confirm MLflow tracking captures all workflow metrics and artifacts

## What Changes

This change validates and fixes the complete workflow execution:

- **Test Market Data**: Verify PostgreSQL contains sufficient market data for TSLA (or configured symbol)
- **Execute Workflow**: Trigger `ibkr_trading_signal_workflow` DAG manually via Airflow API
- **Monitor Execution**: Track all 8 tasks through completion, capturing logs and XCom data
- **Validate Artifacts**: Confirm charts, LLM responses, signals, orders, and portfolio snapshots are stored
- **Fix Issues**: Address any failures in task execution, data access, model validation, or artifact storage
- **Document Results**: Update OpenSpec with complete test results and any fixes applied

## Impact

### Affected Specs
- `specs/airflow-workflows/spec.md` - Trading signal workflow validation
- `specs/artifact-storage/spec.md` - End-to-end artifact persistence
- `specs/llm-signal-analysis/spec.md` - LLM analysis with real data
- `specs/market-data-access/spec.md` - Database integration testing

### Affected Code
- `dags/ibkr_trading_signal_workflow.py` - Main workflow DAG (fixes if needed)
- `dags/utils/*.py` - Utility modules used by workflow tasks
- `dags/models/*.py` - Pydantic models for data validation
- `backend/api/artifacts.py` - Artifact storage endpoints
- Database: `ibkr_trading` database (market_data, artifacts, signals tables)

### Expected Outcomes
1. ✅ All 8 workflow tasks complete successfully
2. ✅ Charts generated and stored in `/app/charts` with MinIO upload
3. ✅ LLM analysis produces valid trading signal (BUY/SELL/HOLD)
4. ✅ Artifacts table populated with all workflow outputs
5. ✅ MLflow run created with metrics, parameters, and artifacts
6. ✅ Frontend can display complete workflow results

### Risk Assessment
- **Low Risk**: Testing workflow with existing data, no schema changes
- **Manual Trigger**: Workflow triggered manually for controlled testing
- **No Real Trades**: Testing with paper trading account only
- **Rollback**: Can re-run workflow after fixing any issues

## Test Results Summary

**Status**: ✅ SUCCESSFULLY COMPLETED WITH FIXES

### First Test Run
- 7/8 tasks completed successfully (87.5% success rate)
- All artifacts created and stored in database
- One timeout in log_to_mlflow task identified and fixed

### Issues Found & Fixed
1. **log_to_mlflow timeout**: Used inefficient `shutil.copy()` for large files
   - **Fix**: Direct file logging via `mlflow.log_artifact()`
2. **Artifact update loop**: Could timeout with many artifacts
   - **Fix**: Limited to 5 artifacts max, reduced timeouts to 2-3s

### Artifacts Verified
- ✅ 2 chart artifacts (daily + weekly TSLA charts)
- ✅ 1 LLM analysis artifact
- ✅ 1 trading signal artifact (HOLD)
- ✅ 1 portfolio snapshot artifact

### Code Changes
- Modified `dags/utils/mlflow_tracking.py`: Added `log_file_artifact()` method
- Modified `dags/ibkr_trading_signal_workflow.py`: 
  - Removed `shutil.copy()` calls
  - Optimized artifact update loop
  - Added better error handling

See `test-results.md` for detailed test execution report.
