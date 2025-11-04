## Why

The current `start-webapp.sh` script has basic health checks but doesn't follow proper service dependency management patterns. This can lead to race conditions and startup failures where services try to start before their dependencies are fully ready.

The reference Airflow setup demonstrates proper initialization patterns using:
- `wait-for-it.sh` utility for service availability checks
- Database initialization scripts that run during container startup
- Proper dependency ordering with health checks

## What Changes

### 1. Improve Startup Script Dependency Management
Replace manual health checks with proper dependency-based startup using patterns from reference files:

**Current approach (problematic):**
- Run `docker-compose up -d`
- Manually check each service with curl commands in sequence
- Race conditions possible if services start out of order

**Improved approach:**
- Use Docker Compose dependency conditions (`service_healthy`, `service_completed_successfully`)
- Implement proper initialization scripts for databases
- Use `wait-for-it.sh` for critical service dependencies
- Parallel startup where possible, sequential only where required

### 2. Add Database Initialization Scripts
Create proper database initialization scripts that run during container startup:
- PostgreSQL initialization for Airflow and MLflow databases
- Automatic bucket creation for MinIO
- Proper user and permission setup

### 3. Service Health Check Improvements
- Use container health checks instead of external curl commands where possible
- Implement timeout and retry logic for critical services
- Better error reporting with specific failure reasons

## Impact

### Affected Files
- **MODIFIED**: `start-webapp.sh` - Improved dependency management and initialization
- **NEW**: `scripts/init-databases.sh` - Database initialization script for external PostgreSQL
- **MODIFIED**: `docker-compose.yml` - Enhanced mc service to use local scripts
- **COPIED**: `scripts/wait-for-it.sh` - Service availability checker

### Performance Improvements
- Faster startup times through parallel initialization
- Reduced race conditions and startup failures
- Better resource utilization during startup

### Reliability Improvements
- Services start in correct dependency order
- Automatic retry logic for transient failures
- Better error diagnostics for startup issues

### Breaking Changes
**None** - This enhances existing functionality without changing APIs or contracts.

## Migration Path

### For Existing Users
1. Pull changes
2. Run updated startup script: `./start-webapp.sh`
3. Services will start with improved dependency management
4. No configuration changes required

### Rollback Plan
- Extremely low risk (enhances startup reliability)
- If issues: revert to previous `start-webapp.sh`
- No data loss or configuration changes

## Testing Checklist

- [x] Script syntax validation (bash -n)
- [x] JQ JSON parsing commands tested and working
- [x] Docker Compose health status monitoring implemented
- [x] Service dependency ordering logic validated
- [x] Error handling provides clear diagnostics with service logs
- [x] Full integration testing with complete startup sequence
- [x] Service health detection working (redis ✓, minio ✓, backend ✓)
- [x] Dependency-based startup ordering confirmed
