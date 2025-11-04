# Deployment Specification

## MODIFIED Requirements

### Requirement: Startup Script Service Management
The startup script SHALL manage all services including workflow orchestration services.

#### Scenario: All services start successfully
- **WHEN** start-webapp.sh is executed
- **THEN** backend, gateway, celery, Airflow, and MLflow services start
- **AND** all required Docker images are built or pulled
- **AND** health checks verify service readiness
- **AND** user is shown access points for all services

#### Scenario: Image building includes orchestration services
- **WHEN** Docker images need to be built
- **THEN** Airflow image (ibkr-airflow:latest) is built
- **AND** MLflow image (ibkr-mlflow:latest) is built
- **AND** existing backend and gateway images are built
- **AND** build progress is displayed to user

#### Scenario: Health checks cover all services
- **WHEN** health checks are performed
- **THEN** PostgreSQL, Redis, MinIO health is verified
- **AND** MLflow server accessibility is checked
- **AND** Airflow webserver accessibility is checked
- **AND** Backend and Gateway health is verified
- **AND** service status is displayed to user

#### Scenario: Service list shows orchestration tools
- **WHEN** startup completes successfully
- **THEN** container list includes Airflow services
- **AND** container list includes MLflow service
- **AND** access points include Airflow UI (port 8080)
- **AND** access points include MLflow UI (port 5500)

#### Scenario: Backward compatibility maintained
- **WHEN** Airflow/MLflow services are not available
- **THEN** script continues to work with original services
- **AND** no errors are shown for missing orchestration services
- **AND** health checks gracefully skip unavailable services

