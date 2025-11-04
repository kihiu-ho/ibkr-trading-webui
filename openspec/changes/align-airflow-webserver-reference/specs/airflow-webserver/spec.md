## MODIFIED Requirements
### Requirement: Airflow Webserver Configuration Pattern
The Airflow webserver SHALL use the same configuration pattern as the reference implementation and working scheduler service.

#### Scenario: Reference Pattern Alignment
- **WHEN** airflow-webserver service is configured
- **THEN** SHALL use `<<: *airflow-common` to inherit common configuration
- **AND** SHALL inherit volumes (DAGs, logs, plugins) from common
- **AND** SHALL inherit user settings and network configuration
- **AND** SHALL use same command structure as scheduler with URL conversion
- **AND** SHALL use `<<: *airflow-common-depends-on` for dependency management

#### Scenario: Configuration Consistency
- **WHEN** comparing Airflow service configurations
- **THEN** webserver SHALL match scheduler pattern
- **AND** SHALL match reference implementation structure
- **AND** SHALL inherit common settings rather than duplicating
- **AND** SHALL maintain URL conversion for external database compatibility

#### Scenario: Volume and Permission Access
- **WHEN** webserver starts with reference pattern
- **THEN** SHALL have access to DAGs directory from common volumes
- **AND** SHALL have access to logs directory from common volumes
- **AND** SHALL have access to plugins directory from common volumes
- **AND** SHALL use correct user permissions from common configuration
- **AND** SHALL be on correct network from common configuration
