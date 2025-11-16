# artifact-management Change: Chart Artifact Context

## ADDED Requirements

### Requirement: Chart Artifact Context Persistence
Chart artifacts SHALL persist the market data snapshot, indicator summary, and LLM analysis context that produced the image.

#### Scenario: Store market data snapshot with chart artifacts
- **GIVEN** the ibkr_trading_signal_workflow generates a chart artifact
- **WHEN** the artifact is stored
- **THEN** metadata SHALL include `market_data_snapshot` with symbol, timeframe, fetched_at, latest_price, bar_count, and OHLCV bars
- **AND** chart metadata SHALL include latest indicator values (SMA, RSI, MACD, Bollinger, volume, ATR, SuperTrend)
- **AND** this context SHALL travel with the artifact so the frontend can render market tables without extra API calls

#### Scenario: Attach LLM analysis context to chart artifacts
- **GIVEN** an LLM analysis completes for the same symbol + execution_id that created the charts
- **WHEN** the workflow stores the LLM artifact
- **THEN** the chart artifacts' `prompt`, `response`, `model_name`, `prompt_length`, and `response_length` fields SHALL be populated with that analysis
- **AND** metadata SHALL add an `llm_analysis` block summarizing action, confidence, reasoning snippet, key factors, and recommended price levels
- **AND** previously created chart artifacts SHALL be hydrated with the best available analysis when fetched if the persisted fields are empty
