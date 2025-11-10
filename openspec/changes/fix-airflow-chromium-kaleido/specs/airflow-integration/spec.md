## MODIFIED Requirements

### Requirement: Workflow Execution
The system SHALL execute Airflow workflows successfully without import or initialization errors.

#### Scenario: Workflow task execution
- **WHEN** a workflow task is triggered
- **THEN** all required modules SHALL be importable
- **AND** tasks SHALL execute without module import errors
- **AND** tasks SHALL complete successfully or fail with meaningful error messages
- **AND** workflow execution SHALL not be blocked by missing optional modules
- **AND** chart generation tasks SHALL have Chromium available for image export
- **AND** chart generation tasks SHALL fall back to HTML export if Chromium is not available
- **AND** workflow SHALL continue execution even if JPEG export fails

#### Scenario: Chart generation in Airflow workflows
- **WHEN** workflow executes chart generation tasks
- **THEN** chart generation SHALL:
  - Have Chromium installed in the Airflow container
  - Use Kaleido with Chromium for JPEG/PNG export
  - Fall back to HTML export if Chromium is not available
  - Continue workflow execution regardless of export format
  - Store charts in MinIO with appropriate format indicator
- **AND** workflow SHALL not fail due to Chromium installation issues
- **AND** error messages SHALL be clear and actionable

## ADDED Requirements

### Requirement: Airflow Container Chromium Support
The Airflow container SHALL have Chromium installed for chart generation tasks.

#### Scenario: Chromium installation
- **GIVEN** Airflow Docker image is built
- **WHEN** container starts
- **THEN** Chromium SHALL be installed
- **AND** Chromium-driver SHALL be installed
- **AND** CHROME_BIN environment variable SHALL be set to /usr/bin/chromium
- **AND** CHROMIUM_PATH environment variable SHALL be set to /usr/bin/chromium
- **AND** Kaleido SHALL be able to use Chromium for image export

#### Scenario: Chart generation error handling
- **WHEN** chart generation encounters Chromium-related errors
- **THEN** the system SHALL:
  - Catch ChromeNotFoundError specifically
  - Provide clear error messages with installation instructions
  - Fall back to HTML export automatically
  - Log helpful error messages for debugging
  - Continue workflow execution with HTML chart
- **AND** workflow SHALL not fail due to Chromium issues

