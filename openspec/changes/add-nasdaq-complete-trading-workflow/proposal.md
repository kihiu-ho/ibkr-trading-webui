## Why
The current trading workflow supports single-symbol analysis and basic order placement. To enable comprehensive multi-symbol trading strategies for NASDAQ stocks (TSLA, NVDA), we need to extend the workflow to:
1. Fetch market data for multiple symbols simultaneously
2. Generate daily and weekly charts with technical indicators for each symbol
3. Pass multi-chart analysis to LLM for comprehensive trading signal generation
4. Execute orders, track trades, and monitor portfolio positions
5. Visualize all artifacts (inputs, outputs, LLM analysis, signals, charts) in a unified interface
6. Integrate Airflow run details with artifact visualization for full lineage tracking

This enhancement transforms the system from a single-symbol analysis tool into a production-ready multi-symbol trading platform with complete observability.

## What Changes
- **ADDED**: Multi-symbol NASDAQ workflow supporting TSLA and NVDA
- **ADDED**: Daily and weekly chart generation with technical indicators (SMA, RSI, MACD, Bollinger Bands)
- **ADDED**: LLM analysis of multiple charts (daily + weekly) for each symbol
- **ADDED**: IBKR order placement, trade retrieval, and portfolio management integration
- **ADDED**: MLflow tracking for all workflow steps (market data, charts, LLM analysis, signals, orders, trades, portfolio)
- **MODIFIED**: Artifact visualization to support grouped view by execution_id with Airflow integration
- **MODIFIED**: Artifacts API to support execution_id grouping and workflow metadata
- **ADDED**: Airflow run details integration showing generated artifacts for each execution

## Impact
- **Affected specs**: 
  - `trading-workflow` - Multi-symbol workflow execution
  - `artifact-management` - Grouped artifacts and Airflow integration
  - `airflow-integration` - Run details with artifacts
  - `chart-generation` - Multi-timeframe chart support
  - `llm-integration` - Multi-chart analysis
  - `order-management` - Order placement via Airflow
  - `portfolio-management` - Portfolio tracking integration
- **Affected code**:
  - `dags/ibkr_trading_signal_workflow.py` - Extend to multi-symbol
  - `backend/api/artifacts.py` - Add grouping endpoints
  - `frontend/templates/artifacts.html` - Enhanced grouped view
  - `backend/services/ibkr_service.py` - Order, trade, portfolio methods
  - `dags/utils/chart_generator.py` - Multi-timeframe support
  - `dags/utils/llm_signal_analyzer.py` - Multi-chart analysis
  - `dags/utils/mlflow_tracking.py` - Enhanced tracking

