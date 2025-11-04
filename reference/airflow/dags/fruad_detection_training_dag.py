from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import logging
logger = logging.getLogger (__name__)
default_args = {
    'owner': 'kh',
    'depends_on_past': False,
    'start_date': datetime(year=2025, month=3, day=22),
    'execution_timeout': timedelta(minutes=120),
    'max_active_runs': 1,
}
def _train_model(**context):
    from fraud_detection_training import FraudDetectionTraining
    try:
        logger.info('Starting training...')
        trainer = FraudDetectionTraining()
        model, precision = trainer.train_model()
        return {'status': 'success', 'precision': precision}

    except Exception as e:
        logger.error(f'Failed to train model: {str(e)}')
        raise AirflowException(f'Failed to train model: {str(e)}')
with DAG(
    dag_id="fraud_detection_training",
    default_args=default_args,
    description='Fraud detection model training pipeline',
    schedule_interval='0 3 * * *',
    catchup=False,
    tags=['fraud', 'ML']
) as dag:

    validate_environment = BashOperator(
        task_id='validate_environment',
        bash_command='''
        echo "Validating environment..."
        test -f /app/config.yaml &&
        test -f /app/.env &&
        echo "Environment is valid!"
        '''
    )

training_task = PythonOperator(
    task_id='execute_training',
    python_callable=_train_model,
    provide_context=True,
)

cleanup_task = BashOperator(
    task_id='cleanup_resources',
    bash_command='rm -f /tmp/*.pkl',
    trigger_rule='all_done'
)

validate_environment >> training_task >> cleanup_task
dag.doc_md = """
### Fraud Detection Training Pipeline

Daily training of fraud detection model using:
- Transaction data from Kafka
- XBoost classifier with precision optimisation
- MLFlow for experiment tracking

"""


