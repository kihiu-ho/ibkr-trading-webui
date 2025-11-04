## 1. Create OpenSpec Change

- [x] Create proposal.md with migration plan
- [x] Create tasks.md (this file)
- [x] Create spec.md for database requirements

## 2. Add PostgreSQL Service to docker-compose.yml

- [x] Add `postgres` service definition
- [x] Configure PostgreSQL image (postgres:15 - updated from 13 to match existing volume)
- [x] Set environment variables (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)
- [x] Add persistent volume for database data
- [x] Mount initialization script (scripts/init-databases.sh)
- [x] Configure health check (pg_isready)
- [x] Add to trading-network
- [x] Set restart policy

## 3. Update Airflow Services Configuration

- [x] Update `x-airflow-common-depends-on` to include postgres health check
- [x] Add `airflow-init` service for database initialization
- [x] Update `airflow-webserver` service:
  - [x] Remove external AIRFLOW_DATABASE_URL dependency
  - [x] Set AIRFLOW__DATABASE__SQL_ALCHEMY_CONN to local postgres in common-env
  - [x] Simplify command (no URL conversion needed)
  - [x] Add postgres and airflow-init dependencies
- [x] Update `airflow-scheduler` service:
  - [x] Remove external AIRFLOW_DATABASE_URL dependency
  - [x] Set AIRFLOW__DATABASE__SQL_ALCHEMY_CONN to local postgres (via common-env)
  - [x] Simplify command
  - [x] Add postgres dependency

## 4. Verify Database Initialization Script

- [ ] Ensure scripts/init-databases.sh exists
- [ ] Verify script creates airflow database and user
- [ ] Verify script creates mlflow database and user
- [ ] Test script syntax

## 5. Update Environment Variables

- [ ] Remove AIRFLOW_DATABASE_URL from .env.example (if exists)
- [ ] Document local PostgreSQL configuration
- [ ] Update any documentation referencing external database

## 6. Test Migration

- [x] Start PostgreSQL service: `docker compose up -d postgres`
- [x] Wait for PostgreSQL to be healthy
- [x] Create airflow database and user manually (init script didn't run due to existing data)
- [x] Run airflow-init to initialize database: `docker compose up airflow-init`
- [x] Start Airflow webserver: `docker compose up -d airflow-webserver`
- [x] Check logs for gunicorn timeout errors (NONE - resolved!)
- [x] Verify webserver starts within 60 seconds (Started in ~26 seconds)
- [x] Test UI accessibility: `curl http://localhost:8080` (HTTP/1.1 302 FOUND - working!)
- [x] Verify webserver status: healthy
- [ ] Start scheduler: `docker compose up -d airflow-scheduler`
- [ ] Verify scheduler connects successfully
- [ ] Test DAG loading and execution

## 7. Validate Performance Improvements

- [x] Measure webserver startup time (26 seconds - well under 60s target!)
- [x] Verify no gunicorn timeout errors (SUCCESS - no timeout errors!)
- [x] Test database connection speed (instant localhost connection)
- [x] Verify UI responsiveness (HTTP 302 response - webserver is working)
- [x] Check resource usage (webserver healthy, all 4 workers started)

## 8. Document Migration

- [ ] Update OpenSpec proposal with test results
- [ ] Document any issues encountered
- [ ] Update INVESTIGATION_SUMMARY.md if timeout is resolved
- [ ] Add migration notes to README if applicable

