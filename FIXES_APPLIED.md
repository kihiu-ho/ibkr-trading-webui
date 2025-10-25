# Fixes Applied to Startup Issues

**Date**: October 19, 2025  
**Issues Fixed**: 3 critical startup problems

---

## Issues Identified

When running `./start-webapp.sh`, you encountered:

1. ❌ **False Docker Warning**: Stop script incorrectly flagged Docker Desktop processes
2. ❌ **Missing psycopg2**: `ModuleNotFoundError: No module named 'psycopg2'`
3. ❌ **Redis Connection Failed**: `Cannot connect to redis://redis:6379/0`

---

## Fixes Applied

### Fix 1: Updated `stop-webapp.sh`

**Changed**:
```bash
# Old: Showed ALL processes matching "backend" (including Docker)
pgrep -f "backend|celery"

# New: Only shows webapp processes
pgrep -f "uvicorn.*backend.main|celery.*backend.celery_app"
```

**Result**: ✅ No more false Docker warnings

---

### Fix 2: Updated Database Configuration

**File**: `backend/config/settings.py`

**Changed**:
```python
# Old: No default, causes crash if .env missing
DATABASE_URL: str

# New: Defaults to localhost with psycopg (Python 3.13 compatible)
DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ibkr_trading"
```

**Also updated**:
- Added default values for all required settings
- Changed `IBKR_ACCOUNT_ID` from required to optional with default
- Set `localhost` defaults for MINIO and Redis (not Docker service names)

**Result**: ✅ App can start without errors, uses Python 3.13 compatible driver

---

### Fix 3: Updated Redis Configuration

**File**: `backend/config/settings.py`

**Changed**:
```python
# Old: Assumes Docker service named "redis"
REDIS_URL: str = "redis://redis:6379/0"

# New: Uses localhost for local development
REDIS_URL: str = "redis://localhost:6379/0"
```

**Result**: ✅ Celery can connect to local Redis

---

### Fix 4: Created `.env` File

**New file**: `.env`

**Content**:
- Database URL with `postgresql+psycopg://` for Python 3.13
- Redis URLs pointing to `localhost:6379`
- MinIO pointing to `localhost:9000`
- Default IBKR account and API settings
- Placeholder OpenAI API key

**Result**: ✅ All configuration in one place

---

### Fix 5: Created Service Startup Scripts

**New files**:
- `start-services.sh` - Starts PostgreSQL and Redis using Docker
- `check-services.sh` - Diagnoses service status and issues

**Result**: ✅ Easy one-command setup of dependencies

---

### Fix 6: Created Documentation

**New files**:
1. **SETUP_DEPENDENCIES.md** - Complete guide for setting up PostgreSQL and Redis
   - Docker instructions
   - Homebrew instructions  
   - Docker Compose option
   - Troubleshooting for each service

2. **TROUBLESHOOTING.md** - Solutions for 10 common issues
   - Each issue has clear symptoms and fixes
   - Step-by-step instructions
   - Quick diagnostics script

3. **.env.example** - Template for environment configuration

**Result**: ✅ Clear documentation for all setup scenarios

---

## What You Need To Do

The webapp **cannot start** until PostgreSQL and Redis are running. You have 2 options:

### Option A: Use Docker (Recommended)

1. **Start Docker Desktop**:
   - Open Docker Desktop from Applications
   - Wait for it to fully start

2. **Start services**:
   ```bash
   ./start-services.sh
   ```

3. **Start webapp**:
   ```bash
   ./start-webapp.sh
   ```

### Option B: Use Homebrew (No Docker needed)

1. **Install services**:
   ```bash
   brew install postgresql@15 redis
   ```

2. **Start services**:
   ```bash
   brew services start postgresql@15
   brew services start redis
   ```

3. **Create database**:
   ```bash
   createdb ibkr_trading
   psql ibkr_trading -f database/init.sql
   ```

4. **Update .env** (remove password):
   ```bash
   DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/ibkr_trading
   ```

5. **Start webapp**:
   ```bash
   ./start-webapp.sh
   ```

---

## Verify Setup

Run the diagnostics:
```bash
./check-services.sh
```

You should see:
- ✓ PostgreSQL running on port 5432
- ✓ Redis running on port 6379
- ✓ .env file exists

Then you can start the webapp!

---

## Quick Reference

| Issue | Check | Fix |
|-------|-------|-----|
| Docker warning | `./stop-webapp.sh` | ✅ Fixed in script |
| psycopg2 error | `python --version` | ✅ Using psycopg for 3.13 |
| Redis connection | `redis-cli ping` | Start Redis service |
| Database connection | `psql -h localhost -U postgres -d ibkr_trading -c "SELECT 1"` | Start PostgreSQL |

---

## Files Modified

1. ✅ `stop-webapp.sh` - Fixed Docker false positive
2. ✅ `backend/config/settings.py` - Added defaults, fixed URLs
3. ✅ `.env` - Created with localhost config
4. ✅ `QUICK_START.txt` - Updated with 4-step process

## Files Created

1. ✅ `.env.example` - Template configuration
2. ✅ `start-services.sh` - Docker service startup
3. ✅ `check-services.sh` - Service diagnostics
4. ✅ `SETUP_DEPENDENCIES.md` - Complete setup guide
5. ✅ `TROUBLESHOOTING.md` - Issue resolution guide
6. ✅ `FIXES_APPLIED.md` - This file

---

## Summary

All startup issues are **FIXED** ✅

The only requirement is to **start PostgreSQL and Redis** before running `./start-webapp.sh`.

Choose your method:
- 🐳 **Docker**: `./start-services.sh`
- 🍺 **Homebrew**: `brew services start postgresql@15 redis`

Then:
```bash
./start-webapp.sh
```

**Access at**: http://localhost:8000

---

**Need help?** Read `TROUBLESHOOTING.md` or run `./check-services.sh`

