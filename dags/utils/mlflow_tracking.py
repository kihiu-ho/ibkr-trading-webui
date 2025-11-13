"""
MLflow tracking utilities for IBKR workflows
Handles experiment tracking, logging, and artifact management
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
import mlflow
from mlflow.tracking import MlflowClient

from .config import config

logger = logging.getLogger(__name__)


class MLflowTracker:
    """MLflow tracking wrapper for IBKR workflows"""
    
    def __init__(self, experiment_name: Optional[str] = None):
        self.experiment_name = experiment_name or config.mlflow_experiment_name
        self.client = MlflowClient(tracking_uri=config.mlflow_tracking_uri)
        self.run_id: Optional[str] = None
        self._setup_experiment()
    
    def _setup_experiment(self):
        """Set up MLflow experiment"""
        try:
            mlflow.set_tracking_uri(config.mlflow_tracking_uri)
            mlflow.set_experiment(self.experiment_name)
            logger.info(f"MLflow experiment set to: {self.experiment_name}")
            logger.info(f"MLflow tracking URI: {config.mlflow_tracking_uri}")
        except Exception as e:
            logger.error(f"Failed to set up MLflow experiment: {e}")
            raise
    
    def start_run(self, run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
        """Start a new MLflow run"""
        try:
            run_name = run_name or f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            default_tags = {
                'workflow_type': 'stock_data_extraction',
                'environment': config.environment,
                'debug_mode': str(config.debug_mode),
            }
            
            if tags:
                default_tags.update(tags)
            
            mlflow.start_run(run_name=run_name, tags=default_tags)
            self.run_id = mlflow.active_run().info.run_id
            
            logger.info(f"Started MLflow run: {run_name} (ID: {self.run_id})")
            
            # Log workflow configuration as parameters
            self.log_params(config.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to start MLflow run: {e}")
            raise
    
    def log_params(self, params: Dict[str, Any]):
        """Log parameters to MLflow"""
        try:
            for key, value in params.items():
                mlflow.log_param(key, value)
            
            if config.debug_mode:
                logger.debug(f"Logged parameters: {params}")
        
        except Exception as e:
            logger.error(f"Failed to log parameters: {e}")
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log metrics to MLflow"""
        try:
            for key, value in metrics.items():
                mlflow.log_metric(key, value, step=step)
            
            logger.info(f"Logged metrics: {metrics}")
        
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")
    
    def log_artifact_dict(self, data: Dict[str, Any], filename: str):
        """Log a dictionary as JSON artifact"""
        try:
            import tempfile
            import os
            
            with tempfile.TemporaryDirectory() as tmpdir:
                filepath = os.path.join(tmpdir, filename)
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                
                mlflow.log_artifact(filepath)
                logger.info(f"Logged artifact: {filename}")
        
        except Exception as e:
            logger.error(f"Failed to log artifact {filename}: {e}")
    
    def log_file_artifact(self, file_path: str, artifact_path: Optional[str] = None):
        """
        Log a file directly as an MLflow artifact
        
        Args:
            file_path: Path to the file to log
            artifact_path: Optional subdirectory within the artifact store
        """
        try:
            if artifact_path:
                mlflow.log_artifact(file_path, artifact_path)
            else:
                mlflow.log_artifact(file_path)
            logger.info(f"Logged file artifact: {file_path}")
        
        except Exception as e:
            logger.error(f"Failed to log file artifact {file_path}: {e}")
    
    def log_dataframe(self, df, filename: str):
        """Log a pandas DataFrame as CSV artifact"""
        try:
            import tempfile
            import os
            
            with tempfile.TemporaryDirectory() as tmpdir:
                filepath = os.path.join(tmpdir, filename)
                df.to_csv(filepath, index=False)
                
                mlflow.log_artifact(filepath)
                logger.info(f"Logged DataFrame artifact: {filename}")
        
        except Exception as e:
            logger.error(f"Failed to log DataFrame: {e}")
    
    def set_tags(self, tags: Dict[str, str]):
        """Set tags on the current run"""
        try:
            for key, value in tags.items():
                mlflow.set_tag(key, value)
            
            if config.debug_mode:
                logger.debug(f"Set tags: {tags}")
        
        except Exception as e:
            logger.error(f"Failed to set tags: {e}")
    
    def end_run(self, status: str = "FINISHED"):
        """End the MLflow run"""
        try:
            mlflow.end_run(status=status)
            logger.info(f"Ended MLflow run with status: {status}")
        
        except Exception as e:
            logger.error(f"Failed to end MLflow run: {e}")
    
    def log_debug_info(self, info: Dict[str, Any]):
        """Log debug information if debug mode is enabled"""
        if config.debug_mode:
            self.log_artifact_dict(info, 'debug_info.json')
            logger.debug(f"Logged debug information: {list(info.keys())}")


# Helper function for easy run context management
class mlflow_run_context:
    """Context manager for MLflow runs"""
    
    def __init__(self, run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
        self.tracker = MLflowTracker()
        self.run_name = run_name
        self.tags = tags
    
    def __enter__(self):
        self.tracker.start_run(run_name=self.run_name, tags=self.tags)
        return self.tracker
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.tracker.end_run(status="FAILED")
            return False
        else:
            self.tracker.end_run(status="FINISHED")
            return True

