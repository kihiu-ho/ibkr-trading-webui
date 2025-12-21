## Why
- We want to add a **TradeMaster-based trading research pipeline** to this project without disrupting existing IBKR/FinAgent workflows.
- TradeMaster’s training/backtest + inference outputs are most useful when they are **tracked, reproducible, and auditable**:
  - **Airflow** for orchestration (per-symbol / batch runs)
  - **MLflow** for parameters, metrics, and artifacts
  - **AutoGen** for an auditable, multi-agent “review” layer that produces a structured decision payload and full conversation trace.
- Operators need consistent “run artifacts” (signal + reasoning + optional charts/backtest summary) visible in the WebUI and linked back to MLflow lineage.

## What Changes
- Add a new Airflow DAG (new DAG id) that runs a TradeMaster pipeline **per symbol** and supports:
  - `mode=both` (default): train/backtest then inference
  - `mode=train_backtest`
  - `mode=inference`
- Define symbol targeting rules:
  - If `dag_run.conf.symbol` is provided, run **only** that symbol (compatible with backend auto-trigger on symbol creation).
  - Otherwise “all symbols” means: **enabled symbols assigned to this DAG** via Workflow Symbols (`/api/workflow-symbols` links).
- Log all parameters/metrics/artifacts to MLflow and persist WebUI-compatible artifacts (signal + llm + optional chart/backtest artifacts) with MLflow lineage.
- Integrate TradeMaster as an upstream dependency (pinned to a commit hash) via one of:
  - vendored source in repo, or
  - build-time install from GitHub, or
  - a packaged wheel included in the Airflow image.

## Impact
- Affected specs:
  - `trading-workflow` (adds TradeMaster pipeline as a supported workflow)
  - New capability spec: `trademaster-autogen-pipeline`
- Affected code (post-approval implementation):
  - New Airflow DAG under `dags/`
  - New utilities under `dags/utils/` for TradeMaster adapter + AutoGen review wrapper
  - Updates to `airflow/requirements-airflow.txt` (TradeMaster deps; pinned)
  - New documentation under `docs/guides/`
- Risk/complexity:
  - TradeMaster dependencies may be heavy (e.g., torch) and require careful container sizing and runtime guardrails.
  - Batch mode can amplify LLM cost and runtime; enforce caps and safe defaults.
