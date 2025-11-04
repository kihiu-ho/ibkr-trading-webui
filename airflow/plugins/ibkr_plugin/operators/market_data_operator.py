"""Market data fetching operator."""
import logging
import time
from typing import List, Optional, Dict, Any
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from ibkr_plugin.hooks.ibkr_hook import IBKRHook
from ibkr_plugin.hooks.mlflow_tracker import MLflowTracker


logger = logging.getLogger(__name__)


class IBKRMarketDataOperator(BaseOperator):
    """
    Operator to fetch market data for symbols via IBKR.
    
    This operator:
    1. Fetches market data for specified symbols
    2. Validates data completeness
    3. Logs metrics to MLflow
    4. Returns data summary via XCom
    """
    
    ui_color = '#4CAF50'
    
    @apply_defaults
    def __init__(
        self,
        symbols: List[str],
        fields: Optional[List[str]] = None,
        strategy_id: Optional[int] = None,
        track_mlflow: bool = True,
        *args,
        **kwargs
    ):
        """
        Initialize market data operator.
        
        Args:
            symbols: List of symbols to fetch
            fields: Optional list of fields (default: last, bid, ask)
            strategy_id: Optional strategy ID for tracking
            track_mlflow: Whether to track in MLflow
        """
        super().__init__(*args, **kwargs)
        self.symbols = symbols
        self.fields = fields or ["31", "84", "86"]  # last, bid, ask
        self.strategy_id = strategy_id
        self.track_mlflow = track_mlflow
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute market data fetch.
        
        Args:
            context: Airflow task context
            
        Returns:
            Market data summary
        """
        logger.info(f"Fetching market data for {len(self.symbols)} symbols: {self.symbols}")
        
        # Initialize hooks
        ibkr_hook = IBKRHook()
        mlflow_tracker = MLflowTracker() if self.track_mlflow else None
        
        start_time = time.time()
        
        try:
            # Fetch market data
            market_data = ibkr_hook.get_market_data(
                symbols=self.symbols,
                fields=self.fields
            )
            
            fetch_duration = time.time() - start_time
            
            # Extract data points
            data_points = 0
            valid_symbols = []
            
            contracts = market_data.get('contracts', {})
            snapshot_data = market_data.get('market_data', {})
            
            for symbol in self.symbols:
                if symbol in contracts and contracts[symbol]:
                    valid_symbols.append(symbol)
                    data_points += len(self.fields)
            
            logger.info(
                f"Fetched data for {len(valid_symbols)}/{len(self.symbols)} symbols "
                f"in {fetch_duration:.2f}s"
            )
            
            # Track in MLflow
            if mlflow_tracker and mlflow_tracker.active_run:
                mlflow_tracker.log_market_data_metrics(
                    symbols=valid_symbols,
                    data_points=data_points,
                    fetch_duration=fetch_duration
                )
            
            # Prepare summary for XCom
            summary = {
                "symbols_requested": len(self.symbols),
                "symbols_fetched": len(valid_symbols),
                "data_points": data_points,
                "fetch_duration": fetch_duration,
                "contracts": contracts,
                "market_data": snapshot_data,
                "timestamp": context['execution_date'].isoformat()
            }
            
            # Push to XCom
            context['task_instance'].xcom_push(key='market_data_summary', value=summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}", exc_info=True)
            raise
        finally:
            ibkr_hook.close()

