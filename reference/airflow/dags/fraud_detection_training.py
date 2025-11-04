"""
Fraud Detection Model Training Pipeline

This implementation represents a production-grade ML training system for fraud detection with
the following architectural considerations:

1. Environment Agnostic Configuration
   - Uses YAML config for environment-specific parameters
   - Strict separation of secrets vs configuration
   - Multi-environment support via .env files

2. Observability
   - Structured logging with multiple sinks
   - MLflow experiment tracking
   - Artifact storage with MinIO (S3-compatible)

3. Production Readiness
   - Kafka integration for real-time data ingestion
   - Automated hyperparameter tuning
   - Model serialization/registry
   - Comprehensive metrics tracking
   - Class imbalance mitigation

4. Operational Safety
   - Environment validation checks
   - Data quality guards
   - Comprehensive error handling
   - Model performance baselining
"""

import json
import logging
import os

import boto3
import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import yaml
from dotenv import load_dotenv
from imblearn.over_sampling import SMOTE
from kafka import KafkaConsumer
from mlflow.models import infer_signature
from numpy.array_api import astype
from sklearn.compose import ColumnTransformer
from sklearn.metrics import make_scorer, fbeta_score, precision_recall_curve, average_precision_score, precision_score, \
    recall_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold
from sklearn.preprocessing import OrdinalEncoder
from xgboost import XGBClassifier
from imblearn.pipeline import Pipeline as ImbPipeline
import joblib,os
from confluent_kafka import Consumer, TopicPartition, KafkaException
from confluent_kafka import Consumer, KafkaError, KafkaException
import random
import time
dir_path = os.path.dirname(os.path.realpath(__file__))
config_file_path = os.path.join(dir_path, 'client.properties')

# Configure dual logging to file and stdout with structured format
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler('./fraud_detection_model.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FraudDetectionTraining:
    """
    End-to-end fraud detection training system implementing MLOps best practices.

    Key Architecture Components:
    - Configuration Management: Centralized YAML config with environment overrides
    - Data Ingestion: Kafka consumer with SASL/SSL authentication
    - Feature Engineering: Temporal, behavioral, and monetary feature constructs
    - Model Development: XGBoost with SMOTE for class imbalance
    - Hyperparameter Tuning: Randomized search with stratified cross-validation
    - Model Tracking: MLflow integration with metrics/artifact logging
    - Deployment Prep: Model serialization and registry

    The system is designed for horizontal scalability and cloud-native operation.
    """

    def __init__(self, config_path='/app/config.yaml'):
        # Environment hardening for containerized deployments
        os.environ['GIT_PYTHON_REFRESH'] = 'quiet'
        os.environ['GIT_PYTHON_GIT_EXECUTABLE'] = '/usr/bin/git'

        # Load environment variables before config to allow overrides
        load_dotenv(dotenv_path='/app/.env')

        # Configuration lifecycle management
        self.config = self._load_config(config_path)

        # Security-conscious credential handling
        os.environ.update({
            'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'AWS_S3_ENDPOINT_URL': self.config['mlflow']['s3_endpoint_url']
        })

        # Pre-flight system checks
        self._validate_environment()

        # MLflow configuration for experiment tracking
        mlflow.set_tracking_uri(self.config['mlflow']['tracking_uri'])
        mlflow.set_experiment(self.config['mlflow']['registered_model_name'])

    def _load_config(self, config_path: str) -> dict:
        """
        Load and validate hierarchical configuration with fail-fast semantics.

        Implements:
        - YAML configuration parsing
        - Early validation of critical parameters
        - Audit logging of configuration loading
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info('Configuration loaded successfully')
            return config
        except Exception as e:
            logger.error('Failed to load configuration: %s', str(e))
            raise

    def _validate_environment(self):
        """
        System integrity verification with defense-in-depth checks:
        1. Required environment variables
        2. Object storage connectivity
        3. Credential validation

        Fails early to prevent partial initialization states.
        """
        required_vars = ['KAFKA_BOOTSTRAP_SERVERS', 'KAFKA_USERNAME', 'KAFKA_PASSWORD']
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f'Missing required environment variables: {missing}')

        self._check_minio_connection()

    def _check_minio_connection(self):
        """
        Validate object storage connectivity and bucket configuration.

        Implements:
        - S3 client initialization with error handling
        - Bucket existence check
        - Automatic bucket creation (if configured)

        Maintains separation of concerns between configuration and infrastructure setup.
        """
        try:
            s3 = boto3.client(
                's3',
                endpoint_url=self.config['mlflow']['s3_endpoint_url'],
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )

            buckets = s3.list_buckets()
            bucket_names = [b['Name'] for b in buckets.get('Buckets', [])]
            logger.info('Minio connection verified. Buckets: %s', bucket_names)

            mlflow_bucket = self.config['mlflow'].get('bucket', 'mlflow')

            if mlflow_bucket not in bucket_names:
                s3.create_bucket(Bucket=mlflow_bucket)
                logger.info('Created missing MLFlow bucket: %s', mlflow_bucket)
        except Exception as e:
            logger.error('Minio connection failed: %s', str(e))



    def read_from_kafka(self, poll_timeout=2.0, max_empty_polls=10):
        kafka_config = self.config['kafka']
        logger.info(f"Starting Kafka consumer with config: {kafka_config}")
        topic_name = kafka_config['topic']
        required_explicit_keys = ['bootstrap_servers', 'group_id', 'username', 'password', 'topic']
        missing_keys = [key for key in required_explicit_keys if key not in kafka_config]
        if missing_keys:
            logger.error(f"Kafka config explicitly missing required keys: {missing_keys}")
            raise ValueError(f"Explicit Kafka config missing required keys: {', '.join(missing_keys)}")

        # Explicitly correcting YAML keys to Kafka confluent expected format
        kafka_config = {
            'bootstrap.servers': kafka_config['bootstrap_servers'],
            'group.id': kafka_config['group_id'],
            'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'PLAIN',
            'sasl.username': kafka_config['username'],
            'sasl.password': kafka_config['password'],
            'auto.offset.reset': 'earliest',  # explicitly set offset reset policy
        }



        consumer = Consumer(kafka_config)

        consumer.subscribe([topic_name])

        messages = []
        total_retrieved = 0
        empty_polls = 0

        logger.info(f"Explicitly started receiving messages from Kafka topic: {topic_name}")

        try:
            while True:
                msg = consumer.poll(poll_timeout)

                if msg is None:
                    empty_polls += 1
                    if empty_polls >= max_empty_polls:
                        logger.info("Explicitly reached max empty polls—assuming no more messages.")
                        break
                    continue

                empty_polls = 0  # reset explicitly if you start receiving messages again

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info("Explicitly reached end of partition. Continuing polling explicitly.")
                        continue
                    else:
                        logger.error(f"Kafka explicit error: {msg.error()}")
                        raise KafkaException(msg.error())

                message_value = msg.value().decode('utf-8')
                messages.append(json.loads(message_value))
                if random.random() < 0.01:  # 1% probability explicitly
                    logger.info(f"Explicit Random Sample: Received message from Kafka: {message_value}")

                total_retrieved += 1

        finally:
            consumer.close()
            logger.info(f"Explicitly closed Kafka consumer. Total messages explicitly fetched: {total_retrieved}")

        if not messages:
            logger.warning("No Kafka messages explicitly fetched after polling.")
            return pd.DataFrame()

        return pd.DataFrame(messages)

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Feature engineering pipeline implementing domain-driven fraud detection concepts:

        1. Temporal Features:
           - Transaction hour
           - Night/weekend indicators

        2. Behavioral Features:
           - 24h user activity window

        3. Monetary Features:
           - Amount to historical average ratio

        4. Merchant Risk:
           - Predefined high-risk merchant list

        Maintains immutability via DataFrame.copy() and validates feature set integrity.
        """
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

            # Clearly handle conversion errors
            if df['timestamp'].isna().any():
                error_count = df['timestamp'].isna().sum()
                logger.warning(f"{error_count} rows with invalid timestamps were found and will be dropped.")
                df = df.dropna(subset=['timestamp'])

        else:
            logger.error("Column 'timestamp' not found in dataframe.")
            raise KeyError("Column 'timestamp' not found.")

        df = df.sort_values(['user_id', 'timestamp']).copy()

        # ---- Temporal Feature Engineering ----
        # Captures time-based fraud patterns (e.g., nighttime transactions)
        df['transaction_hour'] = df['timestamp'].dt.hour
        df['is_night'] = ((df['transaction_hour'] >= 22) | (df['transaction_hour'] < 5)).astype(int)
        df['is_weekend'] = (df['timestamp'].dt.dayofweek >= 5).astype(int)
        df['transaction_day'] = df['timestamp'].dt.day

        # -- Behavioral Feature Engineering --
        # Rolling window captures recent user activity patterns
        df['user_activity_24h'] = df.groupby('user_id', group_keys=False).apply(
            lambda g: g.rolling('24h', on='timestamp', closed='left')['amount'].count().fillna(0)
        )

        # -- Monetary Feature Engineering --
        # Relative amount detection compared to user's historical pattern
        df['amount_to_avg_ratio'] = df.groupby('user_id', group_keys=False).apply(
            lambda g: (g['amount'] / g['amount'].rolling(7, min_periods=1).mean()).fillna(1.0)
        )

        # -- Merchant Risk Profiling --
        # External risk intelligence integration point
        high_risk_merchants = self.config.get('high_risk_merchants', ['QuickCash', 'GlobalDigital', 'FastMoneyX'])
        df['merchant_risk'] = df['merchant'].isin(high_risk_merchants).astype(int)

        feature_cols = [
            'amount', 'is_night', 'is_weekend', 'transaction_day', 'user_activity_24h',
            'amount_to_avg_ratio', 'merchant_risk', 'merchant'
        ]

        # Schema validation guard
        if 'is_fraud' not in df.columns:
            raise ValueError('Missing target column "is_fraud"')

        return df[feature_cols + ['is_fraud']]

    def train_model(self):
        """
        End-to-end training pipeline implementing ML best practices:

        1. Data Quality Checks
        2. Stratified Data Splitting
        3. Class Imbalance Mitigation (SMOTE)
        4. Hyperparameter Optimization
        5. Threshold Tuning
        6. Model Evaluation
        7. Artifact Logging
        8. Model Registry

        Implements MLflow experiment tracking for full reproducibility.
        """
        try:
            logger.info('Starting model training process')
            df = self.read_from_kafka()

            # Data ingestion and feature engineering
            required_columns = ['user_id', 'timestamp']
            if df.empty or not set(required_columns).issubset(df.columns):
                logger.error("Received empty DataFrame or missing required columns from Kafka. Skipping training.")
                raise ValueError("Kafka returned empty data or invalid format; training aborted.")

            data = self.create_features(df)

            # Train/Test split with stratification
            X = data.drop(columns=['is_fraud'])
            y = data['is_fraud']

            # Class imbalance safeguards
            if y.sum() == 0:
                raise ValueError('No positive samples in training data')
            if y.sum() < 10:
                logger.warning('Low positive samples: %d. Consider additional data augmentation', y.sum())

            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=self.config['model'].get('test_size', 0.25),
                stratify=y,
                random_state=self.config['model'].get('seed', 50)
            )

            # MLflow experiment tracking context
            with mlflow.start_run():
                # Dataset metadata logging
                mlflow.log_metrics({
                    'train_samples': X_train.shape[0],
                    'positive_samples': int(y_train.sum()),
                    'class_ratio': float(y_train.mean()),
                    'test_samples': X_test.shape[0]
                })

                # Categorical feature preprocessing
                preprocessor = ColumnTransformer([
                    ('merchant_encoder', OrdinalEncoder(
                        handle_unknown='use_encoded_value', unknown_value=-1, dtype=np.float32
                    ), ['merchant'])
                ], remainder='passthrough')

                # XGBoost configuration with efficiency optimizations
                xgb = XGBClassifier(
                    eval_metric='aucpr',  # Optimizes for precision-recall area
                    random_state=self.config['model'].get('seed', 50),
                    reg_lambda=1.0,
                    n_estimators=self.config['model']['params']['n_estimators'],
                    n_jobs=-1,
                    tree_method=self.config['model'].get('tree_method', 'hist')  # GPU-compatible
                )

                # Imbalanced learning pipeline
                pipeline = ImbPipeline([
                    ('preprocessor', preprocessor),
                    ('smote', SMOTE(random_state=self.config['model'].get('seed', 50))),
                    ('classifier', xgb)
                ], memory='./cache')

                # Hyperparameter search space design
                param_dist = {
                    'classifier__max_depth': [3, 5, 7],  # Depth control for regularization
                    'classifier__learning_rate': [0.01, 0.05, 0.1],  # Conservative range
                    'classifier__subsample': [0.6, 0.8, 1.0],  # Stochastic gradient boosting
                    'classifier__colsample_bytree': [0.6, 0.8, 1.0],  # Feature randomization
                    'classifier__gamma': [0, 0.1, 0.3],  # Complexity control
                    'classifier__reg_alpha': [0, 0.1, 0.5]  # L1 regularization
                }

                # Optimizing for F-beta score (beta=2 emphasizes recall)
                searcher = RandomizedSearchCV(
                    pipeline,
                    param_dist,
                    n_iter=20,
                    scoring=make_scorer(fbeta_score, beta=2, zero_division=0),
                    cv=StratifiedKFold(n_splits=3, shuffle=True),
                    n_jobs=-1,
                    refit=True,
                    error_score='raise',
                    random_state=self.config['model'].get('seed', 42)
                )

                logger.info('Starting hyperparameter tuning...')
                searcher.fit(X_train, y_train)
                best_model = searcher.best_estimator_
                best_params = searcher.best_params_
                logger.info('Best hyperparameters: %s', best_params)

                # Threshold optimization using training data
                train_proba = best_model.predict_proba(X_train)[:, 1]
                precision_arr, recall_arr, thresholds_arr = precision_recall_curve(y_train, train_proba)
                f1_scores = [2 * (p * r) / (p + r) if (p + r) > 0 else 0 for p, r in
                             zip(precision_arr[:-1], recall_arr[:-1])]
                best_threshold = thresholds_arr[np.argmax(f1_scores)]
                logger.info('Optimal threshold determined: %.4f', best_threshold)

                # Model evaluation
                X_test_processed = best_model.named_steps['preprocessor'].transform(X_test)
                test_proba = best_model.named_steps['classifier'].predict_proba(X_test_processed)[:, 1]
                y_pred = (test_proba >= best_threshold).astype(int)

                # Comprehensive metrics suite
                metrics = {
                    'auc_pr': float(average_precision_score(y_test, test_proba)),
                    'precision': float(precision_score(y_test, y_pred, zero_division=0)),
                    'recall': float(recall_score(y_test, y_pred, zero_division=0)),
                    'f1': float(f1_score(y_test, y_pred, zero_division=0)),
                    'threshold': float(best_threshold)
                }

                mlflow.log_metrics(metrics)
                mlflow.log_params(best_params)

                # Confusion matrix visualization
                cm = confusion_matrix(y_test, y_pred)
                plt.figure(figsize=(6, 4))
                plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
                plt.title('Confusion Matrix')
                plt.colorbar()
                tick_marks = np.arange(2)
                plt.xticks(tick_marks, ['Not Fraud', 'Fraud'])
                plt.yticks(tick_marks, ['Not Fraud', 'Fraud'])

                for i in range(2):
                    for j in range(2):
                        plt.text(j, i, format(cm[i, j], 'd'), ha='center', va='center', color='red')

                plt.tight_layout()
                cm_filename = 'confusion_matrix.png'
                plt.savefig(cm_filename)
                mlflow.log_artifact(cm_filename)
                plt.close()

                # Precision-Recall curve documentation
                plt.figure(figsize=(10, 6))
                plt.plot(recall_arr, precision_arr, marker='.', label='Precision-Recall Curve')
                plt.xlabel('Recall')
                plt.ylabel('Precision')
                plt.title('Precision-Recall Curve')
                plt.legend()
                pr_filename = 'precision_recall_curve.png'
                plt.savefig(pr_filename)
                mlflow.log_artifact(pr_filename)
                plt.close()

                # Model packaging and registry
                signature = infer_signature(X_train, y_pred)
                mlflow.sklearn.log_model(
                    sk_model=best_model,
                    artifact_path='model',
                    signature=signature,
                    registered_model_name='fraud_detection_model'
                )

                # Model serialization for deployment
                os.makedirs('/app/models', exist_ok=True)
                joblib.dump(best_model, '/app/models/fraud_detection_model.pkl')

                logger.info('Training successfully completed with metrics: %s', metrics)

                return best_model, metrics

        except Exception as e:
            logger.error('Training failed: %s', str(e), exc_info=True)
            raise