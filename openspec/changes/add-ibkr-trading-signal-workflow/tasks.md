# Implementation Tasks

## 1. OpenSpec Setup
- [x] 1.1 Create proposal.md
- [x] 1.2 Create tasks.md
- [ ] 1.3 Create spec deltas for all capabilities
- [ ] 1.4 Validate with `openspec validate add-ibkr-trading-signal-workflow --strict`

## 2. Pydantic Models
- [ ] 2.1 Create `dags/models/__init__.py`
- [ ] 2.2 Create `MarketData` model (OHLCV data)
- [ ] 2.3 Create `TechnicalIndicators` model (SMA, RSI, MACD, BB)
- [ ] 2.4 Create `ChartConfig` model (timeframe, indicators, styling)
- [ ] 2.5 Create `TradingSignal` model (action, confidence, reasoning)
- [ ] 2.6 Create `Order` model (symbol, quantity, order_type, side)
- [ ] 2.7 Create `Trade` model (execution details)
- [ ] 2.8 Create `Portfolio` model (positions, cash, total_value)

## 3. IBKR Integration
- [ ] 3.1 Create `dags/utils/ibkr_client.py`
- [ ] 3.2 Implement connection to IBKR Gateway
- [ ] 3.3 Implement market data fetching (historical and real-time)
- [ ] 3.4 Implement order placement (market, limit orders)
- [ ] 3.5 Implement trade retrieval
- [ ] 3.6 Implement portfolio status retrieval
- [ ] 3.7 Add error handling and retries
- [ ] 3.8 Add connection status monitoring

## 4. Chart Generation
- [ ] 4.1 Create `dags/utils/chart_generator.py`
- [ ] 4.2 Implement candlestick chart creation
- [ ] 4.3 Calculate and plot SMA (20, 50, 200)
- [ ] 4.4 Calculate and plot RSI (14-period)
- [ ] 4.5 Calculate and plot MACD (12, 26, 9)
- [ ] 4.6 Calculate and plot Bollinger Bands (20, 2)
- [ ] 4.7 Add volume subplot
- [ ] 4.8 Implement chart styling (colors, legends, gridlines)
- [ ] 4.9 Export charts as PNG files (1920x1080)
- [ ] 4.10 Generate both daily and weekly charts

## 5. LLM Signal Generation
- [ ] 5.1 Create `dags/utils/llm_signal_analyzer.py`
- [ ] 5.2 Implement OpenAI integration
- [ ] 5.3 Implement Anthropic Claude integration
- [ ] 5.4 Create prompt template for chart analysis
- [ ] 5.5 Encode charts to base64 for vision models
- [ ] 5.6 Parse LLM response into TradingSignal model
- [ ] 5.7 Implement confidence scoring
- [ ] 5.8 Add multi-timeframe confirmation logic
- [ ] 5.9 Add error handling for API failures

## 6. Main Workflow DAG
- [ ] 6.1 Create `dags/ibkr_trading_signal_workflow.py`
- [ ] 6.2 Implement `fetch_market_data` task
- [ ] 6.3 Implement `generate_daily_chart` task
- [ ] 6.4 Implement `generate_weekly_chart` task
- [ ] 6.5 Implement `analyze_with_llm` task
- [ ] 6.6 Implement `place_order` task
- [ ] 6.7 Implement `get_trades` task
- [ ] 6.8 Implement `get_portfolio` task
- [ ] 6.9 Implement `log_to_mlflow` task
- [ ] 6.10 Set up task dependencies
- [ ] 6.11 Add task retries and error handling

## 7. Configuration
- [ ] 7.1 Add IBKR configuration to docker-compose.yml
- [ ] 7.2 Add LLM API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)
- [ ] 7.3 Add trading parameters (SYMBOL, POSITION_SIZE, etc.)
- [ ] 7.4 Create `.env` template with all required variables
- [ ] 7.5 Document configuration options

## 8. Testing
- [ ] 8.1 Test market data fetching from IBKR
- [ ] 8.2 Test chart generation with all indicators
- [ ] 8.3 Test LLM signal generation
- [ ] 8.4 Test order placement (paper trading)
- [ ] 8.5 Test trade retrieval
- [ ] 8.6 Test portfolio retrieval
- [ ] 8.7 Test complete end-to-end workflow
- [ ] 8.8 Test error scenarios (IBKR down, LLM API error, etc.)
- [ ] 8.9 Verify MLflow tracking
- [ ] 8.10 Verify Pydantic validation catches bad data

## 9. Documentation
- [ ] 9.1 Create workflow usage guide
- [ ] 9.2 Document Pydantic models
- [ ] 9.3 Document IBKR setup requirements
- [ ] 9.4 Document LLM API setup
- [ ] 9.5 Create trading signal interpretation guide
- [ ] 9.6 Add safety warnings for live trading

