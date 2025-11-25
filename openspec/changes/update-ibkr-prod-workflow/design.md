## Context
The trading signal DAG currently uses a convenience mock path whenever `ib_insync` cannot be imported or IBKR connectivity fails. That made local experiments easy but prevents "prod mode" operation: Airflow workers without `ib_insync` never hit real IBKR data, market history can drop below the 1-year lookback we need for indicators, and limit orders reach IBKR without guaranteed prices. We need to harden the workflow for the paper-trading gateway (port 4002) so every run either processes real market data or fails loudly before any order step.

## Goals / Non-Goals
- **Goals**: (1) Enforce strict mode that uses real IBKR data/orders whenever `ENVIRONMENT` indicates prod/paper operations, (2) guarantee ≥252 daily bars per configured symbol, (3) normalize limit prices before orders are placed.
- **Non-Goals**: Switching to the live-money gateway (port 4001), redesigning LLM signal generation, or introducing multi-symbol scheduling changes.

## Decisions
1. **Strict Mode Flag**: Introduce `IBKR_STRICT_MODE` (default true for any environment other than `development`/`test`). When enabled, `IBKRClient` raises a `RuntimeError` if `ib_insync` is missing or the gateway connection fails. Mock data remains available for dev/test by explicitly disabling the flag.
2. **Market Data Guard**: `fetch_market_data_task` explicitly requests `duration='1 Y'` with `bar_size='1 day'` and inspects the resulting `MarketData.bar_count`. If fewer than 252 bars are returned, the task raises `AirflowFailException` with retry semantics so operators can re-run once IBKR data is ready.
3. **Limit Price Normalization**: `place_order_task` builds limit orders using (a) LLM-provided `suggested_entry_price` when valid, else (b) the latest close price from the market data snapshot. If neither path yields a positive decimal, the signal is marked non-actionable and downstream tasks skip order placement. Validation errors never reach IBKR.
4. **Dependency Assurance**: Airflow/venv requirements will explicitly install `ib_insync`. During strict mode runs we also log the detected package version inside the DAG so operators can diagnose mismatched environments.

## Risks / Trade-offs
- Enforcing strict mode could break existing dev workflows if the flag defaults to true everywhere; we mitigate this by keying off `ENVIRONMENT` and documenting overrides.
- Requesting a full year of data increases IBKR API latency; runs might take longer, but the signal pipeline already assumes 60+ lookback periods so the added latency (~1 second) is acceptable. We will set generous but finite timeouts.
- Rejecting orders when limit price normalization fails might reduce trade volume, but it is safer than letting IBKR reject them mid-DAG with ambiguous errors.

## Migration Plan
1. Ship the strict-mode flag + guards but default it to true only when `ENVIRONMENT` is `production` or `paper` to avoid sudden failures locally.
2. Update Airflow image requirements to ensure `ib_insync` is installed; verify by importing during DAG parsing.
3. Roll out the updated DAG and monitor first run; if strict mode causes import errors, instruct operators to install dependencies before re-running.

## Open Questions
- Should we expose the strict-mode toggle via the frontend parameter editor for ad-hoc runs? (Deferred until user feedback.)
- Do we need to cap the number of retries for insufficient market data, or will the default DAG retry policy suffice? (Assume default for now.)
