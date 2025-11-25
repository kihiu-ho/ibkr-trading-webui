## 1. Production Mode Configuration
- [x] 1.1 Add `IBKR_STRICT_MODE` (default true when `ENVIRONMENT` != development) to `WorkflowConfig` and expose it to DAGs/tests.
- [x] 1.2 Document how to toggle strict vs mock mode in `docs/guides/QUICK_REFERENCE.md` (or relevant guide).

## 2. Market Data Coverage
- [x] 2.1 Update `ibkr_trading_signal_workflow.fetch_market_data_task` to request ≥252 daily bars and raise a clear error if fewer are returned.
- [x] 2.2 Persist the bar count + strict-mode metadata in artifacts/logging so downstream steps can assert production data.
- [x] 2.3 Add unit tests covering success/failure when IBKR returns enough vs insufficient bars.

## 3. IBKR Client Strict Mode
- [x] 3.1 Update `IBKRClient` to fail fast (with actionable messaging) when `ib_insync` is unavailable or connection fails while strict mode is enabled.
- [x] 3.2 Keep mock fallback for development/test runs and add regression tests for both modes.
- [x] 3.3 Ensure the Airflow image/install scripts include `ib_insync` so strict mode works out of the box.

## 4. Limit Price Normalization
- [x] 4.1 Enhance `place_order_task` to derive a limit price from the LLM signal or latest market data snapshot, validating it is > 0.
- [x] 4.2 Reject actionable signals (and explain via logs/artifacts) when a valid limit price cannot be computed.
- [x] 4.3 Extend workflow/order tests to cover valid/invalid limit-price cases.

## 5. Validation
- [x] 5.1 Run `pytest tests/workflow/test_ibkr_trading_signal_workflow.py -k prod_mode` (or equivalent targeted suite).
- [ ] 5.2 Trigger `ibkr_trading_signal_workflow` against the paper-trading gateway with strict mode enabled and confirm real market data, bar coverage, and successful (or cleanly rejected) order placement. *(Pending: requires access to IBKR paper gateway, not available in this environment.)*
