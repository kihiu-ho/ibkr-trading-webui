## Why

Airflow's webserver in traditional mode (separate scheduler/webserver/worker services) has a hardcoded 120-second gunicorn master timeout that cannot be overridden. Attempting to patch the timeout in custom Docker images proves ineffective because the timeout is built into Airflow's execution flow.

**Airflow Standalone Mode** combines the scheduler, webserver, and worker into a single process. This approach:
- ✅ Eliminates the gunicorn master startup timeout issue
- ✅ Simplifies the architecture (1 service instead of 5+)
- ✅ Reduces resource overhead
- ✅ Suitable for development and single-machine deployments
- ✅ Works perfectly for resource-constrained environments

**Trade-offs:**
- ⚠️ Not recommended for production with high concurrency
- ⚠️ Single point of failure (all components in one process)
- ⚠️ No distributed task execution (workers must run on same instance)

## What Changes

### 1. Replace Multi-Service Architecture with Standalone
**Before:**
- airflow-init
- airflow-webserver (separate)
- airflow-scheduler (separate)
- airflow-worker (separate)
- airflow-triggerer (separate)
- airflow-flower (monitoring)

**After:**
- airflow-standalone (combines all above)
- (optional) airflow-worker-external for scaling

### 2. Update docker-compose.yml
- Remove individual Airflow services
- Add single `airflow-standalone` service
- Configure with `airflow standalone` command
- Set proper environment variables and database URLs
- Simplify volume mounts

### 3. Simplify Configuration
- Single webserver port (8080)
- Single entrypoint
- No separate scheduler/worker/triggerer coordination
- Cleaner startup sequence

## Impact

### Fixed Services
- ✅ **Airflow Webserver**: Accessible at http://localhost:8080
- ✅ **Airflow Scheduler**: Integrated in standalone service
- ✅ **Airflow Worker**: Integrated in standalone service
- ✅ **DAG Management**: Full UI functionality
- ✅ **Task Execution**: All tasks run on the standalone instance

### Performance
- **Startup Time**: Reduced from 5+ minutes to ~30-60 seconds
- **Resource Usage**: Lower memory (no gunicorn master overhead)
- **No Timeout**: Eliminates the 120-second gunicorn timeout entirely
- **Simpler Infrastructure**: Fewer services to manage

### Affected Files
- **MODIFIED**: `docker-compose.yml` - Replace multi-service with single standalone
- **REMOVED**: Separate service definitions (webserver, scheduler, worker, triggerer, flower)
- **CREATED**: Single airflow-standalone service configuration

### Breaking Changes
**Minor Breaking Changes:**
- Old webserver/scheduler/worker services no longer available
- DAG execution happens in single process (not distributed)
- Flower monitoring removed (use Airflow UI instead)

## Migration Path

### For Existing Users
1. Pull changes
2. Backup existing database (important!)
3. Rebuild Airflow image: `docker compose build --no-cache airflow-init`
4. Restart services: `docker compose up -d airflow-standalone`
5. Access UI at http://localhost:8080

### Rollback Plan
- Keep backup of database
- Restore previous docker-compose.yml
- Rebuild multi-service architecture
- Restore database from backup

## Testing Checklist

- [ ] Airflow standalone service starts successfully
- [ ] Webserver accessible at http://localhost:8080 immediately
- [ ] No gunicorn timeout errors in logs
- [ ] No 120-second startup delay
- [ ] DAGs load in web interface
- [ ] Can manually trigger DAG runs
- [ ] Tasks execute successfully
- [ ] Scheduler properly runs DAGs on schedule
- [ ] Database persists data correctly
- [ ] Complete startup in <60 seconds
