# Add IBKR Stock Data Workflow

## Why
The system needs a robust, debuggable workflow to fetch and process stock data (TSLA, NVDA) from PostgreSQL database. This workflow will serve as the foundation for trading analysis and decision-making, with full observability through MLflow tracking and debug mode capabilities for troubleshooting.

## What Changes
- Create Airflow DAG for fetching TSLA and NVDA stock data from PostgreSQL
- Implement MLflow tracking for all workflow runs (parameters, metrics, artifacts)
- Add debug mode configuration from environment variables
- Create reusable data pipeline components (extraction, validation, transformation)
- Add comprehensive logging and error handling
- Support both scheduled and manual execution modes

## Impact
- **New specs:**
  - `data-pipeline` - Stock data extraction and processing workflow
- **Affected specs:**
  - `trading-workflow` - Extends with data fetching capabilities
  - `database-schema` - Leverages existing PostgreSQL tables
- **Affected code:**
  - New: `dags/ibkr_stock_data_workflow.py` - Main DAG implementation
  - New: `dags/utils/database.py` - Database connection utilities
  - New: `dags/utils/mlflow_tracking.py` - MLflow integration helpers
  - Modified: `.env.example` - Add IBKR workflow configuration variables

## Success Criteria
1. DAG successfully fetches TSLA and NVDA data from PostgreSQL
2. All runs are tracked in MLflow with proper experiment organization
3. Debug mode provides detailed logging when enabled
4. Workflow handles database connection errors gracefully
5. Can be triggered manually or on schedule

