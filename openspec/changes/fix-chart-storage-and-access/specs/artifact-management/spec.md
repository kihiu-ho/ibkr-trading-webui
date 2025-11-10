# Artifact Management - Chart Storage and Access

## MODIFIED Requirements

### Requirement: Chart Storage Location

The system SHALL store chart files in a shared volume accessible by both Airflow and backend containers.

#### Scenario: Shared Volume for Charts
- **Given** charts are generated in Airflow DAGs
- **When** charts are saved to disk
- **Then** they SHALL be saved to `/app/charts` shared volume
- **And** the volume SHALL be mounted in both Airflow and backend containers
- **And** the directory SHALL be writable by the Airflow user

#### Scenario: CHARTS_DIR Environment Variable
- **Given** Airflow services are configured
- **When** DAGs generate charts
- **Then** `CHARTS_DIR` environment variable SHALL be set to `/app/charts`
- **And** DAGs SHALL use this variable to determine chart storage location

### Requirement: Chart Image Endpoint MinIO URL Priority

The system SHALL prioritize MinIO URLs from `chart_data.minio_url` over local file paths.

#### Scenario: Use MinIO URL from chart_data
- **Given** an artifact with `chart_data.minio_url` set
- **When** a request is made to `/api/artifacts/{artifact_id}/image`
- **Then** the endpoint SHALL use the MinIO URL from `chart_data.minio_url`
- **And** proxy the request to MinIO
- **And** return the image from MinIO

#### Scenario: Fallback to Local Paths
- **Given** an artifact without `chart_data.minio_url`
- **When** a request is made to `/api/artifacts/{artifact_id}/image`
- **Then** the endpoint SHALL check `/app/charts` shared volume first
- **And** fall back to other common locations if not found

## ADDED Requirements

### Requirement: Shared Volume Configuration

The system SHALL configure a shared volume for chart files in docker-compose.yml.

#### Scenario: Volume Mount Configuration
- **Given** docker-compose.yml is configured
- **When** Airflow and backend services start
- **Then** both SHALL have access to `charts_data` volume
- **And** the volume SHALL be mounted at `/app/charts`
- **And** the volume SHALL persist across container restarts

