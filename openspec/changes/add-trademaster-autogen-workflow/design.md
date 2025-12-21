## Overview
This change introduces a new Airflow DAG that runs a TradeMaster pipeline per symbol and then uses an AutoGen “review” step to convert TradeMaster outputs into a WebUI-compatible TradingSignal + auditable reasoning trace. Runs are logged to MLflow and persisted to the WebUI artifacts store.

The default behavior is **mode=both** (train/backtest then inference) and “all symbols” means **enabled symbols assigned to this DAG** via Workflow Symbols links (not every symbol in the database).

## Decisions
### DAG id and run modes
- **DAG id**: `trademaster_autogen_pipeline_workflow` (new; does not conflict with existing DAGs).
- **Modes** (via `dag_run.conf.mode`):
  - `both` (default): train/backtest → inference → AutoGen review → persist
  - `train_backtest`
  - `inference`

### Symbol targeting rules
- If `dag_run.conf.symbol` is present: execute only that symbol (backend auto-trigger compatibility).
- Else:
  - Fetch `GET /api/workflow-symbols/?enabled_only=true`
  - Select symbols that have an **active** workflow link with `dag_id == trademaster_autogen_pipeline_workflow`
  - Optionally apply a per-run cap (`max_symbols`) and sort by symbol priority.

### Configuration layering
- Base defaults from environment (bounded epochs/lookback, max symbols per run, etc.).
- Per-run overrides from `dag_run.conf`.
- Per-symbol overrides from `symbol_workflow_links.config` (JSON).

### TradeMaster integration method (pick one during implementation)
Option A (recommended): **Vendor TradeMaster source** into the repo under a dedicated directory and pin to a commit hash.
- Pros: reproducible builds without runtime network dependency, simpler runtime imports.
- Cons: increases repo size; requires a clear update process.

Option B: **Build-time install from GitHub** pinned to a commit hash.
- Pros: keeps repo smaller.
- Cons: requires network during build; can be brittle without a lockfile.

Option C: **Wheel** built from TradeMaster and copied into the Airflow image.
- Pros: reproducible artifact, clean install semantics.
- Cons: extra packaging overhead.

### Logging and persistence
- MLflow:
  - One MLflow run per symbol per DAG run (run_name includes symbol and timestamp).
  - Log training/backtest metrics and key artifacts (e.g., config, equity curve, model bundle reference).
  - Log AutoGen conversation transcript as an artifact.
- WebUI artifacts:
  - Persist `signal` + `llm` artifacts at minimum.
  - Attach MLflow lineage (`run_id`, `experiment_id`) using existing artifact update utilities.

### Airflow implementation notes
- Avoid backend API calls at DAG import time (prevents import errors and scheduler load).
- Prefer dynamic task mapping so each symbol runs independently.
- Avoid pushing large payloads through XCom; store large blobs as MLflow artifacts and pass references.

