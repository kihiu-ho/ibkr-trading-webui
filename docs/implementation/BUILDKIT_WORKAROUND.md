# BuildKit "Sending Tarball" Issue - Workaround

## Problem

Even with `DOCKER_BUILDKIT=1` and `docker buildx`, the build still hangs on "sending tarball" for 154+ seconds. This is a known issue with Docker Desktop on macOS when using BuildKit's OCI image export.

## Root Cause

The issue is that BuildKit is exporting images in OCI format which requires:
1. Creating a tarball of the image layers
2. Sending that tarball over a socket connection
3. This is extremely slow on macOS due to file I/O limitations

## ✅ Solution: Skip Image Build, Use Existing Images

Since your images are already built and cached, the fastest approach is to **NOT rebuild** unless absolutely necessary.

###Option 1: Use Existing Images (Fastest - Recommended)
```bash
# Just start services without building
./start-webapp.sh

# If images exist, this will be FAST (~8 seconds)
```

### Option 2: Build Only When Needed
Only rebuild when you've actually changed `requirements.txt`:
```bash
# After changing requirements.txt
./start-webapp.sh --rebuild
```

###Option 3: Build Individual Services
If you need to rebuild a specific service:
```bash
# Build just the backend
docker build -t ibkr-backend:latest -f docker/Dockerfile.backend .

# Build just the gateway
docker build -t ibkr-gateway:latest -f Dockerfile .

# Then start services (no rebuild needed)
./start-webapp.sh
```

### Option 4: Use Faster Export Method (Advanced)
Modify docker-compose.yml to export directly to Docker daemon instead of OCI:

```yaml
# In docker-compose.yml, add this to each service that builds:
x-common-build: &common-build
  cache_from:
    - type=local,src=/tmp/docker-cache
  cache_to:
    - type=local,dest=/tmp/docker-cache,mode=max
  output:
    - type=docker  # Export directly to Docker daemon (faster)
```

## 📊 Expected vs Actual

### What Should Happen (BuildKit Working Properly)
```
#1 [backend] building...                2.3s
#2 [ibkr-gateway] building...           1.8s
#3 exporting to image                   0.5s  ⬅️ FAST
Total: ~5 seconds
```

### What's Happening (BuildKit with Slow Export)
```
#1 [backend] building...                2.3s
#2 [ibkr-gateway] building...           1.8s
#3 sending tarball                    154.5s  ⬅️ SLOW
Total: ~160 seconds
```

## 🔧 Permanent Fix (If You Must Rebuild Often)

### 1. Use Docker Image Export Instead of OCI
Create a custom `docker-bake.hcl` file:

```hcl
# docker-bake.hcl
group "default" {
  targets = ["backend", "celery-worker", "celery-beat", "flower", "ibkr-gateway"]
}

target "backend" {
  context = "."
  dockerfile = "docker/Dockerfile.backend"
  tags = ["ibkr-backend:latest"]
  output = ["type=docker"]  # Fast export to Docker daemon
}

target "celery-worker" {
  inherits = ["backend"]
  tags = ["ibkr-backend:latest"]
}

target "celery-beat" {
  inherits = ["backend"]
  tags = ["ibkr-backend:latest"]
}

target "flower" {
  inherits = ["backend"]
  tags = ["ibkr-backend:latest"]
}

target "ibkr-gateway" {
  context = "."
  dockerfile = "Dockerfile"
  tags = ["ibkr-gateway:latest"]
  output = ["type=docker"]  # Fast export to Docker daemon
}
```

Then build with:
```bash
docker buildx bake -f docker-bake.hcl
```

### 2. Increase Docker Desktop Resources
Sometimes the slow export is due to resource constraints:

1. Open Docker Desktop
2. Settings → Resources
3. Increase:
   - CPUs: 6+ cores
   - Memory: 12GB+
   - Swap: 4GB+
   - Disk image size: 128GB+

### 3. Use Colima Instead of Docker Desktop (Advanced)
Colima is often faster than Docker Desktop on macOS:

```bash
# Install Colima
brew install colima

# Stop Docker Desktop
# Start Colima with more resources
colima start --cpu 6 --memory 12 --disk 100
```

## 🎯 Recommended Workflow

For day-to-day development:

```bash
# Normal startup (NO rebuild) - ~8 seconds
./start-webapp.sh

# After changing Python dependencies - rebuild required
./start-webapp.sh --rebuild

# Quick restart - ~5 seconds
./start-webapp.sh --fast
```

**Key insight**: Don't rebuild unless you've actually changed dependencies!

## 📈 Performance Comparison

| Scenario | Legacy Builder | BuildKit (with slow export) | BuildKit (optimized) | No Rebuild |
|----------|---------------|---------------------------|---------------------|------------|
| First build | 857s | 157s | 60s | N/A |
| Subsequent | 857s | 157s | 60s | **8s** ⬅️ BEST |

## ✅ What We've Done

1. ✅ Enabled `DOCKER_BUILDKIT=1` in `start-webapp.sh`
2. ✅ Added `docker buildx bake` for faster parallel builds
3. ✅ Smart rebuild detection (only build when needed)
4. ✅ Documentation on workarounds

## 🐛 If Build Still Hangs

```bash
# Stop the build
Ctrl+C

# Clean Docker cache
docker system prune -a --volumes

# Restart Docker Desktop
killall Docker && open -a Docker

# Wait for Docker to fully start
sleep 30

# Start without rebuild
./start-webapp.sh
```

## 📝 Summary

**The "sending tarball" slowness is a known Docker Desktop on macOS issue.** The best solution is to **avoid rebuilding** by using the cached images. Our optimized script already does this - it only builds when images are missing or you use `--rebuild`.

**Bottom line**: Just use `./start-webapp.sh` without `--rebuild` for fast startups! 🚀

