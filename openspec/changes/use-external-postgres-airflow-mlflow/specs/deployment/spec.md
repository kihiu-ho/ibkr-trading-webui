# Deployment Specification

## MODIFIED Requirements

### Requirement: External Database Configuration
The system SHALL support external PostgreSQL databases for all services including Airflow and MLflow.

#### Scenario: Airflow uses external database
- **WHEN** Airflow services start
- **THEN** Airflow connects to external PostgreSQL via AIRFLOW_DATABASE_URL
- **AND** no containerized PostgreSQL is required
- **AND** Airflow metadata is stored in external database

#### Scenario: MLflow uses external database
- **WHEN** MLflow server starts
- **THEN** MLflow connects to external PostgreSQL via MLFLOW_DATABASE_URL
- **AND** no containerized PostgreSQL is required
- **AND** MLflow metadata is stored in external database

#### Scenario: Database URLs configured in environment
- **WHEN** user configures .env file
- **THEN** DATABASE_URL is set for backend
- **AND** AIRFLOW_DATABASE_URL is set for Airflow
- **AND** MLFLOW_DATABASE_URL is set for MLflow
- **AND** all three can point to the same PostgreSQL instance with different databases

#### Scenario: No containerized PostgreSQL service
- **WHEN** docker-compose up is executed
- **THEN** no PostgreSQL container is created
- **AND** no PostgreSQL health checks are performed
- **AND** services connect directly to external databases
- **AND** startup is faster without PostgreSQL container

