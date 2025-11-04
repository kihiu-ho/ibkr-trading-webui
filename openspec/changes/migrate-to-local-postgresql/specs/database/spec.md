## ADDED Requirements

### Requirement: Local PostgreSQL Database Service
The system SHALL provide a local PostgreSQL database service running in Docker Compose for Airflow and MLflow.

#### Scenario: PostgreSQL Service Startup
- **WHEN** docker-compose starts the postgres service
- **THEN** SHALL initialize with airflow and mlflow databases
- **AND** SHALL create airflow user with password 'airflow'
- **AND** SHALL create mlflow user with password 'mlfLow'
- **AND** SHALL expose PostgreSQL on standard port 5432
- **AND** SHALL persist data in Docker volume
- **AND** SHALL pass health check within 10 seconds

#### Scenario: Database Initialization
- **WHEN** postgres container starts for the first time
- **THEN** SHALL execute scripts/init-databases.sh
- **AND** SHALL create airflow database owned by airflow user
- **AND** SHALL create mlflow database owned by mlflow user
- **AND** SHALL grant all privileges to respective users
- **AND** SHALL handle idempotent execution (safe to run multiple times)

#### Scenario: Database Connectivity
- **WHEN** Airflow services connect to postgres service
- **THEN** SHALL use connection string: postgresql+psycopg2://airflow:airflow@postgres/airflow
- **AND** SHALL establish connection within 1 second
- **AND** SHALL NOT require SSL/TLS for local connections
- **AND** SHALL support connection pooling

## MODIFIED Requirements

### Requirement: Airflow Database Connection Configuration
The Airflow services SHALL use local PostgreSQL instead of external database.

#### Scenario: Webserver Database Connection
- **WHEN** airflow-webserver service starts
- **THEN** SHALL connect to local postgres service (not external)
- **AND** SHALL use postgresql+psycopg2://airflow:airflow@postgres/airflow
- **AND** SHALL wait for postgres service to be healthy before starting
- **AND** SHALL establish connection without network latency
- **AND** SHALL NOT require URL format conversion (local postgres supports psycopg2)

#### Scenario: Scheduler Database Connection
- **WHEN** airflow-scheduler service starts
- **THEN** SHALL connect to local postgres service
- **AND** SHALL use same connection string as webserver
- **AND** SHALL wait for postgres service to be healthy
- **AND** SHALL establish connection quickly (<1 second)

#### Scenario: Database Dependency Management
- **WHEN** Airflow services start
- **THEN** SHALL wait for postgres service health check to pass
- **AND** SHALL NOT start before postgres is ready
- **AND** SHALL retry connection if postgres is temporarily unavailable

## REMOVED Requirements

### Requirement: External Database Dependency
The system SHALL NOT depend on external PostgreSQL database for Airflow.

#### Scenario: External Database Removal
- **WHEN** system configuration is updated
- **THEN** SHALL remove AIRFLOW_DATABASE_URL environment variable dependency
- **AND** SHALL NOT require external database credentials
- **AND** SHALL NOT make network requests to external database hosts

