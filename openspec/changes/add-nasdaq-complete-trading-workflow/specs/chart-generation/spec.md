## MODIFIED Requirements
### Requirement: Generate Technical Charts for Multiple Timeframes
The system SHALL generate technical analysis charts for daily and weekly timeframes with technical indicators for each symbol in a multi-symbol workflow.

#### Scenario: Generate daily chart for symbol
- **GIVEN** market data for a symbol (e.g., TSLA or NVDA)
- **WHEN** requesting a daily chart
- **THEN** the system SHALL:
  - Fetch market data for the specified period (200 days)
  - Calculate all technical indicators (SMA 20/50/200, RSI, MACD, Bollinger Bands)
  - Create chart with indicators
  - Export to image format
  - Store chart artifact with symbol, timeframe, and execution_id metadata
  - Return chart path for LLM analysis

#### Scenario: Generate weekly chart for symbol
- **GIVEN** market data for a symbol
- **WHEN** requesting a weekly chart
- **THEN** the system SHALL:
  - Resample daily data to weekly bars
  - Calculate weekly technical indicators
  - Create chart with indicators
  - Export and store the chart
  - Store chart artifact with symbol, timeframe="weekly", and execution_id
  - Return chart path for LLM analysis

#### Scenario: Generate charts for multiple symbols
- **GIVEN** symbol list ["TSLA", "NVDA"]
- **WHEN** workflow generates charts
- **THEN** the system SHALL:
  - Generate daily chart for TSLA
  - Generate weekly chart for TSLA
  - Generate daily chart for NVDA
  - Generate weekly chart for NVDA
  - Store each chart as separate artifact with proper symbol tagging
  - Link all charts to same execution_id for workflow grouping

## ADDED Requirements
### Requirement: Chart Artifact Storage with Workflow Metadata
The system SHALL store chart artifacts with complete workflow execution metadata.

#### Scenario: Store chart with execution context
- **WHEN** chart is generated in Airflow workflow
- **THEN** chart artifact SHALL include:
  - workflow_id (e.g., "ibkr_trading_signal_workflow")
  - execution_id (Airflow run identifier)
  - dag_id (DAG identifier)
  - task_id (task that generated chart)
  - step_name (e.g., "generate_daily_chart")
  - symbol (e.g., "TSLA", "NVDA")
  - timeframe ("daily" or "weekly")
  - indicators_included (list of calculated indicators)

