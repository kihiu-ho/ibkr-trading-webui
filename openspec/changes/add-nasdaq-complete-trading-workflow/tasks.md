## 1. OpenSpec Proposal
- [x] 1.1 Create proposal.md with why/what/impact
- [x] 1.2 Create tasks.md with implementation checklist
- [x] 1.3 Create design.md with technical decisions
- [x] 1.4 Create spec deltas for all affected capabilities
- [ ] 1.5 Validate proposal: `openspec validate add-nasdaq-complete-trading-workflow --strict`

## 2. Multi-Symbol Workflow Implementation
- [ ] 2.1 Update DAG to support multiple symbols (TSLA, NVDA) from NASDAQ
- [ ] 2.2 Implement parallel market data fetching for multiple symbols
- [ ] 2.3 Add symbol parameter to workflow configuration
- [ ] 2.4 Update XCom data structures to handle multi-symbol data

## 3. Chart Generation Enhancement
- [ ] 3.1 Extend chart generator to support daily and weekly timeframes
- [ ] 3.2 Ensure technical indicators (SMA 20/50/200, RSI, MACD, Bollinger Bands) are included
- [ ] 3.3 Generate separate charts for each symbol and timeframe
- [ ] 3.4 Store chart artifacts with proper metadata (symbol, timeframe, indicators)

## 4. LLM Analysis Integration
- [ ] 4.1 Update LLM analyzer to accept multiple charts (daily + weekly) per symbol
- [ ] 4.2 Enhance prompt to analyze both timeframes for comprehensive signals
- [ ] 4.3 Store LLM artifacts with chart references and analysis results
- [ ] 4.4 Generate trading signals with confidence scores based on multi-timeframe analysis

## 5. IBKR Integration
- [ ] 5.1 Implement order placement service for IBKR API
- [ ] 5.2 Add trade retrieval functionality to fetch executed trades
- [ ] 5.3 Implement portfolio management to get current positions
- [ ] 5.4 Add error handling and retry logic for IBKR API calls
- [ ] 5.5 Store order, trade, and portfolio artifacts in database

## 6. MLflow Tracking
- [ ] 6.1 Add MLflow run context to all workflow tasks
- [ ] 6.2 Log market data parameters (symbols, timeframes, bar counts)
- [ ] 6.3 Log chart generation metrics (indicators, chart types)
- [ ] 6.4 Log LLM analysis parameters (model, prompt length, response length)
- [ ] 6.5 Log trading signals (action, confidence, reasoning)
- [ ] 6.6 Log order execution results (order_id, status, fills)
- [ ] 6.7 Log portfolio positions and P&L

## 7. Artifact Visualization Enhancement
- [ ] 7.1 Update artifacts API to support execution_id grouping
- [ ] 7.2 Add workflow metadata to artifact responses (dag_id, execution_id, step_name)
- [ ] 7.3 Enhance frontend grouped view to show all artifact types (charts, LLM, signals, orders, trades, portfolio)
- [ ] 7.4 Add Airflow run details integration showing artifacts per execution
- [ ] 7.5 Implement artifact type filtering and search functionality
- [ ] 7.6 Add artifact detail pages with full metadata display

## 8. Testing
- [ ] 8.1 Test multi-symbol market data fetching
- [ ] 8.2 Test daily and weekly chart generation with indicators
- [ ] 8.3 Test LLM analysis with multiple charts
- [ ] 8.4 Test order placement (paper trading account)
- [ ] 8.5 Test trade retrieval and portfolio management
- [ ] 8.6 Test artifact visualization and grouping
- [ ] 8.7 Test Airflow run details integration
- [ ] 8.8 End-to-end workflow test with TSLA and NVDA

## 9. Documentation
- [ ] 9.1 Update workflow documentation with multi-symbol instructions
- [ ] 9.2 Document artifact visualization features
- [ ] 9.3 Add API documentation for new endpoints
- [ ] 9.4 Create user guide for multi-symbol trading workflow

