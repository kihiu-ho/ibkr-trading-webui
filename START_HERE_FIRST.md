# 🚀 START HERE FIRST

**Quick guide to get the IBKR Trading WebUI running**

---

## ✅ Now Even Easier: Docker Integrated!

**PostgreSQL and Redis are now automatically started!**

---

## 🎯 Quickest Path to Running (Updated!)

### Step 1: Start Docker Desktop

Open Docker Desktop from Applications and wait for it to start (whale icon in menu bar).

### Step 2: Start Everything with One Command

```bash
./start-webapp.sh
```

**That's it!** This command now:
- ✅ Starts PostgreSQL automatically
- ✅ Starts Redis automatically
- ✅ Initializes database
- ✅ Starts backend and Celery
- ✅ Shows all access URLs

### Step 3: Open Browser

```
http://localhost:8000/workflows
```

---

## 📝 Notes

- Docker containers for PostgreSQL and Redis are started automatically
- Database is initialized from `database/init.sql` on first run
- Services have health checks to ensure they're ready
- Containers persist data in Docker volumes

---

## 🔍 If Something Goes Wrong

### Run Diagnostics

```bash
./check-services.sh
```

This will tell you exactly what's missing.

### Common Issues

**"Docker is not running"**
→ Start Docker Desktop, or use Homebrew instead

**"PostgreSQL not running"**
→ Run `./start-services.sh` or `brew services start postgresql@15`

**"Redis not running"**  
→ Run `./start-services.sh` or `brew services start redis`

**"Cannot connect to database"**
→ Create database: `createdb ibkr_trading`

### Get Help

Read the troubleshooting guide:
```bash
cat TROUBLESHOOTING.md
```

Or read the complete setup guide:
```bash
cat SETUP_DEPENDENCIES.md
```

---

## 📚 What's Available

Once running, access:

- **Workflows**: http://localhost:8000/workflows
- **Dashboard**: http://localhost:8000/dashboard
- **Strategies**: http://localhost:8000/strategies
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🎉 Success Looks Like

```
✓ PostgreSQL running on port 5432
✓ Redis running on port 6379
✓ Backend started (PID: 12345)
✓ Celery worker started (PID: 12346)
✓ All services started successfully!

Access the application:
  🌐 Web UI: http://localhost:8000
```

Then open http://localhost:8000/workflows in your browser!

---

## 💡 Quick Tips

1. **First time?** Read `SETUP_DEPENDENCIES.md` for complete setup
2. **Having issues?** Run `./check-services.sh` first
3. **Need to stop?** Run `./stop-webapp.sh`
4. **Want to test?** See `READY_TO_TEST.md`

---

## 📖 Documentation Files

| File | Purpose |
|------|---------|
| `START_HERE_FIRST.md` | ← You are here! Quick start |
| `SETUP_DEPENDENCIES.md` | Complete setup guide |
| `TROUBLESHOOTING.md` | Fix common issues |
| `FIXES_APPLIED.md` | What we fixed today |
| `QUICK_START.txt` | One-page reference |
| `FINAL_IMPLEMENTATION_SUMMARY.md` | Full project overview |

---

## ⚡ TL;DR

```bash
# If you have Docker:
./start-services.sh
./start-webapp.sh

# If you have Homebrew:
brew install postgresql@15 redis
brew services start postgresql@15 redis
createdb ibkr_trading
./start-webapp.sh

# Then open:
# http://localhost:8000/workflows
```

**That's it!** 🎉

---

**Current Status**: All code complete ✅ | Ready to run ✅ | Just needs services ✅

