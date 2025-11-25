## Why
- FinAgent (arXiv:2402.18485) describes a multimodal, dual-reflection trading agent that fuses broker-grade market feeds, news, and chart inputs, yet the current IBKR workflow only performs single-pass LLM analysis.
- The ops team needs an auditable way to execute FinAgent inside Airflow, use FinAgent's GitHub reference implementation, and capture metrics in MLflow before trusting the new signals in IBKR.
- No spec currently maps how IBKR market data, FinAgent modules, Airflow DAGs, and MLflow tracking link together, so engineers lack guidance on data flow, configuration, and validation responsibilities.

## What Changes
- Introduce a FinAgent orchestration module that wraps the DVampire/FinAgent reference code and reuses our existing IBKR data/indicator modules plus `webapp/services/chart_service.py` so it can pull live broker market data, generate charts with our proven Plotly pipeline, and emit BUY/SELL/HOLD signals compatible with existing TradingSignal models.
- Add an Airflow DAG + Python script that sequences market-data ingestion, FinAgent market intelligence/reflection passes, decision emission, and MLflow logging, storing intermediate artifacts (reflections, reasoning traces, chart snapshots) for IBKR review.
- Integrate Weaviate as the vector database for FinAgent’s diversified memory, wiring `.env` variables (`WEAVIATE_URL`, `WEAVIATE_API_KEY`) and the canonical connection snippet:
  ```python
  import os
  import weaviate
  from weaviate.classes.init import Auth

  client = weaviate.connect_to_weaviate_cloud(
      cluster_url=os.environ["WEAVIATE_URL"],
      auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"]),
  )
  ```
  so the Airflow tasks can store/retrieve FinAgent reflections.
- Ensure FinAgent orchestration reads `.env` configuration for the shared PostgreSQL database (`DATABASE_URL`) and LLM provider settings (`OPENAI_API_KEY`, `OPENAI_API_BASE`, `OPENAI_MODEL`, `LLM_VISION_*`) instead of hardcoding credentials, so Airflow, backend, and FinAgent share one source of truth.
- Add a dedicated `NEON_DATABASE` connection string in `.env` that points to the Neon Postgres cluster where we will store FinAgent metadata (reflection transcripts), imported news datasets, normalized market data snapshots, and LLM prompts for auditability.
- Extend workflow specifications so FinAgent is a first-class workflow template with configuration schema (symbols, FinAgent checkpoints, RL baselines, tool toggles, vector DB settings) surfaced via environment variables and/or strategy params.
- Document MLflow + artifact expectations (metrics, parameters, serialized FinAgent state) and validation checkpoints so FinAgent runs can be audited before orders go live.

## Impact
- Affected specs: `finagent-signal-orchestration` (new capability), `trading-workflow` (workflow template support for FinAgent).
- Affected code: Airflow DAGs under `dags/`, shared workflow utilities under `dags/utils/`, backend signal services that read MLflow runs, configuration docs (`docs/guides`, `.env.example`), and reference assets inside `reference/paper/` + new FinAgent wrappers.
