# Airflow Init Error Fix

## Problem

```
sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgresql.psycopg
service "airflow-init" didn't complete successfully: exit 1
```

## Root Cause

Airflow couldn't find the PostgreSQL driver (`psycopg2`) even though `psycopg2-binary` was in requirements.txt. Additionally, the `postgresql+psycopg2://` connection string format needed to be converted to `postgresql://` for Airflow to use properly.

## Solution

### 1. Updated Dockerfile

**File:** `docker/airflow/Dockerfile`

**Changes:**
- Installed `psycopg2-binary` explicitly before other requirements
- Added system dependencies (postgresql-client) for better compatibility

```dockerfile
# Ensure psycopg2-binary is installed first (required for PostgreSQL)
RUN pip install --no-cache-dir psycopg2-binary
```

### 2. Convert Connection String Format

**File:** `docker-compose.yml`

**Changes:**
- Added connection string conversion in `airflow-init` command
- Converts `postgresql+psycopg2://` to `postgresql://` format

```yaml
# Convert DATABASE_URL format for Airflow
if [ -n "$DATABASE_URL" ]; then
  export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=$(echo "$DATABASE_URL" | sed 's/postgresql+psycopg2:/postgresql:/')
  export AIRFLOW__CELERY__RESULT_BACKEND="db+$(echo "$DATABASE_URL" | sed 's/postgresql+psycopg2:/postgresql:/')"
fi
```

## Why This Works

1. **psycopg2-binary installed early**: Ensures the driver is available when Airflow initializes
2. **Connection string conversion**: Airflow works better with `postgresql://` format when psycopg2-binary is installed
3. **Proper environment setup**: Connection string is converted before Airflow tries to connect

## Testing

### Rebuild Image

```bash
docker build -f docker/airflow/Dockerfile -t ibkr-airflow:latest docker/airflow/
```

### Test Init

```bash
docker-compose up airflow-init
```

### Expected Result

```
✓ Airflow version check succeeds
✓ Database connection succeeds
✓ Container exits successfully
```

## Next Steps

1. **Rebuild the Airflow image:**
   ```bash
   docker build -f docker/airflow/Dockerfile -t ibkr-airflow:latest docker/airflow/
   ```

2. **Start services:**
   ```bash
   ./start-webapp.sh
   ```

3. **Verify airflow-init succeeds:**
   ```bash
   docker-compose logs airflow-init
   ```

## Related Files

- `docker/airflow/Dockerfile` - Updated to install psycopg2-binary early
- `docker-compose.yml` - Updated airflow-init command to convert connection string
- `docker/airflow/requirements.txt` - Contains psycopg2-binary (already present)

## Troubleshooting

### If still failing:

1. **Check psycopg2-binary is installed:**
   ```bash
   docker run --rm ibkr-airflow:latest pip list | grep psycopg
   ```

2. **Check connection string format:**
   ```bash
   docker-compose run --rm airflow-init env | grep AIRFLOW__DATABASE
   ```

3. **Test database connection:**
   ```bash
   docker-compose run --rm airflow-init airflow db check
   ```

## Summary

✅ **Fixed:** psycopg2-binary installation  
✅ **Fixed:** Connection string format conversion  
✅ **Result:** Airflow init should now succeed  

---

**Rebuild the image and try again!**

```bash
docker build -f docker/airflow/Dockerfile -t ibkr-airflow:latest docker/airflow/
./start-webapp.sh
```

