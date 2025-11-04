# Gunicorn Timeout Investigation Summary

## Problem Statement

Airflow webserver fails to start with error: "No response from gunicorn master within 120 seconds"

## Root Cause

1. **Hardcoded Timeout**: Airflow's `webserver_command.py` contains a hardcoded 120-second timeout that cannot be overridden
2. **External Database Latency**: Using Neon.tech PostgreSQL adds network latency:
   - SSL/TLS handshake overhead
   - Connection pooling initialization
   - Each worker establishes separate database connections
3. **Resource Constraints**: Current allocation (2G limit) may be below Airflow's recommended 4-8GB

## Investigation Timeline

### Attempt 1: Worker Reduction
- Reduced workers from 4 to 1
- Increased worker timeout to 300s
- **Result**: Still times out (master timeout, not worker timeout)

### Attempt 2: Environment Variables
- Set `AIRFLOW__WEBSERVER__WEB_SERVER_WORKER_TIMEOUT: '300'`
- Set `GUNICORN_CMD_ARGS: '--timeout 300'`
- **Result**: No effect (master timeout is hardcoded)

### Attempt 3: Custom Docker Image
- Attempted to patch `airflow/www/command.py` via sed
- **Result**: File location/search issue

### Attempt 4: Official Entrypoint Pattern
- Used `/entrypoint webserver` following [official docker-compose.yaml](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#fetching-docker-compose-yaml)
- **Result**: Still times out (confirms it's not an entrypoint issue)

### Attempt 5: LocalExecutor
- Switched from CeleryExecutor to LocalExecutor
- Removed Celery-specific variables
- **Result**: Still times out (gunicorn used regardless of executor)

## Key Findings

1. ✅ Database URL conversion works correctly
2. ✅ Database connection retry logic functions
3. ✅ Database migration completes successfully
4. ✅ Official entrypoint pattern implemented correctly
5. ❌ Gunicorn master timeout persists (120s hardcoded)
6. ❌ External database latency exceeds timeout window

## Why Gunicorn Takes So Long

Based on investigation and [Airflow documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#fetching-docker-compose-yaml):

1. **Application Loading**: Each worker loads full Airflow application
2. **Database Connections**: Each worker establishes DB connections:
   - External DB = network latency + SSL handshake
   - Connection pooling initialization
   - Schema validation
3. **Flask/FAB Initialization**: Web framework startup
4. **DAG/Plugin Loading**: Parsing and loading DAGs and plugins
5. **Health Check Setup**: Setting up health check endpoints

With external database, this process takes >120 seconds.

## Recommendations

### For Development (Recommended)
**Use Airflow Standalone Mode**:
- Combines webserver, scheduler, worker in single process
- Avoids gunicorn entirely
- Suitable for development and testing
- Already attempted but needs further investigation

### For Production
1. **Increase Docker Memory**: Allocate 8GB (per Airflow docs recommendation)
2. **Use Local PostgreSQL**: Eliminate network latency
3. **Kubernetes Deployment**: Use official Helm chart (recommended by Airflow)
4. **Monitor Airflow Releases**: Wait for timeout configurability

## References

- [Airflow Docker Compose Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#fetching-docker-compose-yaml)
- Airflow Version: 2.10.5
- Docker Image: `apache/airflow:2.10.5` (custom build with ML packages)

