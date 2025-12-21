# FinAgent Setup Guide

This guide explains how to enable the FinAgent multimodal workflow that pairs IBKR market data with the FinAgent architecture (market intelligence, diversified memory, dual reflections, and decision modules). Use it when you want Airflow to orchestrate FinAgent runs with MLflow tracking, Weaviate vector memory, and Neon metadata storage.

For a task-by-task + internal-stage walkthrough of the DAG, see `docs/guides/FINAGENT_TRADING_SIGNAL_WORKFLOW.md`.

## 1. Prerequisites
- **Docker/Airflow stack** booted via this repository (`start-services.sh` or `start-docker-services.sh`).
- **Python dependencies** rebuilt so the Airflow image includes the latest libraries:
  ```bash
  uv pip install --system -r airflow/requirements-airflow.txt
  ```
  This installs `weaviate-client` plus the existing TA/ML stack. If you plan to use the open-source TradingAgents or FinAgent reference repos directly, install them inside the same environment:
  ```bash
  uv pip install "git+https://github.com/TauricResearch/TradingAgents.git"
  uv pip install "git+https://github.com/DVampire/FinAgent.git"
  ```
  *(Optional – the workflow degrades gracefully if these extras are absent.)*

## 2. Environment Variables
Copy `env.example` to `.env` and review the new FinAgent settings:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Primary PostgreSQL connection string shared by backend, Airflow, and MLflow. |
| `NEON_DATABASE` | Dedicated Neon cluster for FinAgent metadata (market-data snapshots, imported news, prompt/response archives). Falls back to `DATABASE_URL` when unset. |
| `FINAGENT_ENABLED` | Feature flag (set to `true` to surface the DAG/UI toggle). |
| `FINAGENT_MODEL_PATH` | Local path to FinAgent checkpoints or prompt assets. |
| `FINAGENT_PROMPTS_VERSION` | Prompt template version selector (`v1` or `v3`). The paper-v3 DAG forces `v3` regardless of this setting. |
| `FINAGENT_REFLECTION_ROUNDS` | Number of low/high-level reflection iterations. |
| `FINAGENT_TOOLKIT` | Comma-delimited list of FinAgent tools (e.g., `technical_indicators,news_memory,rl_baseline`). |
| `WEAVIATE_URL` / `WEAVIATE_API_KEY` | Vector database connection for diversified memory. |
| `NEWS_API_KEY` | NewsAPI key (used to fetch “latest market intelligence” for the paper-v3 workflow). |
| `NEWS_API_BASE_URL` | NewsAPI endpoint (default: `https://newsapi.org/v2/everything`). |
| `NEWS_API_LANGUAGE` / `NEWS_API_SORT_BY` / `NEWS_API_PAGE_SIZE` / `NEWS_API_TIMEOUT` | NewsAPI request filters and timeouts. |
| `OPENAI_API_KEY` / `OPENAI_API_BASE` / `OPENAI_MODEL` / `LLM_VISION_MODEL` | Reused by FinAgent for market-intelligence prompts. |

Sample Weaviate snippet (mirrors the proposal requirements):
```python
import os
import weaviate
from weaviate.classes.init import Auth

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=os.environ["WEAVIATE_URL"],
    auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"]),
)
print(client.is_ready())
```

## 3. Enabling the FinAgent DAG
1. Ensure `.env` has `FINAGENT_ENABLED=true`.
2. Restart Airflow services so the DAGs are loaded:
   - `finagent_trading_signal_workflow` (existing / adapted prompts)
   - `finagent_paper_v3_workflow` (paper-v3 prompt templates + NewsAPI)
   - `finagent_autogen_pipeline_workflow` (AutoGen multi-agent pipeline with optional train/backtest + inference)
3. In the Airflow UI, trigger the desired DAG manually or schedule it (e.g., `0 13 * * 1-5`).
4. Provide strategy parameters (via the backend UI or DB) with `workflow_type="finagent_multi_modal"`.

## 4. Data & Metadata Flow
1. **IBKR data fetch** – the DAG calls `IBKRClient` for fresh OHLCV bars, generates charts through `webapp/services/chart_service.py`, and snapshots the result in Neon.
2. **FinAgent runner** – builds market-intelligence prompts, interacts with Weaviate (vector memory), executes dual reflections, and compares RL baselines.
   - For `finagent_paper_v3_workflow`, “latest market intelligence” is fetched from NewsAPI when `NEWS_API_KEY` is configured.
   - Prompts/responses are archived in the Neon database for auditing (when `NEON_DATABASE` is configured).
3. **MLflow logging** – parameters, metrics (PnL deltas, Sharpe estimates, confidence), prompts, and chart artifacts are logged via `mlflow_run_context`.
4. **Artifact storage** – final BUY/SELL/HOLD signals, reasoning summaries, RL comparisons, and chart URLs are published through the backend artifact API so the dashboard can display them.

## 5. Verification Checklist
- `airflow dags test finagent_trading_signal_workflow <date>` succeeds.
- MLflow UI contains a run tagged `workflow_type=finagent_signal` with chart and reasoning artifacts.
- Neon DB table `finagent_metadata` contains new rows for `market_data`, `import_data`, and `llm_prompt` kinds.
- Weaviate collection `FinAgentMemory` has embeddings for the latest reflections (use the Weaviate console or `client.collections.get("FinAgentMemory").data.objects.list()`).

## 6. Troubleshooting
| Issue | Fix |
|-------|-----|
| `weaviate` import errors | Re-run the Airflow requirements install; ensure `WEAVIATE_URL`/`WEAVIATE_API_KEY` are set. |
| Neon insert failures | Verify `NEON_DATABASE` uses the `postgresql+psycopg2://` format and that the IP is authorized in Neon. |
| FinAgent runner fallback mode | Install the optional `TradingAgents`/`FinAgent` packages or provide richer prompt assets under `FINAGENT_MODEL_PATH`. |
| MLflow artifacts missing | Confirm `MLFLOW_TRACKING_URI` is reachable and `mlflow server` container is healthy. |

With these settings in place, the FinAgent workflow can analyze IBKR market data using the FinAgent architecture, retain its reasoning traces in Neon/Weaviate, and surface traceable trading signals through the existing artifact UI.
