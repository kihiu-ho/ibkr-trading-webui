# Environment Variable Reload Guide

## Problem: "DATABASE_URL must use postgresql driver. Got: your_database_url"

### Symptoms
- Backend container fails to start
- Error message shows `DATABASE_URL = "your_database_url"` (literal placeholder)
- `.env` file exists and has correct `DATABASE_URL`
- Other services (Redis, MinIO, Gateway) work fine

### Root Cause
**Docker Compose caches environment variables** when containers are created. Simply updating `.env` file is not enough - containers need to be **recreated** to pick up the new values.

---

## ✅ Solution: Use `reload-env.sh`

### Quick Fix (1 minute)
```bash
# Run the reload script
./reload-env.sh

# Output:
# [1/4] Stopping containers... ✓
# [2/4] Recreating containers... ✓
# [3/4] Waiting for services... ✓
# [4/4] Verifying DATABASE_URL... ✓
# Environment Reload Complete! ✅
```

That's it! Your containers now have the updated environment variables.

---

## 📚 When to Use `reload-env.sh`

Use this script whenever you:
- ✅ **Update `.env` file** with new `DATABASE_URL`
- ✅ **Change any environment variable** (API keys, endpoints, etc.)
- ✅ **Switch databases** (from local to Neon, for example)
- ✅ **Get "your_database_url" error** from backend

**Don't use** for:
- ❌ Code changes (just restart: `docker-compose restart backend`)
- ❌ First-time setup (use `./start.sh` instead)
- ❌ Viewing logs (use `docker logs -f ibkr-backend`)

---

## 🔍 Understanding the Issue

### How Docker Compose Loads .env

**Container Creation** (environment variables are set):
```bash
docker-compose up -d
# 1. Reads .env file
# 2. Substitutes ${DATABASE_URL} with actual value
# 3. Creates container with baked-in environment
```

**Container Reuse** (environment variables are NOT updated):
```bash
# Later: Update .env file
echo "DATABASE_URL=new_value" > .env

# Run docker-compose up again
docker-compose up -d
# 1. Containers already exist
# 2. Docker reuses them (fast!)
# 3. Environment variables are NOT re-read ❌
# 4. Old values still in use
```

**Container Recreation** (environment variables ARE updated):
```bash
./reload-env.sh
# or
docker-compose down
docker-compose up -d --force-recreate
# 1. Stops and removes containers
# 2. Re-reads .env file
# 3. Creates new containers with new environment ✅
```

---

## 🛠️ Manual Steps (Alternative to reload-env.sh)

If you prefer to do it manually:

```bash
# Step 1: Stop and remove containers
docker-compose down

# Step 2: Recreate with fresh environment
docker-compose up -d --force-recreate

# Step 3: Verify DATABASE_URL is loaded
docker-compose exec backend printenv DATABASE_URL

# Step 4: Check logs for errors
docker logs ibkr-backend --tail 20
```

---

## ✅ Verification Checklist

After running `reload-env.sh`, verify:

### 1. Container is Running
```bash
docker ps | grep ibkr-backend
# Should show: ibkr-backend   Up X seconds
```

### 2. DATABASE_URL is Loaded
```bash
docker-compose exec backend printenv DATABASE_URL
# Should show: postgresql+psycopg2://...
# NOT: your_database_url
```

### 3. Backend Has No Errors
```bash
docker logs ibkr-backend 2>&1 | grep -i "error\|traceback"
# Should show: (no output) or only harmless warnings
```

### 4. API is Accessible
```bash
curl http://localhost:8000/health
# Should show: {"status":"healthy",...}
```

---

## 🐛 Troubleshooting

### Issue 1: "DATABASE_URL not found in .env"

**Solution**: Add DATABASE_URL to your `.env` file:
```bash
echo "DATABASE_URL=postgresql+psycopg2://user:pass@host/db" >> .env
./reload-env.sh
```

### Issue 2: "Backend container failed to start"

**Check logs**:
```bash
docker logs ibkr-backend
```

**Common causes**:
- Database connection refused (wrong host/port)
- Invalid DATABASE_URL format
- Database not accessible from Docker network

**Fix**:
1. Verify DATABASE_URL format: `postgresql+psycopg2://user:pass@host:port/dbname`
2. Test connection: `psql "$DATABASE_URL" -c "SELECT 1;"`
3. Check firewall/security groups if using external database

### Issue 3: "DATABASE_URL still shows old value"

**Force complete rebuild**:
```bash
# Nuclear option: Remove everything and rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Issue 4: ".env file has DATABASE_URL but still not working"

**Check .env format**:
```bash
# ✅ CORRECT
DATABASE_URL=postgresql+psycopg2://...

# ❌ WRONG (has quotes)
DATABASE_URL="postgresql+psycopg2://..."

# ❌ WRONG (has export)
export DATABASE_URL=postgresql+psycopg2://...

# ❌ WRONG (has spaces)
DATABASE_URL = postgresql+psycopg2://...
```

**Fix**: Ensure `.env` has no quotes, no `export`, no spaces around `=`

---

## 📖 Related Documentation

- `DATABASE_SETUP.md` - How to configure DATABASE_URL
- `TROUBLESHOOTING.md` - General troubleshooting
- `QUICK_START_PROMPT_SYSTEM.md` - Getting started guide
- `docker-compose.yml` - See comments at top of file

---

## 🚀 Best Practices

### When Changing .env
1. ✅ **Edit `.env` file** with new values
2. ✅ **Run `./reload-env.sh`** to apply changes
3. ✅ **Verify** with health check: `curl http://localhost:8000/health`
4. ✅ **Test** your workflow to ensure everything works

### Development Workflow
```bash
# Day 1: Initial setup
cp env.example .env
nano .env  # Set DATABASE_URL
./start.sh

# Day 2: Switch to production database
nano .env  # Update DATABASE_URL
./reload-env.sh  # ← Apply changes

# Day 3: Update API keys
nano .env  # Update OPENAI_API_KEY
./reload-env.sh  # ← Apply changes
```

### Production Deployment
```bash
# 1. Update .env on server
echo "DATABASE_URL=$PROD_DB_URL" > .env

# 2. Reload environment
./reload-env.sh

# 3. Verify deployment
./verify_deployment.sh

# 4. Monitor logs
docker logs -f ibkr-backend
```

---

## 💡 Pro Tips

### Tip 1: Check Current Environment
```bash
# See ALL environment variables in backend container
docker-compose exec backend printenv

# See only DATABASE-related variables
docker-compose exec backend printenv | grep DATABASE
```

### Tip 2: Quick .env Validation
```bash
# Check if all required variables are set
grep -E "DATABASE_URL|OPENAI_API_KEY|IBKR_ACCOUNT_ID" .env

# Should show all three lines with values
```

### Tip 3: Backup .env Before Changes
```bash
# Backup before editing
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Edit safely
nano .env

# Reload
./reload-env.sh

# If something breaks, restore backup
# cp .env.backup.YYYYMMDD_HHMMSS .env
```

### Tip 4: Watch Logs During Reload
```bash
# Terminal 1: Watch logs
docker logs -f ibkr-backend

# Terminal 2: Reload environment
./reload-env.sh

# You'll see the backend restart in Terminal 1
```

---

## ❓ FAQ

### Q: Do I need to reload after every .env change?
**A:** Yes, if you want containers to see the new values. Docker doesn't auto-reload .env.

### Q: Will I lose data when reloading?
**A:** No. `reload-env.sh` only recreates containers, not volumes. Your database data is safe.

### Q: Can I just restart instead of recreate?
**A:** No. `docker-compose restart` keeps old environment. You must recreate with `--force-recreate`.

### Q: How long does reload take?
**A:** Usually 10-30 seconds. Containers stop, recreate, and start.

### Q: Can I reload just one service?
**A:** Yes:
```bash
docker-compose up -d --force-recreate backend
```

### Q: Does reload-env.sh work in production?
**A:** Yes! It's safe for production. Just ensure your `.env` has correct production values first.

---

**Summary**: When you update `.env`, run `./reload-env.sh` to apply changes. It's that simple! ✅

