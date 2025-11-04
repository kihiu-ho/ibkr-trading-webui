"""
IBKR Trading Strategy DAG

This DAG implements a complete trading workflow:
1. Environment validation
2. Market status check
3. IBKR authentication check
4. Market data fetching
5. LLM signal generation
6. Order placement
7. MLflow tracking

The DAG is designed to be instantiated per strategy with custom parameters.
"""
import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# Import custom operators and sensors
import sys
sys.path.append('/opt/airflow/plugins')

from ibkr_plugin.operators.market_data_operator import IBKRMarketDataOperator
from ibkr_plugin.operators.signal_operator import LLMSignalGeneratorOperator
from ibkr_plugin.operators.order_operator import OrderPlacementOperator
from ibkr_plugin.sensors.market_sensor import MarketOpenSensor
from ibkr_plugin.sensors.auth_sensor import IBKRAuthSensor
from ibkr_plugin.hooks.mlflow_tracker import MLflowTracker
from ibkr_plugin.hooks.config_loader import config_loader


logger = logging.getLogger(__name__)


# Default arguments for all tasks
default_args = {
    'owner': 'trading',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1),
}


def start_mlflow_run(**context):
    """Start MLflow tracking run for the workflow."""
    dag_run = context['dag_run']
    execution_date = context['execution_date']
    
    # Get strategy ID from DAG conf or use default
    strategy_id = dag_run.conf.get('strategy_id', 1) if dag_run.conf else 1
    
    # Initialize MLflow tracker
    tracker = MLflowTracker()
    
    # Start run
    run_name = f"strategy_{strategy_id}_{execution_date.strftime('%Y%m%d_%H%M%S')}"
    active_run = tracker.start_run(
        run_name=run_name,
        tags={
            "strategy_id": str(strategy_id),
            "dag_id": context['dag'].dag_id,
            "dag_run_id": dag_run.run_id,
            "execution_date": execution_date.isoformat()
        }
    )
    
    # Log workflow parameters
    tracker.log_params({
        "workflow_type": "trading_strategy",
        "strategy_id": strategy_id,
        "dag_id": context['dag'].dag_id
    })
    
    logger.info(f"Started MLflow run: {active_run.info.run_id}")
    
    # Push run ID to XCom for other tasks
    context['task_instance'].xcom_push(key='mlflow_run_id', value=active_run.info.run_id)
    
    return active_run.info.run_id


def end_mlflow_run(**context):
    """End MLflow tracking run."""
    ti = context['task_instance']
    run_id = ti.xcom_pull(key='mlflow_run_id', task_ids='start_mlflow_tracking')
    
    if run_id:
        tracker = MLflowTracker()
        
        # Check if workflow succeeded
        dag_run = context['dag_run']
        status = "FINISHED" if dag_run.get_state() == 'success' else "FAILED"
        
        tracker.end_run(status=status)
        logger.info(f"Ended MLflow run {run_id} with status: {status}")


# Create the DAG
dag = DAG(
    dag_id='ibkr_trading_strategy',
    default_args=default_args,
    description='Complete IBKR trading workflow with MLflow tracking',
    schedule_interval=None,  # Triggered programmatically or per-strategy schedule
    max_active_runs=1,
    catchup=False,
    tags=['trading', 'ibkr', 'strategy', 'mlflow'],
    # Allow passing strategy_id and other params via trigger
    params={
        'strategy_id': 1,
        'symbols': ['AAPL', 'GOOGL', 'MSFT'],
        'dry_run': True
    }
)

with dag:
    # Task 1: Start MLflow tracking
    start_mlflow = PythonOperator(
        task_id='start_mlflow_tracking',
        python_callable=start_mlflow_run,
        provide_context=True
    )
    
    # Task 2: Validate environment
    validate_env = BashOperator(
        task_id='validate_environment',
        bash_command='''
        echo "=== Environment Validation ==="
        echo "Checking required environment variables..."
        
        if [ -z "$DATABASE_URL" ]; then
            echo "ERROR: DATABASE_URL not set"
            exit 1
        fi
        
        if [ -z "$IBKR_API_BASE_URL" ]; then
            echo "ERROR: IBKR_API_BASE_URL not set"
            exit 1
        fi
        
        if [ ! -f /opt/airflow/config/trading_workflow.yaml ]; then
            echo "ERROR: Configuration file not found"
            exit 1
        fi
        
        echo "✓ All environment checks passed"
        ''',
    )
    
    # Task 3: Check if market is open
    check_market = MarketOpenSensor(
        task_id='check_market_open',
        poke_interval=60,  # Check every minute
        timeout=300,  # Timeout after 5 minutes
        mode='poke'  # Use poke mode for quick checks
    )
    
    # Task 4: Check IBKR authentication
    check_auth = IBKRAuthSensor(
        task_id='check_ibkr_auth',
        poke_interval=30,
        timeout=300,
        attempt_reauth=True
    )
    
    # Task 5: Fetch market data
    fetch_data = IBKRMarketDataOperator(
        task_id='fetch_market_data',
        symbols="{{ params.symbols }}",  # From DAG params
        fields=["31", "84", "86"],  # last, bid, ask
        strategy_id="{{ params.strategy_id }}",
        track_mlflow=True
    )
    
    # Task 6: Generate trading signal with LLM
    generate_signal = LLMSignalGeneratorOperator(
        task_id='llm_signal_generation',
        strategy_id="{{ params.strategy_id }}",
        track_mlflow=True
    )
    
    # Task 7: Place orders based on signal
    place_orders = OrderPlacementOperator(
        task_id='place_orders',
        strategy_id="{{ params.strategy_id }}",
        min_confidence=0.7,
        dry_run="{{ params.dry_run }}",
        track_mlflow=True
    )
    
    # Task 8: End MLflow tracking
    end_mlflow = PythonOperator(
        task_id='end_mlflow_tracking',
        python_callable=end_mlflow_run,
        provide_context=True,
        trigger_rule='all_done'  # Run even if previous tasks fail
    )
    
    # Task 9: Cleanup
    cleanup = BashOperator(
        task_id='cleanup',
        bash_command='echo "Workflow complete. Check Airflow UI and MLflow for results."',
        trigger_rule='all_done'
    )
    
    # Define task dependencies
    start_mlflow >> validate_env >> check_market >> check_auth >> fetch_data
    fetch_data >> generate_signal >> place_orders >> end_mlflow >> cleanup


if __name__ == "__main__":
    dag.test()

