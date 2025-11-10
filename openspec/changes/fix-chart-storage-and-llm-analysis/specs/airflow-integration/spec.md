## MODIFIED Requirements
### Requirement: Artifact Display in Run Details
The system SHALL display generated artifacts grouped by symbol and type in Airflow run details modal.

#### Scenario: Display artifacts grouped by symbol
- **WHEN** user opens run details modal for a completed workflow
- **THEN** fetch artifacts by execution_id
- **AND** group artifacts by symbol first
- **AND** within each symbol, group by type (charts, LLM, signals, etc.)
- **AND** display grouped structure with clear sections

#### Scenario: Chart storage in MinIO
- **WHEN** charts are generated in workflow
- **THEN** upload charts to MinIO
- **AND** store MinIO URLs in artifacts
- **AND** display charts from MinIO URLs in frontend

## ADDED Requirements
### Requirement: LLM Analysis with Bars Data
The system SHALL pass bars data to LLM analysis function to prevent NameError.

#### Scenario: LLM analysis receives bars data
- **WHEN** LLM analysis task runs
- **THEN** retrieve bars data from XCom or market data
- **AND** use bars data for periods_shown calculation
- **AND** complete LLM analysis successfully

