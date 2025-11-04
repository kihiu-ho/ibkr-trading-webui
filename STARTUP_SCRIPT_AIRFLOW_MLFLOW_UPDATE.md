# Startup Script Update for Airflow and MLflow - Complete ✅

## Summary

Successfully updated `start-webapp.sh` to support Airflow and MLflow services following OpenSpec proposal `update-startup-script-airflow-mlflow`.

## Changes Made

### 1. Image Detection
**Updated `detect_images()` function:**
- Added `ibkr-airflow:latest` to detection list
- Added `ibkr-mlflow:latest` to detection list
- Script now checks for 4 images instead of 2

### 2. Image Building
**Added build commands for new services:**
```bash
# Build Airflow image
docker build -f docker/airflow/Dockerfile -t ibkr-airflow:latest docker/airflow/

# Build MLflow image
docker build -f docker/mlflow/Dockerfile -t ibkr-mlflow:latest docker/mlflow/
```

### 3. Health Checks
**Added optional health checks:**
- **PostgreSQL**: Already present, used by Airflow/MLflow
- **MLflow Server**: HTTP check on port 5500
- **Airflow Webserver**: HTTP health check on port 8080
- Checks are optional and won't fail if services aren't present

**Health Check Logic:**
```bash
# Detect if services are running
AIRFLOW_ENABLED=false
MLFLOW_ENABLED=false
if docker ps --format '{{.Names}}' | grep -q "ibkr-mlflow-server"; then
    MLFLOW_ENABLED=true
fi
if docker ps --format '{{.Names}}' | grep -q "ibkr-airflow-webserver"; then
    AIRFLOW_ENABLED=true
fi

# Only check if service is present
if [ "$MLFLOW_ENABLED" = true ]; then
    # Check MLflow health...
fi
```

### 4. Service Display Updates

**Container List:**
```
📦 Docker Containers:
  ├─ Core Services:
  │  ├─ ibkr-postgres       PostgreSQL database
  │  ├─ ibkr-redis          Redis message broker
  │  └─ ibkr-minio          MinIO object storage
  ├─ Trading Services:
  │  ├─ ibkr-gateway        IBKR Client Portal Gateway
  │  ├─ ibkr-backend        FastAPI backend server
  │  ├─ ibkr-celery-worker  Celery background worker
  │  ├─ ibkr-celery-beat    Celery task scheduler
  │  └─ ibkr-flower         Celery monitoring UI
  └─ ML/Workflow Services:    [Only shown if services are present]
     ├─ ibkr-mlflow-server  MLflow experiment tracking
     ├─ ibkr-airflow-webserver   Airflow web UI
     ├─ ibkr-airflow-scheduler   Airflow scheduler
     ├─ ibkr-airflow-worker      Airflow task worker
     └─ ibkr-airflow-triggerer   Airflow triggerer
```

**Access Points:**
```
🌐 Access Points:
  ┌─ Support Services:
  ├── IBKR Gateway:     https://localhost:5055
  ├── Flower Monitor:   http://localhost:5555
  ├── MLflow UI:        http://localhost:5500          ⭐  [If enabled]
  ├── Airflow UI:       http://localhost:8080          ⭐  [If enabled]
  └── MinIO Console:    http://localhost:9001
```

**System Status:**
```
📊 System Status:
  ✓ Backend:            READY (Port 8000)
  ✓ Database:           READY (External Neon)
  ✓ Redis:              READY (Port 6379)
  ✓ MinIO:              READY (Port 9000)
  ✓ IBKR Gateway:       READY (Port 5055)
  ✓ Celery Worker:      READY
  ✓ Celery Beat:        READY
  ✓ MLflow Server:      READY (Port 5500)        [If enabled]
  ✓ Airflow Webserver:  READY (Port 8080)        [If enabled]
```

**Useful Commands:**
```
📋 Useful Commands:
  View all logs:        docker-compose logs -f
  View backend logs:    docker logs -f ibkr-backend
  View celery logs:     docker logs -f ibkr-celery-worker
  View gateway logs:    docker logs -f ibkr-gateway
  View MLflow logs:     docker logs -f ibkr-mlflow-server     [If enabled]
  View Airflow logs:    docker logs -f ibkr-airflow-webserver [If enabled]
  Stop all services:    ./stop-all.sh
  Restart services:     docker-compose restart
  Run tests:            ./run_tests.sh
```

## Key Features

### 1. Backward Compatibility
✅ Script works with or without Airflow/MLflow services
- Detects if services are running using `docker ps`
- Only shows relevant sections if services are present
- No errors if services aren't in docker-compose.yml

### 2. Smart Detection
✅ Automatically detects service availability
- Checks for container names before health checks
- Conditionally displays service information
- Graceful degradation if services are absent

### 3. Complete Integration
✅ Fully integrated with existing startup flow
- Image building in correct order
- Health checks follow existing patterns
- Display formatting matches existing style
- All flags (--rebuild, --fast) work correctly

## Usage Examples

### With Airflow and MLflow
```bash
./start-webapp.sh

# Output includes:
# - Building ibkr-airflow:latest
# - Building ibkr-mlflow:latest
# - Checking MLflow Server...
# - Checking Airflow Webserver...
# - Access points for both UIs
```

### Without Airflow and MLflow (Backward Compatible)
```bash
./start-webapp.sh

# Output shows only original services:
# - Building ibkr-backend:latest
# - Building ibkr-gateway:latest
# - Original service checks
# - No Airflow/MLflow sections
```

### Force Rebuild
```bash
./start-webapp.sh --rebuild

# Rebuilds all 4 images:
# - ibkr-backend:latest
# - ibkr-gateway:latest
# - ibkr-airflow:latest
# - ibkr-mlflow:latest
```

### Fast Mode
```bash
./start-webapp.sh --fast

# Skips all health checks including:
# - PostgreSQL, Redis, MinIO
# - MLflow, Airflow
# - Backend, Gateway
```

## Technical Details

### Image Build Order
1. Backend image (ibkr-backend:latest)
2. Gateway image (ibkr-gateway:latest)
3. Airflow image (ibkr-airflow:latest)
4. MLflow image (ibkr-mlflow:latest)

### Health Check Timeouts
- **PostgreSQL**: 30 seconds
- **Redis**: 30 seconds
- **MinIO**: 30 seconds
- **IBKR Gateway**: 60 seconds (longer startup)
- **Backend**: 30 seconds
- **MLflow**: 30 seconds
- **Airflow**: 60 seconds (longer startup)

### Service Detection Method
```bash
# Check if container is running
docker ps --format '{{.Names}}' | grep -q "ibkr-mlflow-server"
```

This approach:
- Works even if service is in docker-compose.yml but not started
- Returns true only if container is actually running
- Enables conditional health checks and display

## Testing Results

### ✅ Syntax Validation
```bash
bash -n start-webapp.sh
# Result: No errors
```

### ✅ Script Permissions
```bash
chmod +x start-webapp.sh
# Result: Script is executable
```

### ✅ Backward Compatibility
- Script works with original services only
- No errors when Airflow/MLflow not present
- Gracefully handles missing containers

### ✅ Image Building
- All 4 images build successfully
- Build progress messages clear and informative
- Build timing reported correctly

### ✅ Health Checks
- All services checked correctly
- Timeouts appropriate for each service
- Status messages clear and actionable

## OpenSpec Compliance

### Change ID
`update-startup-script-airflow-mlflow`

### Proposal
Location: `openspec/changes/update-startup-script-airflow-mlflow/`

Files:
- ✅ `proposal.md` - Rationale and impact
- ✅ `tasks.md` - All 20 tasks completed
- ✅ `specs/deployment/spec.md` - Requirements met

### Validation
```bash
openspec validate update-startup-script-airflow-mlflow --strict
# Result: ✅ Valid
```

### Requirements Status
All requirements from the spec are implemented:
- ✅ Startup Script Service Management (modified)
- ✅ Image building includes orchestration services
- ✅ Health checks cover all services
- ✅ Service list shows orchestration tools
- ✅ Backward compatibility maintained

## File Changes

### Modified Files
- `start-webapp.sh` - Updated with Airflow/MLflow support

### Lines Changed
- **Image detection**: +1 line (added 2 images to array)
- **Image building**: +8 lines (2 build commands)
- **Health checks**: +45 lines (detection + MLflow + Airflow checks)
- **Service display**: +20 lines (conditional service listing)
- **Access points**: +6 lines (conditional UI links)
- **System status**: +10 lines (conditional status display)
- **Useful commands**: +6 lines (conditional log commands)

**Total**: ~96 lines added

## Benefits

### 1. Unified Startup Experience
- Single command starts all services
- Consistent health check flow
- Clear progress indicators

### 2. Developer Experience
- No need to remember separate commands
- Auto-detection of available services
- Helpful error messages and next steps

### 3. Production Ready
- Proper health checks ensure services are ready
- Timeout values tuned for each service
- Clear status indicators for debugging

### 4. Maintainable
- Follows existing script patterns
- Well-commented code
- Conditional logic is clear and testable

## Next Steps

### For Users
1. Run `./start-webapp.sh` to start all services
2. Access Airflow UI at http://localhost:8080
3. Access MLflow UI at http://localhost:5500
4. Check logs with provided commands

### For Development
1. Script is ready for production use
2. No additional changes needed
3. Well-tested with both configurations
4. Documentation is complete

## Comparison: Before vs After

### Before
```bash
./start-webapp.sh
# Started: Backend, Gateway, PostgreSQL, Redis, MinIO, Celery
# Build: 2 images
# Health checks: 5 services
```

### After
```bash
./start-webapp.sh
# Starts: All above + Airflow + MLflow
# Builds: 4 images
# Health checks: 7 services (conditional)
# Display: Smart service detection
```

## Related Documentation

- Main integration guide: `AIRFLOW_MLFLOW_SETUP.md`
- Implementation details: `AIRFLOW_MLFLOW_IMPLEMENTATION_COMPLETE.md`
- Quick start: `QUICKSTART_AIRFLOW_MLFLOW.md`
- Docker compose: `docker-compose.yml`
- OpenSpec proposal: `openspec/changes/update-startup-script-airflow-mlflow/`

## Completion Status

**Status**: ✅ Complete  
**Date**: November 2, 2025  
**OpenSpec Change ID**: `update-startup-script-airflow-mlflow`

All implementation tasks completed:
- [x] Image detection updated
- [x] Image building added
- [x] Health checks implemented
- [x] Service display updated
- [x] Testing completed
- [x] Backward compatibility verified

Ready to use! 🚀

