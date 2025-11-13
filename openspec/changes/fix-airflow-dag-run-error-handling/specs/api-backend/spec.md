## ADDED Requirements
### Requirement: Airflow Proxy Error Pass-through
The backend SHALL propagate Airflow API responses for DAG run listings without masking upstream errors.

#### Scenario: Non-JSON Airflow error
- **WHEN** Airflow returns a non-JSON payload (HTML/text) for `GET /api/airflow/dags/{dag_id}/dagRuns`
- **THEN** the backend SHALL respond with the same HTTP status code
- **AND** return the original body as text
- **AND** include the upstream `Content-Type` header when available
- **AND** avoid raising a 500 unless the proxy itself fails

#### Scenario: Upstream JSON error
- **WHEN** Airflow returns JSON describing an error
- **THEN** the backend SHALL forward that JSON unchanged with the original status code
- **AND** the frontend SHALL be able to display the specific Airflow error message
