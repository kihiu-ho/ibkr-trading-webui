## 1. Diagnose Gunicorn Timeout Issue

- [x] Check current worker count (default is 4)
- [x] Verify resource constraints (2G memory limit, 1G reservation, 2 CPUs)
- [x] Check logs for gunicorn startup timing
- [x] Identify that external database latency is primary factor
- [x] Confirm timeout is in webserver_command.py (hardcoded 120s)
- [x] Verify timeout cannot be overridden via environment variables
- [x] Test with official entrypoint pattern

## 2. Database Connection Fixes

- [x] Fix database URL format conversion (postgresql+psycopg2:// → postgresql://)
- [x] Add database connection retry logic (30 retries, 2s intervals)
- [x] Remove conflicting database URL from common environment
- [x] Verify database migration completes successfully

## 3. Configuration Optimizations

- [x] Switch to official entrypoint pattern (`/entrypoint webserver`)
- [x] Remove Celery-specific environment variables (using LocalExecutor)
- [x] Clean up environment variable conflicts
- [x] Adjust health check start_period to 120s

## 4. Investigation Attempts

- [x] Attempt 1: Reduce workers from 4 to 1 (still times out)
- [x] Attempt 2: Set environment variables for timeout (no effect)
- [x] Attempt 3: Custom Docker image patching (file location issue)
- [x] Attempt 4: Official entrypoint pattern (still times out)
- [x] Attempt 5: LocalExecutor instead of CeleryExecutor (still times out)

## 5. Document Findings

- [x] Update OpenSpec proposal with investigation results
- [x] Document root cause analysis
- [x] List all attempted solutions
- [x] Provide recommendations for resolution
- [x] Update testing checklist with blocked items

## 6. Remaining Work

- [ ] Investigate Airflow Standalone Mode further (alternative approach)
- [ ] Consider increasing Docker memory allocation to 8GB
- [ ] Evaluate using local PostgreSQL instead of external
- [ ] Monitor Airflow releases for timeout configurability
- [ ] Consider Kubernetes deployment with official Helm chart
