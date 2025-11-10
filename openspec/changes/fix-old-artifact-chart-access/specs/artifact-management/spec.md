# Artifact Management - Old Artifact Chart Access

## MODIFIED Requirements

### Requirement: Chart File Search Logic

The system SHALL search for chart files by filename pattern when exact path doesn't exist.

#### Scenario: Search by Filename Pattern
- **Given** an artifact with `image_path` like `/tmp/NVDA_1W_20251109_050013.png`
- **When** the exact file doesn't exist
- **Then** the endpoint SHALL search for files matching the pattern `{symbol}_{timeframe}_*.png` in `/app/charts`
- **And** return the most recent matching file if found
- **And** return a helpful error message if no matching file is found

#### Scenario: Handle Missing Files Gracefully
- **Given** an old artifact without accessible files
- **When** a request is made to `/api/artifacts/{artifact_id}/image`
- **Then** the endpoint SHALL return a 404 with a descriptive error message
- **And** the error message SHALL indicate that the file may have been deleted or is from an old artifact

### Requirement: Artifact Metadata Storage

The system SHALL ensure artifacts are stored in PostgreSQL database with complete metadata.

#### Scenario: Store Complete Artifact Metadata
- **Given** a chart artifact is created
- **When** the artifact is stored in PostgreSQL
- **Then** it SHALL include `chart_data` with `minio_url` if available
- **And** it SHALL include `image_path` with the correct path
- **And** all metadata SHALL be persisted in the database

