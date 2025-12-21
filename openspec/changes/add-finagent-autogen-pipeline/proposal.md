## Why
- We need a **new, auditable FinAgent pipeline** that runs as a dedicated Airflow DAG (without replacing existing FinAgent DAGs), supports **both training/backtest and inference**, and produces WebUI-compatible artifacts.
- FinAgent-style systems benefit from multi-perspective reasoning (technical analysis, news/sentiment, risk, execution). The project already specifies **Microsoft AutoGen** for multi-agent workflows; we should reuse that capability to orchestrate the FinAgent decision process.
- Operators require full lineage: inputs → agent conversation → decision → (optional) model package/registry, tracked in **MLflow** and linked back to the WebUI artifact pages.

## What Changes
- Add a new Airflow DAG (new DAG id) that can run in **three modes** via `dag_run.conf`:
  - `mode=inference` (default): fetch latest inputs → AutoGen multi-agent FinAgent reasoning → emit signal → persist artifacts.
  - `mode=train_backtest`: run training/backtest pipeline, log metrics, and register a model/config package in MLflow.
  - `mode=both`: execute training/backtest then inference using the newly registered package.
- Integrate `akshata29/finagent` as the upstream FinAgent implementation (pinned to a commit hash) and wrap it with an adapter that normalizes:
  - trading decision → existing TradingSignal-compatible schema
  - metrics → MLflow metrics
  - traces (AutoGen conversation + stage outputs) → MLflow artifacts
- Use Microsoft AutoGen as the orchestration layer for multi-agent collaboration:
  - define required agents (MarketData/Technical, News, Risk, Executor) and optional memory agent (Weaviate-backed, fallback to in-memory)
  - disable arbitrary code execution by default; expose a small, whitelisted tool surface (risk calcs, indicator summary, retrieval)
- Extend documentation with a deep “model logic” guide including flowcharts/diagrams covering:
  - training/backtest flow
  - inference flow + agent conversation lifecycle
  - storage/lineage across Airflow, MLflow, MinIO, Postgres/Neon, optional Weaviate

## Impact
- Affected specs:
  - `trading-workflow` (new workflow template `finagent_autogen_pipeline`)
  - `autogen-framework` (referenced; no breaking changes)
  - New capability spec: `finagent-autogen-pipeline`
- Affected code:
  - New Airflow DAG under `dags/`
  - New utilities under `dags/utils/` for AutoGen orchestration + upstream adapter
  - Updates to `airflow/requirements-airflow.txt` (AutoGen + upstream finagent dependency)
  - New documentation under `docs/guides/` and `docs/implementation/`

