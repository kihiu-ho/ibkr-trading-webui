# Technical Design

## Context

The current startup process unnecessarily rebuilds Docker images on every run due to the `--build` flag in `docker-compose up`. This causes 169+ second startup times when it should be <10 seconds after the initial build. Additionally, Python package installation using `pip` is slower than modern alternatives.

## Goals

- Reduce typical startup time from 169s to <10s
- Maintain ability to rebuild when needed (explicit flag)
- Adopt modern, fast Python tooling (`uv`)
- Improve developer experience with clear feedback
- Maintain backward compatibility

## Non-Goals

- Changing application functionality
- Modifying database schema or migrations
- Altering API contracts
- Implementing hot-reloading (already handled by `--reload` flag)

## Key Decisions

### Decision 1: Use `uv` for Python Package Management

**What**: Replace `pip` with `uv` (https://github.com/astral-sh/uv) for installing Python dependencies.

**Why**:
- **10-100x faster** than pip for package installation
- Written in Rust, highly optimized
- Better dependency resolution
- From Astral (makers of Ruff), becoming ecosystem standard
- Drop-in replacement for pip: `uv pip install` works identically

**Installation in Dockerfile**:
```dockerfile
# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Use uv instead of pip
RUN uv pip install --system -r /app/backend/requirements.txt
```

**Alternatives Considered**:
- **Poetry**: More complex, not just faster installation
- **pip with caching**: Still slower, less optimization
- **pip-tools**: Better but not as fast as uv
- **Keep pip**: Rejected due to poor performance

### Decision 2: Smart Image Detection in Startup Script

**What**: Add logic to detect if Docker images exist before building.

**Implementation**:
```bash
detect_images() {
    local images=("ibkr-backend" "ibkr-gateway")
    local all_exist=true
    
    for image in "${images[@]}"; do
        if ! docker image inspect "$image:latest" &> /dev/null; then
            all_exist=false
            break
        fi
    done
    
    echo "$all_exist"
}

# In main script
if [ "$(detect_images)" = "false" ] || [ "$FORCE_REBUILD" = true ]; then
    print_info "Building Docker images (first run or --rebuild)..."
    $COMPOSE_CMD build
fi

$COMPOSE_CMD up -d  # No --build flag
```

**Why**: Separates build from run, only builds when necessary.

### Decision 3: Optimized Dockerfile Layer Structure

**What**: Restructure Dockerfile to maximize layer caching.

**Current Structure** (inefficient):
```dockerfile
COPY backend /app/backend
RUN pip install -r /app/backend/requirements.txt
```
Problem: Code changes invalidate dependency cache.

**New Structure** (efficient):
```dockerfile
# Layer 1: System dependencies (rarely changes)
RUN apt-get update && apt-get install -y gcc g++ ...

# Layer 2: Python package installer (rarely changes)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Layer 3: Requirements only (changes occasionally)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN uv pip install --system -r /app/backend/requirements.txt

# Layer 4: Application code (changes frequently)
COPY backend /app/backend
COPY frontend /app/frontend
```

**Why**: Docker caches layers. If Layer 4 changes, Layers 1-3 are reused.

### Decision 4: Explicit Rebuild Flags

**What**: Add command-line flags for explicit control.

**Flags**:
- Default: `./start-webapp.sh` → Fast start, build only if needed
- `--rebuild`: Force full rebuild of all images
- `--fast`: Skip health checks (expert mode)
- `--help`: Show usage and examples

**Example Usage**:
```bash
# Normal startup (fast after first run)
./start-webapp.sh

# After dependency changes
./start-webapp.sh --rebuild

# Quick restart (skip health checks)
./start-webapp.sh --fast

# First time or help needed
./start-webapp.sh --help
```

## Implementation Details

### Modified Files

1. **docker/Dockerfile.backend** - Add uv, optimize layers
2. **Dockerfile** (IBKR Gateway) - Check for Python deps, add uv if needed
3. **start-webapp.sh** - Add image detection, flags, timing
4. **docker-compose.yml** - Ensure consistent image tagging
5. **.dockerignore** - Create to exclude unnecessary files

### Dockerfile.backend Changes

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Layer 1: System dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ postgresql-client curl \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Layer 2: Install uv (fast Python package installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Layer 3: Python dependencies (cached unless requirements.txt changes)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN uv pip install --system --no-cache -r /app/backend/requirements.txt

# Layer 4: Application code (changes frequently, doesn't invalidate deps)
COPY backend /app/backend
COPY frontend /app/frontend

ENV PYTHONPATH=/app
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_PATH=/usr/bin/chromium

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### start-webapp.sh Changes

Add at the beginning (after color definitions):
```bash
# Parse command-line arguments
FORCE_REBUILD=false
SKIP_HEALTH_CHECKS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        --fast)
            SKIP_HEALTH_CHECKS=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

show_help() {
    echo "Usage: ./start-webapp.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --rebuild   Force rebuild of all Docker images"
    echo "  --fast      Skip health checks (faster startup)"
    echo "  --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start-webapp.sh              # Normal startup (fast after first run)"
    echo "  ./start-webapp.sh --rebuild    # Rebuild images (after dependency changes)"
    echo "  ./start-webapp.sh --fast       # Quick restart, skip health checks"
}

detect_images() {
    local images=("ibkr-backend:latest" "ibkr-gateway:latest")
    
    for image in "${images[@]}"; do
        if ! docker image inspect "$image" &> /dev/null 2>&1; then
            return 1  # false, image doesn't exist
        fi
    done
    
    return 0  # true, all images exist
}
```

Replace line 167:
```bash
# Before:
# $COMPOSE_CMD up -d --build

# After:
# Build images only if needed
print_header "Preparing Docker Images"

if ! detect_images || [ "$FORCE_REBUILD" = true ]; then
    if [ "$FORCE_REBUILD" = true ]; then
        print_info "Rebuilding images (--rebuild flag)..."
    else
        print_info "Building images (first run)..."
    fi
    
    START_BUILD=$(date +%s)
    $COMPOSE_CMD build
    END_BUILD=$(date +%s)
    BUILD_TIME=$((END_BUILD - START_BUILD))
    
    print_status "Images built in ${BUILD_TIME}s"
else
    print_status "Using cached images (use --rebuild to force rebuild)"
fi

print_header "Starting Services"
START_UP=$(date +%s)
$COMPOSE_CMD up -d
END_UP=$(date +%s)
STARTUP_TIME=$((END_UP - START_UP))

print_status "Services started in ${STARTUP_TIME}s"
```

### .dockerignore File

Create `.dockerignore`:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Node
node_modules/
npm-debug.log*

# Git
.git/
.gitignore

# Documentation (not needed in images)
*.md
docs/

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Test and development
tests/
.pytest_cache/
.coverage

# Build artifacts
*.egg-info/
dist/
build/
```

## Performance Benchmarks (Expected)

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| First run | 169s | 150s | 11% (uv faster than pip) |
| Second run | 169s | 8s | **95%** (no rebuild) |
| After code change | 169s | 8s | **95%** (cached deps) |
| After dependency change | 169s | 90s | 47% (uv + partial cache) |
| With --rebuild flag | 169s | 90s | 47% (explicit rebuild) |

## Risks & Mitigations

### Risk 1: `uv` Compatibility Issues
**Risk**: Some packages might not install correctly with `uv`.

**Likelihood**: Low (uv is pip-compatible)

**Mitigation**:
- Test all current dependencies
- Keep pip available as fallback
- Document any package-specific issues
- `uv pip install` uses same package sources as pip

### Risk 2: Developers Forget to Rebuild After Dependency Changes
**Risk**: Code breaks because new dependencies not installed.

**Likelihood**: Medium

**Mitigation**:
- Clear error messages suggest `--rebuild`
- Add dependency check in startup script
- Document in README when to use `--rebuild`
- CI/CD always uses `--rebuild` to ensure clean builds

### Risk 3: Image Tag Conflicts
**Risk**: Mixing old and new images causes issues.

**Likelihood**: Low

**Mitigation**:
- Use consistent tagging (`:latest`)
- Document cleanup: `docker-compose down --rmi all` for fresh start
- Add `--clean` flag to remove old images

## Migration Plan

### Phase 1: Deploy Changes (Day 1)
1. Merge PR with all changes
2. Update documentation
3. Communicate to team

### Phase 2: Team Transition (Day 1-2)
1. Each developer runs `./start-webapp.sh --rebuild` once
2. Future runs use default (fast mode)
3. Gather feedback on performance improvements

### Phase 3: Validation (Day 3-7)
1. Monitor for any issues
2. Collect startup time metrics
3. Adjust if needed

### Rollback Plan
If critical issues arise:
1. `git revert` the merge commit
2. Redeploy previous version
3. Investigate and fix issues
4. Redeploy with fixes

No data loss or service impact - this is a build optimization only.

## Open Questions

1. **Should we add a `--clean` flag to remove all images and start fresh?**
   - Useful for troubleshooting but adds complexity
   - Could be added in future iteration

2. **Should we use `uv` for production deployments too?**
   - Yes, but test thoroughly first
   - Could improve CI/CD build times

3. **Should we implement multi-stage Docker builds?**
   - Could reduce image size
   - More complex, defer to future optimization

## Success Metrics

- [ ] Startup time reduced from 169s to <10s for subsequent runs
- [ ] First run optimized to ~150s (from 169s)
- [ ] Zero regressions in functionality
- [ ] Positive developer feedback
- [ ] Documentation updated with new flags

