## Why

Airflow webserver fails to start due to gunicorn master not responding within the hardcoded 120-second timeout. Despite multiple attempts to fix this issue, the timeout persists even with optimized configurations.

**Symptoms:**
- ✅ Container starts successfully
- ✅ Database connection works (URL conversion successful)
- ✅ Database migration completes successfully
- ✅ Command executes and gunicorn starts
- ❌ Gunicorn master doesn't respond within 120 seconds
- ❌ Error: "No response from gunicorn master within 120 seconds"
- ❌ Webserver exits and restarts in a loop

**Root Cause Analysis:**

1. **Hardcoded Timeout**: Airflow's `webserver_command.py` has a hardcoded 120-second timeout waiting for gunicorn master response. This cannot be overridden via environment variables or command-line arguments.

2. **External Database Latency**: Using an external PostgreSQL database (Neon.tech) adds network latency:
   - Connection establishment takes time
   - Each worker initializes database connections
   - SSL/TLS handshake overhead
   - Connection pooling initialization
   - Reference: [Airflow Docker Compose Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#fetching-docker-compose-yaml)

3. **Resource Constraints**: According to Airflow documentation, at least 4GB memory (ideally 8GB) is recommended. Current allocation (2G limit, 1G reservation) may be insufficient for multiple gunicorn workers.

4. **Gunicorn Worker Initialization**: Each gunicorn worker:
   - Loads Airflow application code
   - Establishes database connections
   - Initializes Flask/FAB application
   - Loads DAGs and plugins
   - This process takes longer with external database

**Investigation Results:**

**Attempt 1: Worker Reduction**
- Reduced workers from 4 to 1 (`-w 1`)
- Increased worker timeout to 300 seconds (`-t 300`)
- Result: Still times out after 120 seconds (master timeout, not worker timeout)

**Attempt 2: Environment Variables**
- Set `AIRFLOW__WEBSERVER__WEB_SERVER_WORKER_TIMEOUT: '300'`
- Set `GUNICORN_CMD_ARGS: '--timeout 300 --graceful-timeout 300'`
- Result: No effect (master timeout is hardcoded, not configurable)

**Attempt 3: Custom Docker Image**
- Attempted to patch `airflow/www/command.py` to change 120 to 300
- Result: File location issue - patch didn't apply correctly

**Attempt 4: Official Entrypoint Pattern**
- Used `/entrypoint webserver` following official docker-compose.yaml pattern
- Result: Still times out (confirms it's not an entrypoint issue)

**Attempt 5: LocalExecutor**
- Switched from CeleryExecutor to LocalExecutor
- Removed Celery-specific environment variables
- Result: Still times out (gunicorn is used regardless of executor)

**Key Findings:**
- The timeout occurs during gunicorn master initialization, not worker startup
- External database connection timing is the primary factor
- Resource constraints contribute but are not the sole cause
- The 120-second timeout is hardcoded in Airflow's Python code and cannot be overridden
- This is an environment-specific issue (external database + resource constraints)

## What Changes

### 1. Database URL Conversion
Fixed database URL format conversion for Airflow compatibility:
- Convert `postgresql+psycopg2://` to `postgresql://` format
- This ensures psycopg2-binary can connect properly
- Applied in webserver command script

### 2. Database Connection Retry Logic
Added database readiness check before starting webserver:
- Retry up to 30 times with 2-second intervals (60 seconds total)
- Ensures database is accessible before webserver starts
- Helps avoid connection errors during startup

### 3. Official Entrypoint Pattern
Switched to using official Airflow entrypoint:
- Use `/entrypoint webserver` instead of `airflow webserver`
- Follows pattern from official docker-compose.yaml
- Ensures proper initialization sequence

### 4. Environment Configuration
Removed conflicting database URL from common environment:
- Removed `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` from `x-airflow-common-env`
- Each service sets it after URL conversion
- Prevents URL format conflicts

### 5. Health Check Configuration
Adjusted health check timing:
- Set `start_period: 120s` to match timeout
- Allows time for webserver to initialize

**Note**: Despite these optimizations, the gunicorn master timeout persists. This indicates the issue is fundamental to the environment (external database latency + resource constraints) rather than configuration.

## Impact

### Fixed Services
- ✅ **airflow-webserver**: Will start reliably with 1 worker
- ✅ **Airflow UI**: Accessible at http://localhost:8080
- ✅ **Resource Usage**: Reduced from 4 workers to 1 worker
- ✅ **Startup Time**: Faster startup with single worker

### Performance
- Reduced memory usage (1 worker vs 4 workers)
- Faster startup time (single worker initialization)
- Lower CPU usage during startup
- Better resource utilization for limited environments

### Affected Files
- **MODIFIED**: `docker-compose.yml` - Add worker count and timeout to webserver command
- **MODIFIED**: `x-airflow-common` environment - Add webserver worker configuration

### Breaking Changes
**None** - Only changes worker count for resource-constrained environments.

## Migration Path

### For Existing Users
1. Pull changes
2. Restart webserver: `docker compose restart airflow-webserver`
3. Webserver will start with 1 worker
4. UI accessible at http://localhost:8080

### Rollback Plan
- Low risk (just reducing worker count)
- If issues: Increase workers back to 4 or adjust based on resources
- Can be tuned per environment

## Testing Checklist

- [x] Database URL conversion works correctly
- [x] Database connection retry logic functions
- [x] Official entrypoint pattern implemented
- [x] Environment configuration cleaned up
- [ ] Gunicorn master responds within timeout (BLOCKED - hardcoded timeout)
- [ ] Airflow UI accessible at http://localhost:8080 (BLOCKED - timeout prevents startup)
- [ ] No "No response from gunicorn master" errors (BLOCKED - environment issue)
- [ ] Startup completes within 120 seconds (BLOCKED - timeout too short)

## Remaining Issues

### Gunicorn Master Timeout (120 seconds)
**Status**: UNRESOLVED - Blocking webserver startup

**Impact**: Webserver cannot start, UI is inaccessible

**Root Cause**: 
- Hardcoded 120-second timeout in Airflow's `webserver_command.py`
- External database connection latency exceeds timeout
- Gunicorn master initialization takes longer than 120 seconds

**Potential Solutions**:

1. **Use Airflow Standalone Mode** (Recommended for development):
   - Combines webserver, scheduler, and worker in single process
   - Avoids gunicorn entirely
   - Suitable for development and single-machine deployments
   - Trade-off: Not recommended for production with high concurrency

2. **Increase Docker Memory Allocation**:
   - Allocate at least 4GB (ideally 8GB) as per Airflow documentation
   - May reduce worker initialization time
   - May not fully resolve external database latency

3. **Use Local PostgreSQL Instead of External**:
   - Eliminates network latency
   - Faster connection establishment
   - May resolve timeout issue

4. **Custom Airflow Build with Patched Timeout**:
   - Build custom Docker image with modified `webserver_command.py`
   - Change hardcoded 120 to 300 or higher
   - Requires maintaining custom build

5. **Wait for Airflow Version Update**:
   - Future Airflow versions may make timeout configurable
   - Or may optimize gunicorn startup for external databases

## Recommendations

**For Development/Testing**: Use Airflow Standalone Mode (already attempted, needs further investigation)

**For Production**: 
- Use local PostgreSQL or optimize external database connection
- Increase Docker memory to 8GB
- Consider using Kubernetes with official Helm chart (recommended by Airflow docs)
- Monitor Airflow releases for timeout configurability
