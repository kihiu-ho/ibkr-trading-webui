# Use External PostgreSQL for Airflow and MLflow

## Why
The containerized PostgreSQL service (`ibkr-postgres`) is failing to start, blocking Airflow and MLflow services. The system already uses an external PostgreSQL database (via `DATABASE_URL`) for the backend, and we should extend this approach to Airflow and MLflow for consistency and reliability.

## What Changes
- Remove containerized PostgreSQL service from docker-compose.yml
- Add environment variables for external Airflow and MLflow database URLs
- Update Airflow configuration to use external PostgreSQL
- Update MLflow configuration to use external PostgreSQL
- Update env.example with new database URL variables
- Update startup script to remove PostgreSQL health checks
- Make init-multiple-dbs.sh optional (databases should be created externally)

## Impact
- **Affected specs**: deployment (modified)
- **Affected code**:
  - `docker-compose.yml` - remove postgres service, update Airflow/MLflow configs
  - `env.example` - add AIRFLOW_DATABASE_URL and MLFLOW_DATABASE_URL
  - `start-webapp.sh` - remove PostgreSQL health checks
- **Benefits**: 
  - No containerized PostgreSQL dependency
  - Consistent with existing backend pattern
  - More reliable for production
  - Better resource management
- **Migration**: Users need to create `airflow` and `mlflow` databases in their external PostgreSQL instance

