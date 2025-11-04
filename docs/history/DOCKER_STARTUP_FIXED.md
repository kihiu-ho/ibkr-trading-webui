# Docker Startup Issue - Fixed!

## Problem

When running `./start-webapp.sh` immediately after opening Docker Desktop, you got:
```
ℹ Docker not available, checking for local PostgreSQL and Redis...
✗ PostgreSQL is not running
```

**Root Cause**: Docker Desktop takes 10-30 seconds to fully start, and the script ran before Docker was ready.

---

## ✅ Fixes Applied

### 1. Added Docker Readiness Check

The script now waits up to 20 seconds for Docker to be ready:

```bash
# Checks Docker every 2 seconds for up to 20 seconds
# Shows "Waiting for Docker to be ready..." message
```

### 2. Created Helper Script

**`wait-for-docker.sh`** - Wait for Docker to be fully ready

```bash
./wait-for-docker.sh
# Waits up to 60 seconds, shows progress
# Then tells you when Docker is ready
```

---

## 🚀 Recommended Workflow

### Option 1: Wait Helper (Easiest)

```bash
# 1. Start Docker Desktop
open -a Docker

# 2. Run the wait helper
./wait-for-docker.sh

# 3. When it says "Docker is ready", run:
./start-webapp.sh
```

### Option 2: Manual Check

```bash
# 1. Start Docker Desktop
open -a Docker

# 2. Check if Docker is ready
docker ps
# If this works without error, Docker is ready

# 3. Run the script
./start-webapp.sh
```

### Option 3: Automatic Wait (Built-in)

```bash
# 1. Start Docker Desktop
open -a Docker

# 2. Wait 20-30 seconds, then run:
./start-webapp.sh
# The script will now wait for Docker to be ready!
```

---

## 🔍 How to Check Docker Status

### Quick Check
```bash
docker ps
```
- **If it works**: Docker is ready ✓
- **If error**: Docker still starting ⏳

### Detailed Check
```bash
docker info
```
Shows full Docker system info when ready.

### Visual Check
Look at your macOS menu bar:
- 🐳 **Whale icon with progress bar** = Starting ⏳
- 🐳 **Solid whale icon** = Ready ✓
- Click the icon to see status

---

## 📊 What the Script Does Now

### Before (Old Behavior)
```
Check Docker → Not ready → Fail immediately ✗
```

### After (New Behavior)
```
Check Docker → Not ready → Wait up to 20 seconds → Recheck → Success ✓
```

**New Flow**:
```
1. Checks if Docker is installed
2. Tries docker info
3. If fails, shows "Waiting for Docker to be ready..."
4. Retries every 2 seconds for up to 20 seconds
5. If ready → Uses Docker
6. If still not ready → Falls back to checking Homebrew services
```

---

## ⏱️ Typical Timing

| Action | Time |
|--------|------|
| Open Docker Desktop | 0s |
| Docker starts responding | 10-20s |
| Docker fully operational | 20-30s |
| **Total wait time** | **~30 seconds** |

---

## 🎬 Complete Example

```bash
# Terminal output you'll see:

$ open -a Docker
# (Wait a moment)

$ ./start-webapp.sh
==================================
IBKR Trading WebUI Startup
==================================

💡 Tip: For easiest setup, start Docker Desktop first!

✓ Python 3 found: Python 3.13.5
✓ Virtual environment activated
✓ Dependencies installed/updated
✓ Found .env file

Starting required services (PostgreSQL & Redis)...

ℹ Waiting for Docker to be ready...    # ← NEW!
✓ Docker is ready                       # ← NEW!
✓ Docker is available
ℹ Starting PostgreSQL and Redis via Docker...
✓ PostgreSQL is ready
✓ Redis is ready

Starting webapp services...

✓ Backend started (PID: 12345)
✓ Celery worker started (PID: 12346)

📦 Using Docker services:
  PostgreSQL:  Docker container (ibkr-postgres)
  Redis:       Docker container (ibkr-redis)

🌐 Access the application:
  Workflows:    http://localhost:8000/workflows  ⭐
```

---

## 🐛 Troubleshooting

### Docker Still Not Ready After 20 Seconds

**Run the wait helper**:
```bash
./wait-for-docker.sh
# Waits up to 60 seconds
```

### Docker Desktop Won't Start

1. **Restart Docker Desktop**:
   ```bash
   killall Docker
   open -a Docker
   ```

2. **Check Docker Desktop Status**:
   - Click whale icon in menu bar
   - Should say "Docker Desktop is running"

3. **Reinstall if needed**:
   - Download from: https://www.docker.com/products/docker-desktop

### Still Getting "Docker not available"

**Use Homebrew services instead**:
```bash
brew services start postgresql@15 redis
./start-webapp.sh
```

---

## 📝 New Scripts

### `wait-for-docker.sh`
Waits for Docker to be ready (up to 60 seconds)

**Usage**:
```bash
./wait-for-docker.sh
```

**Output**:
```
Waiting for Docker Desktop to be ready...

Docker Desktop is starting...
This usually takes 10-30 seconds

..........
✓ Docker is ready!

Docker version 24.0.6, build ed223bc

You can now run: ./start-webapp.sh
```

---

## 🎯 Best Practice

**The safest workflow**:

```bash
# 1. Start Docker
open -a Docker

# 2. Wait for confirmation
./wait-for-docker.sh

# 3. Start webapp
./start-webapp.sh
```

**OR just wait ~30 seconds after opening Docker**, then run:
```bash
./start-webapp.sh
```

The script now handles the waiting automatically!

---

## Summary

✅ **Built-in wait mechanism** (up to 20 seconds)  
✅ **Helper script** for longer waits (`wait-for-docker.sh`)  
✅ **Better error messages** explaining what to do  
✅ **Automatic fallback** to Homebrew if Docker not ready  

**Just give Docker 20-30 seconds to start, then everything works!** 🎉

