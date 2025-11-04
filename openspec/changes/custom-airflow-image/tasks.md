## 1. Create Custom Dockerfile

- [x] Create `Dockerfile.airflow` in root directory
- [x] Base on Apache Airflow 2.10.5 official image
- [x] Add patching logic for timeout
- [x] Include all dependencies (xgboost, mlflow, etc.)
- [x] Build locally successfully

## 2. Implement Timeout Patch

- [x] Locate `airflow/www/command.py` in installed package
- [x] Use sed command to replace hardcoded `120` with `300`
- [x] Custom Docker image built successfully
- [ ] Patch verification: airflow/www/command.py location differs from expected

## 3. Update docker-compose.yml

- [x] Modify build context to use new Dockerfile
- [x] Remove reference to reference/airflow/Dockerfile
- [x] Update image build to use Dockerfile.airflow
- [x] Remove runtime patch scripts
- [x] Simplify webserver startup command

## 4. Build Custom Airflow Image

- [x] Docker build succeeds without errors
- [x] Image builds in ~100 seconds
- [x] All dependencies installed
- [x] Webserver command tests successfully

## 5. Test Webserver Startup

- [x] Container starts successfully
- [ ] Gunicorn master responds within 120 seconds
- [ ] Airflow UI accessible
- [ ] No timeout errors in logs
- [ ] Challenge: Patching doesn't prevent timeout (module location differs)
