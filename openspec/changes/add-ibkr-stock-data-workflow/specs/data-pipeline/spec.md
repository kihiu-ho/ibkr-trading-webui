# Data Pipeline Specification

## ADDED Requirements

### Requirement: Stock Data Extraction
The workflow SHALL extract stock data for specified symbols (TSLA, NVDA) from the PostgreSQL database.

#### Scenario: Successful data extraction
- **WHEN** the workflow is triggered with valid stock symbols
- **THEN** the system SHALL query PostgreSQL for TSLA and NVDA historical data
- **AND** the system SHALL return all available records for the specified symbols

#### Scenario: Database connection failure
- **WHEN** PostgreSQL database is unavailable
- **THEN** the workflow SHALL log an error with connection details
- **AND** the workflow SHALL retry according to Airflow retry policy
- **AND** the workflow SHALL notify operators if all retries fail

#### Scenario: Missing data for symbol
- **WHEN** a requested symbol has no data in the database
- **THEN** the workflow SHALL log a warning
- **AND** the workflow SHALL continue processing other symbols
- **AND** the workflow SHALL record the missing symbol in MLflow tags

### Requirement: Data Validation
The workflow SHALL validate extracted data for completeness and quality.

#### Scenario: Valid data quality
- **WHEN** extracted data passes validation checks
- **THEN** the workflow SHALL log data quality metrics (row count, date range)
- **AND** the workflow SHALL proceed to transformation step

#### Scenario: Data quality issues detected
- **WHEN** extracted data fails validation (e.g., missing required columns, invalid values)
- **THEN** the workflow SHALL log detailed validation errors
- **AND** the workflow SHALL log the validation report as an MLflow artifact
- **AND** the workflow SHALL fail the task with clear error message

### Requirement: MLflow Experiment Tracking
The workflow SHALL track all runs in MLflow with comprehensive metadata.

#### Scenario: Workflow run tracking
- **WHEN** the workflow executes
- **THEN** the system SHALL create an MLflow run under experiment "ibkr-stock-data"
- **AND** the system SHALL log parameters: symbols, execution_date, debug_mode
- **AND** the system SHALL log metrics: total_rows, symbols_processed, execution_time_seconds

#### Scenario: Artifact logging
- **WHEN** the workflow completes data extraction
- **THEN** the system SHALL log a data summary CSV as an MLflow artifact
- **AND** if debug mode is enabled, the system SHALL log a detailed debug report

#### Scenario: Run tagging
- **WHEN** logging to MLflow
- **THEN** the system SHALL tag runs with: workflow_type, environment, airflow_dag_id
- **AND** if any symbols had missing data, the system SHALL tag: missing_symbols

### Requirement: Debug Mode
The workflow SHALL provide enhanced logging and diagnostics when debug mode is enabled.

#### Scenario: Debug mode enabled
- **WHEN** DEBUG_MODE environment variable is set to "true"
- **THEN** the system SHALL log detailed SQL queries executed
- **AND** the system SHALL log sample data from each processing step
- **AND** the system SHALL create a comprehensive debug artifact in MLflow

#### Scenario: Debug mode disabled
- **WHEN** DEBUG_MODE is not set or set to "false"
- **THEN** the system SHALL log only INFO level messages
- **AND** the system SHALL not create debug artifacts

### Requirement: Database Connection Management
The workflow SHALL manage PostgreSQL connections efficiently and securely.

#### Scenario: Connection configuration
- **WHEN** establishing a database connection
- **THEN** the system SHALL read connection details from environment variables
- **AND** the system SHALL use connection pooling for efficiency
- **AND** the system SHALL not log sensitive credentials

#### Scenario: Connection cleanup
- **WHEN** a task completes or fails
- **THEN** the system SHALL properly close database connections
- **AND** the system SHALL release connection pool resources

### Requirement: Stock Symbol Configuration
The workflow SHALL support configurable stock symbol lists.

#### Scenario: Default symbols
- **WHEN** no stock symbols are specified in configuration
- **THEN** the workflow SHALL use default symbols: TSLA, NVDA

#### Scenario: Custom symbols from environment
- **WHEN** STOCK_SYMBOLS environment variable is set
- **THEN** the workflow SHALL parse the comma-separated symbol list
- **AND** the workflow SHALL validate symbol format (uppercase, valid characters)
- **AND** the workflow SHALL process all valid symbols

### Requirement: Workflow Scheduling
The workflow SHALL support both manual and scheduled execution.

#### Scenario: Manual trigger
- **WHEN** an operator manually triggers the DAG
- **THEN** the workflow SHALL execute immediately
- **AND** the workflow SHALL log the manual trigger in MLflow tags

#### Scenario: Scheduled execution
- **WHEN** the workflow is configured with a schedule interval
- **THEN** Airflow SHALL trigger the workflow according to the schedule
- **AND** the workflow SHALL process data for the appropriate date range

#### Scenario: Catchup disabled
- **WHEN** the DAG is first deployed or has been paused
- **THEN** the workflow SHALL NOT execute historical runs (catchup=False)
- **AND** the workflow SHALL only execute for current schedule periods

