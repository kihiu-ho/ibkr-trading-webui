# Artifact Management - Playwright Testing

## MODIFIED Requirements

### Requirement: Artifact Endpoint Playwright Testing

The system SHALL pass Playwright tests for artifact endpoints.

#### Scenario: Test Artifact 52 Endpoint with Playwright
- **Given** Playwright is installed and configured
- **When** a GET request is made to `/api/artifacts/52` using Playwright
- **Then** the endpoint SHALL return HTTP 200 OK
- **And** the response SHALL contain valid JSON
- **And** the JSON SHALL include:
  - `id`: 52
  - `type`: "chart"
  - `symbol`: "TSLA"
  - `chart_type`: "daily"
  - `chart_data`: Object with `minio_url`, `timeframe`, `bars_count`, `indicators`
  - `image_path`: URL to chart image
- **And** all Decimal values SHALL be converted to float for JSON serialization

#### Scenario: Test Market Data Endpoint with Playwright
- **Given** artifact 52 exists and is a chart artifact
- **When** a GET request is made to `/api/artifacts/52/market-data` using Playwright
- **Then** the endpoint SHALL return HTTP 200 OK
- **And** the response SHALL contain valid JSON
- **And** the JSON SHALL include:
  - `symbol`: "TSLA"
  - `count`: Number of market data bars
  - `data`: Array of market data objects with `date`, `open`, `high`, `low`, `close`, `volume`

#### Scenario: Test Image Endpoint with Playwright
- **Given** artifact 52 exists and has a chart image
- **When** a GET request is made to `/api/artifacts/52/image` using Playwright
- **Then** the endpoint SHALL return HTTP 200 OK
- **And** the Content-Type header SHALL be `image/png` or similar
- **And** the response SHALL contain image data

