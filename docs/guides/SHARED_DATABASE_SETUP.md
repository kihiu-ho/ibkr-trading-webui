# ✅ Shared Database Setup - Simplified!

## 🎉 What Changed

**All services (Backend, Airflow, MLflow) now use the SAME database!**

No more creating separate databases. Just configure `DATABASE_URL` once and you're done.

## 🚀 Quick Start (2 Commands)

```bash
# 1. Verify configuration
./setup-databases-quick.sh

# 2. Start everything
./start-webapp.sh
```

That's it! No database creation needed.

## 📊 How It Works

### One Database, Multiple Services

```
┌─────────────────────────────────────────────────────────┐
│  PostgreSQL Database (from DATABASE_URL)                │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Backend Tables:                                 │   │
│  │  • users, portfolios, trades, etc.              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Airflow Tables:                                 │   │
│  │  • alembic_version, dag, dag_run, task_*, etc.  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ MLflow Tables:                                  │   │
│  │  • mlflow_experiment, mlflow_run, mlflow_*, etc.│   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

Each service creates its own tables with unique prefixes/names, so they don't conflict.

## ⚙️ Configuration

### Your .env File

Only one database URL needed:

```bash
# This is all you need!
DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname?sslmode=require

# Airflow web credentials
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow

# MinIO for MLflow artifacts (optional, has defaults)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### What Was Removed

These are NO LONGER NEEDED:
- ~~`AIRFLOW_DATABASE_URL`~~ ❌ (uses DATABASE_URL)
- ~~`MLFLOW_DATABASE_URL`~~ ❌ (uses DATABASE_URL)
- ~~Database creation steps~~ ❌ (auto-created on first run)

## 🔧 Setup Process

### Step 1: Check Configuration

```bash
./setup-databases-quick.sh
```

**Output:**
```
╔══════════════════════════════════════════════════════════╗
║  Airflow & MLflow Configuration Check                   ║
╚══════════════════════════════════════════════════════════╝

Checking configuration...

✓ DATABASE_URL is configured
  postgresql+psycopg2://user:****@host:5432/dbname?sslmode=require

  Database: ibkr_trading
  Host: ep-xxx.us-east-1.aws.neon.tech:5432
  User: myuser

────────────────────────────────────────────────────────

✓ Configuration Complete!

All services (Backend, Airflow, MLflow) will use the same database.

The services will create their own tables:
  • Backend: Uses existing tables
  • Airflow: Creates tables with 'alembic_version', 'dag_', 'task_', etc.
  • MLflow: Creates tables with 'mlflow_' prefix

No separate database creation needed!

────────────────────────────────────────────────────────

Next Steps:

1. Verify configuration:
   ./scripts/check-env-airflow-mlflow.sh

2. Start all services:
   ./start-webapp.sh
```

### Step 2: Verify (Optional)

```bash
./scripts/check-env-airflow-mlflow.sh
```

**Output:**
```
╔══════════════════════════════════════════════════════════╗
║  Airflow & MLflow Configuration Check                   ║
╚══════════════════════════════════════════════════════════╝

Checking shared database configuration...

✓ DATABASE_URL is set
  postgresql+psycopg2://user:****@host:5432/dbname?sslmode=require

All services (Backend, Airflow, MLflow) use the same DATABASE_URL.
Each service creates its own tables in the shared database.

──────────────────────────────────────────────────────────

Checking Airflow configuration...

✓ _AIRFLOW_WWW_USER_USERNAME is set
✓ _AIRFLOW_WWW_USER_PASSWORD is set

──────────────────────────────────────────────────────────

Checking MLflow configuration...

✓ MLFLOW_TRACKING_URI is set
✓ MLFLOW_S3_ENDPOINT_URL is set

──────────────────────────────────────────────────────────

Checking MinIO configuration (for MLflow artifacts)...

✓ AWS_ACCESS_KEY_ID is set
✓ AWS_SECRET_ACCESS_KEY is set

══════════════════════════════════════════════════════════

✓ All required environment variables are configured!

Next steps:
  1. Run: ./start-webapp.sh
  2. Services will auto-create their tables on first run
```

### Step 3: Start Services

```bash
./start-webapp.sh
```

On first run:
- Airflow will create its tables (alembic_version, dag, dag_run, etc.)
- MLflow will create its tables (mlflow_experiment, mlflow_run, etc.)
- Backend uses its existing tables

## 🌐 Access Your Services

After starting:

| Service | URL | Credentials |
|---------|-----|-------------|
| Backend API | http://localhost:8000 | N/A |
| Airflow UI | http://localhost:8080 | airflow / airflow |
| MLflow UI | http://localhost:5500 | (no login) |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |

## 📋 Database Table Overview

After all services start, your database will have:

### Backend Tables (existing)
- `users`
- `portfolios`
- `trades`
- `market_data`
- `strategies`
- etc.

### Airflow Tables (auto-created)
- `alembic_version` - Airflow DB version
- `dag` - DAG definitions
- `dag_run` - DAG execution history
- `task_instance` - Task execution history
- `log` - Airflow logs
- `job` - Airflow jobs
- And 20+ other Airflow tables

### MLflow Tables (auto-created)
- `mlflow_experiment` - ML experiments
- `mlflow_run` - Experiment runs
- `mlflow_metric` - Metrics
- `mlflow_param` - Parameters
- `mlflow_tag` - Tags
- `mlflow_artifact` - Artifact metadata
- And 10+ other MLflow tables

**Total:** ~50-60 tables in one database (no conflicts!)

## ✅ Benefits

### Before (Separate Databases)
```
❌ Need to create 'airflow' database
❌ Need to create 'mlflow' database
❌ Configure AIRFLOW_DATABASE_URL
❌ Configure MLFLOW_DATABASE_URL
❌ Manage 3 separate databases
❌ More complex setup
❌ More things that can go wrong
```

### After (Shared Database)
```
✅ Only configure DATABASE_URL once
✅ No database creation needed
✅ Services auto-create their tables
✅ Single database to manage
✅ Simpler configuration
✅ Fewer things to go wrong
✅ Just works!
```

## 🔍 Verifying Tables Were Created

After starting services, you can check the database:

```bash
# Using psql
psql "$DATABASE_URL"

# List all tables
\dt

# You should see tables from all three services:
# • Backend tables (your existing tables)
# • Airflow tables (dag, dag_run, task_instance, etc.)
# • MLflow tables (mlflow_experiment, mlflow_run, etc.)

# Exit
\q
```

## 🐛 Troubleshooting

### Issue: "DATABASE_URL not configured"

**Solution:** Add DATABASE_URL to your .env file:
```bash
DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname?sslmode=require
```

### Issue: "Permission denied to create tables"

**Solution:** Ensure your database user has CREATE permissions:
```sql
GRANT CREATE ON DATABASE your_database TO your_user;
```

### Issue: "Table already exists"

**Solution:** This is fine! It means the service already initialized before.
Services handle existing tables gracefully.

### Issue: Airflow webserver won't start

**Possible causes:**
1. First-time initialization (takes 30-90 seconds)
2. Database connection failed

**Check logs:**
```bash
docker logs ibkr-airflow-webserver
```

### Issue: MLflow UI shows no data

**Possible causes:**
1. MLflow hasn't created tables yet (start MLflow container)
2. No experiments created yet (this is normal for fresh install)

**Check logs:**
```bash
docker logs ibkr-mlflow-server
```

## 📊 Migration from Separate Databases

If you previously had separate databases:

### Option 1: Start Fresh (Recommended)
1. Update to use shared DATABASE_URL
2. Start services
3. Services will create new tables
4. Old data in separate databases is not migrated (start fresh)

### Option 2: Migrate Data (Advanced)
1. Export data from old airflow/mlflow databases
2. Import into shared database
3. Update DATABASE_URL
4. Start services

Most users should just start fresh (Option 1).

## 📚 Related Documentation

- **Quick Start**: `READ_ME_FIRST_AIRFLOW_MLFLOW.md`
- **Original Fix**: `FIX_AIRFLOW_INIT_ERROR.md`
- **Complete Guide**: `AIRFLOW_MLFLOW_ALL_FIXES_COMPLETE.md`
- **Quick Reference**: `AIRFLOW_MLFLOW_QUICK_REFERENCE.md`

## 🎯 Summary

✅ **One database for all services**  
✅ **No separate database creation**  
✅ **Auto-creates tables on first run**  
✅ **Simpler configuration**  
✅ **Fewer things to manage**  
✅ **Just works!**  

---

**Run `./setup-databases-quick.sh` to get started!**

The simplified setup is ready to use. Just configure DATABASE_URL and go! 🚀

