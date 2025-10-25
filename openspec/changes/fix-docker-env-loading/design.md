# Design: Fix Docker Compose .env Loading

## Problem Analysis

### Current Behavior
1. User updates `.env` file with `DATABASE_URL`
2. Runs `docker-compose up -d` or `./start.sh`
3. Backend container uses **old** environment variables (cached)
4. Backend crashes with `DATABASE_URL = "your_database_url"`

### Why This Happens
- Docker Compose reads `.env` file **only when creating containers**
- `docker-compose up` without `--force-recreate` reuses existing containers
- Existing containers have environment variables baked in from creation time
- Changes to `.env` are not automatically picked up

## Solution Design

### Approach: Container Recreation

**Steps to Fix**:
1. Stop existing containers
2. Remove containers (not volumes)
3. Recreate containers with fresh environment variables
4. Verify DATABASE_URL is loaded correctly

**Command**:
```bash
docker-compose down
docker-compose up -d --force-recreate
```

Or simpler:
```bash
docker-compose up -d --force-recreate
```

### Implementation Plan

#### 1. Create Helper Script: `reload-env.sh`
```bash
#!/bin/bash
# Reload .env changes into Docker containers

echo "Stopping containers..."
docker-compose down

echo "Recreating containers with new environment..."
docker-compose up -d --force-recreate

echo "Waiting for services..."
sleep 5

echo "Checking backend..."
docker logs ibkr-backend --tail 20
```

#### 2. Update Start Scripts
Modify `start.sh` to check if containers exist and suggest reload if .env changed:
```bash
if [ -f ".env" ] && [ "$(docker-compose ps -q backend)" ]; then
    echo "⚠️  Containers already running."
    echo "If you changed .env, run: ./reload-env.sh"
fi
```

#### 3. Update Documentation
Add to startup guides:
- When to use `reload-env.sh` vs `start.sh`
- How to verify environment variables are loaded
- Troubleshooting section for .env issues

#### 4. Add Verification Command
```bash
# Check what DATABASE_URL the container sees
docker-compose exec backend printenv DATABASE_URL
```

## Files to Modify

### New Files
1. `reload-env.sh` - Helper script to reload .env changes
2. `openspec/changes/fix-docker-env-loading/ENV_RELOAD_GUIDE.md` - Documentation

### Modified Files
1. `start.sh` - Add warning about .env changes
2. `TROUBLESHOOTING.md` - Add .env reload section
3. `QUICK_START_PROMPT_SYSTEM.md` - Add note about .env changes

## Testing Plan

### Test 1: Fresh Start
```bash
# Create .env with DATABASE_URL
echo "DATABASE_URL=postgresql://test" > .env

# Start containers
./start.sh

# Verify
docker-compose exec backend printenv DATABASE_URL
# Expected: postgresql://test
```

### Test 2: Update .env
```bash
# Update .env
echo "DATABASE_URL=postgresql://new" > .env

# Reload
./reload-env.sh

# Verify
docker-compose exec backend printenv DATABASE_URL
# Expected: postgresql://new
```

### Test 3: Backend Startup
```bash
# Ensure backend starts without errors
docker logs ibkr-backend 2>&1 | grep -i "error\|traceback"
# Expected: No output (no errors)
```

## Success Criteria
- ✅ Backend starts without DATABASE_URL validation errors
- ✅ `reload-env.sh` successfully updates environment
- ✅ Documentation clearly explains when/how to reload .env
- ✅ Users can fix the issue themselves in < 1 minute

## Rollback Plan
If issues occur:
```bash
# Stop everything
docker-compose down

# Start fresh
docker-compose up -d
```

No code changes, so rollback is trivial.

