# API Backend Service Startup Specification

## ADDED Requirements

### Requirement: Decision Model Persistence
The system SHALL provide a Decision model for storing trading decisions made by strategies.

#### Scenario: Decision creation
- **GIVEN** a strategy has analyzed market data
- **AND** generated a trading decision
- **WHEN** the decision is saved to the database
- **THEN** a Decision record SHALL be created
- **AND** the record SHALL include strategy_id, decision type, prices, and analysis

#### Scenario: Decision querying from dashboard
- **GIVEN** decisions exist in the database
- **WHEN** the dashboard requests recent decisions count
- **THEN** the query SHALL execute successfully
- **AND** return the count of Decision records

#### Scenario: Decision model schema
- **GIVEN** the Decision model definition
- **THEN** it SHALL have columns: id, strategy_id, code_id, type, current_price, target_price, stop_loss, profit_margin, r_coefficient, analysis_text
- **AND** it SHALL have timestamps: created_at, updated_at
- **AND** it SHALL have foreign key to Strategy model
- **AND** it SHALL have indexes on strategy_id and created_at

### Requirement: Celery Task Import Success
The system SHALL ensure all Celery tasks import successfully without syntax or import errors.

#### Scenario: Celery worker startup
- **GIVEN** the backend code is deployed
- **WHEN** Celery worker starts
- **THEN** it SHALL load backend.celery_app without errors
- **AND** it SHALL import all task modules successfully
- **AND** it SHALL not encounter ModuleNotFoundError
- **AND** it SHALL not encounter SyntaxError

#### Scenario: Task module imports
- **GIVEN** Celery is loading task modules
- **WHEN** importing backend.tasks.strategy_tasks
- **THEN** the import SHALL succeed
- **AND** the module SHALL not use 'await' outside async functions
- **AND** all dependencies SHALL be available

### Requirement: Synchronous Celery Tasks
The system SHALL implement Celery tasks as synchronous functions unless explicitly decorated as async.

#### Scenario: Strategy execution check task
- **GIVEN** a periodic task to check for due strategies
- **WHEN** the task function is defined
- **THEN** it SHALL be a synchronous function (no async def)
- **AND** it SHALL not use 'await' for service calls
- **AND** it SHALL use synchronous database sessions

#### Scenario: Calling synchronous service methods from tasks
- **GIVEN** a Celery task needs to query strategies
- **WHEN** calling StrategyService.get_strategies_due_for_execution()
- **THEN** the method SHALL be called synchronously (no await)
- **AND** the method SHALL return results directly
- **AND** no SyntaxError SHALL occur

### Requirement: Complete Model Registration
The system SHALL register all models in backend.models.__init__ for proper import and database creation.

#### Scenario: Decision model import
- **GIVEN** code needs to import Decision model
- **WHEN** importing from backend.models.decision
- **THEN** the import SHALL succeed
- **AND** the Decision class SHALL be available

#### Scenario: Model inclusion in Base metadata
- **GIVEN** SQLAlchemy Base.metadata
- **WHEN** Base.metadata.create_all() is called
- **THEN** the decisions table SHALL be created
- **AND** all Decision model columns SHALL be present

### Requirement: Service Health Startup
The system SHALL start all Docker services successfully without restart loops.

#### Scenario: Celery worker healthy startup
- **GIVEN** Docker Compose starts services
- **WHEN** the celery-worker container initializes
- **THEN** it SHALL reach "Up" status
- **AND** it SHALL not enter "Restarting" state
- **AND** logs SHALL show "ready" message

#### Scenario: Celery beat healthy startup
- **GIVEN** Docker Compose starts services
- **WHEN** the celery-beat container initializes
- **THEN** it SHALL reach "Up" status
- **AND** it SHALL not enter "Restarting" state
- **AND** it SHALL begin scheduling periodic tasks

#### Scenario: Backend service healthy startup
- **GIVEN** Docker Compose starts services
- **WHEN** the backend container initializes
- **THEN** it SHALL reach "Up" status
- **AND** it SHALL create database tables successfully
- **AND** the FastAPI application SHALL start on port 8000

### Requirement: Clear Error Reporting
The system SHALL provide clear error messages when services fail to start.

#### Scenario: Import error detection
- **GIVEN** a service fails due to ModuleNotFoundError
- **WHEN** checking service logs
- **THEN** the error SHALL clearly identify the missing module
- **AND** the stack trace SHALL show the import chain

#### Scenario: Syntax error detection
- **GIVEN** a service fails due to SyntaxError
- **WHEN** checking service logs
- **THEN** the error SHALL clearly identify the file and line number
- **AND** the error SHALL describe the syntax issue

