# ✨ One Command Start - Simplified!

**The startup scripts have been combined for the ultimate simplicity!**

---

## 🚀 Just One Command!

```bash
./start-webapp.sh
```

**That's it!** This single command now:

1. ✅ Checks if Docker is running
2. ✅ If Docker available → Starts PostgreSQL & Redis in containers
3. ✅ If Docker not available → Uses local Homebrew services
4. ✅ Starts FastAPI backend
5. ✅ Starts Celery worker
6. ✅ Shows all access URLs

---

## 🎯 How It Works

### Automatic Service Detection

The script intelligently decides what to use:

```
┌─────────────────────────────────────────┐
│  Is Docker Desktop running?             │
└─────────────────┬───────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
        YES               NO
         │                 │
         ▼                 ▼
  Use Docker       Check Homebrew
  Containers         Services
         │                 │
         │                 │
         ▼                 ▼
   PostgreSQL         PostgreSQL
   Redis (Docker)     Redis (Homebrew)
         │                 │
         └────────┬────────┘
                  │
                  ▼
           Start Webapp
        (Backend + Celery)
```

---

## 📋 Prerequisites

Choose **ONE** of these:

### Option A: Docker (Recommended)
- ✅ Docker Desktop installed and running
- ❌ No need for PostgreSQL or Redis installation

### Option B: Homebrew
- ✅ PostgreSQL installed: `brew install postgresql@15`
- ✅ Redis installed: `brew install redis`
- ✅ Services running: `brew services start postgresql@15 redis`
- ❌ No need for Docker

**The script will use whichever is available!**

---

## 🎬 Quick Start

### With Docker (Easiest)

```bash
# 1. Start Docker Desktop (from Applications)

# 2. Run one command
./start-webapp.sh

# 3. Open browser
open http://localhost:8000/workflows
```

### With Homebrew

```bash
# 1. Install services (one-time)
brew install postgresql@15 redis

# 2. Start services
brew services start postgresql@15 redis

# 3. Create database (one-time)
createdb ibkr_trading

# 4. Run one command
./start-webapp.sh

# 5. Open browser
open http://localhost:8000/workflows
```

---

## 🛑 Stopping Services

### Stop Webapp Only (Keep DB Running)

```bash
./stop-webapp.sh
```

This stops the backend and worker but keeps PostgreSQL/Redis running for fast restart.

### Stop Everything

```bash
# With Docker
./stop-all.sh

# With Homebrew
./stop-webapp.sh
brew services stop postgresql@15 redis
```

---

## 🔄 Switching Between Docker and Homebrew

The script automatically detects what's available!

**To switch from Homebrew to Docker**:
```bash
# Stop Homebrew services
brew services stop postgresql@15 redis

# Start Docker Desktop
open -a Docker

# Run (will auto-use Docker)
./start-webapp.sh
```

**To switch from Docker to Homebrew**:
```bash
# Stop Docker containers
docker-compose -f docker-compose.services.yml down

# Ensure Homebrew services are running
brew services start postgresql@15 redis

# Run (will auto-use Homebrew)
./start-webapp.sh
```

---

## 📊 What You'll See

### Starting with Docker

```
==================================
IBKR Trading WebUI Startup
==================================

✓ Python 3 found: Python 3.13.5
✓ Virtual environment activated
✓ Dependencies installed/updated
✓ Found .env file

Starting required services (PostgreSQL & Redis)...

✓ Docker is available
ℹ Starting PostgreSQL and Redis via Docker...
ℹ Waiting for services to be ready...
✓ PostgreSQL is ready
✓ Redis is ready

Starting webapp services...

✓ Backend started (PID: 12345)
✓ Celery worker started (PID: 12346)

==================================
✓ All services started successfully!
==================================

📦 Using Docker services:
  PostgreSQL:  Docker container (ibkr-postgres)
  Redis:       Docker container (ibkr-redis)

🌐 Access the application:

  Workflows:    http://localhost:8000/workflows  ⭐
  Dashboard:    http://localhost:8000/dashboard
  API Docs:     http://localhost:8000/docs
```

### Starting with Homebrew

```
==================================
IBKR Trading WebUI Startup
==================================

✓ Python 3 found: Python 3.13.5
✓ Virtual environment activated
✓ Dependencies installed/updated
✓ Found .env file

Starting required services (PostgreSQL & Redis)...

ℹ Docker not available, checking for local PostgreSQL and Redis...
✓ PostgreSQL is running on port 5432
✓ Redis is running on port 6379

Starting webapp services...

✓ Backend started (PID: 12345)
✓ Celery worker started (PID: 12346)

==================================
✓ All services started successfully!
==================================

🏠 Using local services:
  PostgreSQL:  localhost:5432 (Homebrew)
  Redis:       localhost:6379 (Homebrew)

🌐 Access the application:

  Workflows:    http://localhost:8000/workflows  ⭐
  Dashboard:    http://localhost:8000/dashboard
  API Docs:     http://localhost:8000/docs
```

---

## 🐛 Troubleshooting

### "PostgreSQL is not running"

**If you want to use Docker**:
```bash
# Start Docker Desktop
open -a Docker
# Wait for it to start, then run again
./start-webapp.sh
```

**If you want to use Homebrew**:
```bash
brew services start postgresql@15
./start-webapp.sh
```

### "Redis is not running"

**If you want to use Docker**:
```bash
open -a Docker
./start-webapp.sh
```

**If you want to use Homebrew**:
```bash
brew install redis
brew services start redis
./start-webapp.sh
```

### Docker containers won't start

```bash
# Check Docker is running
docker ps

# Clean up old containers
docker-compose -f docker-compose.services.yml down

# Try again
./start-webapp.sh
```

---

## ℹ️ About the Scripts

### What Happened to `start-docker-services.sh`?

It still exists! But you don't need it anymore because `start-webapp.sh` now does everything automatically.

**You can still use it** if you want to start only Docker services:
```bash
./start-docker-services.sh  # Start Docker services only
```

But most users will just use:
```bash
./start-webapp.sh  # Does everything!
```

### Script Responsibilities

| Script | What It Does |
|--------|--------------|
| `start-webapp.sh` | ⭐ **All-in-one**: Starts services + webapp |
| `start-docker-services.sh` | Docker services only (optional) |
| `stop-webapp.sh` | Stop webapp, keep DB running |
| `stop-all.sh` | Stop everything including Docker |
| `check-services.sh` | Diagnose what's running |

---

## 🎉 Summary

**Before**: Multiple scripts, confusing setup, manual service management

**After**: 
```bash
./start-webapp.sh
```

**One command. Everything starts. Automatically. Done.** ✨

---

## 📚 More Info

- **Quick Reference**: `cat START_NOW.txt`
- **Complete Guide**: `FINAL_SETUP_GUIDE.md`
- **All Fixes**: `ALL_FIXES_SUMMARY.md`
- **Docker Details**: `DOCKER_INTEGRATED.md`

---

**Just run `./start-webapp.sh` and you're good to go!** 🚀

