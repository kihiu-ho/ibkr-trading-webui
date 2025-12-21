## ADDED Requirements
### Requirement: FinAgent AutoGen Pipeline DAG
The system SHALL provide a dedicated Airflow DAG that runs a FinAgent pipeline orchestrated by Microsoft AutoGen and logs all run artifacts to MLflow.

#### Scenario: Run inference mode (default)
- **WHEN** the FinAgent AutoGen DAG executes with `mode="inference"`
- **THEN** it SHALL prepare inputs (market data, optional news, optional chart)
- **AND** it SHALL run an AutoGen multi-agent conversation to produce a structured BUY/SELL/HOLD decision
- **AND** it SHALL persist signal + reasoning artifacts for the WebUI and link them to the MLflow run id

#### Scenario: Run training/backtest mode
- **WHEN** the FinAgent AutoGen DAG executes with `mode="train_backtest"`
- **THEN** it SHALL run a training/backtest pipeline using the configured dataset sources and horizon
- **AND** it SHALL log training/backtest metrics and artifacts to MLflow
- **AND** it SHALL register a model/config package for later inference (MLflow registry or equivalent)

#### Scenario: Run both modes in one execution
- **WHEN** the FinAgent AutoGen DAG executes with `mode="both"`
- **THEN** it SHALL execute training/backtest first and register a model/config package
- **AND** it SHALL run inference using the newly registered package
- **AND** it SHALL emit a final TradingSignal payload suitable for the WebUI

### Requirement: AutoGen Conversation Audit Trail
The system SHALL record the AutoGen multi-agent conversation used to reach the trading decision.

#### Scenario: Store conversation as an artifact
- **WHEN** AutoGen agents exchange messages during a FinAgent run
- **THEN** the full conversation SHALL be stored as an MLflow artifact (e.g., JSONL)
- **AND** it SHALL include agent_name, message_type, message_content, timestamps, and token usage if available

### Requirement: WebUI-Compatible Artifact Persistence
The system SHALL convert FinAgent AutoGen outputs into existing artifact types so they can be displayed in the WebUI.

#### Scenario: Persist signal + reasoning + chart artifacts
- **WHEN** a FinAgent AutoGen inference run completes
- **THEN** the system SHALL store:
  - a `signal` artifact containing BUY/SELL/HOLD + confidence and levels
  - an `llm` artifact containing the final synthesized reasoning and conversation reference
  - a `chart` artifact when a chart image is available
- **AND** it SHALL attach lineage to the associated MLflow run/experiment

