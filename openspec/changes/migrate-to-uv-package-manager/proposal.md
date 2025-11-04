# Migrate to UV Package Manager

## Why
- Faster package installation (10-100x faster than pip)
- Better dependency resolution
- More reliable builds
- Consistent Python environment management
- Fixes airflow-init error by ensuring proper package installation

## What Changes
- Replace pip with uv in all Dockerfiles
- Update installation commands
- Ensure psycopg2-binary is properly installed
- Fix airflow-init connection string handling
- Improve build reliability

## Impact
- **Affected specs**: deployment (modified)
- **Affected code**: 
  - `docker/airflow/Dockerfile` - migrate to uv
  - `docker/mlflow/Dockerfile` - migrate to uv
  - `docker-compose.yml` - ensure proper setup
- **Benefits**: 
  - Faster Docker builds
  - More reliable package installation
  - Better dependency management
  - Fixes current airflow-init error

