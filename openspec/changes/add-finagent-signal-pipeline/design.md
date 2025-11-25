## Overview
FinAgent adds a multimodal dual-reflection agent (Market Intelligence + Memory + Low/High-level Reflection + Decision) described in arXiv:2402.18485. We will embed the DVampire/FinAgent modules next to our Airflow DAG so that IBKR market data and our existing market-data/indicator modules drive the environment while MLflow captures every run. The orchestrator lives in `dags/utils/finagent_runner.py` and exposes a single `run_finagent_signal(symbol, config)` routine called from a dedicated Airflow DAG.

## Component Boundaries
1. **IBKR market data adapter + chart service**
   - Uses existing `utils.ibkr_client.IBKRClient`, indicator utilities, and `webapp/services/chart_service.py` (Plotly-based) to pull OHLCV windows, compute technical studies, and capture chart JPEGs directly from the broker feed.
   - Normalizes outputs into our existing `MarketData`/`TechnicalIndicators` models and reuses `chart_service.generate_technical_chart` for consistent visuals that FinAgent consumes and we store in artifacts/minio.
2. **FinAgent wrapper**
   - Downloads/loads FinAgent checkpoints + prompt templates from DVampire/FinAgent.
   - Exposes hooks for: market intelligence prompt building, diversified memory retrieval (news embeddings, price reflections), low/high reflection loops, and final decision.
   - Accepts runtime config (agent prompts, number of reflection passes, RL baseline toggles, FinAgent tool flags) pulled from Airflow variables or `.env` (DATABASE_URL, NEON_DATABASE, OPENAI_* / LLM_VISION_*), ensuring LLM credentials + Postgres connection stay centralized.
   - Reuses `DATABASE_URL` for core app interactions and `NEON_DATABASE` for FinAgent-specific metadata stores (imported news datasets, normalized market data snapshots, LLM prompt/response archives) so we keep a clean audit trail in Neon without touching transactional tables.
3. **Vector memory (Weaviate)**
   - Establishes a connection using the prescribed snippet:
     ```python
     import os
     import weaviate
     from weaviate.classes.init import Auth

     client = weaviate.connect_to_weaviate_cloud(
         cluster_url=os.environ["WEAVIATE_URL"],
         auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"]),
     )
     ```
   - Stores/retrieves FinAgent diversified memory (news embeddings, reflection summaries, tool outputs) keyed by symbol + workflow execution, enabling low/high-level reflection to ground on prior context.
4. **Airflow DAG** (`finagent_trading_signal_workflow`)
   - Tasks: `prepare_datasets` → `run_finagent_inference` → `score_risk_and_signal` → `log_mlflow_artifacts` → `persist_signal`.
   - Uses XCom (JSON) to handoff outputs; uses `IBKRClient` only after FinAgent decision passes risk filters.
   - Loads `.env` via the existing config helper so each task has access to DATABASE_URL, NEON_DATABASE, and OPENAI_* variables without redefining settings.
5. **MLflow tracking + artifact sync**
   - `mlflow_run_context` wrapper logs: parameters (agent config, dataset, FinAgent version), metrics (expected return, Sharpe, FinAgent profit, decision confidence), artifacts (market intelligence prompt, dual reflection transcripts, final reasoning, chart PNGs).
   - Links MLflow run_id back to workflow_execution_id + strategy_id in database for traceability.
6. **Signal persistence + APIs**
   - Convert FinAgent output into `TradingSignal` record and store via existing backend service, including FinAgent-specific fields (reflection summary, RL baseline comparison, risk label).

## Data Flow
1. Airflow fetches latest OHLCV bars + news directly from IBKR (via `IBKRClient`) and our existing news adapters, then generates updated indicator snapshots + charts through `chart_service.generate_technical_chart`.
2. Market intelligence module synthesizes multimodal context + charts.
3. Memory + dual reflection modules iterate (configurable rounds), persist reflections to Weaviate, and retrieve the most relevant memories for the current context.
4. Decision module reasons over FinAgent reflections + optional RL baseline stats (sourced from TradingAgents reference runs or replay buffers) to emit action + reasoning.
5. Metadata snapshots (imported news, normalized market data, LLM prompts/responses) are persisted to the Neon Postgres instance via `NEON_DATABASE` for auditing.
6. MLflow run logs context + metrics; artifacts uploaded to MinIO via existing helpers.
7. Backend signal service ingests MLflow run metadata and surfaces FinAgent decision via API.

## Tooling / Dependencies
- Add optional extras to `requirements.txt` / `backend/requirements.txt`: `finagent`, `transformers`, `sentence-transformers`, `weaviate-client`, `trading-agents` (for RL baseline comparisons only), `vllm` (behind feature flag) if not already available.
- Provide config flags: `FINAGENT_ENABLED`, `FINAGENT_MODEL_PATH`, `FINAGENT_REFLECTION_ROUNDS`, `FINAGENT_TOOLKIT`.
- Extend `.env.example` with `WEAVIATE_URL`, `WEAVIATE_API_KEY`, and `NEON_DATABASE` documenting how Neon stores FinAgent metadata/import data/LLM prompts.
- Provide mocks/unit tests for FinAgent adapter when GPU is unavailable; allow CPU-safe fallback by stubbing FinAgent call.

## Open Questions / Assumptions
- Assume FinAgent repo is vendored via git submodule or packaged wheel; initial implementation can vendor a thin subset under `reference/finagent_runtime` if dependency management becomes a bottleneck.
- TradingAgents artifacts (for PPO/DQN/SAC baseline comparisons) live under `reference/workflow/trading_agents_data/`; we only need read-only access because live market data now originates from IBKR workflows.
