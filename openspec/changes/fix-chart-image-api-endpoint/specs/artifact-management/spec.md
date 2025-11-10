# Artifact Management - Chart Image API Endpoint

## MODIFIED Requirements

### Requirement: Chart Image Endpoint File Search

The system SHALL search for chart files using pattern matching when exact file path doesn't exist.

#### Scenario: Pattern Matching for Old Artifacts
- **Given** an artifact with `image_path` like `/tmp/NVDA_1D_20251109_050611.png`
- **And** the exact file doesn't exist
- **When** a request is made to `/api/artifacts/{artifact_id}/image`
- **Then** the endpoint SHALL search for files matching pattern `{symbol}_{timeframe_code}_*.png` in `/app/charts`
- **And** map `chart_type` to timeframe code (`daily` → `1D`, `weekly` → `1W`)
- **And** return the most recent matching file if found
- **And** return a helpful error message if no matching file is found

#### Scenario: MinIO URL Priority
- **Given** an artifact with `chart_data.minio_url` set
- **When** a request is made to `/api/artifacts/{artifact_id}/image`
- **Then** the endpoint SHALL use the MinIO URL from `chart_data.minio_url` first
- **And** proxy the request to MinIO
- **And** return the image from MinIO

#### Scenario: Helpful Error Messages
- **Given** an old artifact without accessible files
- **When** a request is made to `/api/artifacts/{artifact_id}/image`
- **Then** the endpoint SHALL return a 404 with a descriptive error message
- **And** the error message SHALL explain that this may be an old artifact
- **And** the error message SHALL indicate that files were stored in `/tmp/` and may have been deleted
- **And** the error message SHALL explain that new artifacts use `/app/charts` and MinIO

