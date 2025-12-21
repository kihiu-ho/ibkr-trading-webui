## MODIFIED Requirements
### Requirement: Workflow Template Support
The system SHALL support different workflow templates including AutoGen multi-agent workflows **and TradeMaster AutoGen pipeline workflows**.

#### Scenario: Execute TradeMaster AutoGen pipeline
- **GIVEN** a symbol is assigned to `dag_id="trademaster_autogen_pipeline_workflow"`
- **WHEN** the TradeMaster workflow is triggered (single symbol or batch)
- **THEN** Airflow SHALL execute the dedicated TradeMaster DAG for the targeted symbol(s)
- **AND** the run SHALL support `mode=inference`, `mode=train_backtest`, or `mode=both` via run configuration
- **AND** the workflow SHALL log an auditable trail to MLflow and persist WebUI-compatible artifacts
