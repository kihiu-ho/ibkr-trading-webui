# Startup Guide - IBKR Trading WebUI

**Date**: 2025-10-19  
**Purpose**: Easy startup scripts for backend and frontend

---

## 🚀 Quick Start (One Command)

### Option 1: Production Mode (Single Terminal)

Starts everything in one terminal with log aggregation:

```bash
./start-webapp.sh
```

**What it does**:
- ✅ Activates virtual environment
- ✅ Installs/updates dependencies
- ✅ Starts FastAPI backend (port 8000)
- ✅ Starts Celery worker
- ✅ Captures logs to `logs/` directory
- ✅ Shows live logs in terminal
- ✅ Graceful shutdown with Ctrl+C

**Output**:
```
==================================
IBKR Trading WebUI Startup
==================================

✓ Python 3 found: Python 3.11.0
✓ Virtual environment activated
✓ Dependencies installed/updated
✓ DATABASE_URL is set
✓ Found .env file

Starting services...

✓ Backend started (PID: 12345)
✓ Backend logs: logs/backend.log
✓ Celery worker started (PID: 12346)
✓ Celery logs: logs/celery.log

==================================
✓ All services started successfully!
==================================

Access the application:

  🌐 Web UI:          http://localhost:8000
  📊 Dashboard:       http://localhost:8000/dashboard
  🔄 Workflows:       http://localhost:8000/workflows
  🧠 Strategies:      http://localhost:8000/strategies
  📚 API Docs:        http://localhost:8000/docs
  🏥 Health Check:    http://localhost:8000/health

Logs:
  Backend:  tail -f logs/backend.log
  Celery:   tail -f logs/celery.log

Press Ctrl+C to stop all services
```

### Option 2: Development Mode (Multiple Tabs)

Opens 3 terminal tabs (macOS/Linux with GUI):

```bash
./start-dev.sh
```

**What it does**:
- ✅ Opens Tab 1: FastAPI backend
- ✅ Opens Tab 2: Celery worker
- ✅ Opens Tab 3: Log viewer
- ✅ Each in separate tab for easy monitoring

**Best for**:
- Development
- Debugging
- Watching logs in real-time
- Easy access to each service

---

## 🛑 Stop Services

Stop all running services:

```bash
./stop-webapp.sh
```

**What it does**:
- ✅ Gracefully stops FastAPI backend
- ✅ Gracefully stops Celery worker
- ✅ Force kills if needed
- ✅ Shows any remaining processes

**Output**:
```
Stopping IBKR Trading WebUI services...

Stopping celery.*backend.celery_app...
  Killed PID: 12346
✓ celery.*backend.celery_app stopped

Stopping uvicorn.*backend.main:app...
  Killed PID: 12345
✓ uvicorn.*backend.main:app stopped

✓ All services stopped
```

Or press **Ctrl+C** in the terminal running `start-webapp.sh`

---

## 📁 Files Created

### Main Scripts

1. **`start-webapp.sh`** - Production startup script
   - Single terminal mode
   - Log aggregation
   - Graceful shutdown
   - Health checks

2. **`start-dev.sh`** - Development mode
   - Multiple terminal tabs
   - Separate logs per service
   - macOS/Linux GUI support

3. **`stop-webapp.sh`** - Stop all services
   - Graceful shutdown
   - Force kill if needed
   - Clean process cleanup

### Log Files (Auto-created)

Located in `logs/` directory:
- `backend.log` - FastAPI backend logs
- `celery.log` - Celery worker logs

---

## 🔧 Configuration

### Environment Variables

Set in `.env` file or environment:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# IBKR
IBKR_GATEWAY_URL=https://localhost:5055

# OpenAI
OPENAI_API_KEY=your_api_key_here

# Backend
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
```

### Port Configuration

Default ports:
- **Backend**: 8000 (configurable in scripts)
- **IBKR Gateway**: 5055 (if using)

To change backend port, edit `start-webapp.sh`:
```bash
BACKEND_PORT=9000  # Change this line
```

---

## 📋 What Each Script Does

### start-webapp.sh (Detailed)

```bash
1. Check Python 3 availability
2. Create/activate virtual environment
3. Install/update dependencies from requirements.txt
4. Load environment variables from .env
5. Start FastAPI backend (uvicorn)
   - Host: 0.0.0.0
   - Port: 8000
   - Reload: enabled
   - Logs: logs/backend.log
6. Start Celery worker
   - Concurrency: 2
   - Log level: info
   - Logs: logs/celery.log
7. Display access URLs
8. Show live logs (tail -f)
9. Trap Ctrl+C for graceful shutdown
```

### start-dev.sh (Detailed)

```bash
1. Detect OS (macOS/Linux)
2. Open Terminal/gnome-terminal
3. Create 3 tabs:
   Tab 1: Backend (uvicorn)
   Tab 2: Celery worker
   Tab 3: Log viewer + URLs
4. Each tab runs independently
5. Easy to switch between tabs
```

### stop-webapp.sh (Detailed)

```bash
1. Find all uvicorn processes
2. Find all celery processes
3. Send SIGTERM (graceful)
4. Wait 1 second
5. Send SIGKILL if still running (force)
6. Report status
7. Show any remaining processes
```

---

## 🧪 Testing the Scripts

### Test 1: Basic Startup

```bash
# Start services
./start-webapp.sh

# In another terminal, test health
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

### Test 2: Access Web UI

Open browser:
```
http://localhost:8000/workflows
```

Should see the workflows page.

### Test 3: Stop Services

```bash
# Press Ctrl+C in terminal running start-webapp.sh
# OR in another terminal:
./stop-webapp.sh
```

Should see services stop gracefully.

### Test 4: Development Mode

```bash
./start-dev.sh
```

Should open 3 terminal tabs (macOS).

---

## 🐛 Troubleshooting

### Issue: "Permission denied"

**Solution**:
```bash
chmod +x start-webapp.sh start-dev.sh stop-webapp.sh
```

### Issue: "Port 8000 already in use"

**Check what's using the port**:
```bash
lsof -i :8000
```

**Kill the process**:
```bash
kill <PID>
```

**Or change the port** in `start-webapp.sh`

### Issue: "Virtual environment not activating"

**Solution**:
```bash
# Remove old venv
rm -rf venv

# Recreate
python3 -m venv venv

# Run script again
./start-webapp.sh
```

### Issue: "Dependencies not installing"

**Manual install**:
```bash
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Issue: "Celery worker won't start"

**Check Redis/RabbitMQ** (if required):
```bash
# For Redis
redis-cli ping

# For RabbitMQ
rabbitmqctl status
```

**Check logs**:
```bash
cat logs/celery.log
```

### Issue: "Can't access web UI"

**Check backend is running**:
```bash
curl http://localhost:8000/health
```

**Check logs**:
```bash
tail -f logs/backend.log
```

**Check firewall**:
```bash
# macOS
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Linux
sudo ufw status
```

---

## 📊 Monitoring

### View Logs in Real-Time

```bash
# Backend logs
tail -f logs/backend.log

# Celery logs
tail -f logs/celery.log

# Both together
tail -f logs/*.log
```

### Check Running Processes

```bash
# All related processes
ps aux | grep -E "uvicorn|celery" | grep -v grep

# Just PIDs
pgrep -f "uvicorn.*backend"
pgrep -f "celery.*backend"
```

### Monitor Resource Usage

```bash
# CPU and Memory
top -pid $(pgrep -f "uvicorn.*backend")

# Or with htop
htop -p $(pgrep -f "uvicorn.*backend")
```

---

## 🚀 Production Deployment

For production, consider:

### 1. Use Process Manager

**Supervisor** (Linux):
```ini
[program:ibkr-backend]
command=/path/to/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
directory=/path/to/ibkr-trading-webui
autostart=true
autorestart=true
user=your_user

[program:ibkr-celery]
command=/path/to/venv/bin/celery -A backend.celery_app worker --loglevel=info
directory=/path/to/ibkr-trading-webui
autostart=true
autorestart=true
user=your_user
```

**systemd** (Linux):
```ini
[Unit]
Description=IBKR Trading Backend
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/ibkr-trading-webui
ExecStart=/path/to/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. Use Reverse Proxy

**Nginx**:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. Use Production WSGI Server

Replace uvicorn with gunicorn:
```bash
gunicorn backend.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

---

## 📚 Additional Resources

- **Testing Guide**: `TEST_AND_DEPLOY_GUIDE.md`
- **User Guide**: `FRONTEND_COMPLETE_USER_GUIDE.md`
- **Quick Start**: `READY_TO_TEST.md`
- **Implementation**: `COMPLETE_FRONTEND_IMPLEMENTATION.md`

---

## ✅ Quick Reference

### Start Everything
```bash
./start-webapp.sh
```

### Stop Everything
```bash
./stop-webapp.sh
# or Ctrl+C
```

### Development Mode
```bash
./start-dev.sh
```

### View Logs
```bash
tail -f logs/*.log
```

### Test Health
```bash
curl http://localhost:8000/health
```

### Access Web UI
```
http://localhost:8000/workflows
```

---

**Status**: ✅ **Ready to Use**

Just run `./start-webapp.sh` and you're good to go! 🚀

