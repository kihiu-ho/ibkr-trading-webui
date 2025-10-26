# Fix SQLAlchemy JSONB Import, Reserved Name & Docker Image Issues

## Why
The system is encountering three critical errors preventing startup:

1. **SQLAlchemy JSONB Import Error**: `backend/models/lineage.py` is importing `JSONB` from `sqlalchemy`, but in SQLAlchemy 2.0+, `JSONB` is PostgreSQL-specific and should use the generic `JSON` type from the main `sqlalchemy` module.

2. **SQLAlchemy Reserved Name Error**: The `metadata` column name is reserved by SQLAlchemy's Declarative API and cannot be used as a column name.

3. **Docker Image Error**: The IBKR Gateway service is failing to start because the image tag is not explicit in docker-compose.yml, causing Docker to look for a pre-built image instead of building it.

## What Changes

### 1. Fix SQLAlchemy JSONB Import
**File**: `backend/models/lineage.py`
- Change import from `from sqlalchemy import JSONB` to `from sqlalchemy import JSON`
- Replace all `JSONB` column types with `JSON`
- `JSON` type works with PostgreSQL and automatically uses JSONB on PostgreSQL backends

### 2. Fix Reserved Name Conflict
**Files**: 
- `backend/models/lineage.py` - Rename column `metadata` to `step_metadata`
- `backend/services/lineage_tracker.py` - Update 3 references to use `step_metadata`
- `database/migrations/001_add_workflow_lineage.sql` - Update table schema
- API compatibility maintained: `to_dict()` still returns `metadata` key

### 3. Fix Docker Image Tag
**File**: `docker-compose.yml`
- Change `image: ibkr-gateway` to `image: ibkr-gateway:latest`
- This ensures Docker Compose builds and tags the image correctly

## Impact
- **Affected Files**: 
  - `backend/models/lineage.py` - Fixed JSONB import + renamed metadata column
  - `backend/services/lineage_tracker.py` - Updated references
  - `database/migrations/001_add_workflow_lineage.sql` - Updated schema
  - `docker-compose.yml` - Fixed image tag
- **Breaking Changes**: None (API still returns `metadata` in JSON responses)
- **Database Changes**: Column rename (`metadata` → `step_metadata`)

## Benefits
- System can start without import errors
- Docker images build correctly
- Compatible with SQLAlchemy 2.0+
- Works across different database backends

## Technical Details

### Why JSON instead of JSONB?
- SQLAlchemy 2.0+ moved database-specific types to dialect modules
- `JSON` type from `sqlalchemy` automatically uses the best JSON type for the backend
- For PostgreSQL, it uses JSONB under the hood
- More portable across different databases
- No functional difference for our PostgreSQL use case

### Why Explicit Image Tag?
- Docker Compose needs explicit tags to properly build and cache images
- `image: ibkr-gateway` without a tag can cause Docker to look for pre-existing images
- `image: ibkr-gateway:latest` ensures the built image is properly tagged

## Testing
- [x] System starts without import errors
- [x] All services build correctly
- [x] Lineage records can be created and retrieved
- [x] No functional changes to JSON storage

**Status**: ✅ FIXED - Both errors resolved

