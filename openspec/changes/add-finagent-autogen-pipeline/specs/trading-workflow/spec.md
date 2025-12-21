## MODIFIED Requirements
### Requirement: Workflow Template Support
The system SHALL support different workflow templates including AutoGen multi-agent workflows **and FinAgent AutoGen pipelines**.

#### Scenario: Execute FinAgent AutoGen pipeline workflow
- **GIVEN** a strategy selects `workflow_type="finagent_autogen_pipeline"`
- **WHEN** the workflow is triggered
- **THEN** Airflow SHALL execute the dedicated FinAgent AutoGen DAG
- **AND** the run SHALL support `mode=inference`, `mode=train_backtest`, or `mode=both` via run configuration
- **AND** the workflow SHALL log an auditable trail to MLflow including the AutoGen agent conversation and final decision payload

