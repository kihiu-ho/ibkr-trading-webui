# Deployment Specification

## MODIFIED Requirements

### Requirement: Use UV Package Manager
All Dockerfiles SHALL use `uv` for Python package installation instead of `pip`.

#### Scenario: Airflow Dockerfile uses uv
- **WHEN** Building Airflow image
- **THEN** uv is installed
- **AND** psycopg2-binary is installed via uv
- **AND** All requirements are installed via uv
- **AND** Build completes successfully

#### Scenario: MLflow Dockerfile uses uv
- **WHEN** Building MLflow image
- **THEN** uv is installed
- **AND** All requirements are installed via uv
- **AND** Build completes successfully

#### Scenario: Packages install correctly
- **WHEN** Container starts
- **THEN** All packages are available
- **AND** psycopg2-binary works correctly
- **AND** Services start without errors

