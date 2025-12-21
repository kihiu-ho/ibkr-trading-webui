## Why
- Operators need a **paper-faithful FinAgent workflow** (arXiv:2402.18485v3 Appendix F prompts) that can be audited end-to-end in Airflow/MLflow before relying on its signals.
- The existing FinAgent workflow uses mocked news by default; FinAgent’s market-intelligence stage is designed to ingest **latest market intelligence**, so we need a configurable **NewsAPI** source via `.env`.
- A new DAG id is required to keep the existing `finagent_trading_signal_workflow` stable while introducing v3 prompt fidelity and news ingestion.

## What Changes
- Add a new Airflow DAG (new DAG id) that runs the FinAgent pipeline using **verbatim v3 prompt templates** (system + stage prompts + XML output formats) sourced from `reference/paper/2402.18485v3.pdf`.
- Add a NewsAPI client utility driven by `.env` (`NEWS_API_KEY`, endpoint and filters) and pass fetched headlines/descriptions into the FinAgent market-intelligence stages.
- Expand MLflow logging for FinAgent runs to include **per-stage prompts, raw model responses, parsed XML**, and final signal artifacts, tagged with `analysis_method=finagent_v3`.

## Impact
- Affected specs: `finagent-v3-workflow` (new capability), `trading-workflow` (workflow template support update).
- Affected code: `dags/`, `dags/utils/`, `docs/guides/`, `env.example`.
