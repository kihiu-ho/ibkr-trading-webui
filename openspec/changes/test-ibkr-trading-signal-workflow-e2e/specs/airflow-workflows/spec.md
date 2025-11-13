# Airflow Workflows Specification - Delta

## MODIFIED Requirements

### Requirement: MLflow Logging Task Performance
The `log_to_mlflow` task in the `ibkr_trading_signal_workflow` SHALL complete within its execution timeout and SHALL handle artifact file operations efficiently.

#### Scenario: Chart artifact logging with mlflow
- **WHEN** the `log_to_mlflow` task attempts to log chart image artifacts
- **THEN** it SHALL use the MLflow tracking API's native file logging methods
- **AND** it SHALL NOT attempt to copy large files to the task working directory
- **AND** it SHALL complete within the 5-minute execution timeout

#### Scenario: Artifact update with backend API
- **WHEN** the `log_to_mlflow` task updates artifacts with MLflow run_id
- **THEN** it SHALL limit the number of artifacts updated to prevent timeout
- **AND** it SHALL use short timeouts (2-3 seconds) for API requests
- **AND** it SHALL handle API failures gracefully without task failure

### Requirement: Workflow Artifact Storage
The trading signal workflow SHALL store artifacts for all workflow steps including charts, LLM analysis, signals, orders, trades, and portfolio snapshots.

#### Scenario: Complete workflow artifact persistence
- **WHEN** the `ibkr_trading_signal_workflow` DAG executes successfully
- **THEN** artifacts SHALL be created for each major step
- **AND** chart artifacts SHALL include MinIO URLs and local file paths
- **AND** signal artifacts SHALL include confidence scores and LLM reasoning
- **AND** portfolio artifacts SHALL include position details and P&L data
