# Use Same Database for Backend, Airflow, and MLflow

## Why
Simplify deployment by having all services (Backend, Airflow, MLflow) use the same PostgreSQL database instead of requiring separate databases. This reduces setup complexity and database management overhead.

## What Changes
- Configure Airflow to use DATABASE_URL directly
- Configure MLflow to use DATABASE_URL directly
- Remove need to create separate `airflow` and `mlflow` databases
- Update setup scripts to skip database creation
- Simplify documentation

## Impact
- **Affected specs**: deployment (modified)
- **Affected code**: 
  - `docker-compose.yml` - use DATABASE_URL for all services
  - `setup-databases-quick.sh` - simplified (no separate DBs)
  - `env.example` - remove separate URLs
- **Benefits**: 
  - Simpler setup (no database creation needed)
  - Single database to manage
  - Works immediately with existing DATABASE_URL
  - Reduced storage requirements

