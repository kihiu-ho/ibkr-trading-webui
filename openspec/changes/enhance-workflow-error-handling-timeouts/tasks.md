# Enhance Workflow Error Handling and Timeouts - Implementation Tasks

## Implementation Checklist

### Phase 1: Add Task Execution Timeouts

- [ ] 1.1 Add `execution_timeout` to `fetch_market_data` task
- [ ] 1.2 Add `execution_timeout` to `generate_daily_chart` task (10 minutes)
- [ ] 1.3 Add `execution_timeout` to `generate_weekly_chart` task (10 minutes)
- [ ] 1.4 Add `execution_timeout` to `analyze_with_llm` task (15 minutes)
- [ ] 1.5 Add `execution_timeout` to `place_order` task (5 minutes)
- [ ] 1.6 Add `execution_timeout` to all other tasks
- [ ] 1.7 Test timeout behavior with short timeout values

### Phase 2: Chart Generation Timeout Handling

- [ ] 2.1 Create timeout utility function for chart generation
- [ ] 2.2 Wrap `pio.write_image()` with timeout handler
- [ ] 2.3 Add fallback to PNG format if JPEG times out
- [ ] 2.4 Add retry logic for chart generation with exponential backoff
- [ ] 2.5 Test timeout handling with simulated delays
- [ ] 2.6 Test fallback mechanisms

### Phase 3: Enhanced Error Handling

- [ ] 3.1 Add comprehensive try-catch in `generate_daily_chart_task`
- [ ] 3.2 Add comprehensive try-catch in `generate_weekly_chart_task`
- [ ] 3.3 Add error context storage in XCom
- [ ] 3.4 Add detailed error logging with stack traces
- [ ] 3.5 Add error type classification (transient vs permanent)
- [ ] 3.6 Test error scenarios (missing data, invalid config, etc.)

### Phase 4: Retry Strategy Improvements

- [ ] 4.1 Implement exponential backoff utility
- [ ] 4.2 Add error-type-specific retry logic
- [ ] 4.3 Configure max retries per task type
- [ ] 4.4 Add retry delay configuration
- [ ] 4.5 Test retry behavior with various error types
- [ ] 4.6 Verify retries don't exceed max attempts

### Phase 5: Failure Callbacks and Notifications

- [ ] 5.1 Create on-failure callback function
- [ ] 5.2 Add failure callback to critical tasks
- [ ] 5.3 Implement error notification system (logging initially)
- [ ] 5.4 Store failure artifacts (error logs, context)
- [ ] 5.5 Update workflow status tracking
- [ ] 5.6 Test failure callbacks

### Phase 6: Health Checks

- [ ] 6.1 Add pre-task health check for dependencies
- [ ] 6.2 Add post-task validation for outputs
- [ ] 6.3 Implement deadlock detection mechanism
- [ ] 6.4 Add health check logging
- [ ] 6.5 Test health check mechanisms

### Phase 7: Testing and Validation

- [ ] 7.1 Test timeout behavior
- [ ] 7.2 Test error handling
- [ ] 7.3 Test retry logic
- [ ] 7.4 Test failure callbacks
- [ ] 7.5 Test health checks
- [ ] 7.6 Run end-to-end workflow test
- [ ] 7.7 Verify no performance degradation

## Implementation Details

### Timeout Configuration

```python
from datetime import timedelta

PythonOperator(
    task_id='generate_daily_chart',
    execution_timeout=timedelta(minutes=10),
    ...
)
```

### Timeout Wrapper for Chart Generation

```python
import signal
from contextlib import contextmanager
from typing import Callable, Any

@contextmanager
def timeout_context(seconds: int):
    """Context manager for operation timeouts"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def with_timeout(func: Callable, timeout_seconds: int, *args, **kwargs) -> Any:
    """Execute function with timeout"""
    with timeout_context(timeout_seconds):
        return func(*args, **kwargs)
```

### Error Handling Pattern

```python
def generate_daily_chart_task(**context):
    try:
        # Task logic
        ...
    except TimeoutError as e:
        logger.error(f"Chart generation timed out: {e}")
        # Store error context
        context['task_instance'].xcom_push(key='error', value=str(e))
        raise
    except Exception as e:
        logger.error(f"Chart generation failed: {e}", exc_info=True)
        context['task_instance'].xcom_push(key='error', value=str(e))
        raise
```

## Testing Commands

```bash
# Test timeout behavior
# Trigger workflow and monitor for timeout

# Test error handling
# Simulate errors and verify handling

# Test retry logic
# Verify retries work correctly
```

## Success Criteria

- ✅ All tasks have execution timeouts
- ✅ Chart generation has timeout handling
- ✅ Comprehensive error handling implemented
- ✅ Retry logic with exponential backoff
- ✅ Failure callbacks working
- ✅ Health checks implemented
- ✅ No hanging tasks
- ✅ Better error messages and diagnostics

