## MODIFIED Requirements

### Requirement: Real-time Artifact Updates
Airflow services SHALL expose dependency health checks before runs start.

#### Scenario: Artifact generated during active run
- **AND** Airflow containers SHALL expose a health check (`scripts/verify_kaleido.sh` or similar) that confirms Kaleido is installed before workflows execute, failing fast when the dependency is missing.

### Requirement: Workflow-Artifact Linking (Infrastructure)
The custom Airflow image SHALL install Kaleido during build and document the rebuild flow for operators.

#### Scenario: Link from DAG to artifacts
- **AND** the custom Airflow image build SHALL include a documented step that installs and validates `kaleido==0.2.1`; CI/build scripts SHALL fail if `python -c "import kaleido"` does not succeed.
- **AND** deployment docs SHALL instruct operators to rebuild the Airflow services after dependency updates and to run the Kaleido verification helper before triggering workflows.
