## ADDED Requirements
### Requirement: Service Startup Management
The system SHALL provide reliable service startup and initialization management to ensure all services start in the correct order with proper dependencies.

#### Scenario: Database Initialization
- **WHEN** external PostgreSQL databases are configured
- **THEN** Airflow and MLflow databases SHALL be automatically created if they don't exist
- **AND** required users and permissions SHALL be granted
- **AND** database connectivity SHALL be verified before dependent services start

#### Scenario: Service Dependency Ordering
- **WHEN** starting all services
- **THEN** Redis and MinIO SHALL start first (no dependencies)
- **AND** database-dependent services SHALL wait for healthy database
- **AND** application services SHALL wait for their dependencies
- **AND** no service SHALL start before its dependencies are ready

#### Scenario: Service Health Verification
- **WHEN** a service dependency is specified
- **THEN** the service SHALL wait for dependency health check to pass
- **OR** SHALL wait for dependency completion (for init containers)
- **AND** SHALL retry failed health checks with exponential backoff
- **AND** SHALL provide clear error messages on startup failures

#### Scenario: Parallel Startup Optimization
- **WHEN** services have no mutual dependencies
- **THEN** they SHALL start in parallel to minimize total startup time
- **AND** SHALL not block each other unnecessarily
- **AND** SHALL maintain dependency ordering where required

### Requirement: Startup Script Reliability
The startup script SHALL use proper dependency management instead of manual health checks to ensure reliable service initialization.

#### Scenario: Dependency-Based Startup
- **WHEN** executing the startup script
- **THEN** SHALL use Docker Compose dependency conditions
- **AND** SHALL not rely on external curl commands for dependency checking
- **AND** SHALL let Docker Compose handle service ordering
- **AND** SHALL provide status updates during startup process

#### Scenario: Error Handling and Recovery
- **WHEN** a service fails to start
- **THEN** SHALL provide specific error details
- **AND** SHALL suggest remediation steps
- **AND** SHALL allow partial startup (non-critical services can fail)
- **AND** SHALL provide logs for debugging failed services

### Requirement: Initialization Script Management
The system SHALL use initialization scripts for proper database and service setup during container startup.

#### Scenario: Database Setup Scripts
- **WHEN** external databases are configured
- **THEN** SHALL provide initialization scripts for database setup
- **AND** SHALL create airflow and mlflow databases when needed
- **AND** SHALL set up proper user permissions
- **AND** SHALL handle connection failures gracefully

#### Scenario: MinIO Bucket Initialization
- **WHEN** MinIO is healthy
- **THEN** mc service SHALL create required buckets
- **AND** SHALL use wait-for-it.sh to ensure MinIO availability
- **AND** SHALL create mlflow bucket for artifact storage
- **AND** SHALL handle bucket creation failures gracefully
