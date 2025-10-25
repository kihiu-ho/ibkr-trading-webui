# MinIO URL Generation

## ADDED Requirements

### Requirement: Chart Image URLs Must Be Browser-Accessible
The system SHALL generate MinIO URLs that are accessible from user browsers, not just from backend services.

#### Scenario: Chart image loads in browser
- **WHEN** user views a chart in the gallery
- **THEN** chart thumbnail image loads successfully
- **AND** image URL uses browser-accessible hostname (not internal Docker hostname)

#### Scenario: Chart download works
- **WHEN** user clicks download button
- **THEN** browser can access the MinIO URL
- **AND** file downloads successfully

#### Scenario: Backend can still access MinIO
- **WHEN** backend uploads a chart
- **THEN** backend connects to MinIO using internal endpoint
- **AND** upload succeeds
- **AND** generated URL uses public endpoint

### Requirement: Separate Internal and External MinIO Endpoints
The system SHALL support different MinIO endpoints for internal (backend) and external (browser) access.

#### Scenario: Docker deployment with internal network
- **WHEN** running in Docker
- **THEN** backend uses internal endpoint (minio:9000) for connections
- **AND** generated URLs use public endpoint (localhost:9000)
- **AND** both backend and browser can access MinIO

#### Scenario: Local development
- **WHEN** running locally without Docker
- **THEN** both endpoints default to localhost:9000
- **AND** system works without additional configuration

