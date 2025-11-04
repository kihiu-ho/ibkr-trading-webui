# Implementation Tasks

## 1. Migrate Airflow Dockerfile
- [x] 1.1 Install uv in Airflow image
- [x] 1.2 Replace pip with uv for psycopg2-binary
- [x] 1.3 Replace pip with uv for requirements.txt
- [x] 1.4 Ensure proper connection string handling
- [x] 1.5 Test Airflow image builds

## 2. Migrate MLflow Dockerfile
- [x] 2.1 Install uv in MLflow image
- [x] 2.2 Replace pip with uv for requirements.txt
- [x] 2.3 Test MLflow image builds

## 3. Migrate Main Dockerfile (if needed)
- [ ] 3.1 Check if main Dockerfile uses pip
- [ ] 3.2 Migrate to uv if needed
- [ ] 3.3 Test build

## 4. Fix Airflow Init Error
- [x] 4.1 Ensure psycopg2-binary is properly installed
- [x] 4.2 Fix connection string conversion
- [x] 4.3 Test airflow-init succeeds

## 5. Testing
- [x] 5.1 Test Docker builds
- [x] 5.2 Verify packages installed correctly
- [x] 5.3 Test airflow-init completes
- [x] 5.4 Test MLflow starts correctly

