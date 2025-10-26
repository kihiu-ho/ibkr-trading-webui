# Troubleshooting Guide

**Quick fixes for common issues when starting the webapp**

---

## Issue 1: `ModuleNotFoundError: No module named 'psycopg2'`

**Cause**: Missing PostgreSQL driver for Python 3.13

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate

# Install psycopg (for Python 3.13+)
pip install 'psycopg[binary]>=3.1.0'

# Or install psycopg2-binary (for Python < 3.13)
pip install psycopg2-binary
```

---

## Issue 2: `Cannot connect to redis://redis:6379/0`

**Cause**: Redis service not running or using wrong hostname

**Solutions**:

### Solution A: Start Redis

**Using Docker**:
```bash
docker run -d --name ibkr-redis -p 6379:6379 redis:7-alpine
```

**Using Homebrew**:
```bash
brew install redis
brew services start redis
```

### Solution B: Update Configuration

Edit `.env` and change:
```bash
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

**Verify Redis is running**:
```bash
redis-cli ping
# Should return: PONG
```

---

## Issue 3: `Docker is not running`

**Cause**: Docker Desktop is not started

**Solution**:

1. **Start Docker Desktop**:
   - Open Docker Desktop from Applications
   - Wait for it to fully start (whale icon in menu bar)

2. **Verify Docker is running**:
   ```bash
   docker info
   ```

3. **Alternative - Use Homebrew** (if you don't want Docker):
   ```bash
   brew install postgresql@15 redis
   brew services start postgresql@15
   brew services start redis
   createdb ibkr_trading
   ```

---

## Issue 4: Database Connection Error

**Symptoms**:
- `connection refused` to localhost:5432
- `database "ibkr_trading" does not exist`

**Solutions**:

### Check if PostgreSQL is running

```bash
# Check if port 5432 is in use
lsof -i :5432

# If nothing, start PostgreSQL
docker run -d --name ibkr-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=ibkr_trading -p 5432:5432 postgres:15

# Or with Homebrew
brew services start postgresql@15
```

### Create database if missing

```bash
# Using Docker
docker exec ibkr-postgres psql -U postgres -c "CREATE DATABASE ibkr_trading"

# Using Homebrew
createdb ibkr_trading

# Initialize schema
psql -h localhost -U postgres -d ibkr_trading -f database/init.sql
```

---

## Issue 5: Port Already in Use

**Symptoms**:
- `Address already in use` on port 8000, 5432, or 6379

**Solution**:

### Find and kill process using the port

```bash
# For port 8000 (Backend)
lsof -ti :8000 | xargs kill -9

# For port 5432 (PostgreSQL)
lsof -ti :5432 | xargs kill -9

# For port 6379 (Redis)
lsof -ti :6379 | xargs kill -9
```

### Use different port

Edit `.env`:
```bash
BACKEND_PORT=8001  # Use different port
```

---

## Issue 6: Docker Backend Warning (False Positive)

**Symptoms**:
```
Warning: Some related processes still running:
/Applications/Docker.app/Contents/MacOS/com.docker.backend
```

**This is FIXED**: The `stop-webapp.sh` script now ignores Docker Desktop processes.

If you still see webapp processes, force kill:
```bash
pkill -9 -f "uvicorn.*backend.main"
pkill -9 -f "celery.*backend.celery_app"
```

---

## Issue 7: Virtual Environment Activation Failed

**Symptoms**:
- `command not found: python`
- `No module named 'uvicorn'`

**Solution**:

```bash
# Delete old venv
rm -rf venv

# Create new venv with Python 3.13
python3 -m venv venv

# Activate
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
```

---

## Issue 8: `.env` File Not Found

**Solution**:

```bash
# Create from example
cp .env.example .env

# Or create manually
cat > .env << 'EOF'
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ibkr_trading
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
IBKR_ACCOUNT_ID=DU1234567
OPENAI_API_KEY=your_key_here
EOF
```

---

## Issue 9: Frontend Not Loading

**Symptoms**:
- Blank page
- 404 errors

**Solutions**:

### Verify backend is running

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check logs
tail -f logs/backend.log
```

### Clear browser cache

- Hard refresh: Cmd+Shift+R (macOS) or Ctrl+Shift+R (Windows)
- Or open in incognito/private window

---

## Issue 10: Celery Tasks Not Running

**Symptoms**:
- Workflows stuck in "pending" status
- "Cannot connect to redis" in logs

**Solutions**:

### Check Celery worker is running

```bash
# Check process
ps aux | grep celery

# Check logs
tail -f logs/celery.log
```

### Restart Celery worker

```bash
./stop-webapp.sh
./start-webapp.sh
```

### Verify Redis connection

```bash
# Test Redis
redis-cli ping

# Check Redis is listening
lsof -i :6379
```

---

## Issue 11: Environment Variables Not Loading After `.env` Changes

**Symptoms**:
- Changed `DATABASE_URL` or other variables in `.env`
- Services still use old values
- Backend shows errors like: `Got: your_database_url`

**Root Cause**: Docker Compose caches environment variables. Running `docker-compose restart` doesn't reload `.env` changes.

**Solution**: Use the reload script to properly recreate containers:

```bash
# Quick reload after .env changes
./reload-env.sh
```

**Manual Steps** (if script not available):
```bash
# Stop containers (but keep volumes/network)
docker-compose down

# Recreate containers with new environment
docker-compose up -d

# Verify new values loaded
docker-compose exec backend printenv DATABASE_URL
```

**When to Reload**:
- ✅ After changing `DATABASE_URL`
- ✅ After updating `OPENAI_API_KEY`
- ✅ After modifying any variable in `.env`
- ❌ After code changes (just restart: `docker-compose restart`)

**Verification**:
```bash
# Check environment variable inside container
docker-compose exec backend printenv DATABASE_URL

# Should match your .env file (not cached values)
```

**See Also**: `ENV_RELOAD_GUIDE.md` for detailed documentation

---

## Complete Clean Restart

If all else fails:

```bash
# 1. Stop everything
./stop-webapp.sh
docker stop ibkr-postgres ibkr-redis 2>/dev/null || true

# 2. Clean up
rm -rf venv logs/*.log

# 3. Start fresh
./start-services.sh  # Start Docker services
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
./start-webapp.sh
```

---

## Quick Diagnostics

Run this to check all services:

```bash
#!/bin/bash
echo "=== Service Status ==="
echo ""

# Python version
echo "Python: $(python3 --version)"

# Virtual environment
if [ -d "venv" ]; then
    echo "✓ Virtual environment exists"
else
    echo "✗ Virtual environment missing"
fi

# PostgreSQL
if lsof -i :5432 > /dev/null 2>&1; then
    echo "✓ PostgreSQL running on port 5432"
else
    echo "✗ PostgreSQL not running"
fi

# Redis
if lsof -i :6379 > /dev/null 2>&1; then
    echo "✓ Redis running on port 6379"
else
    echo "✗ Redis not running"
fi

# Backend
if lsof -i :8000 > /dev/null 2>&1; then
    echo "✓ Backend running on port 8000"
else
    echo "✗ Backend not running"
fi

# .env file
if [ -f ".env" ]; then
    echo "✓ .env file exists"
else
    echo "✗ .env file missing"
fi

# Test connections
echo ""
echo "=== Testing Connections ==="
redis-cli ping 2>/dev/null && echo "✓ Redis: PONG" || echo "✗ Redis: Not responding"
psql -h localhost -U postgres -d ibkr_trading -c "SELECT 1" > /dev/null 2>&1 && echo "✓ PostgreSQL: Connected" || echo "✗ PostgreSQL: Cannot connect"
curl -s http://localhost:8000/health > /dev/null && echo "✓ Backend: Healthy" || echo "✗ Backend: Not responding"
```

Save as `check-services.sh`, make executable with `chmod +x check-services.sh`, and run `./check-services.sh`.

---

## Getting Help

If issues persist:

1. **Check logs**:
   ```bash
   tail -f logs/backend.log
   tail -f logs/celery.log
   ```

2. **Run diagnostics**:
   ```bash
   ./check-services.sh
   ```

3. **Review documentation**:
   - `SETUP_DEPENDENCIES.md` - Service setup
   - `STARTUP_GUIDE.md` - Startup scripts
   - `FINAL_IMPLEMENTATION_SUMMARY.md` - Complete overview

4. **Create GitHub issue** with:
   - Error messages
   - Output from `check-services.sh`
   - Contents of `logs/*.log`

---

**Most Common Fix**: Start the required services first!
```bash
./start-services.sh  # or use Homebrew
./start-webapp.sh
```

