# Airflow & MLflow Quick Start Guide

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites
- Docker and Docker Compose installed
- `.env` file configured (see `env.example`)

### 2. Start Services
```bash
# Start all services (including Airflow and MLflow)
docker-compose up -d

# Or start just Airflow/MLflow services
docker-compose up -d redis postgres minio mc mlflow-server airflow-webserver airflow-scheduler airflow-worker
```

### 3. Access Web Interfaces
- **Airflow UI**: http://localhost:8080
  - Username: `airflow`
  - Password: `airflow`
  
- **MLflow UI**: http://localhost:5500
  - No authentication required

- **MinIO Console**: http://localhost:9001
  - Username: `minioadmin`
  - Password: `minioadmin`

## 📋 Test the Integration

Run the automated test script:
```bash
./test-airflow-mlflow.sh
```

This will:
- Validate configuration
- Start core services
- Build images
- Test connectivity
- Verify web UIs are accessible

## 📝 Create Your First DAG

1. Create a file in `dags/` directory:
```bash
touch dags/my_first_dag.py
```

2. Add a simple DAG:
```python
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import mlflow

def my_task():
    mlflow.set_experiment("my_experiment")
    with mlflow.start_run():
        mlflow.log_param("task", "test")
        mlflow.log_metric("value", 42)
    print("Task completed!")

with DAG(
    'my_first_dag',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,  # Manual trigger
    catchup=False,
) as dag:
    
    PythonOperator(
        task_id='my_task',
        python_callable=my_task,
    )
```

3. Trigger the DAG in Airflow UI
4. View results in MLflow UI

## 🔧 Common Commands

### Service Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart a specific service
docker-compose restart airflow-scheduler

# View logs
docker-compose logs -f airflow-webserver
docker-compose logs -f mlflow-server
```

### Airflow Commands
```bash
# List DAGs
docker-compose exec airflow-webserver airflow dags list

# Trigger a DAG
docker-compose exec airflow-webserver airflow dags trigger my_first_dag

# Check DAG status
docker-compose exec airflow-webserver airflow dags list-runs -d my_first_dag
```

### MLflow Commands
```bash
# Access MLflow CLI
docker-compose exec mlflow-server mlflow --help

# List experiments
docker-compose exec mlflow-server mlflow experiments list

# Search runs
docker-compose exec mlflow-server mlflow runs list --experiment-id 0
```

## 📊 Service Status Check

```bash
# Check all services
docker-compose ps

# Check specific services
docker-compose ps | grep airflow
docker-compose ps | grep mlflow

# Check service health
docker-compose ps postgres  # Should show "healthy"
docker-compose ps minio     # Should show "healthy"
```

## 🐛 Troubleshooting

### Airflow UI Not Accessible
```bash
# Check if webserver is running
docker-compose ps airflow-webserver

# Check logs
docker-compose logs airflow-webserver

# Restart webserver
docker-compose restart airflow-webserver
```

### MLflow Connection Issues
```bash
# Check MLflow logs
docker-compose logs mlflow-server

# Verify MinIO bucket exists
docker-compose exec minio mc ls minio/mlflow

# Check PostgreSQL connection
docker-compose exec postgres psql -U mlflow -d mlflow -c "\dt"
```

### Permission Issues (Linux)
```bash
# Set correct ownership
export AIRFLOW_UID=$(id -u)
echo "AIRFLOW_UID=$AIRFLOW_UID" >> .env
sudo chown -R $AIRFLOW_UID:0 logs/airflow dags plugins
```

### Reset Everything
```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker volume rm ibkr_postgres_data ibkr_minio_data

# Start fresh
docker-compose up -d
```

## 📖 Next Steps

1. **Read Full Documentation**: See `AIRFLOW_MLFLOW_SETUP.md` for comprehensive guide
2. **Review Implementation**: See `AIRFLOW_MLFLOW_IMPLEMENTATION_COMPLETE.md`
3. **Example DAGs**: Check `dags/example_dag.py` for reference
4. **OpenSpec Details**: View `openspec/changes/add-airflow-mlflow-orchestration/`

## 💡 Key Features

### Airflow
- ✅ Web-based UI for DAG management
- ✅ Scheduled and manual DAG execution
- ✅ Task dependencies and workflows
- ✅ Celery executor for distributed tasks
- ✅ Integrated with existing Redis

### MLflow
- ✅ Experiment tracking
- ✅ Model registry
- ✅ Artifact storage (MinIO/S3)
- ✅ Parameter and metric logging
- ✅ Model versioning

### Integration
- ✅ Shared infrastructure (Redis, MinIO)
- ✅ Automatic environment configuration
- ✅ Easy DAG creation for ML workflows
- ✅ Persistent storage for experiments

## 🔗 Useful Links

- Airflow Documentation: https://airflow.apache.org/docs/
- MLflow Documentation: https://mlflow.org/docs/latest/
- Reference Airflow Setup: `reference/airflow/`
- Test Script: `test-airflow-mlflow.sh`

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs [service-name]`
2. Review documentation: `AIRFLOW_MLFLOW_SETUP.md`
3. Check OpenSpec proposal: `openspec/changes/add-airflow-mlflow-orchestration/`

---

**Status**: ✅ Ready to Use  
**Version**: 1.0  
**Last Updated**: November 2, 2025

