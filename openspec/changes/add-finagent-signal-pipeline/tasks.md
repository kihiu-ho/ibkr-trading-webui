## 1. Specification + Dependencies
- [ ] 1.1 Vendor/declare FinAgent (plus optional TradingAgents extras for RL baselines) and update `.env.example` with FINAGENT_* settings.
- [ ] 1.2 Capture GPU/CPU fallback assumptions + dataset locations inside docs (`docs/guides/FINAGENT_SETUP.md`).
- [ ] 1.3 Add `WEAVIATE_URL` / `WEAVIATE_API_KEY` env variables with the provided connection snippet and describe deployment expectations (cloud cluster, auth mode).
- [ ] 1.4 Document/re-confirm usage of existing `.env` entries (`DATABASE_URL`, `NEON_DATABASE`, `OPENAI_API_KEY`, `OPENAI_API_BASE`, `OPENAI_MODEL`, `LLM_VISION_*`) for FinAgent so no credentials are duplicated in code.

## 2. FinAgent Runner + Tests
- [ ] 2.1 Implement `dags/utils/finagent_runner.py` to pull live IBKR market data via existing workflow modules, render charts through `webapp/services/chart_service.py`, invoke DVampire/FinAgent components (market intelligence, dual reflection, decision), and emit a normalized signal payload (JSON serializable) with reasoning + metrics.
- [ ] 2.2 Add unit tests under `dags/tests/` (or `tests/unit/workflows/`) that stub FinAgent outputs and verify we correctly map to TradingSignal schema + risk checks.
- [ ] 2.3 Wire diversified memory + reflection storage into Weaviate (mock in tests) so the runner can upsert/query embeddings keyed by symbol + workflow execution.

## 3. Airflow DAG + MLflow Tracking
- [ ] 3.1 Add `dags/finagent_trading_signal_workflow.py` containing tasks for dataset prep, FinAgent inference, MLflow logging, and signal persistence; reuse `mlflow_run_context` helpers and store artifacts to MinIO.
- [ ] 3.2 Update DAG configs + CLI docs to explain how to trigger FinAgent workflows (Airflow variables, schedule, fallback behavior).

## 4. Backend / API Wiring
- [ ] 4.1 Ensure backend services understand FinAgent-specific fields (reflection summary, RL baselines) when reading MLflow runs and exposing `/api/signals`.
- [ ] 4.2 Document API/contract changes in `docs/guides/FINAGENT_SETUP.md` + README.

## 5. Validation
- [ ] 5.1 Run `pytest tests/unit/workflows/test_finagent_runner.py -q` (or equivalent) and attach logs.
- [ ] 5.2 Run `AIRFLOW__CORE__LOAD_EXAMPLES=0 airflow dags test finagent_trading_signal_workflow <date>` locally to ensure DAG imports succeed.
- [ ] 5.3 Capture MLflow UI screenshot / describe run_id verifying FinAgent metrics recorded.
