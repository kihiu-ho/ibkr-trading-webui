## Why
IBKR workflows (ibkr_stock_data_workflow, ibkr_multi_symbol_workflow, ibkr_trading_signal_workflow) are not appearing in the Airflow monitor page. Only the example_ibkr_dag is visible, preventing users from accessing and managing the actual IBKR trading workflows.

## What Changes
- Investigate why IBKR workflows are not being discovered by Airflow
- Fix DAG discovery/loading issues (syntax errors, import errors, configuration issues)
- Ensure DAGs are properly registered and visible in Airflow API
- Update frontend to properly display all IBKR workflows
- Add error handling and logging for DAG discovery issues

## Impact
- Affected specs: `airflow-integration`
- Affected code:
  - `dags/ibkr_stock_data_workflow.py` - Fix DAG definition if needed
  - `dags/ibkr_multi_symbol_workflow.py` - Fix DAG definition if needed
  - `dags/ibkr_trading_signal_workflow.py` - Fix DAG definition if needed
  - `backend/app/routes/airflow_proxy.py` - Improve error handling
  - `frontend/templates/airflow_monitor.html` - Add filtering/display improvements

