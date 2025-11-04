## Why

The Airflow webserver is experiencing gunicorn master timeout issues due to external database (Neon.tech) connection latency. Network latency, SSL/TLS handshake overhead, and connection pooling initialization cause gunicorn master initialization to exceed the hardcoded 120-second timeout.

**Problem:**
- External PostgreSQL database adds significant network latency
- SSL/TLS handshake overhead for each connection
- Connection pooling initialization delays
- Gunicorn master timeout occurs before database connections are ready
- Reference: [Gunicorn Timeout Investigation](../fix-gunicorn-timeout/INVESTIGATION_SUMMARY.md)

**Solution:**
Migrate to local PostgreSQL database running in Docker Compose:
- Eliminates network latency (localhost connection)
- Faster connection establishment
- No SSL/TLS overhead in local network
- Should resolve gunicorn timeout issue
- Follows pattern from [reference docker-compose.yaml](../../reference/airflow/docker-compose.yaml)

## What Changes

### 1. Add Local PostgreSQL Service
**New Service:**
- `postgres` service using `postgres:13` image
- Health checks with `pg_isready`
- Persistent volume for database data
- Network: `trading-network`
- Initialization script: `scripts/init-databases.sh`

### 2. Update Airflow Services
**Modify Airflow services to use local PostgreSQL:**
- Remove dependency on external `AIRFLOW_DATABASE_URL` environment variable
- Set `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` to use local postgres service
- Update database URL format (no conversion needed for local postgres)
- Add dependency on `postgres` service with health check condition

### 3. Update Database Initialization
**Ensure proper initialization:**
- Use existing `scripts/init-databases.sh` script
- Mount script to `/docker-entrypoint-initdb.d/init-multiple-dbs.sh`
- Create `airflow` and `mlflow` databases and users automatically

### 4. Environment Configuration
**Update environment variables:**
- Remove external database URL references
- Use local database connection string: `postgresql+psycopg2://airflow:airflow@postgres/airflow`
- Keep URL conversion logic for compatibility (though not needed for local)

## Impact

### Fixed Services
- ✅ **airflow-webserver**: Should start without gunicorn timeout
- ✅ **airflow-scheduler**: Faster database connections
- ✅ **All Airflow services**: Reduced connection latency

### Performance
- **Connection Speed**: Near-instant localhost connections vs. network latency
- **Startup Time**: Expected reduction from >120s to <60s
- **Reliability**: No external database dependency or network issues
- **Resource Usage**: Minimal overhead (PostgreSQL container)

### Affected Files
- **MODIFIED**: `docker-compose.yml` - Add postgres service, update Airflow services
- **MODIFIED**: `scripts/init-databases.sh` - Already exists, will be used
- **REMOVED**: External database URL environment variable dependency

### Breaking Changes
**Minor Breaking Changes:**
- External database no longer used (must migrate data if needed)
- Local PostgreSQL requires Docker volume for persistence
- Environment variable `AIRFLOW_DATABASE_URL` no longer needed

## Migration Path

### For Existing Users

1. **Backup External Database** (if data exists):
   ```bash
   pg_dump -h <external-host> -U <user> -d airflow > airflow_backup.sql
   ```

2. **Pull Changes**

3. **Start PostgreSQL Service**:
   ```bash
   docker compose up -d postgres
   ```

4. **Wait for PostgreSQL to be healthy**:
   ```bash
   docker compose ps postgres
   ```

5. **Restore Data** (if needed):
   ```bash
   docker compose exec postgres psql -U airflow -d airflow < airflow_backup.sql
   ```

6. **Start Airflow Services**:
   ```bash
   docker compose up -d airflow-webserver airflow-scheduler
   ```

7. **Verify Webserver Starts**:
   ```bash
   docker compose logs airflow-webserver | grep -E "(gunicorn|timeout|Running)"
   curl http://localhost:8080/health
   ```

### Rollback Plan
- Keep external database credentials
- Restore previous `docker-compose.yml` configuration
- Restore `AIRFLOW_DATABASE_URL` environment variable
- Rebuild and restart services

## Testing Checklist

- [ ] PostgreSQL service starts successfully
- [ ] Database initialization script runs correctly
- [ ] `airflow` and `mlflow` databases created
- [ ] Airflow webserver connects to local PostgreSQL
- [ ] No gunicorn timeout errors
- [ ] Webserver starts within 60 seconds
- [ ] Airflow UI accessible at http://localhost:8080
- [ ] Database persists data across container restarts
- [ ] Scheduler connects successfully
- [ ] DAGs load and execute correctly
- [ ] MLflow service can connect to local PostgreSQL

## Success Criteria

1. **Webserver Startup**: Completes within 60 seconds without timeout
2. **No Gunicorn Errors**: No "No response from gunicorn master" errors
3. **UI Accessibility**: Airflow UI fully functional at http://localhost:8080
4. **Database Performance**: Connection establishment <1 second
5. **Data Persistence**: Database survives container restarts

