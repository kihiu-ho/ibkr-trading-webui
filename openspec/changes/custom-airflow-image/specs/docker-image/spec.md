## ADDED Requirements
### Requirement: Custom Airflow Image with Patched Timeout
The custom Airflow Docker image SHALL have the gunicorn master timeout patched from 120 seconds to 300 seconds.

#### Scenario: Successful Image Build
- **WHEN** custom Dockerfile builds
- **THEN** SHALL compile successfully without errors
- **AND** SHALL include all Airflow dependencies
- **AND** SHALL include ML dependencies (xgboost, mlflow, etc.)
- **AND** SHALL contain patched timeout in webserver command

#### Scenario: Timeout Patch Verification
- **WHEN** image is built
- **THEN** SHALL verify timeout patch was applied
- **AND** SHALL show "300 seconds" instead of "120 seconds"
- **AND** SHALL contain patched `airflow/www/command.py`
- **AND** Dockerfile SHALL include verification step

#### Scenario: Webserver Startup with Patched Image
- **WHEN** webserver starts with patched image
- **THEN** SHALL wait up to 300 seconds for gunicorn master
- **AND** SHALL NOT timeout with "No response within 120 seconds"
- **AND** SHALL complete startup within 300 seconds
- **AND** Gunicorn master SHALL respond and be ready
