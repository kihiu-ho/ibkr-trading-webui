# Enhance Workflow Error Handling and Timeouts

## Summary

**Why**: The `generate_daily_chart` task is hanging indefinitely (2+ hours) when using `pio.write_image()` with Kaleido, causing workflows to stall. Additionally, there's no comprehensive error handling, timeout management, or failure recovery mechanisms in the workflows.

**What Changes**: 
- Add execution timeouts to all tasks
- Implement timeout handling for chart generation (Kaleido operations)
- Add comprehensive error handling with retry logic
- Add failure callbacks and notifications
- Implement task-level and DAG-level timeout configurations
- Add health checks and deadlock detection

**Impact**: 
- Workflows will fail fast instead of hanging indefinitely
- Better error messages and diagnostics
- Automatic retry with exponential backoff
- Improved reliability and observability

## Problem Statement

### Current Issues

1. **Task Hanging**: `generate_daily_chart` task hangs for 2+ hours at `pio.write_image()` call
2. **No Timeouts**: Tasks have no execution timeouts, allowing infinite hangs
3. **Poor Error Handling**: Limited error handling and recovery mechanisms
4. **No Failure Notifications**: No alerts when tasks fail or timeout
5. **No Deadlock Detection**: No mechanism to detect and recover from hung tasks

### Root Causes

1. **Kaleido Issues**: `pio.write_image()` with Kaleido can hang in Docker containers
2. **Missing Timeouts**: No `execution_timeout` configured on tasks
3. **No Timeout Handling**: Chart generation doesn't handle Kaleido timeouts
4. **Limited Retry Logic**: Basic retry without exponential backoff or smart retry strategies

## Proposed Solution

### 1. Add Task Execution Timeouts

Configure execution timeouts for all tasks:
```python
PythonOperator(
    task_id='generate_daily_chart',
    execution_timeout=timedelta(minutes=10),  # Fail after 10 minutes
    ...
)
```

### 2. Implement Chart Generation Timeout

Add timeout wrapper for Kaleido operations:
```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout_context(seconds):
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
```

### 3. Enhanced Error Handling

- Add try-catch blocks with specific error types
- Log detailed error information
- Store error context in XCom for downstream tasks
- Implement graceful degradation (e.g., fallback to PNG if JPEG fails)

### 4. Retry Strategy Improvements

- Exponential backoff for retries
- Different retry strategies for different error types
- Max retry limits with failure notifications
- Retry only on transient errors (not on permanent failures)

### 5. Failure Callbacks and Notifications

- On-failure callbacks to log errors
- Send notifications for critical failures
- Store failure artifacts for debugging
- Update workflow status in database

### 6. Health Checks

- Pre-task health checks (verify dependencies)
- Post-task validation (verify outputs)
- Deadlock detection (check for hung processes)

## Success Criteria

- [ ] All tasks have execution timeouts configured
- [ ] Chart generation has timeout handling for Kaleido operations
- [ ] Tasks fail fast instead of hanging indefinitely
- [ ] Comprehensive error handling with detailed logging
- [ ] Retry logic with exponential backoff
- [ ] Failure callbacks and notifications implemented
- [ ] Health checks for critical operations

## Implementation Plan

### Phase 1: Add Timeouts
1. Add `execution_timeout` to all PythonOperator tasks
2. Configure appropriate timeout values per task type
3. Test timeout behavior

### Phase 2: Chart Generation Timeout
1. Implement timeout wrapper for `pio.write_image()`
2. Add fallback mechanisms (retry with different format, etc.)
3. Test timeout handling

### Phase 3: Error Handling
1. Add comprehensive try-catch blocks
2. Implement error context storage
3. Add detailed error logging
4. Test error scenarios

### Phase 4: Retry Improvements
1. Implement exponential backoff
2. Add error-type-specific retry logic
3. Configure max retries per task
4. Test retry behavior

### Phase 5: Failure Handling
1. Implement on-failure callbacks
2. Add notification system
3. Store failure artifacts
4. Test failure scenarios

### Phase 6: Health Checks
1. Add pre-task health checks
2. Add post-task validation
3. Implement deadlock detection
4. Test health check mechanisms

## Breaking Changes

None - this adds new features without breaking existing functionality.

## Dependencies

- Airflow 2.10.5+ (supports execution_timeout)
- Signal handling for timeouts (Unix systems)
- Notification system (optional, can use logging initially)

## Testing Strategy

1. **Timeout Tests**: Verify tasks fail after timeout
2. **Error Handling Tests**: Test various error scenarios
3. **Retry Tests**: Verify retry logic works correctly
4. **Integration Tests**: Test full workflow with failures
5. **Performance Tests**: Ensure timeouts don't impact normal execution

## Timeline

- Phase 1 (Timeouts): 1 hour
- Phase 2 (Chart Timeout): 1 hour
- Phase 3 (Error Handling): 2 hours
- Phase 4 (Retry Improvements): 1 hour
- Phase 5 (Failure Handling): 1 hour
- Phase 6 (Health Checks): 1 hour
- Testing: 2 hours
- **Total**: ~9 hours

## Rollback Plan

If issues occur:
1. Remove timeout configurations
2. Revert error handling changes
3. Restore original retry logic
4. Monitor for stability

