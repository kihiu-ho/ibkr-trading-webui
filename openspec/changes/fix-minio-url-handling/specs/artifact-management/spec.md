# Artifact Management - MinIO URL Handling

## MODIFIED Requirements

### Requirement: Chart Image Endpoint MinIO URL Detection

The system SHALL check for MinIO URLs in `chart_data.minio_url` when `image_path` is a local path.

#### Scenario: Use MinIO URL from chart_data
- **Given** an artifact with `image_path` as a local path (e.g., `/tmp/chart.png`)
- **And** `chart_data.minio_url` contains a MinIO URL
- **When** a request is made to `/api/artifacts/{artifact_id}/image`
- **Then** the endpoint SHALL use the MinIO URL from `chart_data.minio_url`
- **And** proxy the request to MinIO
- **And** return the image from MinIO

#### Scenario: Fallback to image_path if no MinIO URL
- **Given** an artifact with `image_path` as a local path
- **And** `chart_data` is None or doesn't contain `minio_url`
- **When** a request is made to `/api/artifacts/{artifact_id}/image`
- **Then** the endpoint SHALL fall back to checking local file paths
- **And** return the file if found locally

#### Scenario: Prioritize MinIO URLs
- **Given** an artifact with both `image_path` as a MinIO URL and `chart_data.minio_url`
- **When** a request is made to `/api/artifacts/{artifact_id}/image`
- **Then** the endpoint SHALL use the MinIO URL (from either source)
- **And** proxy the request to MinIO

