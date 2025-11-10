# Artifact Management - Chart Image Proxy

## ADDED Requirements

### Requirement: Chart Image Proxy Endpoint

The system SHALL provide a new endpoint `/api/artifacts/{artifact_id}/image` that serves chart images from MinIO URLs or local file paths.

#### Scenario: Proxy MinIO Chart Images
- **Given** an artifact with `image_path` starting with `http://` or `https://`
- **When** a request is made to `/api/artifacts/{artifact_id}/image`
- **Then** the endpoint should proxy the request to the MinIO URL
- **And** return the image with proper content-type headers
- **And** handle errors gracefully if MinIO is unavailable

#### Scenario: Serve Local Chart Files
- **Given** an artifact with `image_path` as a local file path (e.g., `/tmp/chart.png`)
- **When** a request is made to `/api/artifacts/{artifact_id}/image`
- **Then** the endpoint should search for the file in common locations:
  - Original path
  - `/opt/airflow/{path}`
  - `/opt/airflow/{filename}`
  - `/tmp/{filename}`
  - `/opt/airflow/dags/{filename}`
  - `/opt/airflow/logs/{filename}`
- **And** return the file if found
- **And** return 404 with descriptive error if not found

#### Scenario: Frontend Uses Proxy Endpoint
- **Given** a chart artifact is displayed in the frontend
- **When** the frontend renders the chart image
- **Then** it should use `/api/artifacts/{artifact_id}/image` instead of direct `image_path`
- **And** display error message if image fails to load

## MODIFIED Requirements

### Requirement: Frontend Chart Display

Frontend templates SHALL use the proxy endpoint instead of direct image paths.

#### Scenario: Display Chart via Proxy
- **Given** artifacts are displayed in `artifacts.html` or `artifact_detail.html`
- **When** a chart artifact is rendered
- **Then** the image `src` should be `/api/artifacts/{artifact_id}/image`
- **And** error handling should show a user-friendly message if image fails to load

