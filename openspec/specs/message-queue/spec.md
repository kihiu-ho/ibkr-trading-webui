# message-queue Specification

## Purpose
TBD - created by archiving change add-fastapi-trading-webapp. Update Purpose after archive.
## Requirements
### Requirement: Celery Task Queue Integration
The system SHALL integrate Celery task queue with Redis broker to enable concurrent execution of multiple trading workflows.

#### Scenario: Celery configuration
- **WHEN** the application starts
- **THEN** Celery SHALL be configured with Redis broker
- **AND** worker pool SHALL be initialized
- **AND** task routes SHALL be defined for different task types

#### Scenario: Task serialization
- **WHEN** task data is serialized
- **THEN** JSON serialization SHALL be used for compatibility
- **AND** complex objects (dataframes, charts) SHALL be stored externally with references passed to tasks

### Requirement: Asynchronous Workflow Execution
The system SHALL execute trading workflows as asynchronous Celery tasks to enable concurrent processing.

#### Scenario: Submit workflow as task
- **WHEN** user triggers workflow execution via API
- **THEN** a Celery task SHALL be created with: strategy_id, symbols, priority, user_id
- **AND** task_id SHALL be returned immediately
- **AND** task SHALL be queued for execution
- **AND** workflow_execution record SHALL be created in database with task_id

#### Scenario: Execute workflow task
- **WHEN** Celery worker picks up workflow task
- **THEN** update workflow_execution status to 'running'
- **AND** execute workflow steps sequentially
- **AND** log each step completion
- **AND** on completion, update status to 'completed' or 'failed'
- **AND** store results in task result backend

#### Scenario: Multiple workflows concurrently
- **WHEN** multiple workflow tasks are queued
- **THEN** available workers SHALL pick up tasks concurrently
- **AND** each workflow SHALL execute independently
- **AND** workers SHALL respect resource limits (max concurrent tasks per worker)

### Requirement: Task Priority Queue
The system SHALL support prioritized task execution to ensure critical workflows run first.

#### Scenario: Submit high-priority task
- **WHEN** workflow is submitted with priority='high'
- **THEN** task SHALL be added to high-priority queue
- **AND** workers SHALL process high-priority queue first
- **AND** high-priority tasks SHALL preempt lower-priority tasks if workers are busy

#### Scenario: Priority levels
- **WHEN** tasks are queued
- **THEN** support three priority levels: 'high', 'normal', 'low'
- **AND** default priority SHALL be 'normal'
- **AND** tasks SHALL be processed in priority order within each queue

### Requirement: Task Status Tracking
The system SHALL track task status and provide real-time updates to users.

#### Scenario: Query task status
- **WHEN** user requests task status via GET /api/tasks/{task_id}
- **THEN** return current task state: 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE', 'RETRY', 'REVOKED'
- **AND** include progress information if available
- **AND** include result or error message if completed

#### Scenario: Update task progress
- **WHEN** workflow task is executing
- **THEN** task SHALL update progress: {current_step, total_steps, current_symbol, completed_symbols}
- **AND** progress SHALL be stored in result backend
- **AND** progress SHALL be queryable via API

#### Scenario: Task result retrieval
- **WHEN** task completes successfully
- **THEN** result SHALL be stored in Redis result backend
- **AND** result SHALL include: decisions made, orders placed, errors encountered
- **AND** result SHALL be accessible for 24 hours (configurable TTL)

### Requirement: Task Retry and Error Handling
The system SHALL automatically retry failed tasks with configurable retry policies.

#### Scenario: Task fails with retryable error
- **WHEN** task fails due to temporary error (network, rate limit, timeout)
- **THEN** task SHALL be automatically retried
- **AND** retry SHALL use exponential backoff (1s, 2s, 4s, 8s...)
- **AND** max retries SHALL be 3 (configurable)
- **AND** each retry SHALL be logged

#### Scenario: Task fails with non-retryable error
- **WHEN** task fails due to permanent error (invalid data, authentication failure)
- **THEN** task SHALL NOT be retried
- **AND** status SHALL be set to 'FAILURE'
- **AND** error SHALL be logged with full traceback
- **AND** user SHALL be notified

#### Scenario: Task timeout
- **WHEN** task exceeds max execution time (default 1 hour)
- **THEN** task SHALL be terminated
- **AND** status SHALL be set to 'FAILURE' with timeout error
- **AND** partial results SHALL be saved if available

### Requirement: Task Cancellation
The system SHALL allow users to cancel queued or running tasks.

#### Scenario: Cancel queued task
- **WHEN** user requests to cancel task via DELETE /api/tasks/{task_id}
- **THEN** if task is queued, remove from queue
- **AND** set status to 'REVOKED'
- **AND** return cancellation confirmation

#### Scenario: Cancel running task
- **WHEN** user requests to cancel running task
- **THEN** send termination signal to worker
- **AND** worker SHALL gracefully stop execution
- **AND** cleanup resources (close connections, save state)
- **AND** set status to 'REVOKED'

### Requirement: Worker Management
The system SHALL manage Celery workers and monitor their health.

#### Scenario: Worker pool configuration
- **WHEN** workers are started
- **THEN** workers SHALL be configured with: concurrency (number of parallel tasks), pool type (prefork/threads), resource limits
- **AND** workers SHALL register with broker
- **AND** workers SHALL start consuming tasks from queues

#### Scenario: Worker health monitoring
- **WHEN** monitoring worker health
- **THEN** check worker heartbeat via Celery inspect
- **AND** report active tasks per worker
- **AND** report worker resource usage (CPU, memory)
- **AND** alert if worker is unresponsive

#### Scenario: Worker scaling
- **WHEN** task queue grows beyond threshold
- **THEN** system SHALL alert to scale workers
- **AND** support horizontal scaling (add more worker containers)
- **AND** workers SHALL automatically join pool when started

### Requirement: Task Result Cleanup
The system SHALL automatically clean up expired task results to manage storage.

#### Scenario: Result TTL
- **WHEN** task completes
- **THEN** result SHALL be stored with TTL (default 24 hours)
- **AND** after TTL expires, result SHALL be removed from Redis
- **AND** workflow_execution record SHALL remain in database

#### Scenario: Periodic cleanup
- **WHEN** periodic cleanup job runs (daily)
- **THEN** remove expired results from result backend
- **AND** remove old workflow_execution records (configurable retention)
- **AND** log cleanup statistics

### Requirement: Task Scheduling
The system SHALL support scheduled and periodic task execution.

#### Scenario: Schedule workflow execution
- **WHEN** user schedules workflow to run at specific time
- **THEN** create Celery beat schedule entry
- **AND** task SHALL be queued at scheduled time
- **AND** support cron-like schedules (daily, weekly, custom)

#### Scenario: Periodic workflows
- **WHEN** workflow is configured as periodic (e.g., every 4 hours)
- **THEN** Celery beat SHALL queue task on schedule
- **AND** previous execution must complete before next starts (unless configured otherwise)
- **AND** schedule can be enabled/disabled via API

### Requirement: Task Monitoring and Metrics
The system SHALL provide monitoring interface for task queue health and performance.

#### Scenario: Task queue metrics
- **WHEN** viewing monitoring dashboard
- **THEN** display: tasks queued, tasks active, tasks completed, tasks failed, average task duration, worker count, queue length per priority
- **AND** metrics SHALL be updated real-time (WebSocket or polling)

#### Scenario: Flower monitoring integration
- **WHEN** Flower monitoring tool is deployed
- **THEN** Flower SHALL connect to Redis broker
- **AND** provide web UI for: task history, worker status, task details, retry management
- **AND** Flower SHALL be accessible at separate port (5555)

### Requirement: Task Chaining and Workflows
The system SHALL support chaining multiple tasks into complex workflows.

#### Scenario: Chain tasks
- **WHEN** workflow consists of dependent steps
- **THEN** use Celery chain to execute tasks sequentially
- **AND** output of one task SHALL be input to next
- **AND** chain SHALL stop if any task fails

#### Scenario: Parallel task execution
- **WHEN** workflow has independent steps
- **THEN** use Celery group to execute tasks in parallel
- **AND** wait for all tasks to complete before proceeding
- **AND** collect results from all parallel tasks

