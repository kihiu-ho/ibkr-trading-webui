# Database Setup Script Fix - Complete ✅

## ✅ Problem Solved!

The `setup-databases-quick.sh` script now works correctly with external PostgreSQL databases.

## What Was Wrong

**Error:** Script tried to connect to local socket instead of external database
```
psql: error: connection to server on socket "/tmp/.s.PGSQL.5432" failed
```

**Cause:** Connection string parsing was broken - variables were empty when building psql connection.

## What Was Fixed

### 1. Connection String Parsing ✅
- **Before:** Simple regex that missed details
- **After:** Robust parsing that extracts username, password, host:port, database, SSL mode

### 2. psql Connection ✅
- **Before:** Connected to localhost (empty variables)
- **After:** Connects to correct external database with all details

### 3. Error Handling ✅
- **Before:** Cryptic psql errors
- **After:** Clear messages explaining possible causes

### 4. User Experience ✅
- **Before:** No feedback on what's happening
- **After:** Shows connection details, masked passwords, clear status

## How to Use

### Run the Fixed Script

```bash
./setup-databases-quick.sh
```

**What it does:**

1. **Detects your database configuration:**
   ```
   ✓ Backend DATABASE_URL is already configured
     Detected connection: myuser@ep-xxx.us-east-1.aws.neon.tech:5432
     Existing database: ibkr_trading
     Will create: airflow, mlflow (in same server)
   ```

2. **Configures .env automatically:**
   ```
   ✓ Added AIRFLOW_DATABASE_URL to .env
   ✓ Added MLFLOW_DATABASE_URL to .env
   ```

3. **Offers to create databases:**
   ```
   Would you like to create the databases now? (y/N)
   > y
   
   Creating databases...
   Connecting to: postgresql://myuser:****@ep-xxx.aws.neon.tech:5432/postgres?sslmode=require
   
   Creating airflow database...
   Creating mlflow database...
   Verifying databases...
   
   ✓ Databases created successfully!
   
   You can now start the services:
     ./start-webapp.sh
   ```

## Example Output (Fixed)

```bash
$ ./setup-databases-quick.sh

╔══════════════════════════════════════════════════════════╗
║  Airflow & MLflow Database Setup Helper                 ║
╚══════════════════════════════════════════════════════════╝

✓ Backend DATABASE_URL is already configured
  Detected connection: myuser@ep-cool-fire-123.us-east-1.aws.neon.tech:5432
  Existing database: ibkr_trading
  Will create: airflow, mlflow (in same server)

────────────────────────────────────────────────────────

✓ Added AIRFLOW_DATABASE_URL to .env
✓ Added MLFLOW_DATABASE_URL to .env

────────────────────────────────────────────────────────

Next Steps:

1. Create the databases in PostgreSQL:
   psql "postgresql://myuser:****@ep-cool-fire-123.us-east-1.aws.neon.tech:5432/postgres?sslmode=require"

   Then run:
   CREATE DATABASE airflow;
   CREATE DATABASE mlflow;
   \q

2. Or if using Neon, create databases via web UI at https://neon.tech

3. Start the services:
   ./start-webapp.sh

────────────────────────────────────────────────────────

Would you like to create the databases now? (y/N)
> y

Creating databases...

Connecting to: postgresql://myuser:****@ep-cool-fire-123.us-east-1.aws.neon.tech:5432/postgres?sslmode=require

Creating airflow database...
Creating mlflow database...
Verifying databases...

 Database Created 
------------------
 airflow
 mlflow
(2 rows)

✓ Databases created successfully!

You can now start the services:
  ./start-webapp.sh

Configuration complete!
```

## If Automatic Creation Doesn't Work

The script now provides helpful fallback:

```
⚠ Could not create databases automatically

This might be because:
  • Databases already exist (this is fine!)
  • Connection details are incorrect
  • Network/firewall issues

Please verify manually or create via web UI:
  https://neon.tech (if using Neon)

Then start services:
  ./start-webapp.sh
```

## Manual Database Creation (Alternative)

If you prefer to create databases manually:

### For Neon Users:
1. Go to https://neon.tech
2. Select your project
3. Click "Databases"
4. Create database named `airflow`
5. Create database named `mlflow`

### Using psql:
```bash
# Connect to your PostgreSQL
psql "your_connection_string"

# Create databases
CREATE DATABASE airflow;
CREATE DATABASE mlflow;

# Verify
\l airflow
\l mlflow

# Exit
\q
```

## Verification

After running the script, verify everything:

```bash
# Check configuration
./scripts/check-env-airflow-mlflow.sh

# Should show:
# ✓ AIRFLOW_DATABASE_URL is set
# ✓ MLFLOW_DATABASE_URL is set
# ✓ All required environment variables are configured!
```

## Next Steps

1. ✅ Run: `./setup-databases-quick.sh`
2. ✅ Create databases (automatic or manual)
3. ✅ Verify: `./scripts/check-env-airflow-mlflow.sh`
4. ✅ Start: `./start-webapp.sh`

## OpenSpec Compliance

**Change ID:** `fix-database-setup-script`
- ✅ Proposal created
- ✅ All 29 tasks completed
- ✅ Validated with strict mode
- ✅ Script tested successfully

## Files Modified

1. **setup-databases-quick.sh** - Fixed connection string handling

## Files Created

1. **DATABASE_SETUP_SCRIPT_FIXED.md** - Technical details
2. **SETUP_SCRIPT_FIX_COMPLETE.md** - This summary
3. OpenSpec proposal (3 files)

## Technical Details

### Connection String Extraction

**Input:**
```
DATABASE_URL=postgresql+psycopg2://myuser:mypass@ep-abc.us-east-1.aws.neon.tech:5432/ibkr_trading?sslmode=require
```

**Extracted:**
- User: `myuser`
- Password: `mypass`
- Host: `ep-abc.us-east-1.aws.neon.tech:5432`
- Database: `ibkr_trading`
- SSL Mode: `require`

**Generated psql connection:**
```
postgresql://myuser:mypass@ep-abc.us-east-1.aws.neon.tech:5432/postgres?sslmode=require
```

This now works correctly! ✅

## Benefits

✅ **Automatic Setup** - One command to configure everything  
✅ **Smart Detection** - Extracts credentials from existing config  
✅ **External Databases** - Works with Neon, AWS RDS, etc.  
✅ **Error Recovery** - Clear messages and manual fallback  
✅ **Secure** - Masks passwords in output  

## Summary

The database setup script is now **fully functional** and can:
1. ✅ Parse DATABASE_URL correctly
2. ✅ Extract all connection components
3. ✅ Connect to external PostgreSQL
4. ✅ Create databases automatically
5. ✅ Provide helpful error messages
6. ✅ Offer manual fallback options

---

**Run `./setup-databases-quick.sh` to get started!** 🚀

The script will guide you through the entire setup process with clear feedback at every step.

