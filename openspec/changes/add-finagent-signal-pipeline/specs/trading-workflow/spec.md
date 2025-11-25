## MODIFIED Requirements
### Requirement: Workflow Template Support
The system SHALL support different workflow templates including AutoGen multi-agent workflows **and FinAgent multimodal workflows**.

#### Scenario: Execute FinAgent workflow
- **GIVEN** a strategy with `workflow_type="finagent_multi_modal"`
- **WHEN** the workflow is triggered
- **THEN** Airflow SHALL call the FinAgent runner (market intelligence + reflection + decision modules) before risk validation
- **AND** FinAgent-specific configuration (agent checkpoint path, reflection rounds, RL baseline toggles, MLflow experiment name) SHALL be injected from strategy params or environment variables
- **AND** the workflow SHALL reuse `webapp/services/chart_service.py` for chart generation and connect to the configured Weaviate cluster via `WEAVIATE_URL`/`WEAVIATE_API_KEY` for reflection storage
- **AND** it SHALL load `DATABASE_URL`, `NEON_DATABASE`, `OPENAI_API_KEY`, `OPENAI_API_BASE`, and `OPENAI_MODEL` from `.env` so FinAgent uses the same Postgres + Neon metadata + LLM configuration as the rest of the platform
- **AND** the workflow SHALL output a TradingSignal payload flagged as `analysis_method="finagent_v1"` and emit the MLflow `run_id` for auditing
- **AND** fallback logic SHALL mark the workflow failed (not HOLD) if FinAgent modules raise unrecoverable errors so operators can rerun after fixing dependencies
