## Why
The `ibkr_trading_signal_workflow` still behaves like a dev-only DAG: it silently falls back to mock market data when `ib_insync` is missing, does not guarantee a full year of history, and forwards whatever limit price the LLM returns (including null/negative values). Those gaps block us from running the workflow in "prod mode" against the paper-trading gateway because:
- Real IBKR market data never gets fetched when the Airflow image is missing `ib_insync`, so downstream charting/LLM steps run on synthetic candles.
- Technical indicators require at least one year (≈252 daily bars) to align with our trading playbooks, but we never assert that requirement.
- IBKR rejects limit orders with missing or invalid prices, so actionable signals fail during live order placement.

## What Changes
- Enforce a production/paper trading mode flag so any missing `ib_insync` dependency or IBKR connection error fails the DAG instead of switching to mocked data; keep mock fallback for explicit dev/test runs only.
- Update the market-data task to explicitly request ≥252 daily bars per configured symbol and raise a retriable error when IBKR returns fewer bars; persist the actual bar count in artifacts/logs.
- Normalize limit prices before sending orders to IBKR by deriving them from LLM output or the latest fetched close price, validating they are positive decimals, and rejecting the signal when the workflow cannot produce a valid price.

## Impact
- Affected specs: `trading-workflow`, `order-management`
- Affected code: `dags/ibkr_trading_signal_workflow.py`, `dags/utils/config.py`, `dags/utils/ibkr_client.py`, `tests/workflow/test_ibkr_trading_signal_workflow.py`, Airflow image dependencies/documentation
