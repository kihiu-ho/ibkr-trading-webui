# Optimize Docker Startup and Python Dependency Management

## Why

The current Docker startup process rebuilds all images on every run, taking 169+ seconds due to:
1. The `start-webapp.sh` script uses `docker-compose up --build`, forcing complete rebuilds
2. Python package installation uses `pip`, which is significantly slower than modern alternatives
3. No intelligent caching or image existence checking
4. No differentiation between first-run and subsequent runs

This creates a poor developer experience with:
- **169+ seconds** per startup (should be <10 seconds after first build)
- Unnecessary network bandwidth usage downloading packages repeatedly
- Developer frustration and reduced productivity

## What Changes

### 1. Smart Docker Build Logic
- Remove `--build` flag from default startup
- Add intelligent image detection that only builds when necessary
- Implement `--rebuild` option for explicit rebuilds
- Cache Docker images between runs

### 2. Adopt `uv` for Python Package Management
- Replace `pip` with `uv` (Astral's Rust-based package installer)
- **10-100x faster** package installation
- Better dependency resolution
- Improved caching and lockfile support
- Modern Python tooling aligned with industry best practices (same team as Ruff)

### 3. Enhanced Startup Script
- Add build status detection
- Provide clear user feedback about what's happening
- Add `--rebuild` and `--fast` flags
- Show timing information for optimization tracking

### 4. Optimized Dockerfile Layer Caching
- Restructure Dockerfile layers for better caching
- Separate dependency installation from code copying
- Use multi-stage builds where appropriate

## Impact

### Performance Improvements
- **First run**: ~150 seconds (one-time cost, optimized dependency installation)
- **Subsequent runs**: ~5-10 seconds (no rebuild, just container startup)
- **Rebuild when needed**: ~60-90 seconds (cached layers + fast uv)
- **Overall**: ~90% reduction in typical startup time

### Affected Components
- **Scripts**: `start-webapp.sh`
- **Docker**: `docker-compose.yml`, `docker/Dockerfile.backend`, `Dockerfile`
- **Dependencies**: `backend/requirements.txt` (add uv)
- **New Capability**: `deployment-infrastructure` spec (handles deployment/startup)

### Breaking Changes
None - this is backward compatible. Developers can still force rebuilds with `--rebuild`.

### Benefits
1. **Developer Experience**: Faster iteration cycles
2. **Resource Efficiency**: Less CPU/network usage
3. **Modern Tooling**: Aligns with Python ecosystem trends (`uv` is becoming standard)
4. **Explicit Control**: Clear flags for rebuild vs fast-start
5. **Better Feedback**: Users understand what's happening during startup

## Migration Path

### For Existing Users
1. Pull changes
2. Run `./start-webapp.sh --rebuild` once to build optimized images
3. Future runs use `./start-webapp.sh` (fast mode, no rebuild)

### Rollback Plan
- Git revert restores previous behavior
- Old images remain available
- No database or data impact

