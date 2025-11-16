## MODIFIED Requirements
### Requirement: Indicator Calculation
The system SHALL calculate all technical indicators required for chart display using a Python-only indicator engine that is shipped with every runtime (backend, webapp, Airflow, tests) and has no external runtime dependencies (e.g., .NET, pythonnet, stock_indicators).

#### Scenario: Shared indicator module
- **GIVEN** any service (FastAPI backend, Flask webapp, Airflow DAG, or CLI test) needs chart indicators
- **WHEN** the service imports the indicator engine
- **THEN** the module SHALL be available on `PYTHONPATH` from the shared code directory without referencing `webapp.*`
- **AND** the module SHALL rely only on pandas/numpy/Plotly-compatible helpers (no CLR/.NET runtime).

#### Scenario: Indicator availability in Airflow
- **GIVEN** Airflow loads `dags/utils/chart_generator.py`
- **WHEN** the DAG parses modules
- **THEN** importing the shared indicator engine SHALL succeed without requiring `webapp` packages or stock_indicators, preventing Broken DAG errors.
