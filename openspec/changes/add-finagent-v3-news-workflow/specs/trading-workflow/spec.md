## MODIFIED Requirements
### Requirement: Workflow Template Support
The system SHALL support different workflow templates including AutoGen multi-agent workflows **and FinAgent paper-v3 workflows**.

#### Scenario: Execute FinAgent paper-v3 workflow
- **GIVEN** a strategy selects a FinAgent workflow template (e.g., `workflow_type="finagent_paper_v3"`)
- **WHEN** the workflow is triggered
- **THEN** Airflow SHALL execute the FinAgent v3 DAG using the v3 prompt templates
- **AND** it SHALL fetch latest market intelligence via NewsAPI when `NEWS_API_KEY` is configured
- **AND** it SHALL emit a TradingSignal payload flagged as `analysis_method="finagent_v3"` and include the MLflow `run_id` for auditing
