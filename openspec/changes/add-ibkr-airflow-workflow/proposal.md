# Add IBKR Airflow Trading Workflow

## Why

The IBKR trading system needs **automated, scheduled workflow orchestration** for reliable execution of trading strategies. Currently, workflows are triggered manually or via simple Celery tasks without comprehensive orchestration, monitoring, or retry logic. Airflow provides production-grade workflow management with:
- **Scheduled execution** with cron-like scheduling
- **Dependency management** between workflow tasks  
- **Retry logic** and error handling
- **Visual monitoring** and debugging via Airflow UI
- **MLflow integration** for experiment tracking and model management
- **Scalability** for multiple concurrent strategies

## What Changes

- Create **Airflow DAGs** for IBKR trading workflows:
  - Market data collection and caching
  - Technical indicator calculation
  - Chart generation and analysis
  - LLM-based signal generation
  - Risk assessment and validation
  - Order placement and execution
  - Portfolio monitoring and updates
  - Performance tracking with MLflow

- **Integrate with existing services**:
  - IBKR Gateway authentication
  - Database (strategies, signals, orders, positions)
  - Redis (Celery broker)
  - MinIO (chart storage)
  - MLflow (experiment tracking)

- **Add workflow configuration**:
  - YAML configuration for workflows
  - DAG templates for different strategy types
  - Retry policies and error handling
  - Alert mechanisms for failures

- **Create supporting modules**:
  - Python operators for IBKR operations
  - Sensors for market data availability
  - Hooks for IBKR API interaction
  - MLflow tracking integration

## Impact

### Affected Specs
- `trading-workflow` - Add Airflow orchestration requirements
- `strategy-integration` - May need updates for Airflow scheduling
- `order-management` - Integration with Airflow tasks

### Affected Code
- `docker-compose.yml` - Already has Airflow services
- `docker/airflow/` - Airflow Dockerfile and requirements
- New: `airflow/dags/` - Airflow DAG definitions
- New: `airflow/plugins/` - Custom Airflow operators/hooks
- New: `airflow/config/` - Workflow configurations
- Backend services - Integration points for Airflow

### Benefits
- ✅ **Automated execution**: Strategies run on schedule without manual intervention
- ✅ **Reliability**: Built-in retry logic and error handling
- ✅ **Observability**: Visual workflow monitoring and debugging
- ✅ **Scalability**: Handle multiple strategies concurrently
- ✅ **Reproducibility**: MLflow tracking for all workflow executions
- ✅ **Maintainability**: Declarative workflow definitions

### Risks
- **Complexity**: Airflow adds operational overhead
  - *Mitigation*: Use simplified setup, clear documentation
- **Learning curve**: Team needs to learn Airflow concepts
  - *Mitigation*: Provide reference implementations, training docs
- **Resource usage**: Airflow services consume memory/CPU
  - *Mitigation*: Already integrated, optimize configurations

