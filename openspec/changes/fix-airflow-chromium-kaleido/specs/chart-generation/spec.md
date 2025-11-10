## MODIFIED Requirements

### Requirement: Chart Export and Storage
The system SHALL export charts as images and store them accessibly.

#### Scenario: Export chart to image
- **GIVEN** a completed Plotly figure
- **WHEN** exporting the chart
- **THEN** the system SHALL:
  - Use Kaleido with Chromium to render JPEG/PNG
  - Set image dimensions to 1920x1400 pixels
  - Optimize for LLM vision model consumption
  - Return binary image data
- **AND** if Chromium is not available, SHALL fall back to HTML export
- **AND** SHALL log warning when using HTML fallback
- **AND** SHALL continue workflow execution even if JPEG export fails

#### Scenario: Chromium requirement handling
- **GIVEN** Kaleido requires Chromium for image export
- **WHEN** Chromium is not installed or not accessible
- **THEN** the system SHALL:
  - Catch ChromeNotFoundError
  - Export chart to HTML format as fallback
  - Log clear error message with installation instructions
  - Continue workflow execution with HTML chart
  - Store HTML chart in MinIO
- **AND** SHALL not fail the workflow task due to Chromium issues

#### Scenario: Store chart in MinIO
- **GIVEN** chart image binary data or HTML content
- **WHEN** storing the chart
- **THEN** the system SHALL:
  - Generate unique filename: {symbol}_{timeframe}_{timestamp}.jpg (or .html if fallback)
  - Upload to MinIO bucket: trading-charts/signals/
  - Set public read permissions
  - Return public URL using MINIO_PUBLIC_ENDPOINT
- **AND** SHALL support both JPEG and HTML chart formats
- **AND** SHALL indicate chart format in metadata

## ADDED Requirements

### Requirement: Chromium Installation for Chart Generation
The system SHALL have Chromium installed in the Airflow container for Kaleido chart export.

#### Scenario: Chromium availability
- **GIVEN** Airflow container is running
- **WHEN** chart generation tasks execute
- **THEN** Chromium SHALL be installed and accessible
- **AND** Chromium path SHALL be configured via CHROMIUM_PATH environment variable
- **AND** Kaleido SHALL be able to find and use Chromium
- **AND** chart generation SHALL succeed without ChromeNotFoundError

#### Scenario: Kaleido Chromium configuration
- **GIVEN** Chromium is installed in the container
- **WHEN** initializing Kaleido for chart export
- **THEN** the system SHALL:
  - Set Kaleido scope chromium path if CHROMIUM_PATH is set
  - Configure Kaleido with single-process mode for Docker containers
  - Handle Kaleido initialization errors gracefully
  - Fall back to HTML export if Chromium is not available

