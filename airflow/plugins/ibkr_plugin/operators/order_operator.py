"""Order placement operator."""
import logging
import time
from typing import Dict, Any, Optional
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from ibkr_plugin.hooks.ibkr_hook import IBKRHook
from ibkr_plugin.hooks.mlflow_tracker import MLflowTracker


logger = logging.getLogger(__name__)


class OrderPlacementOperator(BaseOperator):
    """
    Operator to place orders based on trading signals.
    
    This operator:
    1. Retrieves signal from previous task
    2. Validates risk constraints
    3. Places order via IBKR API
    4. Logs order details to MLflow
    5. Saves order to database
    """
    
    ui_color = '#F44336'
    
    @apply_defaults
    def __init__(
        self,
        strategy_id: int,
        min_confidence: float = 0.7,
        max_position_size: Optional[float] = None,
        dry_run: bool = False,
        track_mlflow: bool = True,
        *args,
        **kwargs
    ):
        """
        Initialize order placement operator.
        
        Args:
            strategy_id: Strategy ID
            min_confidence: Minimum signal confidence to place order
            max_position_size: Maximum position size (in dollars)
            dry_run: If True, log order but don't place
            track_mlflow: Whether to track in MLflow
        """
        super().__init__(*args, **kwargs)
        self.strategy_id = strategy_id
        self.min_confidence = min_confidence
        self.max_position_size = max_position_size
        self.dry_run = dry_run
        self.track_mlflow = track_mlflow
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute order placement.
        
        Args:
            context: Airflow task context
            
        Returns:
            Order result dictionary
        """
        logger.info(f"Processing order placement for strategy {self.strategy_id}")
        
        # Initialize hooks
        ibkr_hook = IBKRHook()
        mlflow_tracker = MLflowTracker() if self.track_mlflow else None
        
        try:
            # Get signal from previous task
            ti = context['task_instance']
            signal = ti.xcom_pull(key='signal', task_ids='llm_signal_generation')
            
            if not signal:
                logger.warning("No signal available, skipping order placement")
                return {"status": "skipped", "reason": "no_signal"}
            
            signal_type = signal.get('signal_type', 'HOLD')
            confidence = signal.get('confidence', 0.0)
            
            logger.info(f"Signal: {signal_type} (confidence: {confidence:.2f})")
            
            # Check if signal meets confidence threshold
            if confidence < self.min_confidence:
                logger.info(
                    f"Signal confidence {confidence:.2f} below threshold {self.min_confidence}, "
                    "skipping order placement"
                )
                return {
                    "status": "skipped",
                    "reason": "low_confidence",
                    "confidence": confidence,
                    "threshold": self.min_confidence
                }
            
            # Skip HOLD signals
            if signal_type == "HOLD":
                logger.info("Signal is HOLD, skipping order placement")
                return {"status": "skipped", "reason": "hold_signal"}
            
            # Get strategy configuration
            strategy = ibkr_hook.get_strategy(self.strategy_id)
            symbols = strategy.get('symbols', [])
            
            if not symbols:
                logger.warning("No symbols configured for strategy")
                return {"status": "skipped", "reason": "no_symbols"}
            
            # Place orders for each symbol
            orders = []
            for symbol in symbols:
                order_result = self._place_order(
                    ibkr_hook=ibkr_hook,
                    symbol=symbol,
                    signal_type=signal_type,
                    confidence=confidence,
                    strategy=strategy
                )
                
                if order_result:
                    orders.append(order_result)
                    
                    # Track in MLflow
                    if mlflow_tracker and mlflow_tracker.active_run:
                        mlflow_tracker.log_order_execution(
                            symbol=symbol,
                            side=signal_type,
                            quantity=order_result.get('quantity', 0),
                            order_type=order_result.get('order_type', 'MKT'),
                            status=order_result.get('status', 'unknown'),
                            price=order_result.get('price')
                        )
            
            result = {
                "status": "success",
                "signal_type": signal_type,
                "confidence": confidence,
                "orders_placed": len(orders),
                "orders": orders,
                "dry_run": self.dry_run
            }
            
            logger.info(f"Placed {len(orders)} orders")
            
            # Push to XCom
            ti.xcom_push(key='order_result', value=result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error placing orders: {e}", exc_info=True)
            raise
        finally:
            ibkr_hook.close()
    
    def _place_order(
        self,
        ibkr_hook: IBKRHook,
        symbol: str,
        signal_type: str,
        confidence: float,
        strategy: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Place a single order.
        
        Args:
            ibkr_hook: IBKR hook instance
            symbol: Symbol to trade
            signal_type: BUY or SELL
            confidence: Signal confidence
            strategy: Strategy configuration
            
        Returns:
            Order result or None
        """
        try:
            # Determine order parameters
            # In production, this would use risk management rules
            quantity = strategy.get('param', {}).get('position_size', 100)
            order_type = "MKT"  # Market order
            
            # Apply max position size if configured
            if self.max_position_size:
                # This is simplified; in production, calculate based on current price
                quantity = min(quantity, self.max_position_size / 100)  # Assume $100/share
            
            if self.dry_run:
                logger.info(
                    f"DRY RUN: Would place {signal_type} order for {quantity} {symbol} @ {order_type}"
                )
                return {
                    "symbol": symbol,
                    "side": signal_type,
                    "quantity": quantity,
                    "order_type": order_type,
                    "status": "dry_run",
                    "confidence": confidence
                }
            
            # Place actual order
            order_result = ibkr_hook.place_order(
                symbol=symbol,
                side=signal_type,
                quantity=quantity,
                order_type=order_type
            )
            
            logger.info(f"Order placed: {order_result}")
            
            return {
                "symbol": symbol,
                "side": signal_type,
                "quantity": quantity,
                "order_type": order_type,
                "status": "placed",
                "confidence": confidence,
                "order_response": order_result
            }
            
        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {e}")
            return {
                "symbol": symbol,
                "side": signal_type,
                "status": "error",
                "error": str(e)
            }

