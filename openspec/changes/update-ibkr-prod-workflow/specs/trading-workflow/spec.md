## ADDED Requirements
### Requirement: Production Mode IBKR Connectivity
The `ibkr_trading_signal_workflow` SHALL enforce a strict production mode that uses real IBKR market data via the paper-trading gateway (port 4002) whenever `ENVIRONMENT` is set to `paper` or `production`, or when `IBKR_STRICT_MODE=true`.

#### Scenario: Strict mode fetches real IBKR data
- **WHEN** the workflow runs with strict mode enabled
- **THEN** it SHALL verify that `ib_insync` is installed and importable before any task executes
- **AND** it SHALL attempt to connect to the IBKR Client Portal Gateway at the configured host and port 4002
- **AND** if the dependency is missing or the connection fails, the DAG SHALL fail fast with a clear error instead of falling back to mock data

#### Scenario: Mock fallback restricted to development
- **WHEN** the workflow runs with strict mode disabled (e.g., `ENVIRONMENT=development`)
- **THEN** it MAY use the existing mock market data/order paths for local testing
- **AND** the DAG SHALL log that it is running with mock data so operators do not mistake the run for production

### Requirement: One-Year Market Data Coverage
The `fetch_market_data` step SHALL retrieve at least 252 daily bars (≈ 1 trading year) for the configured symbol before downstream analysis begins.

#### Scenario: Enforce ≥252 daily bars
- **WHEN** strict mode is enabled and market data is fetched
- **THEN** the task SHALL request `duration='1 Y'` and `bar_size='1 day'`
- **AND** it SHALL inspect the returned `MarketData.bar_count`
- **AND** if fewer than 252 bars are returned, the task SHALL raise a retriable failure explaining the deficiency

#### Scenario: Single-symbol focus
- **WHEN** multiple symbols are configured via `STOCK_SYMBOLS`
- **THEN** the production-mode workflow SHALL select the first symbol only (matching current behavior)
- **AND** it SHALL log the symbol + bar count so reviewers can audit which ticker satisfied the ≥252-bar guarantee
