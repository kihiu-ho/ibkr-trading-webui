"""LLM-based signal generation operator."""
import logging
import time
import json
from typing import Dict, Any, Optional
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from ibkr_plugin.hooks.ibkr_hook import IBKRHook
from ibkr_plugin.hooks.mlflow_tracker import MLflowTracker


logger = logging.getLogger(__name__)


class LLMSignalGeneratorOperator(BaseOperator):
    """
    Operator to generate trading signals using LLM analysis.
    
    This operator:
    1. Loads strategy configuration
    2. Fetches chart and indicator data
    3. Calls LLM with configured prompt
    4. Parses signal from LLM response
    5. Saves signal to database
    6. Logs to MLflow
    """
    
    ui_color = '#FF9800'
    
    @apply_defaults
    def __init__(
        self,
        strategy_id: int,
        track_mlflow: bool = True,
        *args,
        **kwargs
    ):
        """
        Initialize signal generator operator.
        
        Args:
            strategy_id: Strategy ID to generate signals for
            track_mlflow: Whether to track in MLflow
        """
        super().__init__(*args, **kwargs)
        self.strategy_id = strategy_id
        self.track_mlflow = track_mlflow
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute signal generation.
        
        Args:
            context: Airflow task context
            
        Returns:
            Signal dictionary
        """
        logger.info(f"Generating signal for strategy {self.strategy_id}")
        
        # Initialize hooks
        ibkr_hook = IBKRHook()
        mlflow_tracker = MLflowTracker() if self.track_mlflow else None
        
        start_time = time.time()
        
        try:
            # Get strategy configuration
            strategy = ibkr_hook.get_strategy(self.strategy_id)
            logger.info(f"Strategy: {strategy.get('name')}")
            
            # Get market data from previous task
            ti = context['task_instance']
            market_data_summary = ti.xcom_pull(
                key='market_data_summary',
                task_ids='fetch_market_data'
            )
            
            if not market_data_summary:
                logger.warning("No market data available, skipping signal generation")
                return {"status": "skipped", "reason": "no_market_data"}
            
            # Here you would normally:
            # 1. Generate charts using backend API
            # 2. Call LLM with chart and prompt
            # 3. Parse LLM response for signal
            
            # For now, create a simple signal based on market data
            # In production, this would call the LLM service
            signal_data = self._generate_signal(
                strategy=strategy,
                market_data=market_data_summary
            )
            
            generation_duration = time.time() - start_time
            
            # Save signal to database
            saved_signal = ibkr_hook.save_signal(signal_data)
            
            logger.info(
                f"Generated {signal_data['signal_type']} signal "
                f"with confidence {signal_data['confidence']:.2f} "
                f"in {generation_duration:.2f}s"
            )
            
            # Track in MLflow
            if mlflow_tracker and mlflow_tracker.active_run:
                mlflow_tracker.log_signal_generation(
                    signal_type=signal_data['signal_type'],
                    confidence=signal_data['confidence'],
                    llm_duration=generation_duration
                )
            
            # Push to XCom
            ti.xcom_push(key='signal', value=saved_signal)
            
            return saved_signal
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}", exc_info=True)
            raise
        finally:
            ibkr_hook.close()
    
    def _generate_signal(
        self,
        strategy: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate trading signal.
        
        In production, this would:
        1. Call backend chart generation API
        2. Call LLM analysis API with chart and prompt
        3. Parse LLM response
        
        For now, returns a placeholder signal.
        
        Args:
            strategy: Strategy configuration
            market_data: Market data summary
            
        Returns:
            Signal dictionary
        """
        # Simple placeholder logic
        # In production, this calls the LLM service
        
        symbols_fetched = market_data.get('symbols_fetched', 0)
        
        if symbols_fetched == 0:
            signal_type = "HOLD"
            confidence = 0.0
            reasoning = "No market data available"
        else:
            # Placeholder: generate HOLD signal
            signal_type = "HOLD"
            confidence = 0.5
            reasoning = "Market data fetched, awaiting LLM analysis"
        
        signal_data = {
            "strategy_id": self.strategy_id,
            "signal_type": signal_type,
            "confidence": confidence,
            "reasoning": reasoning,
            "metadata": {
                "symbols_analyzed": market_data.get('symbols_requested', []),
                "data_points": market_data.get('data_points', 0),
                "timestamp": market_data.get('timestamp')
            }
        }
        
        return signal_data

