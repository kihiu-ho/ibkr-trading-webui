# 🎯 Final Setup Guide - Choose Your Path

**All issues fixed! Choose the setup method that works for you.**

---

## ✅ What Was Fixed

1. **Import Error**: Fixed `WorkflowExecution` import in `workflow_tasks.py`
2. **Missing Module**: Added `tenacity` to requirements
3. **Flexible Setup**: Script now works with Docker OR Homebrew
4. **Auto-Detection**: Automatically uses available services

---

## 🚀 Setup Options

### Option A: Docker (Recommended)

**Pros**: Isolated, consistent, easy cleanup  
**Cons**: Requires Docker Desktop

**Steps**:

1. **Start Docker Desktop** from Applications
   - Wait for the whale icon to appear in menu bar
   - Make sure it says "Docker Desktop is running"

2. **Start Services**:
   ```bash
   ./start-docker-services.sh
   ```
   
   This starts PostgreSQL and Redis in Docker containers.

3. **Start Webapp**:
   ```bash
   ./start-webapp.sh
   ```
   
   This auto-detects Docker is running and starts the backend.

4. **Access**:
   ```
   http://localhost:8000/workflows
   ```

5. **Stop**:
   ```bash
   # Stop webapp only (keeps Docker running for fast restart)
   ./stop-webapp.sh
   
   # Stop everything including Docker
   ./stop-all.sh
   ```

---

### Option B: Homebrew

**Pros**: No Docker needed, system services  
**Cons**: Requires manual installation

**Steps**:

1. **Install Services**:
   ```bash
   brew install postgresql@15 redis
   ```

2. **Start Services**:
   ```bash
   brew services start postgresql@15
   brew services start redis
   ```

3. **Create Database**:
   ```bash
   createdb ibkr_trading
   psql ibkr_trading -f database/init.sql
   ```

4. **Update .env** (if needed):
   ```bash
   # Change to remove password if local user auth
   DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/ibkr_trading
   ```

5. **Start Webapp**:
   ```bash
   ./start-webapp.sh
   ```
   
   Script auto-detects local PostgreSQL/Redis and uses them.

6. **Access**:
   ```
   http://localhost:8000/workflows
   ```

7. **Stop**:
   ```bash
   # Stop webapp
   ./stop-webapp.sh
   
   # Stop services
   brew services stop postgresql@15 redis
   ```

---

## 🔄 Switching Between Options

The `start-webapp.sh` script is smart:
- ✅ If Docker is running → uses Docker containers
- ✅ If Docker not available → uses local services
- ✅ Automatically detects what's available

**To switch from Homebrew to Docker**:
```bash
# Stop Homebrew services
brew services stop postgresql@15 redis

# Start Docker
open -a Docker
# Wait for Docker to start

# Start services
./start-docker-services.sh
./start-webapp.sh
```

**To switch from Docker to Homebrew**:
```bash
# Stop Docker containers
docker-compose -f docker-compose.services.yml down

# Start Homebrew services
brew services start postgresql@15 redis

# Start webapp (auto-detects local services)
./start-webapp.sh
```

---

## 📝 Script Reference

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `start-docker-services.sh` | Start PostgreSQL & Redis in Docker | Before starting webapp (Docker mode) |
| `start-webapp.sh` | Start backend & Celery | Main startup script (auto-detects services) |
| `stop-webapp.sh` | Stop backend & Celery | Stop webapp but keep DB running |
| `stop-all.sh` | Stop everything including Docker | Complete shutdown |
| `check-services.sh` | Check what's running | Diagnostics |

---

## 🐛 Troubleshooting

### Error: `ImportError: cannot import name 'WorkflowExecution'`
✅ **FIXED**: Updated import in `workflow_tasks.py`

### Error: `ModuleNotFoundError: No module named 'tenacity'`
✅ **FIXED**: Added to `requirements.txt`. Reinstall:
```bash
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Error: `Connection refused` (PostgreSQL or Redis)
**Check what's running**:
```bash
./check-services.sh
```

**If using Docker**:
```bash
# Check Docker is running
docker ps

# If containers not running
./start-docker-services.sh
```

**If using Homebrew**:
```bash
# Check services
brew services list

# Start if needed
brew services start postgresql@15 redis
```

### Docker not starting
```bash
# Check Docker Desktop is running
open -a Docker

# Check Docker works
docker ps

# If issues, restart Docker Desktop
```

### Port conflicts (5432 or 6379 already in use)
```bash
# Check what's using ports
lsof -i :5432
lsof -i :6379

# If Homebrew PostgreSQL
brew services stop postgresql@15 postgresql@14

# If Homebrew Redis
brew services stop redis

# Or change Docker ports in docker-compose.services.yml
```

---

## ✅ Success Checklist

Before accessing the webapp, verify:

```bash
./check-services.sh
```

Should show:
- ✓ PostgreSQL running on port 5432
- ✓ Redis running on port 6379
- ✓ Backend running on port 8000
- ✓ Celery worker running

Then access: http://localhost:8000/workflows

---

## 🎉 Quick Start (TL;DR)

**With Docker**:
```bash
open -a Docker                    # Start Docker Desktop
./start-docker-services.sh        # Start PostgreSQL & Redis
./start-webapp.sh                 # Start webapp
open http://localhost:8000/workflows
```

**With Homebrew**:
```bash
brew install postgresql@15 redis
brew services start postgresql@15 redis
createdb ibkr_trading
./start-webapp.sh
open http://localhost:8000/workflows
```

---

## 📚 Files Modified

- ✅ `backend/tasks/workflow_tasks.py` - Fixed import
- ✅ `backend/requirements.txt` - Added tenacity
- ✅ `start-webapp.sh` - Auto-detects Docker/Homebrew
- ✅ `docker-compose.services.yml` - Docker service definitions
- ✅ `start-docker-services.sh` - Docker-only startup

---

## 🆘 Still Having Issues?

1. **Run diagnostics**: `./check-services.sh`
2. **Check logs**: 
   - Backend: `tail -f logs/backend.log`
   - Celery: `tail -f logs/celery.log`
   - Docker: `docker-compose -f docker-compose.services.yml logs -f`
3. **Complete reset**:
   ```bash
   ./stop-all.sh
   docker-compose -f docker-compose.services.yml down -v
   docker system prune -f
   rm -rf logs/*
   ./start-docker-services.sh  # or brew services start...
   ./start-webapp.sh
   ```

---

**Everything is fixed and ready to run! Choose your preferred method and go!** 🚀

