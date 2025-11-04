# ⚡ Quick Fix: Database Setup Script

## Problem You Had

```
psql: error: connection to server on socket "/tmp/.s.PGSQL.5432" failed
```

## ✅ It's Fixed!

The `setup-databases-quick.sh` script now works correctly with external PostgreSQL databases.

## Run This Now

```bash
./setup-databases-quick.sh
```

The script will:
1. ✅ Detect your DATABASE_URL automatically
2. ✅ Extract username, password, host correctly
3. ✅ Create AIRFLOW_DATABASE_URL in .env
4. ✅ Create MLFLOW_DATABASE_URL in .env
5. ✅ Offer to create databases automatically
6. ✅ Connect to the RIGHT database (not localhost!)

## What You'll See

```bash
✓ Backend DATABASE_URL is already configured
  Detected connection: myuser@ep-xxx.us-east-1.aws.neon.tech:5432
  Existing database: ibkr_trading
  Will create: airflow, mlflow (in same server)

✓ Added AIRFLOW_DATABASE_URL to .env
✓ Added MLFLOW_DATABASE_URL to .env

Would you like to create the databases now? (y/N)
> y

Creating databases...
Connecting to: postgresql://myuser:****@ep-xxx.aws.neon.tech:5432/postgres?sslmode=require

✓ Databases created successfully!

You can now start the services:
  ./start-webapp.sh
```

## If It Still Doesn't Work

### Option 1: Create Databases Manually (Neon)
1. Go to https://neon.tech
2. Select your project
3. Click "Databases" tab
4. Create database: `airflow`
5. Create database: `mlflow`
6. Run: `./start-webapp.sh`

### Option 2: Create via psql
```bash
# Get your connection string from .env
cat .env | grep DATABASE_URL

# Connect (replace with your actual connection string)
psql "postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech:5432/postgres?sslmode=require"

# Create databases
CREATE DATABASE airflow;
CREATE DATABASE mlflow;

# Verify
\l

# Exit
\q
```

## Verify Configuration

```bash
./scripts/check-env-airflow-mlflow.sh
```

Should show:
```
✓ AIRFLOW_DATABASE_URL is set
✓ MLFLOW_DATABASE_URL is set
✓ All required environment variables are configured!
```

## Then Start Everything

```bash
./start-webapp.sh
```

## What Was Fixed

### Before (Broken)
- Tried to connect to `/tmp/.s.PGSQL.5432` (local socket)
- Used empty variables
- No error messages

### After (Working)
- Extracts all details from DATABASE_URL
- Connects to actual external database
- Shows clear status messages
- Masks passwords for security

## Technical Details

If you want to know exactly what was fixed, see:
- **Full Details**: `DATABASE_SETUP_SCRIPT_FIXED.md`
- **User Guide**: `SETUP_SCRIPT_FIX_COMPLETE.md`
- **OpenSpec**: `openspec/changes/fix-database-setup-script/`

## That's It!

Just run `./setup-databases-quick.sh` and follow the prompts. The script is now smart enough to handle external databases correctly.

---

**TL;DR:**
```bash
./setup-databases-quick.sh    # Fix configuration
./start-webapp.sh              # Start everything
```

🎉 Done!
