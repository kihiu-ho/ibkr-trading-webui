# Artifact Management - Chart File Access

## MODIFIED Requirements

### Requirement: Chart File Storage Location

The system SHALL store chart files in a location accessible by both Airflow and backend containers.

#### Scenario: Shared Volume for Charts
- **Given** charts are generated in Airflow DAGs
- **When** charts are saved to disk
- **Then** they SHALL be saved to a shared volume accessible by both containers
- **And** the path SHALL be `/app/charts` or `/opt/airflow/charts`
- **And** the volume SHALL be mounted in both Airflow and backend containers

#### Scenario: Chart File Access
- **Given** a chart file is stored in the shared volume
- **When** the backend tries to serve the chart image
- **Then** it SHALL find the file in the shared volume location
- **And** it SHALL return the file if found
- **And** it SHALL return a 404 with descriptive error if not found

## ADDED Requirements

### Requirement: Shared Volume Configuration

The system SHALL configure a shared volume for chart files in docker-compose.yml.

#### Scenario: Volume Mount Configuration
- **Given** docker-compose.yml is configured
- **When** Airflow and backend services start
- **Then** both SHALL have access to a shared charts volume
- **And** the volume SHALL be mounted at `/app/charts` or `/opt/airflow/charts`
- **And** the volume SHALL persist across container restarts

### Requirement: Chart Storage Path Update

DAGs SHALL save charts to the shared volume instead of `/tmp/`.

#### Scenario: Save Charts to Shared Volume
- **Given** a DAG generates a chart
- **When** the chart is saved to disk
- **Then** it SHALL be saved to the shared volume path
- **And** the path SHALL be included in artifact metadata
- **And** MinIO upload SHALL still be attempted if available

