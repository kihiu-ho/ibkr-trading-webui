# minio-storage Specification

## Purpose
TBD - created by archiving change add-indicator-charting. Update Purpose after archive.
## Requirements
### Requirement: Chart Storage
The system SHALL persistently store generated charts in MinIO.

#### Scenario: Upload chart to MinIO
- **WHEN** chart is generated
- **THEN** system uploads to MinIO bucket trading-charts

#### Scenario: Chart storage metadata
- **WHEN** storing chart
- **THEN** metadata includes: symbol, strategy_id, indicator_ids, generated_date, period, frequency

#### Scenario: Retrieve stored chart
- **WHEN** GET /api/charts/{chart_id}
- **THEN** system retrieves chart URL and metadata from MinIO

### Requirement: Chart Access
The system SHALL provide URLs for accessing stored charts.

#### Scenario: Get chart URL
- **WHEN** requesting chart detail
- **THEN** response includes MinIO URL for direct access

#### Scenario: Access control
- **WHEN** accessing chart URL
- **THEN** chart is accessible with proper permissions

### Requirement: Chart Retention
The system SHALL implement retention policy for stored charts.

#### Scenario: Automatic cleanup
- **WHEN** chart reaches 30 days old
- **THEN** system automatically deletes from MinIO

#### Scenario: Manual deletion
- **WHEN** user clicks delete
- **THEN** chart removed from MinIO immediately

### Requirement: Storage Efficiency
The system SHALL optimize storage usage.

#### Scenario: Compression
- **WHEN** storing JPEG
- **THEN** applies quality optimization

#### Scenario: Chart metadata
- **WHEN** chart is stored
- **THEN** metadata tracked in PostgreSQL indicator_charts table

