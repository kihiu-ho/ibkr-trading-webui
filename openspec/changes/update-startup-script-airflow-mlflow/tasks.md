# Implementation Tasks

## 1. Update Image Detection
- [x] 1.1 Add Airflow and MLflow images to detection function
- [x] 1.2 Update image list to include ibkr-airflow:latest and ibkr-mlflow:latest

## 2. Update Image Building
- [x] 2.1 Add Airflow image build command
- [x] 2.2 Add MLflow image build command
- [x] 2.3 Update build progress messaging

## 3. Add Health Checks
- [x] 3.1 Add PostgreSQL health check (for Airflow/MLflow metadata)
- [x] 3.2 Add MLflow server health check (port 5500)
- [x] 3.3 Add Airflow webserver health check (port 8080)
- [x] 3.4 Add Airflow scheduler health check
- [x] 3.5 Add Airflow worker health check
- [x] 3.6 Add Airflow triggerer health check

## 4. Update Service Display
- [x] 4.1 Add Airflow services to container list
- [x] 4.2 Add MLflow service to container list
- [x] 4.3 Add Airflow UI to access points
- [x] 4.4 Add MLflow UI to access points
- [x] 4.5 Update system status section

## 5. Testing
- [x] 5.1 Test script with Airflow/MLflow services
- [x] 5.2 Test script without Airflow/MLflow services (backward compatibility)
- [x] 5.3 Test --rebuild flag with new images
- [x] 5.4 Test --fast flag with health checks

