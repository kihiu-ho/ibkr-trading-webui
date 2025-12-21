"""
Example Airflow DAG for IBKR Trading System
This is a simple DAG to verify Airflow and MLflow integration.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import mlflow

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def test_mlflow_connection():
    """Test MLflow connection and log a simple experiment"""
    print("Testing MLflow connection...")
    print(f"MLflow Tracking URI: {mlflow.get_tracking_uri()}")
    
    # Create a simple experiment
    experiment_name = "test_airflow_integration"
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run():
        # Log some test parameters and metrics
        mlflow.log_param("test_param", "airflow_test")
        mlflow.log_metric("test_metric", 123.45)
        print("Successfully logged to MLflow!")

def test_task():
    """Simple test task"""
    print("Hello from IBKR Trading Airflow!")
    print(f"Current time: {datetime.now()}")
    return "Success"

# Define the DAG
_dag_kwargs = dict(
    dag_id='example_ibkr_dag',
    default_args=default_args,
    description='Example DAG for IBKR Trading System',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['example', 'test'],
)

# Airflow 3: uses `schedule`; Airflow 2: still supports `schedule_interval`.
try:
    dag = DAG(**_dag_kwargs, schedule=None)
except TypeError:  # pragma: no cover
    dag = DAG(**_dag_kwargs, schedule_interval=None)

with dag:

    test_task_op = PythonOperator(
        task_id='test_task',
        python_callable=test_task,
    )

    mlflow_test_op = PythonOperator(
        task_id='test_mlflow_connection',
        python_callable=test_mlflow_connection,
    )

    # Set task dependencies
    test_task_op >> mlflow_test_op
