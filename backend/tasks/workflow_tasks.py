"""Celery tasks for trading workflow execution."""
from celery import Task
from backend.celery_app import celery_app
from backend.core.database import SessionLocal
from backend.models.strategy import Strategy, Code
from backend.models.decision import Decision
from backend.models.market import MarketData
from backend.models.order import Order
from backend.models.workflow import WorkflowExecution
from backend.models.workflow_log import WorkflowLog
from backend.services.ibkr_service import IBKRService
from backend.services.chart_service import ChartService
from backend.services.storage_service import StorageService
from backend.services.ai_service import AIService
from datetime import datetime, timezone
import pandas as pd
import logging
import asyncio
import time
from typing import Dict, Any, List

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


def _log_workflow_step(
    db,
    execution_id: int,
    step_name: str,
    step_type: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    success: bool = True,
    error_message: str = None,
    duration_ms: int = None,
    code: str = None,
    conid: int = None
):
    """Log a workflow step with full I/O data."""
    log_entry = WorkflowLog(
        workflow_execution_id=execution_id,
        step_name=step_name,
        step_type=step_type,
        code=code,
        conid=conid,
        input_data=input_data,
        output_data=output_data,
        success=success,
        error_message=error_message,
        duration_ms=duration_ms
    )
    db.add(log_entry)
    db.commit()
    logger.info(f"Logged step: {step_name} ({step_type}) - Success: {success}")


@celery_app.task(
    base=WorkflowTask,
    bind=True,
    name='workflow.execute_trading_workflow',
    max_retries=3,
    default_retry_delay=60
)
def execute_trading_workflow(self, strategy_id: int):
    """
    Execute complete trading workflow for a strategy with multiple codes.
    
    Args:
        strategy_id: Database ID of the strategy to execute
        
    Returns:
        Workflow execution results
    """
    db = SessionLocal()
    execution_id = None
    
    try:
        logger.info(f"Starting trading workflow for strategy {strategy_id}")
        
        # Get strategy from database with associated codes
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
        
        # Log workflow start
        _log_workflow_step(
            db, execution_id, 
            "workflow_start", "initialization",
            {"strategy_id": strategy_id, "strategy_name": strategy.name, "workflow_id": strategy.workflow_id},
            {"execution_id": execution_id, "status": "started"}
        )
        
        # Get all codes associated with this strategy
        codes = strategy.codes
        if not codes:
            raise ValueError(f"No codes associated with strategy {strategy_id}")
        
        logger.info(f"Processing {len(codes)} symbols for strategy {strategy.name}")
        
        # Run async workflow for all codes
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            _execute_workflow_for_multiple_codes(
                self,
                db,
                strategy,
                codes,
                execution_id
            )
        )
        
        # Update execution record
        execution.status = 'completed'
        execution.completed_at = datetime.now(timezone.utc)
        execution.result = result
        db.commit()
        
        # Log workflow completion
        _log_workflow_step(
            db, execution_id,
            "workflow_complete", "completion",
            {"execution_id": execution_id},
            result
        )
        
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
                
                # Log error
                _log_workflow_step(
                    db, execution_id,
                    "workflow_error", "error",
                    {"strategy_id": strategy_id},
                    {},
                    success=False,
                    error_message=str(e)
                )
        
        # Retry on failure
        raise self.retry(exc=e)
        
    finally:
        db.close()


async def _execute_workflow_for_multiple_codes(
    task: WorkflowTask,
    db,
    strategy: Strategy,
    codes: List[Code],
    execution_id: int
) -> Dict[str, Any]:
    """Execute workflow for multiple codes sequentially."""
    
    results = {
        'strategy_id': strategy.id,
        'strategy_name': strategy.name,
        'execution_id': execution_id,
        'codes_processed': [],
        'codes_failed': [],
        'total_codes': len(codes),
        'summary': {}
    }
    
    for idx, code_obj in enumerate(codes):
        logger.info(f"Processing code {idx+1}/{len(codes)}: {code_obj.symbol} (conid: {code_obj.conid})")
        
        try:
            # Execute workflow for this code
            code_result = await _execute_workflow_for_code(
                task, db, strategy, code_obj, execution_id
            )
            results['codes_processed'].append(code_result)
            
            # Add delay between processing codes (60 seconds as per spec)
            if idx < len(codes) - 1:
                logger.info(f"Waiting 60 seconds before processing next code...")
                _log_workflow_step(
                    db, execution_id,
                    f"delay_between_codes", "delay",
                    {"current_code": code_obj.symbol, "next_code": codes[idx+1].symbol},
                    {"delay_seconds": 60},
                    code=code_obj.symbol,
                    conid=code_obj.conid
                )
                await asyncio.sleep(60)
                
        except Exception as e:
            logger.error(f"Failed to process code {code_obj.symbol}: {e}")
            results['codes_failed'].append({
                'symbol': code_obj.symbol,
                'conid': code_obj.conid,
                'error': str(e)
            })
            
            _log_workflow_step(
                db, execution_id,
                f"code_processing_error", "error",
                {"symbol": code_obj.symbol, "conid": code_obj.conid},
                {},
                success=False,
                error_message=str(e),
                code=code_obj.symbol,
                conid=code_obj.conid
            )
    
    # Generate summary
    results['summary'] = {
        'total_processed': len(results['codes_processed']),
        'total_failed': len(results['codes_failed']),
        'success_rate': len(results['codes_processed']) / len(codes) if codes else 0
    }
    
    return results


async def _execute_workflow_for_code(
    task: WorkflowTask,
    db,
    strategy: Strategy,
    code_obj: Code,
    execution_id: int
) -> Dict[str, Any]:
    """Execute the trading workflow for a single code with comprehensive logging."""
    
    start_time = time.time()
    symbol = code_obj.symbol
    conid = code_obj.conid
    
    logger.info(f"Starting workflow for {symbol} (conid: {conid})")
    
    # Log code processing start
    _log_workflow_step(
        db, execution_id,
        f"start_code_processing", "initialization",
        {"symbol": symbol, "conid": conid, "strategy": strategy.name},
        {"started_at": datetime.now(timezone.utc).isoformat()},
        code=symbol,
        conid=conid
    )
    
    # Step 1: Fetch historical data for daily chart
    logger.info("Step 1: Fetching daily historical data")
    step_start = time.time()
    
    try:
        daily_data_raw = await task.ibkr.get_historical_data(conid, period="1y", bar="1d")
        step_duration = int((time.time() - step_start) * 1000)
        
        _log_workflow_step(
            db, execution_id,
            "fetch_daily_data", "fetch_data",
            {"symbol": symbol, "conid": conid, "period": "1y", "bar": "1d"},
            {"data_points": len(daily_data_raw.get('data', [])), "raw_response_keys": list(daily_data_raw.keys())},
            duration_ms=step_duration,
            code=symbol,
            conid=conid
        )
    except Exception as e:
        _log_workflow_step(
            db, execution_id,
            "fetch_daily_data", "fetch_data",
            {"symbol": symbol, "conid": conid, "period": "1y", "bar": "1d"},
            {},
            success=False,
            error_message=str(e),
            code=symbol,
            conid=conid
        )
        raise
    
    # Parse daily data
    daily_df = _parse_historical_data(daily_data_raw)
    
    # Step 2: Generate daily chart
    logger.info("Step 2: Generating daily chart")
    step_start = time.time()
    
    daily_chart_png = task.chart.generate_chart(daily_df, symbol, "1D")
    daily_chart_name = f"charts/{symbol}_daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    daily_chart_url = task.storage.upload_chart(daily_chart_png, daily_chart_name)
    step_duration = int((time.time() - step_start) * 1000)
    
    _log_workflow_step(
        db, execution_id,
        "generate_daily_chart", "chart_generation",
        {"symbol": symbol, "timeframe": "1D", "data_points": len(daily_df)},
        {"chart_url": daily_chart_url, "chart_name": daily_chart_name},
        duration_ms=step_duration,
        code=symbol,
        conid=conid
    )
    
    logger.info(f"Daily chart uploaded: {daily_chart_url}")
    
    # Step 3: Analyze daily chart with AI
    logger.info("Step 3: Analyzing daily chart with AI")
    step_start = time.time()
    
    daily_analysis = await task.ai.analyze_daily_chart(symbol, daily_chart_url)
    step_duration = int((time.time() - step_start) * 1000)
    
    _log_workflow_step(
        db, execution_id,
        "analyze_daily_chart", "ai_analysis",
        {"symbol": symbol, "chart_url": daily_chart_url},
        {"analysis_length": len(daily_analysis), "analysis_preview": daily_analysis[:500]},
        duration_ms=step_duration,
        code=symbol,
        conid=conid
    )
    
    # Step 4: Fetch weekly data
    logger.info("Step 4: Fetching weekly historical data")
    step_start = time.time()
    
    try:
        weekly_data_raw = await task.ibkr.get_historical_data(conid, period="5y", bar="1w")
        step_duration = int((time.time() - step_start) * 1000)
        
        _log_workflow_step(
            db, execution_id,
            "fetch_weekly_data", "fetch_data",
            {"symbol": symbol, "conid": conid, "period": "5y", "bar": "1w"},
            {"data_points": len(weekly_data_raw.get('data', [])), "raw_response_keys": list(weekly_data_raw.keys())},
            duration_ms=step_duration,
            code=symbol,
            conid=conid
        )
    except Exception as e:
        _log_workflow_step(
            db, execution_id,
            "fetch_weekly_data", "fetch_data",
            {"symbol": symbol, "conid": conid, "period": "5y", "bar": "1w"},
            {},
            success=False,
            error_message=str(e),
            code=symbol,
            conid=conid
        )
        raise
        
    weekly_df = _parse_historical_data(weekly_data_raw)
    
    # Step 5: Generate weekly chart
    logger.info("Step 5: Generating weekly chart")
    step_start = time.time()
    
    weekly_chart_png = task.chart.generate_chart(weekly_df, symbol, "1W")
    weekly_chart_name = f"charts/{symbol}_weekly_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    weekly_chart_url = task.storage.upload_chart(weekly_chart_png, weekly_chart_name)
    step_duration = int((time.time() - step_start) * 1000)
    
    _log_workflow_step(
        db, execution_id,
        "generate_weekly_chart", "chart_generation",
        {"symbol": symbol, "timeframe": "1W", "data_points": len(weekly_df)},
        {"chart_url": weekly_chart_url, "chart_name": weekly_chart_name},
        duration_ms=step_duration,
        code=symbol,
        conid=conid
    )
    
    logger.info(f"Weekly chart uploaded: {weekly_chart_url}")
    
    # Step 6: Analyze weekly chart with AI
    logger.info("Step 6: Analyzing weekly chart with AI")
    step_start = time.time()
    
    weekly_analysis = await task.ai.analyze_weekly_chart(symbol, weekly_chart_url)
    step_duration = int((time.time() - step_start) * 1000)
    
    _log_workflow_step(
        db, execution_id,
        "analyze_weekly_chart", "ai_analysis",
        {"symbol": symbol, "chart_url": weekly_chart_url},
        {"analysis_length": len(weekly_analysis), "analysis_preview": weekly_analysis[:500]},
        duration_ms=step_duration,
        code=symbol,
        conid=conid
    )
    
    # Step 7: Consolidate analysis
    logger.info("Step 7: Consolidating multi-timeframe analysis")
    step_start = time.time()
    
    consolidated_analysis = await task.ai.consolidate_analysis(daily_analysis, weekly_analysis)
    step_duration = int((time.time() - step_start) * 1000)
    
    _log_workflow_step(
        db, execution_id,
        "consolidate_analysis", "ai_analysis",
        {"symbol": symbol, "daily_analysis_length": len(daily_analysis), "weekly_analysis_length": len(weekly_analysis)},
        {"consolidated_length": len(consolidated_analysis), "consolidated_preview": consolidated_analysis[:500]},
        duration_ms=step_duration,
        code=symbol,
        conid=conid
    )
    
    # Step 8: Generate trading decision
    logger.info("Step 8: Generating trading decision")
    step_start = time.time()
    
    decision_data = await task.ai.generate_trading_decision(
        consolidated_analysis,
        symbol,
        strategy.name
    )
    step_duration = int((time.time() - step_start) * 1000)
    
    _log_workflow_step(
        db, execution_id,
        "generate_decision", "decision",
        {"symbol": symbol, "strategy": strategy.name, "analysis_length": len(consolidated_analysis)},
        decision_data,
        duration_ms=step_duration,
        code=symbol,
        conid=conid
    )
    
    # Step 9: Save decision to database
    logger.info(f"Step 9: Saving decision to database")
    step_start = time.time()
    
    # Find code_id from the code object
    code_record = db.query(Code).filter(Code.conid == conid).first()
    if not code_record:
        # Create code record if it doesn't exist
        code_record = Code(
            symbol=symbol,
            conid=conid,
            exchange=code_obj.exchange,
            name=code_obj.name
        )
        db.add(code_record)
        db.commit()
        db.refresh(code_record)
    
    decision = Decision(
        strategy_id=strategy.id,
        code_id=code_record.id,
        type=decision_data['type'],
        current_price=decision_data['current_price'],
        target_price=decision_data['target_price'],
        stop_loss=decision_data['stop_loss'],
        profit_margin=decision_data['profit_margin'],
        r_coefficient=decision_data['R_coefficient'],
        analysis_text=consolidated_analysis
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    step_duration = int((time.time() - step_start) * 1000)
    
    _log_workflow_step(
        db, execution_id,
        "save_decision", "decision",
        {"symbol": symbol, "decision_type": decision.type},
        {"decision_id": decision.id, "saved": True},
        duration_ms=step_duration,
        code=symbol,
        conid=conid
    )
    
    logger.info(f"Decision saved: {decision.type} for {symbol}")
    
    # Step 10: Place order if decision is buy/sell
    order_result = None
    order_id = None
    
    if decision.type in ['buy', 'sell']:
        logger.info(f"Step 10: Placing {decision.type} order")
        step_start = time.time()
        
        try:
            # Calculate position size based on strategy parameters
            quantity = _calculate_position_size(
                decision.current_price,
                decision.stop_loss,
                strategy.param or {}
            )
            
            # Place market order
            order_result = await task.ibkr.place_order(
                conid=conid,
                order_type="MKT",
                side="BUY" if decision.type == "buy" else "SELL",
                quantity=quantity,
                tif="DAY"
            )
            step_duration = int((time.time() - step_start) * 1000)
            
            # Save order to database
            if order_result:
                order = Order(
                    strategy_id=strategy.id,
                    decision_id=decision.id,
                    conid=conid,
                    code=symbol,
                    type=decision.type,
                    order_type="MKT",
                    quantity=quantity,
                    price=decision.current_price,
                    status='submitted',
                    ibkr_order_id=str(order_result.get('order_id', ''))
                )
                db.add(order)
                db.commit()
                db.refresh(order)
                order_id = order.id
                
                _log_workflow_step(
                    db, execution_id,
                    "place_order", "order",
                    {"symbol": symbol, "conid": conid, "side": "BUY" if decision.type == "buy" else "SELL", 
                     "quantity": quantity, "type": "MKT"},
                    {"order_id": order_id, "ibkr_order_id": order.ibkr_order_id, "status": "submitted"},
                    duration_ms=step_duration,
                    code=symbol,
                    conid=conid
                )
                
                logger.info(f"Order placed: {order.type} {order.quantity} {symbol}")
        
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            _log_workflow_step(
                db, execution_id,
                "place_order", "order",
                {"symbol": symbol, "conid": conid, "decision_type": decision.type},
                {},
                success=False,
                error_message=str(e),
                code=symbol,
                conid=conid
            )
    else:
        logger.info(f"Decision type is '{decision.type}', no order placed")
        _log_workflow_step(
            db, execution_id,
            "skip_order", "order",
            {"symbol": symbol, "decision_type": decision.type},
            {"reason": f"Decision type is {decision.type}, not buy/sell"},
            code=symbol,
            conid=conid
        )
    
    # Calculate total duration
    total_duration = int((time.time() - start_time) * 1000)
    
    # Log completion for this code
    _log_workflow_step(
        db, execution_id,
        "complete_code_processing", "completion",
        {"symbol": symbol, "conid": conid},
        {
            "total_duration_ms": total_duration,
            "decision_id": decision.id,
            "order_id": order_id,
            "completed_at": datetime.now(timezone.utc).isoformat()
        },
        duration_ms=total_duration,
        code=symbol,
        conid=conid
    )
    
    # Return workflow results for this code
    return {
        'symbol': symbol,
        'conid': conid,
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
        'order': {
            'id': order_id,
            'result': order_result
        } if order_id else None,
        'total_duration_ms': total_duration,
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

