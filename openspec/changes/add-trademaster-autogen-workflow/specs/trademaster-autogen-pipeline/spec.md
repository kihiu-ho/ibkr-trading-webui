## ADDED Requirements
### Requirement: TradeMaster AutoGen Pipeline DAG
The system SHALL provide a dedicated Airflow DAG (`trademaster_autogen_pipeline_workflow`) that runs a TradeMaster pipeline per symbol, logs artifacts to MLflow, and uses AutoGen to produce an auditable trading decision payload.

#### Scenario: Run both modes by default
- **WHEN** the TradeMaster DAG executes without an explicit `mode`
- **THEN** it SHALL execute `mode="both"` (train/backtest then inference)
- **AND** it SHALL emit a final TradingSignal-style decision payload suitable for WebUI persistence

#### Scenario: Run training/backtest only
- **WHEN** the TradeMaster DAG executes with `mode="train_backtest"`
- **THEN** it SHALL run the training/backtest pipeline
- **AND** it SHALL log training/backtest metrics and artifacts to MLflow

#### Scenario: Run inference only
- **WHEN** the TradeMaster DAG executes with `mode="inference"`
- **THEN** it SHALL run inference using the configured model/artifact inputs
- **AND** it SHALL execute the AutoGen review step to produce a structured decision

### Requirement: Assigned-Symbol Batch Execution
The system SHALL interpret “all symbols” as enabled symbols assigned to the TradeMaster DAG via Workflow Symbols links.

#### Scenario: Single-symbol execution (backend auto-trigger compatible)
- **WHEN** a DAG run is triggered with `dag_run.conf.symbol`
- **THEN** the system SHALL process only that symbol
- **AND** it SHALL not expand to other symbols assigned to the DAG

#### Scenario: Batch execution uses Workflow Symbols assignments
- **WHEN** a DAG run is triggered without `dag_run.conf.symbol`
- **THEN** the system SHALL fetch enabled symbols from `/api/workflow-symbols/?enabled_only=true`
- **AND** it SHALL filter to symbols that are assigned to `dag_id="trademaster_autogen_pipeline_workflow"`
- **AND** it SHALL execute the pipeline once per selected symbol

### Requirement: MLflow Audit Trail
The system SHALL record parameters, metrics, and artifacts for each symbol run in MLflow.

#### Scenario: Log TradeMaster and AutoGen artifacts
- **WHEN** the TradeMaster pipeline executes for a symbol
- **THEN** the system SHALL log key parameters (symbol, mode, hyperparameters, data window)
- **AND** it SHALL log backtest/training metrics when training is executed
- **AND** it SHALL store the AutoGen conversation transcript as an MLflow artifact

### Requirement: WebUI-Compatible Artifact Persistence
The system SHALL persist TradeMaster + AutoGen outputs into existing WebUI artifact types and attach MLflow lineage.

#### Scenario: Persist signal + reasoning artifacts with lineage
- **WHEN** a symbol run completes inference and AutoGen review
- **THEN** the system SHALL store:
  - a `signal` artifact with BUY/SELL/HOLD + confidence and any available levels/targets
  - an `llm` artifact with the final synthesized reasoning and a reference to the conversation transcript
- **AND** it SHALL attach `run_id` and `experiment_id` lineage fields matching the MLflow run

