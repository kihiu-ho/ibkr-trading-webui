# Implementation Tasks: Fix SQLAlchemy JSONB & Docker Issues

## Phase 1: Fix SQLAlchemy JSONB Import ✅
- [x] 1.1 Update `backend/models/lineage.py` import
- [x] 1.2 Change `from sqlalchemy import JSONB` to `from sqlalchemy import JSON`
- [x] 1.3 Replace all `JSONB` column types with `JSON`
- [x] 1.4 Test that JSON type works with PostgreSQL

## Phase 2: Fix Reserved Name Conflict ✅
- [x] 2.1 Rename `metadata` column to `step_metadata` in `backend/models/lineage.py`
- [x] 2.2 Update `to_dict()` method to maintain API compatibility
- [x] 2.3 Update `backend/services/lineage_tracker.py` references (3 places)
- [x] 2.4 Update `database/migrations/001_add_workflow_lineage.sql`
- [x] 2.5 Test lineage record creation and retrieval

## Phase 3: Fix Docker Image Tag ✅
- [x] 3.1 Update `docker-compose.yml` ibkr-gateway service
- [x] 3.2 Change `image: ibkr-gateway` to `image: ibkr-gateway:latest`
- [x] 3.3 Test Docker image builds correctly
- [x] 3.4 Verify all services start successfully

## Phase 4: Testing & Verification ✅
- [x] 4.1 Stop all services
- [x] 4.2 Rebuild containers with `docker-compose build`
- [x] 4.3 Start services with `docker-compose up -d`
- [x] 4.4 Check all services are running: `docker-compose ps`
- [x] 4.5 Test backend health: `curl http://localhost:8000/health`
- [x] 4.6 Verify lineage tracking works without errors
- [x] 4.7 Confirm no import errors in logs

## Status: ✅ COMPLETE

All fixes have been implemented and verified:
- ✅ SQLAlchemy imports use generic `JSON` type
- ✅ Reserved name conflict resolved with `step_metadata`
- ✅ Docker image tags properly configured
- ✅ All services start successfully
- ✅ No breaking changes to API

