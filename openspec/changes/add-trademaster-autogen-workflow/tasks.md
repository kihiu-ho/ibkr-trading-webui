## 1. Specification + Planning
- [ ] 1.1 Confirm DAG id (`trademaster_autogen_pipeline_workflow`) and document run modes (`train_backtest`, `inference`, `both`).
- [ ] 1.2 Define symbol targeting rules:
  - `dag_run.conf.symbol` runs single-symbol mode
  - otherwise run enabled symbols assigned to this DAG via Workflow Symbols links
- [ ] 1.3 Define TradeMaster integration method (vendor vs build-time install vs wheel) and pin to a commit/version.

## 2. Dependencies + Container Wiring
- [ ] 2.1 Add pinned TradeMaster dependencies to `airflow/requirements-airflow.txt` (and any required system libs if needed).
- [ ] 2.2 Ensure Airflow image builds and the new DAG imports cleanly (no import errors in Airflow UI).
- [ ] 2.3 Add any new env/config entries to `env.example` (bounded training defaults, max symbols per batch, etc.).

## 3. TradeMaster Adapter Layer
- [ ] 3.1 Inspect upstream TradeMaster entrypoints and define a minimal wrapper API:
  - `train_backtest(symbol, market_data, config) -> {metrics, model_uri/artifacts}`
  - `infer(symbol, market_data, model_uri, config) -> {outputs, metrics}`
- [ ] 3.2 Implement dataset/environment adapters from existing `MarketData` into TradeMaster input format.
- [ ] 3.3 Normalize TradeMaster outputs into:
  - MLflow metrics/artifacts
  - WebUI-compatible artifacts metadata (for display and auditing)

## 4. AutoGen Review Layer
- [ ] 4.1 Implement/extend an AutoGen orchestrator that takes TradeMaster outputs + market context and emits a structured decision.
- [ ] 4.2 Store full conversation transcript as an MLflow artifact and persist `signal` + `llm` artifacts in the WebUI.

## 5. New Airflow DAG (Assigned Symbols)
- [ ] 5.1 Add DAG `trademaster_autogen_pipeline_workflow` that resolves symbols at runtime (no backend calls at import time).
- [ ] 5.2 Implement single-symbol mode via `dag_run.conf.symbol` for backend auto-trigger compatibility.
- [ ] 5.3 Implement batch mode that fetches `/api/workflow-symbols/?enabled_only=true` and filters to symbols assigned to this DAG.
- [ ] 5.4 Implement default mode `both` (train/backtest + inference), overridable via `dag_run.conf.mode`.
- [ ] 5.5 Add guardrails (max symbols per run, bounded epochs/lookback defaults, safe retries/backoff).

## 6. Documentation + Validation
- [ ] 6.1 Add docs describing:
  - how to unpause the DAG
  - how to assign symbols to the DAG in Workflow Symbols
  - how to trigger single-symbol vs batch runs and pass per-run config via `dag_run.conf`
- [ ] 6.2 Smoke-run in docker compose and verify:
  - MLflow runs contain expected params/metrics/artifacts
  - WebUI artifacts are persisted and linked to MLflow lineage
