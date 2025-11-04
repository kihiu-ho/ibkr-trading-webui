# Airflow and MLflow Integration

This document describes the Airflow and MLflow integration added to the IBKR Trading WebUI system.

## Overview

The system now includes:
- **Apache Airflow** for workflow orchestration and task scheduling
- **MLflow** for ML experiment tracking and model registry
- **PostgreSQL** for Airflow and MLflow metadata storage
- **MinIO** for MLflow artifact storage (S3-compatible)

## Architecture

### Services Added

1. **PostgreSQL** (ibkr-postgres)
   - Hosts metadata for both Airflow and MLflow
   - Databases: `airflow` and `mlflow`
   - Port: Internal only (not exposed)

2. **MinIO Client** (ibkr-mc)
   - Creates the `mlflow` bucket on startup
   - One-time initialization service

3. **MLflow Server** (ibkr-mlflow-server)
   - Experiment tracking and model registry
   - Port: 5500
   - Backend: PostgreSQL
   - Artifact Storage: MinIO (S3-compatible)

4. **Airflow Services**:
   - **airflow-init**: Initializes database and creates admin user
   - **airflow-webserver**: Web UI (Port: 8080)
   - **airflow-scheduler**: Schedules DAG runs
   - **airflow-worker**: Executes tasks via Celery
   - **airflow-triggerer**: Handles deferrable operators

### Service Dependencies

```
Redis + PostgreSQL (parallel startup)
    ↓
MinIO
    ↓
MinIO Client (mc) - creates buckets
    ↓
MLflow Server + Airflow Init
    ↓
Airflow Webserver, Scheduler, Worker, Triggerer
```

## Configuration

### Environment Variables

Add these to your `.env` file (already in `env.example`):

```bash
# Airflow Configuration
AIRFLOW_UID=50000
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
AIRFLOW_PROJ_DIR=.

# MinIO (used by MLflow)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### Ports

| Service | Port | Description |
|---------|------|-------------|
| Airflow Web UI | 8080 | http://localhost:8080 |
| MLflow Server | 5500 | http://localhost:5500 |
| MinIO API | 9000 | S3-compatible storage |
| MinIO Console | 9001 | MinIO web UI |

## Usage

### Starting Services

```bash
# Start all services including Airflow and MLflow
docker-compose up -d

# Start only specific services
docker-compose up -d redis postgres minio mc mlflow-server airflow-webserver airflow-scheduler
```

### Accessing Airflow

1. Open http://localhost:8080
2. Login with:
   - Username: `airflow` (or value from `_AIRFLOW_WWW_USER_USERNAME`)
   - Password: `airflow` (or value from `_AIRFLOW_WWW_USER_PASSWORD`)

### Accessing MLflow

1. Open http://localhost:5500
2. No login required (add authentication if needed)

### Creating DAGs

Place your Airflow DAG files in the `dags/` directory:

```python
# dags/my_trading_dag.py
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import mlflow

def my_task():
    # Your trading logic here
    with mlflow.start_run():
        mlflow.log_param("symbol", "AAPL")
        mlflow.log_metric("profit", 123.45)

with DAG(
    'my_trading_dag',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
) as dag:
    
    task = PythonOperator(
        task_id='execute_strategy',
        python_callable=my_task,
    )
```

### Using MLflow in Trading Strategies

```python
import mlflow

# Set tracking URI (automatically set via environment)
# mlflow.set_tracking_uri("http://mlflow-server:5500")

# Create or get experiment
mlflow.set_experiment("trading_strategy_backtest")

# Start a run
with mlflow.start_run():
    # Log parameters
    mlflow.log_param("symbol", "NVDA")
    mlflow.log_param("strategy", "momentum")
    
    # Log metrics
    mlflow.log_metric("total_return", 15.2)
    mlflow.log_metric("sharpe_ratio", 1.8)
    
    # Log artifacts (charts, reports)
    mlflow.log_artifact("backtest_report.pdf")
    
    # Log model
    mlflow.sklearn.log_model(model, "trading_model")
```

## Directory Structure

```
.
├── dags/                       # Airflow DAG files
│   └── example_dag.py         # Example DAG
├── logs/
│   └── airflow/               # Airflow logs
├── plugins/                   # Airflow plugins
├── docker/
│   ├── airflow/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── mlflow/
│       ├── Dockerfile
│       └── requirements.txt
└── scripts/
    ├── init-multiple-dbs.sh   # PostgreSQL initialization
    └── wait-for-it.sh         # Service dependency helper
```

## Resource Allocation

### Memory Limits

| Service | Limit | Reserved |
|---------|-------|----------|
| PostgreSQL | 512MB | 256MB |
| Airflow Webserver | 1GB | 512MB |
| Airflow Scheduler | 1GB | 512MB |
| Airflow Worker | 1GB | 512MB |
| Airflow Triggerer | 512MB | 256MB |
| MLflow Server | 512MB | 256MB |

### Scaling Workers

To increase Airflow workers, modify `docker-compose.yml`:

```yaml
airflow-worker:
  # ...
  deploy:
    mode: replicated
    replicas: 2  # Change this number
```

## Troubleshooting

### Airflow Not Starting

1. Check logs: `docker-compose logs airflow-init`
2. Verify PostgreSQL is healthy: `docker-compose ps postgres`
3. Check environment variables in `.env`

### MLflow Connection Issues

1. Verify MinIO is running: `docker-compose ps minio`
2. Check bucket was created: `docker-compose logs mc`
3. Verify PostgreSQL connection: `docker-compose logs mlflow-server`

### Permission Issues (Linux)

```bash
# Set correct AIRFLOW_UID
export AIRFLOW_UID=$(id -u)
echo "AIRFLOW_UID=$AIRFLOW_UID" >> .env

# Fix permissions
mkdir -p logs/airflow dags plugins
sudo chown -R $AIRFLOW_UID:0 logs/airflow dags plugins
```

### Clearing Airflow Database

```bash
# Stop services
docker-compose down

# Remove volumes
docker volume rm ibkr_postgres_data

# Restart
docker-compose up -d
```

## Integration with Existing Services

### Sharing Redis

Airflow Celery workers use the same Redis instance as the existing backend Celery workers, but on the same broker URL. This is efficient and reduces resource usage.

### Environment Variables Propagation

All services have access to:
- `MLFLOW_TRACKING_URI`: Points to MLflow server
- `MLFLOW_S3_ENDPOINT_URL`: Points to MinIO for artifacts
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`: MinIO credentials

## Example Use Cases

### 1. Scheduled Strategy Backtests

Create a DAG that runs backtests daily and logs results to MLflow:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import mlflow

def run_backtest():
    mlflow.set_experiment("daily_backtest")
    with mlflow.start_run():
        # Run backtest
        results = execute_backtest()
        mlflow.log_metrics(results)

with DAG('daily_backtest', schedule_interval='@daily', start_date=datetime(2024, 1, 1)) as dag:
    PythonOperator(task_id='backtest', python_callable=run_backtest)
```

### 2. Model Training Pipeline

Train models periodically and track experiments:

```python
def train_model():
    with mlflow.start_run():
        model = train_trading_model()
        mlflow.sklearn.log_model(model, "model")
        mlflow.log_metrics({"accuracy": 0.95})
```

### 3. Strategy Optimization

Run parameter sweeps and track results:

```python
def optimize_strategy():
    for param in parameter_grid:
        with mlflow.start_run():
            mlflow.log_params(param)
            result = test_strategy(param)
            mlflow.log_metric("sharpe", result)
```

## Security Notes

1. **Default Credentials**: Change default Airflow and MinIO credentials in production
2. **Network Exposure**: Consider restricting ports with firewall rules
3. **Authentication**: Add authentication to MLflow if needed
4. **SSL/TLS**: Consider adding SSL for production deployments

## Performance Tuning

### Airflow

- Adjust worker replicas based on workload
- Configure parallelism in Airflow settings
- Use connection pooling for database

### MLflow

- Use batch logging for high-frequency metrics
- Consider separate artifact storage for large files
- Enable caching for model registry

## References

- [Airflow Documentation](https://airflow.apache.org/docs/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [MinIO Documentation](https://min.io/docs/minio/kubernetes/upstream/index.html)

## OpenSpec

This integration was implemented following the OpenSpec proposal:
- Change ID: `add-airflow-mlflow-orchestration`
- Proposal: `openspec/changes/add-airflow-mlflow-orchestration/proposal.md`
- Tasks: `openspec/changes/add-airflow-mlflow-orchestration/tasks.md`
- Spec: `openspec/changes/add-airflow-mlflow-orchestration/specs/workflow-orchestration/spec.md`

To validate: `openspec validate add-airflow-mlflow-orchestration --strict`

