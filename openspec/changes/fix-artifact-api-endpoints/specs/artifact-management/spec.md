# Artifact Management - API Endpoints

## MODIFIED Requirements

### Requirement: Artifact Retrieval Endpoint Verification

The system SHALL provide verified GET endpoints to retrieve individual artifacts by ID with proper JSON serialization.

#### Scenario: Retrieve Chart Artifact (Verified)
- **Given** a chart artifact exists with ID 43
- **When** a GET request is made to `/api/artifacts/43`
- **Then** the endpoint SHALL return HTTP 200 OK
- **And** the response SHALL contain valid JSON
- **And** the response SHALL include:
  - `id`: 43
  - `type`: "chart"
  - `symbol`: "TSLA"
  - `chart_data`: Object with `minio_url`, `timeframe`, `bars_count`, `indicators`
  - `image_path`: URL to chart image
- **And** all Decimal values SHALL be converted to float for JSON serialization
- **And** JSON serialization SHALL complete without errors

#### Scenario: Retrieve Signal Artifact (Verified)
- **Given** a signal artifact exists with ID 45
- **When** a GET request is made to `/api/artifacts/45`
- **Then** the endpoint SHALL return HTTP 200 OK
- **And** the response SHALL contain valid JSON
- **And** the response SHALL include:
  - `id`: 45
  - `type`: "signal"
  - `symbol`: "TSLA"
  - `action`: "HOLD" | "BUY" | "SELL"
  - `confidence`: Float between 0 and 1
  - `signal_data`: Object with `reasoning`, `stop_loss`, `entry_price`, `take_profit`, `key_factors`, etc.
- **And** all Decimal values SHALL be converted to float for JSON serialization
- **And** JSON serialization SHALL complete without errors

### Requirement: Chart Image Endpoint Verification

The system SHALL provide verified GET endpoints to retrieve chart images.

#### Scenario: Retrieve Chart Image (Verified)
- **Given** a chart artifact exists with ID 43
- **When** a GET request is made to `/api/artifacts/43/image`
- **Then** the endpoint SHALL return HTTP 200 OK
- **And** the response SHALL contain the image data
- **And** the Content-Type header SHALL be `image/png`
- **And** the image SHALL be accessible from MinIO URL if available
- **And** the image data SHALL be properly streamed to the client
