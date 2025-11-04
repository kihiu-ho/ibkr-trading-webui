# Quick Fix: PostgreSQL Container Error

## ✅ Problem Fixed!

The `ibkr-postgres` container error has been resolved. The system now uses external PostgreSQL databases.

## 🚀 Quick Setup (3 Steps)

### Step 1: Create Databases

Connect to your PostgreSQL instance and run:

```sql
CREATE DATABASE airflow;
CREATE DATABASE mlflow;
```

### Step 2: Update .env File

Add these two lines to your `.env` file:

```bash
# Use your actual PostgreSQL connection details
AIRFLOW_DATABASE_URL=postgresql+psycopg2://user:password@host:port/airflow?sslmode=require
MLFLOW_DATABASE_URL=postgresql+psycopg2://user:password@host:port/mlflow?sslmode=require
```

**Example for Neon:**
```bash
AIRFLOW_DATABASE_URL=postgresql+psycopg2://myuser:mypass@ep-xxx.us-east-1.aws.neon.tech/airflow?sslmode=require
MLFLOW_DATABASE_URL=postgresql+psycopg2://myuser:mypass@ep-xxx.us-east-1.aws.neon.tech/mlflow?sslmode=require
```

### Step 3: Start Services

```bash
./start-webapp.sh
```

## ✅ What Changed

- ✅ No more `ibkr-postgres` container
- ✅ All services use external PostgreSQL
- ✅ More reliable and production-ready

## 📋 Database Summary

You need **3 databases** total:
1. **ibkr_trading** (or your custom name) - Backend (already configured via DATABASE_URL)
2. **airflow** (new) - Airflow metadata
3. **mlflow** (new) - MLflow experiments

All three can be in the same PostgreSQL instance.

## 🔍 Verify It Works

```bash
# Check services are running
docker-compose ps

# You should NOT see ibkr-postgres
# All other services should be Up/Healthy
```

## 📚 Full Documentation

- **Database Setup Guide**: `DATABASE_SETUP_AIRFLOW_MLFLOW.md`
- **Complete Migration Info**: `EXTERNAL_POSTGRES_MIGRATION_COMPLETE.md`

## ❓ Common Issues

### "database does not exist"
→ Create the database: `CREATE DATABASE airflow;`

### "variable is not set"
→ Add `AIRFLOW_DATABASE_URL` and `MLFLOW_DATABASE_URL` to `.env`

### "password authentication failed"
→ Check credentials and URL-encode special characters

---

**That's it!** The error is fixed. Just create the databases and update your `.env` file.

