"""Celery tasks for trading workflow execution."""
from celery import Task
from backend.celery_app import celery_app
from backend.core.database import SessionLocal
from backend.models.strategy import Strategy
from backend.models.decision import Decision
from backend.models.market import MarketData
from backend.models.order import Order
from backend.models.agent import WorkflowExecution
from backend.services.ibkr_service import IBKRService
from backend.services.chart_service import ChartService
from backend.services.storage_service import StorageService
from backend.services.ai_service import AIService
from datetime import datetime, timezone
import pandas as pd
import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)


class WorkflowTask(Task):
    """Base class for workflow tasks with shared resources."""
    
    def __init__(self):
        self._ibkr = None
        self._chart = None
        self._storage = None
        self._ai = None
    
    @property
    def ibkr(self):
        if self._ibkr is None:
            self._ibkr = IBKRService()
        return self._ibkr
    
    @property
    def chart(self):
        if self._chart is None:
            self._chart = ChartService()
        return self._chart
    
    @property
    def storage(self):
        if self._storage is None:
            self._storage = StorageService()
        return self._storage
    
    @property
    def ai(self):
        if self._ai is None:
            self._ai = AIService()
        return self._ai


@celery_app.task(
    base=WorkflowTask,
    bind=True,
    name='workflow.execute_trading_workflow',
    max_retries=3,
    default_retry_delay=60
)
def execute_trading_workflow(self, strategy_id: int):
    """
    Execute complete trading workflow for a strategy.
    
    Args:
        strategy_id: Database ID of the strategy to execute
        
    Returns:
        Workflow execution results
    """
    db = SessionLocal()
    execution_id = None
    
    try:
        logger.info(f"Starting trading workflow for strategy {strategy_id}")
        
        # Get strategy from database
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        # Create workflow execution record
        execution = WorkflowExecution(
            workflow_id=strategy.workflow_id,
            strategy_id=strategy_id,
            status='running',
            started_at=datetime.now(timezone.utc)
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        execution_id = execution.id
        
        # Run async workflow
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            _execute_workflow_async(
                self,
                db,
                strategy,
                execution_id
            )
        )
        
        # Update execution record
        execution.status = 'completed'
        execution.completed_at = datetime.now(timezone.utc)
        execution.result = result
        db.commit()
        
        logger.info(f"Trading workflow completed for strategy {strategy_id}")
        return result
        
    except Exception as e:
        logger.error(f"Trading workflow failed for strategy {strategy_id}: {e}")
        
        if execution_id:
            execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
            if execution:
                execution.status = 'failed'
                execution.completed_at = datetime.now(timezone.utc)
                execution.error = str(e)
                db.commit()
        
        # Retry on failure
        raise self.retry(exc=e)
        
    finally:
        db.close()


async def _execute_workflow_async(
    task: WorkflowTask,
    db,
    strategy: Strategy,
    execution_id: int
) -> Dict[str, Any]:
    """Execute the trading workflow asynchronously."""
    
    # Step 1: Search for contract
    logger.info(f"Step 1: Searching for contract {strategy.code}")
    contracts = await task.ibkr.search_contracts(strategy.code)
    
    if not contracts:
        raise ValueError(f"No contracts found for symbol {strategy.code}")
    
    conid = contracts[0].get('conid')
    if not conid:
        raise ValueError(f"No conid found for symbol {strategy.code}")
    
    logger.info(f"Found contract with conid: {conid}")
    
    # Step 2: Fetch historical data for daily chart
    logger.info("Step 2: Fetching daily historical data")
    daily_data_raw = await task.ibkr.get_historical_data(conid, period="1y", bar="1d")
    
    # Parse daily data
    daily_df = _parse_historical_data(daily_data_raw)
    
    # Step 3: Generate daily chart
    logger.info("Step 3: Generating daily chart")
    daily_chart_png = task.chart.generate_chart(daily_df, strategy.code, "1D")
    
    # Upload to storage
    daily_chart_name = f"charts/{strategy.code}_daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    daily_chart_url = task.storage.upload_chart(daily_chart_png, daily_chart_name)
    
    logger.info(f"Daily chart uploaded: {daily_chart_url}")
    
    # Step 4: Analyze daily chart with AI
    logger.info("Step 4: Analyzing daily chart with AI")
    daily_analysis = await task.ai.analyze_daily_chart(strategy.code, daily_chart_url)
    
    # Step 5: Fetch and analyze weekly chart
    logger.info("Step 5: Fetching weekly historical data")
    weekly_data_raw = await task.ibkr.get_historical_data(conid, period="5y", bar="1w")
    weekly_df = _parse_historical_data(weekly_data_raw)
    
    logger.info("Generating weekly chart")
    weekly_chart_png = task.chart.generate_chart(weekly_df, strategy.code, "1W")
    
    weekly_chart_name = f"charts/{strategy.code}_weekly_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    weekly_chart_url = task.storage.upload_chart(weekly_chart_png, weekly_chart_name)
    
    logger.info(f"Weekly chart uploaded: {weekly_chart_url}")
    
    logger.info("Step 6: Analyzing weekly chart with AI")
    weekly_analysis = await task.ai.analyze_weekly_chart(strategy.code, weekly_chart_url)
    
    # Step 7: Consolidate analysis
    logger.info("Step 7: Consolidating multi-timeframe analysis")
    consolidated_analysis = await task.ai.consolidate_analysis(daily_analysis, weekly_analysis)
    
    # Step 8: Generate trading decision
    logger.info("Step 8: Generating trading decision")
    decision_data = await task.ai.generate_trading_decision(
        consolidated_analysis,
        strategy.code,
        strategy.name
    )
    
    # Save decision to database
    decision = Decision(
        strategy_id=strategy.id,
        code=decision_data['code'],
        type=decision_data['type'],
        current_price=decision_data['current_price'],
        target_price=decision_data['target_price'],
        stop_loss=decision_data['stop_loss'],
        profit_margin=decision_data['profit_margin'],
        r_coefficient=decision_data['R_coefficient'],
        created_at=datetime.now(timezone.utc),
        analysis_text=consolidated_analysis
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    
    logger.info(f"Decision saved: {decision.type} for {decision.code}")
    
    # Step 9: Place order if decision is buy/sell
    order_result = None
    if decision.type in ['buy', 'sell']:
        logger.info(f"Step 9: Placing {decision.type} order")
        
        # Calculate position size based on strategy parameters
        quantity = _calculate_position_size(
            decision.current_price,
            decision.stop_loss,
            strategy.param
        )
        
        # Place market order
        order_result = await task.ibkr.place_order(
            conid=conid,
            order_type="MKT",
            side="BUY" if decision.type == "buy" else "SELL",
            quantity=quantity,
            tif="DAY"
        )
        
        # Save order to database
        if order_result:
            order = Order(
                strategy_id=strategy.id,
                decision_id=decision.id,
                conid=conid,
                code=decision.code,
                type=decision.type,
                order_type="MKT",
                quantity=quantity,
                price=decision.current_price,
                status='submitted',
                submitted_at=datetime.now(timezone.utc),
                ibkr_order_id=str(order_result.get('order_id', ''))
            )
            db.add(order)
            db.commit()
            
            logger.info(f"Order placed: {order.type} {order.quantity} {order.code}")
    
    # Return workflow results
    return {
        'strategy_id': strategy.id,
        'strategy_name': strategy.name,
        'code': strategy.code,
        'execution_id': execution_id,
        'decision': {
            'id': decision.id,
            'type': decision.type,
            'current_price': decision.current_price,
            'target_price': decision.target_price,
            'stop_loss': decision.stop_loss,
            'profit_margin': decision.profit_margin,
            'r_coefficient': decision.r_coefficient
        },
        'charts': {
            'daily': daily_chart_url,
            'weekly': weekly_chart_url
        },
        'order': order_result,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def _parse_historical_data(raw_data: Dict[str, Any]) -> pd.DataFrame:
    """Parse IBKR historical data into DataFrame."""
    if 'data' not in raw_data:
        raise ValueError("No data field in historical response")
    
    data_list = raw_data['data']
    
    # Parse data
    df = pd.DataFrame([
        {
            'date': pd.to_datetime(item['t'], unit='ms'),
            'open': item.get('o', 0),
            'high': item.get('h', 0),
            'low': item.get('l', 0),
            'close': item.get('c', 0),
            'volume': item.get('v', 0)
        }
        for item in data_list
    ])
    
    return df


def _calculate_position_size(
    current_price: float,
    stop_loss: float,
    strategy_params: Dict[str, Any]
) -> int:
    """Calculate position size based on risk parameters."""
    # Default risk per trade: 2% of account
    risk_per_trade = strategy_params.get('risk_per_trade', 0.02)
    account_size = strategy_params.get('account_size', 100000)  # Default $100k
    
    # Calculate position size
    risk_amount = account_size * risk_per_trade
    risk_per_share = abs(current_price - stop_loss)
    
    if risk_per_share == 0:
        return 1  # Minimum position
    
    quantity = int(risk_amount / risk_per_share)
    
    # Ensure minimum quantity
    return max(1, quantity)

