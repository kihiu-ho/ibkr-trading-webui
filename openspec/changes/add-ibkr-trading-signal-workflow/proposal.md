# Add IBKR Trading Signal Workflow

## Why
Build a complete end-to-end trading workflow that fetches real-time market data from IBKR, generates technical analysis charts, uses LLM to generate trading signals, executes orders, and tracks portfolio performance. This represents the core automated trading capability of the system.

## What Changes
- Create comprehensive trading signal workflow using Pydantic for data validation
- Integrate IBKR Gateway for market data, order placement, and portfolio retrieval
- Implement chart generation with technical indicators (SMA, RSI, MACD, Bollinger Bands)
- Integrate LLM (OpenAI/Anthropic) for chart analysis and signal generation
- Track all workflow runs and trading decisions in MLflow
- Support multiple timeframes (daily, weekly) for better signal confirmation

## Impact
- **New specs:**
  - `market-data-fetching` - IBKR market data retrieval
  - `chart-generation` - Technical chart creation with indicators
  - `llm-signal-generation` - LLM-based trading signal generation
  - `order-placement` - IBKR order execution
  - `portfolio-tracking` - Trade and portfolio monitoring
- **Affected specs:**
  - `trading-workflow` - Extends with complete signal-to-execution pipeline
  - `ibkr-auth` - Leverages existing IBKR authentication
  - `llm-integration` - Extends for chart analysis use case
- **Affected code:**
  - New: `dags/models/` - Pydantic models for all workflow entities
  - New: `dags/ibkr_trading_signal_workflow.py` - Main DAG
  - New: `dags/utils/ibkr_client.py` - IBKR Gateway integration
  - New: `dags/utils/chart_generator.py` - Chart creation with indicators
  - New: `dags/utils/llm_signal_analyzer.py` - LLM signal generation
  - Modified: `docker-compose.yml` - Add LLM API keys configuration

## Success Criteria
1. Workflow successfully fetches TSLA market data from IBKR
2. Charts generated with all required indicators (SMA, RSI, MACD, BB)
3. LLM generates actionable trading signals (BUY/SELL/HOLD)
4. Orders placed successfully to IBKR (paper trading first)
5. Trades and portfolio tracked in MLflow
6. Complete workflow runs end-to-end within 60 seconds
7. All data validated using Pydantic models

