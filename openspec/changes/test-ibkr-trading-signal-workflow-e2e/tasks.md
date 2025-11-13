# Implementation Tasks

## 1. Pre-Flight Checks
- [ ] 1.1 Verify PostgreSQL `ibkr_trading` database is running
- [ ] 1.2 Check `market_data` table has data for TSLA (or configured symbol)
- [ ] 1.3 Verify Airflow scheduler and webserver are healthy
- [ ] 1.4 Confirm MLflow server is accessible
- [ ] 1.5 Check LLM configuration (provider, model, API key)
- [ ] 1.6 Verify IBKR Gateway is running (for order placement)

## 2. Database Validation
- [ ] 2.1 Query `market_data` table for TSLA records
- [ ] 2.2 Verify at least 200 days of OHLCV data exists
- [ ] 2.3 Check data quality (no null prices, valid volumes)
- [ ] 2.4 Confirm `artifacts` table schema is correct
- [ ] 2.5 Test artifact storage endpoints (`POST /api/artifacts/`)

## 3. Workflow Trigger
- [ ] 3.1 Locate DAG ID: `ibkr_trading_signal_workflow`
- [ ] 3.2 Trigger DAG via Airflow CLI: `airflow dags trigger ibkr_trading_signal_workflow`
- [ ] 3.3 Capture DAG run ID for monitoring
- [ ] 3.4 Monitor DAG run status in Airflow UI
- [ ] 3.5 Track execution via frontend Airflow monitor

## 4. Task Monitoring
- [ ] 4.1 Monitor Task 1: `fetch_market_data` - Verify market data retrieval
- [ ] 4.2 Monitor Task 2: `generate_daily_chart` - Check chart file creation
- [ ] 4.3 Monitor Task 3: `generate_weekly_chart` - Verify weekly chart
- [ ] 4.4 Monitor Task 4: `analyze_with_llm` - Confirm LLM signal generation
- [ ] 4.5 Monitor Task 5: `place_order` - Check order placement logic
- [ ] 4.6 Monitor Task 6: `get_trades` - Verify trade retrieval
- [ ] 4.7 Monitor Task 7: `get_portfolio` - Confirm portfolio snapshot
- [ ] 4.8 Monitor Task 8: `log_to_mlflow` - Check MLflow logging

## 5. Log Analysis
- [ ] 5.1 Retrieve logs for each task via Airflow API
- [ ] 5.2 Check for errors, warnings, or exceptions
- [ ] 5.3 Verify XCom data passing between tasks
- [ ] 5.4 Confirm Pydantic model validation passes
- [ ] 5.5 Document any task failures with stack traces

## 6. Artifact Validation
- [ ] 6.1 Verify daily chart file exists in `/app/charts`
- [ ] 6.2 Verify weekly chart file exists in `/app/charts`
- [ ] 6.3 Check MinIO bucket for uploaded chart artifacts
- [ ] 6.4 Query `artifacts` table for all workflow artifacts
- [ ] 6.5 Verify artifact types: chart, llm, signal, order, trade, portfolio
- [ ] 6.6 Confirm artifact metadata (symbol, workflow_id, execution_id)

## 7. Signal Analysis Validation
- [ ] 7.1 Retrieve LLM trading signal from XCom
- [ ] 7.2 Verify signal action (BUY/SELL/HOLD)
- [ ] 7.3 Check confidence score and level
- [ ] 7.4 Validate entry price, stop loss, take profit suggestions
- [ ] 7.5 Confirm `is_actionable` flag logic
- [ ] 7.6 Review LLM reasoning and key factors

## 8. MLflow Validation
- [ ] 8.1 Query MLflow for workflow run by run_name
- [ ] 8.2 Verify parameters logged (symbol, position_size, llm_provider)
- [ ] 8.3 Confirm metrics logged (price, confidence, portfolio_value)
- [ ] 8.4 Check artifacts logged (signal JSON, charts, portfolio JSON)
- [ ] 8.5 Verify run tags (workflow_type, symbol, airflow_run_id)

## 9. Issue Fixes
- [ ] 9.1 Fix any import errors in DAG or utility modules
- [ ] 9.2 Fix database connection issues
- [ ] 9.3 Fix missing environment variables
- [ ] 9.4 Fix Pydantic model validation errors
- [ ] 9.5 Fix artifact storage failures
- [ ] 9.6 Fix chart generation timeouts
- [ ] 9.7 Fix LLM API authentication or timeout issues
- [ ] 9.8 Fix MLflow tracking errors

## 10. Re-Test After Fixes
- [ ] 10.1 Clear previous DAG run data
- [ ] 10.2 Trigger workflow again with fixes applied
- [ ] 10.3 Monitor all tasks to successful completion
- [ ] 10.4 Verify all artifacts created correctly
- [ ] 10.5 Confirm MLflow run has complete data

## 11. Frontend Validation
- [ ] 11.1 Open Airflow monitor in frontend
- [ ] 11.2 Verify workflow run appears in list
- [ ] 11.3 Check task logs display correctly
- [ ] 11.4 View generated charts in artifact viewer
- [ ] 11.5 Confirm LLM signal details are visible
- [ ] 11.6 Verify portfolio snapshot is accurate

## 12. Documentation
- [ ] 12.1 Document test execution timeline
- [ ] 12.2 Record all issues found and fixes applied
- [ ] 12.3 Screenshot successful workflow completion
- [ ] 12.4 Update proposal.md with final results
- [ ] 12.5 Create summary of workflow performance metrics
- [ ] 12.6 Document any configuration changes required
