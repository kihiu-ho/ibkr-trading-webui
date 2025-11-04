"""MLflow tracking integration for trading workflows."""
import mlflow
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from ibkr_plugin.hooks.config_loader import config_loader


logger = logging.getLogger(__name__)


class MLflowTracker:
    """Track workflow executions with MLflow."""
    
    def __init__(self, experiment_name: Optional[str] = None):
        """
        Initialize MLflow tracker.
        
        Args:
            experiment_name: Name of MLflow experiment.
                           Defaults to config value.
        """
        mlflow_config = config_loader.get_mlflow_config()
        
        # Set tracking URI
        tracking_uri = mlflow_config.get('tracking_uri', 'http://mlflow-server:5500')
        mlflow.set_tracking_uri(tracking_uri)
        
        # Set experiment
        if experiment_name is None:
            experiment_name = mlflow_config.get('experiment_name', 'ibkr_trading_workflows')
        
        mlflow.set_experiment(experiment_name)
        
        self.experiment_name = experiment_name
        self.active_run = None
    
    def start_run(
        self,
        run_name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> mlflow.ActiveRun:
        """
        Start a new MLflow run.
        
        Args:
            run_name: Name for the run
            tags: Optional tags dictionary
            
        Returns:
            Active MLflow run
        """
        if self.active_run:
            logger.warning("Active run already exists, ending it before starting new one")
            self.end_run()
        
        default_tags = {
            "execution_date": datetime.now().isoformat(),
            "workflow_type": "trading_strategy"
        }
        
        if tags:
            default_tags.update(tags)
        
        self.active_run = mlflow.start_run(run_name=run_name, tags=default_tags)
        logger.info(f"Started MLflow run: {run_name}")
        
        return self.active_run
    
    def end_run(self, status: str = "FINISHED"):
        """
        End the active MLflow run.
        
        Args:
            status: Run status (FINISHED, FAILED, KILLED)
        """
        if self.active_run:
            mlflow.end_run(status=status)
            logger.info(f"Ended MLflow run with status: {status}")
            self.active_run = None
    
    def log_params(self, params: Dict[str, Any]):
        """
        Log parameters to MLflow.
        
        Args:
            params: Parameters dictionary
        """
        if not self.active_run:
            logger.warning("No active MLflow run, skipping log_params")
            return
        
        try:
            # MLflow has param value length limit, truncate if needed
            safe_params = {}
            for key, value in params.items():
                str_value = str(value)
                if len(str_value) > 500:
                    str_value = str_value[:497] + "..."
                safe_params[key] = str_value
            
            mlflow.log_params(safe_params)
            logger.debug(f"Logged {len(safe_params)} parameters")
        except Exception as e:
            logger.error(f"Error logging params: {e}")
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """
        Log metrics to MLflow.
        
        Args:
            metrics: Metrics dictionary
            step: Optional step number
        """
        if not self.active_run:
            logger.warning("No active MLflow run, skipping log_metrics")
            return
        
        try:
            mlflow.log_metrics(metrics, step=step)
            logger.debug(f"Logged {len(metrics)} metrics")
        except Exception as e:
            logger.error(f"Error logging metrics: {e}")
    
    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """
        Log artifact to MLflow.
        
        Args:
            local_path: Path to local file
            artifact_path: Optional artifact path in MLflow
        """
        if not self.active_run:
            logger.warning("No active MLflow run, skipping log_artifact")
            return
        
        try:
            mlflow.log_artifact(local_path, artifact_path=artifact_path)
            logger.debug(f"Logged artifact: {local_path}")
        except Exception as e:
            logger.error(f"Error logging artifact: {e}")
    
    def log_dict(self, dictionary: Dict[str, Any], artifact_file: str):
        """
        Log dictionary as JSON artifact.
        
        Args:
            dictionary: Dictionary to log
            artifact_file: Artifact filename
        """
        if not self.active_run:
            logger.warning("No active MLflow run, skipping log_dict")
            return
        
        try:
            mlflow.log_dict(dictionary, artifact_file=artifact_file)
            logger.debug(f"Logged dict as artifact: {artifact_file}")
        except Exception as e:
            logger.error(f"Error logging dict: {e}")
    
    def set_tags(self, tags: Dict[str, str]):
        """
        Set tags on the active run.
        
        Args:
            tags: Tags dictionary
        """
        if not self.active_run:
            logger.warning("No active MLflow run, skipping set_tags")
            return
        
        try:
            mlflow.set_tags(tags)
            logger.debug(f"Set {len(tags)} tags")
        except Exception as e:
            logger.error(f"Error setting tags: {e}")
    
    def log_workflow_execution(
        self,
        workflow_name: str,
        strategy_id: int,
        dag_run_id: str,
        execution_date: str,
        params: Dict[str, Any],
        status: str = "running"
    ):
        """
        Log workflow execution metadata.
        
        Args:
            workflow_name: Name of the workflow
            strategy_id: Strategy ID
            dag_run_id: Airflow DAG run ID
            execution_date: Execution datetime
            params: Workflow parameters
            status: Execution status
        """
        tags = {
            "workflow_name": workflow_name,
            "strategy_id": str(strategy_id),
            "dag_run_id": dag_run_id,
            "execution_date": execution_date,
            "status": status
        }
        
        self.set_tags(tags)
        self.log_params(params)
    
    def log_market_data_metrics(
        self,
        symbols: list,
        data_points: int,
        fetch_duration: float
    ):
        """
        Log market data collection metrics.
        
        Args:
            symbols: List of symbols fetched
            data_points: Number of data points
            fetch_duration: Fetch duration in seconds
        """
        metrics = {
            "symbols_count": len(symbols),
            "data_points": data_points,
            "fetch_duration_seconds": fetch_duration,
            "points_per_second": data_points / fetch_duration if fetch_duration > 0 else 0
        }
        
        self.log_metrics(metrics)
        self.log_params({"symbols": ",".join(symbols)})
    
    def log_signal_generation(
        self,
        signal_type: str,
        confidence: float,
        llm_tokens: Optional[int] = None,
        llm_duration: Optional[float] = None
    ):
        """
        Log trading signal generation.
        
        Args:
            signal_type: Signal type (BUY, SELL, HOLD)
            confidence: Signal confidence score
            llm_tokens: Optional LLM token count
            llm_duration: Optional LLM call duration
        """
        metrics = {
            "signal_confidence": confidence
        }
        
        if llm_tokens:
            metrics["llm_tokens"] = llm_tokens
        
        if llm_duration:
            metrics["llm_duration_seconds"] = llm_duration
            if llm_tokens:
                metrics["tokens_per_second"] = llm_tokens / llm_duration
        
        self.log_metrics(metrics)
        self.set_tags({"signal_type": signal_type})
    
    def log_order_execution(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str,
        status: str,
        price: Optional[float] = None
    ):
        """
        Log order execution details.
        
        Args:
            symbol: Symbol traded
            side: BUY or SELL
            quantity: Order quantity
            order_type: Order type
            status: Order status
            price: Optional execution price
        """
        metrics = {
            "order_quantity": quantity
        }
        
        if price:
            metrics["order_price"] = price
            metrics["order_value"] = quantity * price
        
        self.log_metrics(metrics)
        
        tags = {
            "order_symbol": symbol,
            "order_side": side,
            "order_type": order_type,
            "order_status": status
        }
        
        self.set_tags(tags)
    
    def log_portfolio_metrics(
        self,
        total_value: float,
        cash: float,
        positions_count: int,
        daily_pnl: Optional[float] = None,
        total_pnl: Optional[float] = None
    ):
        """
        Log portfolio metrics.
        
        Args:
            total_value: Total portfolio value
            cash: Cash balance
            positions_count: Number of positions
            daily_pnl: Optional daily P&L
            total_pnl: Optional total P&L
        """
        metrics = {
            "portfolio_value": total_value,
            "portfolio_cash": cash,
            "portfolio_positions_count": positions_count
        }
        
        if daily_pnl is not None:
            metrics["daily_pnl"] = daily_pnl
        
        if total_pnl is not None:
            metrics["total_pnl"] = total_pnl
        
        self.log_metrics(metrics)

