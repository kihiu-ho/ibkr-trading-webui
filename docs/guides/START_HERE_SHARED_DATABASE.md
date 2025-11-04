# ⚡ Start Here: Shared Database Setup

## 🎯 What You Need to Know

**All services (Backend, Airflow, MLflow) now share ONE database!**

No more:
- ~~Creating separate `airflow` database~~ ❌
- ~~Creating separate `mlflow` database~~ ❌
- ~~Configuring `AIRFLOW_DATABASE_URL`~~ ❌
- ~~Configuring `MLFLOW_DATABASE_URL`~~ ❌

Just configure `DATABASE_URL` and you're done! ✅

## 🚀 Quick Start (2 Commands)

```bash
# 1. Verify configuration
./setup-databases-quick.sh

# 2. Start all services
./start-webapp.sh
```

## 📝 Your .env File

Only need this for database:

```bash
# One database URL for all services
DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname?sslmode=require

# Airflow credentials (optional, has defaults)
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
```

## 🎓 What Happens

### On First Start

Services auto-create their tables in the shared database:

1. **Backend** - Uses existing tables (users, trades, etc.)
2. **Airflow** - Creates ~30 tables (dag, dag_run, task_instance, etc.)
3. **MLflow** - Creates ~15 tables (mlflow_run, mlflow_experiment, etc.)

Total: ~50-60 tables in one database, all working together! ✅

### On Subsequent Starts

Services detect their existing tables and start normally. No re-initialization needed.

## 🌐 Access Services

After `./start-webapp.sh`:

| Service | URL | Login |
|---------|-----|-------|
| Backend | http://localhost:8000 | N/A |
| Airflow | http://localhost:8080 | airflow / airflow |
| MLflow | http://localhost:5500 | (no login) |
| MinIO | http://localhost:9001 | minioadmin / minioadmin |

## ✅ Verification

Check configuration:
```bash
./scripts/check-env-airflow-mlflow.sh
```

Expected output:
```
✓ DATABASE_URL is set
  postgresql+psycopg2://user:****@host:5432/dbname

All services (Backend, Airflow, MLflow) use the same DATABASE_URL.
Each service creates its own tables in the shared database.

✓ All required environment variables are configured!
```

## 📊 Architecture

```
┌───────────────────────────────────────┐
│  Your .env File                       │
│  DATABASE_URL=postgresql+psycopg2://  │
└────────────────┬──────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────┐
│  PostgreSQL Database                   │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ Backend Tables                   │ │
│  │ Airflow Tables (30+)             │ │
│  │ MLflow Tables (15+)              │ │
│  └──────────────────────────────────┘ │
│                                        │
│  All services share one database! ✅   │
└────────────────────────────────────────┘
```

## 🐛 Troubleshooting

### "DATABASE_URL not configured"
```bash
# Add to .env file:
DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname?sslmode=require
```

### "Permission denied"
```sql
-- Grant CREATE permission:
GRANT CREATE ON DATABASE your_db TO your_user;
```

### Airflow slow to start
**Normal!** First start takes 30-90 seconds while creating tables.

### Want to see the tables?
```bash
psql "$DATABASE_URL"
\dt
# You'll see tables from Backend, Airflow, and MLflow
\q
```

## 📖 Documentation

- **This file** - Quick start (you are here!)
- **SHARED_DATABASE_SETUP.md** - Complete guide
- **SIMPLIFIED_SETUP_COMPLETE.md** - What changed
- **AIRFLOW_MLFLOW_QUICK_REFERENCE.md** - Command reference

## 🎉 Benefits

✅ **50% simpler** - One DATABASE_URL vs three  
✅ **Auto-setup** - No manual database creation  
✅ **Auto-tables** - Services create their own tables  
✅ **One database** - Easier to manage and backup  
✅ **Just works** - Configure once, forget about it  

## 🚀 Ready?

```bash
./setup-databases-quick.sh
./start-webapp.sh
```

Open http://localhost:8080 for Airflow UI!

---

**That's it!** Configure `DATABASE_URL`, run two commands, done! 🎉

