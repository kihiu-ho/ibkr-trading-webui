# Add Airflow and MLflow Orchestration

## Why
The current system lacks workflow orchestration and experiment tracking capabilities. Adding Airflow and MLflow will enable:
- Automated workflow scheduling and management for trading strategies
- ML model training and versioning with MLflow
- Experiment tracking for strategy optimization
- Integration with S3-compatible storage (MinIO) for artifacts

## What Changes
- Add Apache Airflow services (webserver, scheduler, worker, triggerer) for workflow orchestration
- Add MLflow server for ML experiment tracking and model registry
- Add PostgreSQL database for Airflow metadata (shared with existing services)
- Configure Airflow with Celery executor using existing Redis
- Integrate MLflow with existing MinIO for artifact storage
- Add required Dockerfiles and configuration files
- Update docker-compose.yml with new services
- Add network connectivity between all services

## Impact
- **Affected specs**: workflow-orchestration (new), message-queue (modified), minio-storage (modified)
- **Affected code**: 
  - `docker-compose.yml` - add new services
  - `docker/airflow/` - new Dockerfile and requirements
  - `docker/mlflow/` - new Dockerfile and requirements  
  - `scripts/init-multiple-dbs.sh` - new database initialization script
  - `.env.example` - add Airflow and MLflow environment variables
- **Dependencies**: Requires PostgreSQL, Redis, and MinIO
- **Ports**: 
  - 8080: Airflow web UI
  - 5500: MLflow server
  - 5555: Flower (existing, for Airflow Celery monitoring)

