# Update Startup Script for Airflow and MLflow

## Why
The `start-webapp.sh` script needs to be updated to support the newly integrated Airflow and MLflow services. Currently, it only handles the original services (backend, gateway, postgres, redis, minio, celery) but doesn't build images or perform health checks for Airflow and MLflow.

## What Changes
- Add Airflow and MLflow image building to startup script
- Add health checks for Airflow services (webserver, scheduler, worker, triggerer)
- Add health check for MLflow server
- Update service list display to include new services
- Add Airflow UI (port 8080) and MLflow UI (port 5500) to access points
- Update container list to show all Airflow/MLflow containers

## Impact
- **Affected specs**: deployment (modified)
- **Affected code**: 
  - `start-webapp.sh` - add Airflow/MLflow support
- **Dependencies**: Requires Airflow and MLflow services in docker-compose.yml
- **Backward compatibility**: Fully backward compatible, script will work with or without Airflow/MLflow services running

