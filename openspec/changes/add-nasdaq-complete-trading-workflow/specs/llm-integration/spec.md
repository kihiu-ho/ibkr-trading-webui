## MODIFIED Requirements
### Requirement: LLM Vision API Integration
The system SHALL integrate with LLM vision models to analyze multiple technical charts (daily and weekly) for comprehensive trading signal generation.

#### Scenario: Analyze multiple charts with LLM
- **GIVEN** daily and weekly chart images for a symbol
- **WHEN** requesting chart analysis
- **THEN** the system SHALL:
  - Download both daily and weekly chart images
  - Encode both images to base64
  - Send to LLM vision API with prompt requesting analysis of both timeframes
  - Receive comprehensive analysis considering both timeframes
  - Parse response into structured trading signal
  - Store LLM artifact with both chart references

#### Scenario: Multi-timeframe analysis prompt
- **GIVEN** daily and weekly charts for a symbol
- **WHEN** constructing the analysis prompt
- **THEN** the system SHALL include:
  - Instructions to analyze both daily and weekly charts
  - Request for trend alignment check (daily vs weekly)
  - Multi-timeframe signal confirmation
  - Comprehensive trading recommendation based on both timeframes
  - Risk assessment considering both short-term and long-term trends

## ADDED Requirements
### Requirement: LLM Artifact Storage with Workflow Metadata
The system SHALL store LLM analysis artifacts with complete workflow execution metadata and chart references.

#### Scenario: Store LLM analysis with execution context
- **WHEN** LLM analysis is completed in Airflow workflow
- **THEN** LLM artifact SHALL include:
  - workflow_id (e.g., "ibkr_trading_signal_workflow")
  - execution_id (Airflow run identifier)
  - dag_id (DAG identifier)
  - task_id (task that performed analysis)
  - step_name (e.g., "analyze_with_llm")
  - symbol (e.g., "TSLA", "NVDA")
  - prompt (full prompt text sent to LLM)
  - response (full LLM response text)
  - model_name (LLM model used)
  - chart_references (links to daily and weekly chart artifacts)
  - prompt_length and response_length for metrics

