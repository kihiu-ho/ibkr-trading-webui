## 1. Specification + Configuration
- [ ] 1.1 Add NewsAPI configuration to `env.example` (`NEWS_API_KEY`, `NEWS_API_BASE_URL`, and request filters) and document in `docs/guides/FINAGENT_SETUP.md`.
- [ ] 1.2 Add `FINAGENT_PROMPTS_VERSION` and document prompt-version behavior (v1 vs v3).

## 2. News API Integration
- [ ] 2.1 Implement `dags/utils/news_api_client.py` to fetch latest headlines for a ticker via NewsAPI (`/v2/everything`) with timeouts and graceful failure behavior.
- [ ] 2.2 Add unit tests for the news client response parsing (no network; stub responses).

## 3. Prompt Fidelity (Paper v3)
- [ ] 3.1 Implement `dags/utils/finagent_prompts_v3.py` containing verbatim prompt text for the FinAgent trading pipeline (Appendix F: market intelligence, low-level reflection, high-level reflection, decision-making).
- [ ] 3.2 Add unit tests that assert key placeholders and required sections exist in each v3 prompt template.

## 4. FinAgent Runner Wiring
- [ ] 4.1 Update `dags/utils/finagent_runner.py` to support prompt-version selection and to accept real news items from the DAG.
- [ ] 4.2 Ensure MLflow artifacts include per-stage prompt/response/parsed output for auditability.

## 5. New Airflow DAG
- [ ] 5.1 Add a new DAG (new DAG id) that fetches market data, fetches news via NewsAPI, runs FinAgent v3, logs to MLflow, and persists artifacts.
- [ ] 5.2 Keep the existing `finagent_trading_signal_workflow` unchanged.

## 6. Validation
- [ ] 6.1 Run `pytest tests/unit/workflows -q` (with `source venv/bin/activate`) and ensure all tests pass.
- [ ] 6.2 Run `airflow dags test <new_dag_id> <date>` in the Airflow environment and confirm DAG imports.
