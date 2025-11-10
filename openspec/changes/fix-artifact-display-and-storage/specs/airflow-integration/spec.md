## MODIFIED Requirements
### Requirement: Artifact Display in Run Details
The system SHALL display artifacts with complete data and MinIO chart URLs.

#### Scenario: Display chart artifacts from MinIO
- **WHEN** viewing artifacts in Airflow run details
- **THEN** display chart images from MinIO URLs
- **AND** show complete artifact data including metadata
- **AND** handle both MinIO URLs and local paths gracefully

