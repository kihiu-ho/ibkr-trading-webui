# IBKR Trading Workflow with Airflow - Complete Guide

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

## 🎯 Overview

The IBKR Trading Workflow system uses **Apache Airflow** for orchestrating automated trading strategies. It provides:

- **Scheduled Execution**: Run strategies on a cron-like schedule
- **Dependency Management**: Clear task dependencies with automatic retry logic
- **Visual Monitoring**: Monitor workflows via Airflow UI
- **MLflow Integration**: Track all executions and results
- **Error Handling**: Robust error handling with alerts
- **Scalability**: Run multiple strategies concurrently

### Key Features

✅ **Automated Trading**: Strategies execute automatically on schedule  
✅ **LLM-Powered Signals**: Generate trading signals using AI/ML  
✅ **Risk Management**: Built-in risk assessment and validation  
✅ **Reproducibility**: Full MLflow tracking for every execution  
✅ **Observability**: Complete visibility into workflow execution  
✅ **Reliability**: Retry logic and error recovery  

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Airflow Scheduler                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         IBKR Trading Strategy DAG                      │  │
│  │                                                         │  │
│  │  1. Start MLflow → 2. Validate Env → 3. Check Market  │  │
│  │  4. Check Auth → 5. Fetch Data → 6. Generate Signal   │  │
│  │  7. Place Orders → 8. End MLflow → 9. Cleanup         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              Backend API Services                            │
│   (IBKR, Charts, Signals, Orders, Portfolio)                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│   External: IBKR Gateway, MinIO, MLflow, PostgreSQL         │
└─────────────────────────────────────────────────────────────┘
```

### Workflow Steps

1. **Start MLflow Tracking**: Initialize experiment tracking
2. **Validate Environment**: Check configuration and dependencies
3. **Check Market Open**: Wait for market to open (sensor)
4. **Check IBKR Auth**: Verify IBKR session is valid (sensor)
5. **Fetch Market Data**: Get real-time market data for symbols
6. **Generate Signal**: Use LLM to analyze and generate trading signals
7. **Place Orders**: Execute orders based on signals (with risk checks)
8. **End MLflow Tracking**: Log final metrics and status
9. **Cleanup**: Finalize workflow execution

## 📦 Components

### Custom Airflow Hooks

#### `IBKRHook`
HTTP client for interacting with IBKR API via backend service.

**Key Methods**:
- `check_auth_status()`: Verify authentication
- `get_market_data()`: Fetch market data snapshots
- `place_order()`: Place trading orders
- `get_portfolio_positions()`: Get current positions

#### `MLflowTracker`
MLflow integration for experiment tracking.

**Key Methods**:
- `start_run()`: Start tracking run
- `log_metrics()`: Log workflow metrics
- `log_artifacts()`: Log charts and reports
- `end_run()`: Finalize tracking

#### `ConfigLoader`
Load and manage workflow configuration from YAML.

**Key Methods**:
- `get_backend_config()`: Get backend API settings
- `get_mlflow_config()`: Get MLflow settings
- `get_market_config()`: Get market hours/days

### Custom Operators

#### `IBKRMarketDataOperator`
Fetch market data for specified symbols.

**Parameters**:
- `symbols`: List of symbols to fetch (e.g., `['AAPL', 'GOOGL']`)
- `fields`: Data fields (default: last, bid, ask)
- `strategy_id`: Strategy ID for tracking
- `track_mlflow`: Enable MLflow tracking

**Output**: Market data summary via XCom

#### `LLMSignalGeneratorOperator`
Generate trading signals using LLM analysis.

**Parameters**:
- `strategy_id`: Strategy ID
- `track_mlflow`: Enable MLflow tracking

**Output**: Trading signal (BUY/SELL/HOLD) with confidence score

#### `OrderPlacementOperator`
Place orders based on trading signals.

**Parameters**:
- `strategy_id`: Strategy ID
- `min_confidence`: Minimum signal confidence (default: 0.7)
- `max_position_size`: Max position size in dollars
- `dry_run`: If True, simulate orders without placing
- `track_mlflow`: Enable MLflow tracking

**Output**: Order execution results

### Sensors

#### `MarketOpenSensor`
Wait for market to open before executing trades.

**Parameters**:
- `market_config`: Market hours configuration (from YAML)
- `poke_interval`: Check interval in seconds
- `timeout`: Max wait time

**Behavior**: Returns `True` when market is open (Monday-Friday, 9:30 AM - 4:00 PM ET)

#### `IBKRAuthSensor`
Check IBKR authentication status.

**Parameters**:
- `attempt_reauth`: Attempt reauthentication if needed
- `poke_interval`: Check interval
- `timeout`: Max wait time

**Behavior**: Returns `True` when authenticated, attempts reauth if enabled

## 🚀 Getting Started

### Prerequisites

1. **IBKR Gateway Running**:
   ```bash
   docker ps | grep ibkr-gateway
   ```

2. **Backend Services Running**:
   ```bash
   docker ps | grep ibkr-backend
   ```

3. **Airflow Services Running**:
   ```bash
   docker ps | grep airflow
   ```

### Quick Start

1. **Access Airflow UI**:
   ```
   http://localhost:8080
   
   Username: airflow
   Password: airflow
   ```

2. **Trigger Trading Workflow**:
   - Navigate to DAGs page
   - Find `ibkr_trading_strategy`
   - Click "Trigger DAG"
   - Provide parameters:
     ```json
     {
       "strategy_id": 1,
       "symbols": ["AAPL", "GOOGL", "MSFT"],
       "dry_run": true
     }
     ```

3. **Monitor Execution**:
   - Click on DAG run to see graph view
   - Click on tasks to see logs
   - Check MLflow for metrics: http://localhost:5500

### Configuration

The workflow is configured via `/opt/airflow/config/trading_workflow.yaml`:

```yaml
# Backend API settings
backend:
  base_url: "http://backend:8000"
  timeout: 30
  retry_attempts: 3

# MLflow settings
mlflow:
  tracking_uri: "http://mlflow-server:5500"
  experiment_name: "ibkr_trading_workflows"

# Market settings
market:
  trading_hours:
    start: "09:30"  # 9:30 AM ET
    end: "16:00"    # 4:00 PM ET
    timezone: "America/New_York"
  trading_days: [1, 2, 3, 4, 5]  # Mon-Fri

# Default workflow settings
defaults:
  owner: "trading"
  retries: 3
  retry_delay: 300  # 5 minutes
```

## 💻 Usage

### Running a Strategy

#### Via Airflow UI

1. Navigate to http://localhost:8080
2. Find `ibkr_trading_strategy` DAG
3. Click "Trigger DAG w/ config"
4. Provide configuration:
   ```json
   {
     "strategy_id": 1,
     "symbols": ["AAPL"],
     "dry_run": true
   }
   ```
5. Click "Trigger"

#### Via Airflow CLI

```bash
# Trigger with default params
docker exec ibkr-airflow-scheduler \
  airflow dags trigger ibkr_trading_strategy

# Trigger with custom params
docker exec ibkr-airflow-scheduler \
  airflow dags trigger ibkr_trading_strategy \
  --conf '{"strategy_id": 1, "symbols": ["AAPL"], "dry_run": true}'
```

#### Via API

```bash
curl -X POST "http://localhost:8080/api/v1/dags/ibkr_trading_strategy/dagRuns" \
  -H "Content-Type: application/json" \
  -u "airflow:airflow" \
  -d '{
    "conf": {
      "strategy_id": 1,
      "symbols": ["AAPL", "GOOGL"],
      "dry_run": true
    }
  }'
```

### Scheduling a Strategy

To run a strategy on a schedule, create a custom DAG:

```python
# airflow/dags/my_strategy_dag.py
from airflow import DAG
from airflow.utils.dates import days_ago
from ibkr_trading_strategy_dag import create_trading_dag

# Create scheduled DAG for your strategy
my_dag = DAG(
    dag_id='my_momentum_strategy',
    description='My momentum strategy',
    schedule_interval='0 9 * * 1-5',  # 9 AM weekdays
    start_date=days_ago(1),
    catchup=False,
    default_args={
        'strategy_id': 1,
        'symbols': ['AAPL', 'GOOGL', 'MSFT'],
        'dry_run': False  # Live trading!
    }
)
```

## 📊 Monitoring

### Airflow UI

- **DAG View**: See all workflows and their status
- **Graph View**: Visualize task dependencies
- **Task Logs**: View detailed execution logs
- **Gantt Chart**: See execution timeline
- **Task Duration**: Monitor performance

### MLflow UI

Access at http://localhost:5500

- **Experiments**: See all workflow runs
- **Metrics**: View performance metrics
- **Parameters**: Compare configurations
- **Artifacts**: Download charts and reports

**Key Metrics**:
- `symbols_count`: Number of symbols analyzed
- `data_points`: Market data points fetched
- `fetch_duration_seconds`: Data fetch time
- `signal_confidence`: Signal confidence score
- `order_quantity`: Shares traded
- `order_value`: Order value in dollars

### Logs

```bash
# Airflow scheduler logs
docker logs ibkr-airflow-scheduler --tail 100 -f

# Airflow worker logs
docker logs ibkr-airflow-worker --tail 100 -f

# Specific task logs
docker exec ibkr-airflow-scheduler \
  airflow tasks logs ibkr_trading_strategy fetch_market_data 2024-01-01
```

## 🔧 Troubleshooting

### Common Issues

#### 1. DAG Not Appearing in UI

**Problem**: New DAG doesn't show up in Airflow UI

**Solutions**:
```bash
# Check DAG syntax
docker exec ibkr-airflow-scheduler \
  python /opt/airflow/dags/ibkr_trading_strategy_dag.py

# Check Airflow logs for parsing errors
docker logs ibkr-airflow-scheduler | grep -i error

# Force DAG refresh
docker exec ibkr-airflow-scheduler \
  airflow dags list-import-errors
```

#### 2. Task Stuck in "Running"

**Problem**: Task shows as running but making no progress

**Solutions**:
```bash
# Check worker logs
docker logs ibkr-airflow-worker --tail 100 -f

# Check task instance state
docker exec ibkr-airflow-scheduler \
  airflow tasks state ibkr_trading_strategy fetch_market_data 2024-01-01

# Clear task state
docker exec ibkr-airflow-scheduler \
  airflow tasks clear ibkr_trading_strategy -t fetch_market_data -y
```

#### 3. IBKR Authentication Fails

**Problem**: `check_ibkr_auth` sensor times out

**Solutions**:
```bash
# Check IBKR Gateway status
curl -k https://localhost:5055/v1/api/tickle

# Check backend connectivity
curl http://localhost:8000/api/ibkr/auth/status

# Manually authenticate via browser
open https://localhost:5055
```

#### 4. Market Closed Sensor Timeout

**Problem**: `check_market_open` sensor waits too long

**Solutions**:
- Increase timeout parameter
- Run during market hours
- Or skip sensor for testing:
  ```python
  check_market = BashOperator(
      task_id='check_market_open',
      bash_command='echo "Skipping market check for testing"'
  )
  ```

#### 5. MLflow Connection Error

**Problem**: Can't connect to MLflow

**Solutions**:
```bash
# Check MLflow server
docker ps | grep mlflow
curl http://localhost:5500/health

# Check environment variable
docker exec ibkr-airflow-scheduler env | grep MLFLOW

# Verify network connectivity
docker exec ibkr-airflow-scheduler \
  curl -v http://mlflow-server:5500/
```

## 🚀 Advanced Topics

### Custom Operators

Create custom operators for specific workflow needs:

```python
# airflow/plugins/ibkr_plugin/operators/my_operator.py
from airflow.models import BaseOperator
from ibkr_plugin.hooks.ibkr_hook import IBKRHook

class MyCustomOperator(BaseOperator):
    def __init__(self, my_param, **kwargs):
        super().__init__(**kwargs)
        self.my_param = my_param
    
    def execute(self, context):
        ibkr_hook = IBKRHook()
        # Your custom logic here
        result = ibkr_hook.some_method(self.my_param)
        return result
```

### Dynamic DAG Generation

Generate DAGs dynamically from database:

```python
# airflow/dags/dynamic_strategies.py
from backend.models import Strategy
from ibkr_trading_strategy_dag import create_trading_dag

# Fetch active strategies from database
strategies = Strategy.query.filter_by(active=True).all()

# Create a DAG for each strategy
for strategy in strategies:
    dag = create_trading_dag(
        dag_id=f"strategy_{strategy.id}",
        schedule=strategy.schedule,
        strategy_id=strategy.id,
        symbols=strategy.symbols
    )
    globals()[f"strategy_{strategy.id}"] = dag
```

### Backfilling

Run workflow for historical dates:

```bash
# Backfill last 7 days
docker exec ibkr-airflow-scheduler \
  airflow dags backfill ibkr_trading_strategy \
  --start-date 2024-01-01 \
  --end-date 2024-01-07
```

### Parallel Execution

Run multiple strategies in parallel by adjusting pool configuration:

```bash
# Check current pools
docker exec ibkr-airflow-scheduler \
  airflow pools list

# Create trading pool
docker exec ibkr-airflow-scheduler \
  airflow pools set trading_pool 5 "Trading strategy pool"

# Assign tasks to pool
place_orders = OrderPlacementOperator(
    task_id='place_orders',
    pool='trading_pool',
    ...
)
```

## 📚 Additional Resources

- **Airflow Documentation**: https://airflow.apache.org/docs/
- **MLflow Documentation**: https://mlflow.org/docs/latest/index.html
- **IBKR API Documentation**: https://interactivebrokers.github.io/cpwebapi/

## 🎯 Next Steps

1. ✅ **Test with Dry Run**: Run workflows with `dry_run=true` first
2. ✅ **Monitor Results**: Check Airflow and MLflow UIs
3. ✅ **Validate Signals**: Review LLM-generated signals
4. ✅ **Go Live**: Set `dry_run=false` when confident
5. ✅ **Add Strategies**: Create more DAGs for different strategies
6. ✅ **Optimize**: Tune parameters based on performance

## 📞 Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review Airflow logs
3. Check MLflow experiments
4. Review backend API logs

---

**Happy Trading! 📈🚀**

