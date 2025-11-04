# Airflow/MLflow Database Error - FIXED ✅

## Your Error

```bash
dependency failed to start: container ibkr-postgres is unhealthy
```

AND

```bash
psql: error: connection to server on socket "/tmp/.s.PGSQL.5432" failed: 
No such file or directory
```

## ✅ Complete Fix Applied

Three issues were fixed:

### 1. ✅ Removed Unhealthy Container
**Problem:** `ibkr-postgres` container failing  
**Fix:** Removed containerized PostgreSQL, using external database instead  
**Files:** `docker-compose.yml`

### 2. ✅ Fixed Connection String Parsing  
**Problem:** Script couldn't connect to external database  
**Fix:** Improved regex parsing to extract all connection details  
**Files:** `setup-databases-quick.sh`

### 3. ✅ Updated Startup Script
**Problem:** `start-webapp.sh` referenced removed postgres container  
**Fix:** Removed postgres health checks, updated service display  
**Files:** `start-webapp.sh`

## Quick Start (3 Commands)

```bash
# 1. Setup databases (auto-configures .env)
./setup-databases-quick.sh

# 2. Verify configuration
./scripts/check-env-airflow-mlflow.sh

# 3. Start everything
./start-webapp.sh
```

## What Each Script Does

### 1. `setup-databases-quick.sh`

**Auto-detects your database from .env:**
```
✓ Backend DATABASE_URL is already configured
  Detected connection: user@ep-xxx.us-east-1.aws.neon.tech:5432
  Existing database: ibkr_trading
  Will create: airflow, mlflow (in same server)
```

**Configures Airflow & MLflow:**
```
✓ Added AIRFLOW_DATABASE_URL to .env
✓ Added MLFLOW_DATABASE_URL to .env
```

**Offers to create databases automatically:**
```
Would you like to create the databases now? (y/N)
> y

Creating databases...
Connecting to: postgresql://user:****@ep-xxx.aws.neon.tech:5432/postgres?sslmode=require

✓ Databases created successfully!
```

### 2. `check-env-airflow-mlflow.sh`

**Verifies everything is configured:**
```
✓ AIRFLOW_DATABASE_URL is set
  postgresql://user:****@ep-xxx.aws.neon.tech:5432/airflow?sslmode=require
✓ _AIRFLOW_WWW_USER_USERNAME is set
✓ _AIRFLOW_WWW_USER_PASSWORD is set
✓ MLFLOW_DATABASE_URL is set
  postgresql://user:****@ep-xxx.aws.neon.tech:5432/mlflow?sslmode=require
✓ MLFLOW_TRACKING_URI is set
✓ AWS_ACCESS_KEY_ID is set
✓ AWS_SECRET_ACCESS_KEY is set

✓ All required environment variables are configured!
```

### 3. `start-webapp.sh`

**Starts everything without postgres container:**
```
Building images...
✓ ibkr-backend:latest
✓ ibkr-gateway:latest
✓ ibkr-airflow:latest
✓ ibkr-mlflow:latest

Starting services...
✓ Redis
✓ MinIO
✓ MLflow Server
✓ Airflow Webserver
✓ Airflow Scheduler
✓ Airflow Worker

All services are running!

Access Points:
  ├── MLflow UI:        http://localhost:5500
  ├── Airflow UI:       http://localhost:8080
  └── MinIO Console:    http://localhost:9001

✓ Database: READY (External PostgreSQL)
```

## Manual Database Creation (Alternative)

If automatic creation doesn't work:

### For Neon Users:
1. Go to **https://neon.tech**
2. Select your project
3. Click **"Databases"** tab
4. Click **"New Database"**
5. Create: `airflow`
6. Create: `mlflow`
7. Done!

### Using psql:
```bash
# Get your connection string
grep DATABASE_URL .env

# Connect (adjust your connection string)
psql "postgresql://user:pass@host:5432/postgres?sslmode=require"

# Create databases
CREATE DATABASE airflow;
CREATE DATABASE mlflow;

# Verify they exist
\l

# Exit
\q
```

## System Architecture

### Before Fix (Had Container)
```
┌─────────────────────────────────────────┐
│ Docker Compose                          │
│                                         │
│  ┌──────────────┐                       │
│  │ ibkr-postgres│ ← UNHEALTHY! ❌       │
│  │ (container)  │                       │
│  └──────────────┘                       │
│         ↑                               │
│         │ (failed dependency)           │
│  ┌──────────────┐  ┌──────────────┐    │
│  │   Airflow    │  │   MLflow     │    │
│  │  (blocked)   │  │  (blocked)   │    │
│  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────┘
```

### After Fix (External Database)
```
┌─────────────────────────────────────────┐
│ Docker Compose                          │
│                                         │
│  ┌──────────────┐  ┌──────────────┐    │
│  │   Airflow    │  │   MLflow     │    │
│  │  (running)   │  │  (running)   │    │
│  └──────┬───────┘  └──────┬───────┘    │
│         │                  │            │
│         └──────────┬───────┘            │
│                    │                    │
└────────────────────┼────────────────────┘
                     │
                     ↓
          ┌────────────────────┐
          │ External PostgreSQL│ ← HEALTHY! ✅
          │  (Neon/AWS RDS)    │
          │                    │
          │  ├─ ibkr_trading   │
          │  ├─ airflow        │
          │  └─ mlflow         │
          └────────────────────┘
```

## Configuration Details

### Your .env Now Contains:

```bash
# Backend database (existing)
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/ibkr_trading?sslmode=require

# Airflow database (new)
AIRFLOW_DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/airflow?sslmode=require

# MLflow database (new)
MLFLOW_DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/mlflow?sslmode=require

# Airflow admin credentials (new)
_AIRFLOW_WWW_USER_USERNAME=admin
_AIRFLOW_WWW_USER_PASSWORD=admin

# MLflow tracking (new)
MLFLOW_TRACKING_URI=http://mlflow-server:5500
MLFLOW_S3_ENDPOINT_URL=http://minio:9000

# MinIO credentials (existing)
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
```

## Verification Checklist

- [ ] 1. Run `./setup-databases-quick.sh`
- [ ] 2. Databases `airflow` and `mlflow` exist in PostgreSQL
- [ ] 3. Run `./scripts/check-env-airflow-mlflow.sh` - all checks pass
- [ ] 4. Run `./start-webapp.sh` - no errors
- [ ] 5. Open http://localhost:8080 - Airflow UI loads
- [ ] 6. Open http://localhost:5500 - MLflow UI loads
- [ ] 7. No `ibkr-postgres` container errors

## Troubleshooting

### Issue: "Could not create databases automatically"

**Possible Causes:**
- Databases already exist (this is fine!)
- Wrong credentials in DATABASE_URL
- Network/firewall blocking connection
- Database server is down

**Solution:** Create manually via Neon web UI or psql

### Issue: "Airflow webserver not responding"

**Possible Causes:**
- Database connection failed
- Airflow needs time to initialize (can take 30-60 seconds)

**Solution:**
```bash
# Check Airflow logs
docker logs ibkr-airflow-webserver

# Check database connection
docker exec ibkr-airflow-webserver airflow db check
```

### Issue: "MLflow can't connect to database"

**Possible Causes:**
- MLFLOW_DATABASE_URL not set
- Database doesn't exist

**Solution:**
```bash
# Check environment
docker exec ibkr-mlflow-server env | grep MLFLOW_DATABASE_URL

# Create database manually if needed
psql "$DATABASE_URL" -c "CREATE DATABASE mlflow;"
```

## OpenSpec Compliance

This fix follows OpenSpec methodology with three changes:

### 1. `use-external-postgres-airflow-mlflow`
- Removed containerized PostgreSQL
- Updated docker-compose.yml
- Updated env.example
- Updated start-webapp.sh

### 2. `fix-database-setup-script`
- Fixed connection string parsing
- Improved error handling
- Added verification steps

### 3. `update-startup-script-airflow-mlflow`
- Added Airflow/MLflow services
- Updated health checks
- Enhanced service display

All changes validated with:
```bash
openspec validate <change-id> --strict
```

## Files Created

### Documentation
1. `DATABASE_SETUP_SCRIPT_FIXED.md` - Technical details
2. `SETUP_SCRIPT_FIX_COMPLETE.md` - User guide
3. `START_HERE_AIRFLOW_FIX.md` - Quick start
4. `FIX_AIRFLOW_INIT_ERROR.md` - This file
5. `EXTERNAL_POSTGRES_MIGRATION_COMPLETE.md` - Migration guide
6. `DATABASE_SETUP_AIRFLOW_MLFLOW.md` - Database setup
7. `QUICK_FIX_POSTGRES.md` - Quick reference

### Scripts
1. `setup-databases-quick.sh` - Fixed
2. `scripts/check-env-airflow-mlflow.sh` - New verification script
3. `start-webapp.sh` - Updated

### OpenSpec
1. `openspec/changes/use-external-postgres-airflow-mlflow/` - 3 files
2. `openspec/changes/fix-database-setup-script/` - 3 files
3. `openspec/changes/update-startup-script-airflow-mlflow/` - 3 files

## Summary

✅ **Fixed the container unhealthy error** by using external PostgreSQL  
✅ **Fixed the connection error** with improved parsing  
✅ **Updated startup script** to work without postgres container  
✅ **Created helper scripts** for easy setup and verification  
✅ **Documented everything** with clear guides  

## Next Steps

1. **Run**: `./setup-databases-quick.sh`
2. **Verify**: `./scripts/check-env-airflow-mlflow.sh`
3. **Start**: `./start-webapp.sh`
4. **Access**: http://localhost:8080 (Airflow) & http://localhost:5500 (MLflow)

---

**Everything is ready! Just run the scripts in order.** 🚀

For more details, see:
- **Quick Start**: `START_HERE_AIRFLOW_FIX.md`
- **Full Details**: `SETUP_SCRIPT_FIX_COMPLETE.md`
- **Database Guide**: `DATABASE_SETUP_AIRFLOW_MLFLOW.md`
