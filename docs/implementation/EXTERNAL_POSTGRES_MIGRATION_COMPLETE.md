# External PostgreSQL Migration Complete ✅

## Summary

Successfully migrated Airflow and MLflow to use external PostgreSQL databases, removing the containerized PostgreSQL dependency and fixing the `ibkr-postgres` container error.

## Problem Solved

**Original Error:**
```
✘ Container ibkr-postgres           Error
dependency failed to start: container ibkr-postgres is unhealthy
```

**Solution:** Removed containerized PostgreSQL and configured all services to use external PostgreSQL databases via environment variables.

## Changes Made

### 1. Environment Variables (`env.example`)

**Added:**
```bash
# Airflow database connection
AIRFLOW_DATABASE_URL=postgresql+psycopg2://user:password@host:port/airflow?sslmode=require

# MLflow database connection  
MLFLOW_DATABASE_URL=postgresql+psycopg2://user:password@host:port/mlflow?sslmode=require
```

### 2. Docker Compose (`docker-compose.yml`)

**Removed:**
- `postgres` service (entire container)
- `postgres_data` volume
- PostgreSQL health check dependencies
- `init-multiple-dbs.sh` volume mount

**Updated:**
- Airflow environment: `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: "${AIRFLOW_DATABASE_URL}"`
- MLflow command: `--backend-store-uri ${MLFLOW_DATABASE_URL}`
- Removed `postgres` from all `depends_on` sections

### 3. Startup Script (`start-webapp.sh`)

**Removed:**
- PostgreSQL health check logic
- PostgreSQL from container display list

**Updated:**
- Database status message: "External PostgreSQL" instead of "External Neon"
- Added comment explaining external database configuration

### 4. Documentation

**Created:**
- `DATABASE_SETUP_AIRFLOW_MLFLOW.md` - Comprehensive database setup guide

## Database Requirements

You now need **three databases** in your external PostgreSQL instance:

1. **Backend database** (existing): `ibkr_trading` (or your custom name)
2. **Airflow database** (new): `airflow`
3. **MLflow database** (new): `mlflow`

## Quick Setup Guide

### Step 1: Create Databases

```sql
-- Connect to your PostgreSQL instance
psql "postgresql://username:password@host:port/postgres?sslmode=require"

-- Create new databases
CREATE DATABASE airflow;
CREATE DATABASE mlflow;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE airflow TO your_user;
GRANT ALL PRIVILEGES ON DATABASE mlflow TO your_user;
```

### Step 2: Configure .env File

```bash
# Edit your .env file
nano .env

# Add these lines (update with your actual credentials):
AIRFLOW_DATABASE_URL=postgresql+psycopg2://user:password@host:port/airflow?sslmode=require
MLFLOW_DATABASE_URL=postgresql+psycopg2://user:password@host:port/mlflow?sslmode=require
```

### Step 3: Start Services

```bash
# Start all services
./start-webapp.sh

# Or use docker-compose directly
docker-compose up -d
```

## Neon PostgreSQL Example

If using Neon (recommended):

```bash
# All three databases in the same Neon project
DATABASE_URL=postgresql+psycopg2://user:pass@ep-xxx.us-east-1.aws.neon.tech/ibkr_trading?sslmode=require
AIRFLOW_DATABASE_URL=postgresql+psycopg2://user:pass@ep-xxx.us-east-1.aws.neon.tech/airflow?sslmode=require
MLFLOW_DATABASE_URL=postgresql+psycopg2://user:pass@ep-xxx.us-east-1.aws.neon.tech/mlflow?sslmode=require
```

## Benefits

✅ **No Container Dependency**: No more `ibkr-postgres` container failures  
✅ **Consistent Pattern**: All services use external databases  
✅ **Better Performance**: Use managed PostgreSQL with backups  
✅ **Easier Management**: Single PostgreSQL instance for all databases  
✅ **Production Ready**: Suitable for production deployments  

## Architecture Changes

### Before (With Containerized PostgreSQL)

```
Docker Compose Services:
├── postgres (REMOVED)
├── redis
├── minio
├── backend → DATABASE_URL
├── airflow → postgres container
└── mlflow → postgres container
```

### After (All External)

```
Docker Compose Services:
├── redis
├── minio
├── backend → DATABASE_URL (external)
├── airflow → AIRFLOW_DATABASE_URL (external)
└── mlflow → MLFLOW_DATABASE_URL (external)

External PostgreSQL:
├── Database: ibkr_trading (backend)
├── Database: airflow (airflow)
└── Database: mlflow (mlflow)
```

## Service Status Display

**New Output:**
```
📦 Docker Containers:
  ├─ Core Services:
  │  ├─ ibkr-redis          Redis message broker
  │  └─ ibkr-minio          MinIO object storage
  ├─ Trading Services:
  │  ├─ ibkr-gateway        IBKR Client Portal Gateway
  │  ├─ ibkr-backend        FastAPI backend server
  │  ├─ ibkr-celery-worker  Celery background worker
  │  ├─ ibkr-celery-beat    Celery task scheduler
  │  └─ ibkr-flower         Celery monitoring UI
  └─ ML/Workflow Services:
     ├─ ibkr-mlflow-server  MLflow experiment tracking
     ├─ ibkr-airflow-webserver   Airflow web UI
     ├─ ibkr-airflow-scheduler   Airflow scheduler
     ├─ ibkr-airflow-worker      Airflow task worker
     └─ ibkr-airflow-triggerer   Airflow triggerer

📊 System Status:
  ✓ Backend:            READY (Port 8000)
  ✓ Database:           READY (External PostgreSQL)  ← Updated
  ✓ Redis:              READY (Port 6379)
  ✓ MinIO:              READY (Port 9000)
```

Note: **No PostgreSQL container** in the list!

## Testing Results

### ✅ Configuration Valid
```bash
docker-compose config > /dev/null
# Result: Syntax valid (warnings about unset vars expected until .env configured)
```

### ✅ Startup Script Valid
```bash
bash -n start-webapp.sh
# Result: No syntax errors
```

### ✅ OpenSpec Validation
```bash
openspec validate use-external-postgres-airflow-mlflow --strict
# Result: Valid
```

## Verification Steps

After configuring your databases:

### 1. Check Airflow Connection
```bash
docker-compose run --rm airflow-webserver airflow db check
# Should show: "Database: airflow"
```

### 2. Check MLflow Connection
```bash
docker-compose logs mlflow-server | grep "Connected"
# Should show successful database connection
```

### 3. Check Services Running
```bash
docker-compose ps
# Should NOT show ibkr-postgres
# All other services should be "Up" or "Healthy"
```

## Troubleshooting

### Error: "database 'airflow' does not exist"

**Solution:** Create the database:
```sql
CREATE DATABASE airflow;
```

### Error: "database 'mlflow' does not exist"

**Solution:** Create the database:
```sql
CREATE DATABASE mlflow;
```

### Error: "AIRFLOW_DATABASE_URL is not set"

**Solution:** Add the variable to your `.env` file:
```bash
AIRFLOW_DATABASE_URL=postgresql+psycopg2://...
```

### Error: "password authentication failed"

**Solution:** 
1. Check your credentials in `.env`
2. URL-encode special characters in password
3. Verify user has access to the databases

## Migration from Old Setup

If you had the containerized PostgreSQL running:

### 1. Backup Data (Optional)

```bash
# Only if you have existing Airflow/MLflow data to preserve
docker exec ibkr-postgres pg_dump -U airflow airflow > airflow_backup.sql
docker exec ibkr-postgres pg_dump -U mlflow mlflow > mlflow_backup.sql
```

### 2. Import to External Database

```bash
# Import backups to your external PostgreSQL
psql "$AIRFLOW_DATABASE_URL" < airflow_backup.sql
psql "$MLFLOW_DATABASE_URL" < mlflow_backup.sql
```

### 3. Clean Up Old Container

```bash
# Stop all services
docker-compose down

# Remove old PostgreSQL volume
docker volume rm ibkr_postgres_data

# Start with new configuration
./start-webapp.sh
```

## OpenSpec Compliance

### Change ID
`use-external-postgres-airflow-mlflow`

### Proposal Files
- ✅ `proposal.md` - Rationale and impact
- ✅ `tasks.md` - All 20 tasks completed
- ✅ `specs/deployment/spec.md` - Requirements met

### Validation
```bash
openspec validate use-external-postgres-airflow-mlflow --strict
# Result: ✅ Valid
```

## Files Modified

### Modified (3 files)
1. `docker-compose.yml` - Removed postgres, updated Airflow/MLflow configs
2. `env.example` - Added AIRFLOW_DATABASE_URL and MLFLOW_DATABASE_URL
3. `start-webapp.sh` - Removed postgres health checks

### Created (2 files)
1. `DATABASE_SETUP_AIRFLOW_MLFLOW.md` - Database setup guide
2. `EXTERNAL_POSTGRES_MIGRATION_COMPLETE.md` - This summary

### OpenSpec (3 files)
1. `openspec/changes/use-external-postgres-airflow-mlflow/proposal.md`
2. `openspec/changes/use-external-postgres-airflow-mlflow/tasks.md`
3. `openspec/changes/use-external-postgres-airflow-mlflow/specs/deployment/spec.md`

## Related Documentation

- **Database Setup**: `DATABASE_SETUP_AIRFLOW_MLFLOW.md` - Start here!
- **Airflow/MLflow Setup**: `AIRFLOW_MLFLOW_SETUP.md`
- **Quick Start**: `QUICKSTART_AIRFLOW_MLFLOW.md`
- **Environment Config**: `env.example`

## Next Steps

1. **Create databases** in your PostgreSQL instance (airflow, mlflow)
2. **Update .env** with database URLs
3. **Start services**: `./start-webapp.sh`
4. **Verify** Airflow UI (http://localhost:8080) and MLflow UI (http://localhost:5500)

## Completion Status

**Status**: ✅ Complete  
**Date**: November 2, 2025  
**OpenSpec Change**: `use-external-postgres-airflow-mlflow`

All tasks completed:
- [x] Environment variables updated
- [x] Docker compose updated
- [x] Startup script updated
- [x] Documentation created
- [x] Testing passed
- [x] OpenSpec validated

---

## 🎉 Problem Solved!

The `ibkr-postgres` container error is now fixed. All services use external PostgreSQL databases for better reliability and consistency.

**To use the system:**
1. Follow the guide in `DATABASE_SETUP_AIRFLOW_MLFLOW.md`
2. Create the required databases
3. Configure your `.env` file
4. Run `./start-webapp.sh`

Ready to go! 🚀

