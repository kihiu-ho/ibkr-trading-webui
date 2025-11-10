# Artifact Management - Visualization and Storage

## MODIFIED Requirements

### Requirement: Chart Artifact Visualization

The system SHALL display chart images from MinIO URLs stored in `chart_data.minio_url`.

#### Scenario: Display Chart from MinIO URL
- **Given** an artifact with `chart_data.minio_url` set
- **When** the artifact is displayed in the frontend
- **Then** the chart image SHALL be displayed using the MinIO URL
- **And** the image SHALL be loaded from MinIO via the proxy endpoint
- **And** the image SHALL be visible in the artifact view

#### Scenario: Fallback to Local Path
- **Given** an artifact without `chart_data.minio_url`
- **When** the artifact is displayed in the frontend
- **Then** the system SHALL attempt to load from local path
- **And** display an appropriate message if file not found

### Requirement: LLM Artifact Visualization

The system SHALL display LLM prompt, response, and metadata in the frontend.

#### Scenario: Display LLM Prompt and Response
- **Given** an LLM artifact with `prompt` and `response` set
- **When** the artifact is displayed in the frontend
- **Then** the prompt SHALL be displayed in a readable format
- **And** the response SHALL be displayed in a readable format
- **And** metadata (model, lengths, etc.) SHALL be shown

#### Scenario: Display LLM Metadata
- **Given** an LLM artifact with metadata
- **When** the artifact is displayed in the frontend
- **Then** model name SHALL be displayed
- **And** prompt length and response length SHALL be shown
- **And** other metadata SHALL be visible

## ADDED Requirements

### Requirement: Database Storage Verification

The system SHALL store all artifacts in PostgreSQL database using DATABASE_URL from .env.

#### Scenario: Artifact Storage in PostgreSQL
- **Given** DATABASE_URL is configured in .env
- **When** an artifact is created
- **Then** it SHALL be stored in PostgreSQL database
- **And** it SHALL be retrievable via API
- **And** all fields SHALL be persisted correctly

#### Scenario: Database Connection Configuration
- **Given** .env file exists
- **When** the backend starts
- **Then** DATABASE_URL SHALL be read from .env
- **And** database connection SHALL be established
- **And** artifacts table SHALL exist

