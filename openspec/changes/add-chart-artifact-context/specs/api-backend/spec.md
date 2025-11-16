# api-backend Change: Enriched Chart Artifact Responses

## ADDED Requirements

### Requirement: Chart Artifact API Hydration
The artifacts API SHALL return chart artifacts with embedded market data and LLM context without requiring additional endpoints.

#### Scenario: GET /api/artifacts returns enriched chart artifacts
- **GIVEN** chart artifacts exist for execution_id `ibkr_trading_signal_workflow`
- **WHEN** GET `/api/artifacts?type=chart` is called
- **THEN** each chart artifact SHALL include metadata.market_data_snapshot populated with OHLCV bars, timeframe, and fetched_at
- **AND** metadata.llm_analysis SHALL include action, confidence score, reasoning snippet, key factors, and recommended price levels
- **AND** prompt/response/model_name/prompt_length/response_length SHALL be filled, even if they were missing in the original row (via hydration logic)

#### Scenario: GET /api/artifacts/{id} hydrates missing context
- **GIVEN** a legacy chart artifact lacks persisted market data or LLM analysis
- **WHEN** GET `/api/artifacts/{id}` is called
- **THEN** the API SHALL fetch the latest cached market data for the symbol and attach it to metadata.market_data_snapshot
- **AND** the API SHALL derive prompt, response, and llm_analysis from the latest related LLM/signal artifacts when available before returning the payload
