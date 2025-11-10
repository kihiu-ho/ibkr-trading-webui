## MODIFIED Requirements
### Requirement: Artifact Grouping
The system SHALL provide a grouped view of artifacts organized by symbol first, then by type.

#### Scenario: Group artifacts by symbol and type
- **WHEN** displaying artifacts in Airflow run details
- **THEN** group artifacts by symbol first
- **AND** within each symbol, group by type (charts, LLM, signals, etc.)
- **AND** display clear sections for each symbol and type
- **AND** show artifact counts per symbol and type

#### Scenario: Chart artifacts with MinIO URLs
- **WHEN** charts are stored as artifacts
- **THEN** store MinIO URLs instead of local paths
- **AND** display charts from MinIO URLs
- **AND** ensure charts are accessible after container restart

