## Why

Airflow services (webserver, scheduler, worker) are failing to start with SSL connection errors to PostgreSQL, even though the airflow-init container successfully connects and migrates the database.

**Root Cause:** Database URL format mismatch
- Backend services use: `postgresql+psycopg2://...` (works for SQLAlchemy)
- Airflow needs: `postgresql://...` (works for psycopg2 directly)
- Only airflow-init converts the URL format, other containers don't

**Current State:**
- ✅ airflow-init: Successfully connects and migrates database
- ❌ airflow-webserver: "No response from gunicorn master within 120 seconds"
- ❌ airflow-scheduler: "SSL SYSCALL error: EOF detected"
- ❌ airflow-worker: Similar connection failures
- ❌ Airflow UI: Completely inaccessible

## What Changes

### 1. Fix Database URL Format Conversion
Apply the same URL conversion logic used in airflow-init to all Airflow containers:

**Current (broken):**
```yaml
environment:
  AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: "${AIRFLOW_DATABASE_URL}"  # postgresql+psycopg2://...
```

**Fixed:**
```yaml
command:
  - -c
  - |
    # Convert AIRFLOW_DATABASE_URL format for Airflow
    if [ -n "$AIRFLOW_DATABASE_URL" ]; then
      export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=$(echo "$AIRFLOW_DATABASE_URL" | sed 's/postgresql+psycopg[^:]*:/postgresql:/')
      export AIRFLOW__CELERY__RESULT_BACKEND="db+$(echo "$AIRFLOW_DATABASE_URL" | sed 's/postgresql+psycopg[^:]*:/postgresql:/')"
    fi
    exec /usr/bin/dumb-init -- "$@"
```

### 2. Add Connection Validation
Add startup validation to ensure database connectivity before starting Airflow services.

### 3. Improve Error Handling
Add better error messages and connection retry logic for database issues.

## Impact

### Fixed Services
- ✅ **airflow-webserver**: Will start successfully and serve UI on port 8080
- ✅ **airflow-scheduler**: Will connect to database and schedule DAGs
- ✅ **airflow-worker**: Will execute tasks via Celery
- ✅ **Airflow UI**: Fully accessible at http://localhost:8080

### Performance
- Services start in <60 seconds (instead of failing after init)
- No more SSL connection errors
- Reliable database connectivity

### Affected Files
- **MODIFIED**: `docker-compose.yml` - Add URL conversion to all Airflow services
- **OPTIONAL**: `reference/airflow/airflow/entrypoint.sh` - Enhanced error handling

### Database
- No schema changes required
- Uses existing airflow database successfully created by airflow-init
- Connection format compatible with psycopg2-binary

### Breaking Changes
**None** - Fixes broken functionality without changing any APIs.

## Migration Path

### For Existing Users
1. Pull changes
2. Restart Airflow services: `docker compose restart airflow-webserver airflow-scheduler airflow-worker`
3. Airflow UI becomes accessible at http://localhost:8080
4. All Airflow functionality works normally

### Rollback Plan
- Extremely low risk (fixes connection issue)
- If issues: `docker compose down` and revert docker-compose.yml
- No data loss (database already migrated by airflow-init)

## Testing Checklist

- [ ] All Airflow services start without connection errors
- [ ] Airflow UI accessible at http://localhost:8080
- [ ] Database connections work for all Airflow components
- [ ] DAGs can be loaded and executed
- [ ] No SSL SYSCALL errors in logs
- [ ] Services remain stable after restart
