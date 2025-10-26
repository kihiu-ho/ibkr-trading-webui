# Quick Start Guide - Optimized Docker Startup

## TL;DR

```bash
# First time
./start-webapp.sh
# ↳ Builds images once (~90s)

# Every time after
./start-webapp.sh
# ↳ Fast startup (~50s, no rebuild!)

# After changing requirements.txt
./start-webapp.sh --rebuild
# ↳ Rebuilds with fast uv (~90s)
```

## New Optimized Startup

### Normal Startup (Default - Recommended)
```bash
./start-webapp.sh
```
- **First run**: Builds images (~90s)
- **Subsequent runs**: Uses cached images (~50s)
- **Includes**: Health checks for all services

### Fast Mode (Expert - Skip Health Checks)
```bash
./start-webapp.sh --fast
```
- **Time**: ~50s
- **Skips**: Health check waits
- **Use when**: Debugging, know services are stable

### Rebuild Mode (After Dependencies Change)
```bash
./start-webapp.sh --rebuild
```
- **Time**: ~90s
- **Forces**: Full image rebuild with uv
- **Use when**: Changed `requirements.txt` or `package.json`

### Help
```bash
./start-webapp.sh --help
```

## What Changed?

### Before (Slow 😢)
```bash
# Every single startup rebuilt everything
./start-webapp.sh
# ↳ 169+ seconds EVERY TIME
```

### After (Fast 🚀)
```bash
# Smart detection - only builds when needed
./start-webapp.sh
# ↳ 50 seconds (uses cached images)
```

## When to Use Each Command

| Situation | Command | Time |
|-----------|---------|------|
| Daily development | `./start-webapp.sh` | 50s |
| After code changes | `./start-webapp.sh` | 50s |
| After `pip install` | `./start-webapp.sh --rebuild` | 90s |
| Quick debug restart | `./start-webapp.sh --fast` | 50s |
| First time ever | `./start-webapp.sh` | 90s |
| Troubleshooting | `./start-webapp.sh --rebuild` | 90s |

## Performance Comparison

```
Before Optimization:
├─ First run:      169s (rebuild)
├─ Second run:     169s (unnecessary rebuild)
├─ Third run:      169s (unnecessary rebuild)
└─ Every run:      169s (always rebuilding)

After Optimization:
├─ First run:      90s (build with uv)
├─ Second run:     50s (cached!)
├─ Third run:      50s (cached!)
└─ Daily average:  50s (70% faster!)
```

## Behind the Scenes

### Smart Image Detection
The script automatically checks if Docker images exist:
- **Images found** → Skip build, start fast ✅
- **Images missing** → Build once, then fast next time
- **--rebuild flag** → Force rebuild when needed

### Fast Dependencies with `uv`
- Traditional `pip`: 60-90 seconds
- With `uv`: 15-20 seconds
- **Result**: 4-6x faster package installation

### Optimized Docker Layers
```dockerfile
Layer 1: System packages    (rarely changes)
Layer 2: uv installer       (rarely changes)
Layer 3: Python dependencies (occasional changes)
Layer 4: Your code          (frequent changes)
```
**Result**: Code changes don't rebuild dependencies!

## Tips for Developers

### Daily Workflow
```bash
# Morning: Start everything
./start-webapp.sh

# Edit code all day
# Just restart the specific service
docker-compose restart backend

# End of day: Stop everything
docker-compose down
```

### After Installing Packages
```bash
# Added a new dependency
pip install new-package
echo "new-package>=1.0.0" >> requirements.txt

# Rebuild images
./start-webapp.sh --rebuild
```

### Troubleshooting
```bash
# Services acting weird?
./start-webapp.sh --rebuild

# Want completely fresh start?
docker-compose down --rmi all
./start-webapp.sh
```

## Common Questions

**Q: Why is the first run slower?**  
A: It's building Docker images for the first time. This only happens once (or when you use `--rebuild`).

**Q: Do I need to use `--rebuild` after every code change?**  
A: No! Just use `./start-webapp.sh` (default). Only use `--rebuild` after changing `requirements.txt`.

**Q: Can I still use `docker-compose up`?**  
A: Yes, but you'll lose the optimizations. Use `./start-webapp.sh` instead for best performance.

**Q: What if I want to see logs during startup?**  
A: The script shows logs for failures. For success cases, use `docker-compose logs -f` after startup.

**Q: Is `uv` safe to use?**  
A: Yes! It's from Astral (makers of Ruff), uses the same PyPI packages as pip, and is becoming an industry standard.

## More Information

- **Full Documentation**: `DOCKER_OPTIMIZATION_COMPLETE.md`
- **Service Fixes**: `SERVICE_STARTUP_FIXES_COMPLETE.md`
- **Help**: `./start-webapp.sh --help`

---

**🚀 Enjoy your 70% faster development workflow!**

