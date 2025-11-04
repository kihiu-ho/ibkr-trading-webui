# Deployment Specification

## MODIFIED Requirements

### Requirement: Shared Database Configuration
All services (Backend, Airflow, MLflow) SHALL use the same PostgreSQL database specified by DATABASE_URL.

#### Scenario: Services use shared database
- **WHEN** DATABASE_URL is configured in .env
- **THEN** Backend uses DATABASE_URL
- **AND** Airflow uses DATABASE_URL
- **AND** MLflow uses DATABASE_URL
- **AND** All services can access their tables in the same database

#### Scenario: Simplified setup
- **WHEN** User configures DATABASE_URL
- **THEN** No additional database URLs are required
- **AND** No separate database creation is needed
- **AND** All services work immediately

#### Scenario: Service isolation within database
- **WHEN** Multiple services use same database
- **THEN** Each service uses its own table prefix/schema
- **AND** Services don't conflict with each other
- **AND** Database migrations are handled per service

