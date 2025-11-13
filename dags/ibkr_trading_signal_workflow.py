"""
IBKR Trading Signal Workflow
Complete end-to-end trading workflow: Market Data → Charts → LLM Analysis → Order → Portfolio Tracking
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
# from airflow.utils.dates import days_ago # Deprecated in Airflow 2.x+
import logging
import os
from decimal import Decimal

# Import models
from models.market_data import MarketData, OHLCVBar
from models.indicators import TechnicalIndicators
from models.chart import ChartConfig, ChartResult, Timeframe
from models.signal import TradingSignal, SignalAction, SignalConfidence
from models.order import Order, OrderType, OrderSide, OrderStatus
from models.trade import Trade, TradeExecution
from models.portfolio import Portfolio, Position

# Import utilities
from utils.config import config
from utils.ibkr_client import IBKRClient
from utils.chart_generator import ChartGenerator
from utils.llm_signal_analyzer import LLMSignalAnalyzer
from utils.mlflow_tracking import mlflow_run_context
from utils.artifact_storage import (
    store_chart_artifact,
    store_llm_artifact,
    store_signal_artifact,
    store_order_artifact,
    store_trade_artifact,
    store_portfolio_artifact
)
from utils.minio_upload import upload_chart_to_minio

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.debug_mode else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# DAG default arguments
default_args = {
    'owner': 'ibkr-trading',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Configuration from environment
SYMBOL = config.stock_symbols[0] if config.stock_symbols else "TSLA"
IBKR_HOST = "gateway"  # Docker service name
IBKR_PORT = 4002  # Paper trading port
POSITION_SIZE = 10  # Number of shares
LLM_PROVIDER = config.llm_provider  # from LLM_PROVIDER env var
LLM_MODEL = config.llm_model  # from LLM_MODEL env var
LLM_API_KEY = config.llm_api_key  # from LLM_API_KEY env var
LLM_API_BASE_URL = config.llm_api_base_url  # from LLM_API_BASE_URL env var

# Workflow schedule configuration
# Default: None (manual trigger only)
# Examples: '@daily', '0 9 * * 1-5' (9 AM weekdays), '@hourly'
WORKFLOW_SCHEDULE = os.getenv('WORKFLOW_SCHEDULE', None) or None  # Convert empty string to None


def fetch_market_data_task(**context):
    """Fetch market data from IBKR"""
    logger.info("="*60)
    logger.info(f"Fetching market data for {SYMBOL}")
    logger.info("="*60)
    
    try:
        with IBKRClient(host=IBKR_HOST, port=IBKR_PORT) as client:
            # Fetch daily data
            market_data = client.fetch_market_data(
                symbol=SYMBOL,
                exchange="SMART",
                duration="200 D",
                bar_size="1 day"
            )
            
            logger.info(f"Fetched {market_data.bar_count} bars")
            logger.info(f"Latest price: ${market_data.latest_price}")
            
            # Store in XCom as dict
            task_instance = context['task_instance']
            task_instance.xcom_push(key='market_data', value=market_data.model_dump_json())
            
            return {
                'symbol': market_data.symbol,
                'bars': market_data.bar_count,
                'latest_price': float(market_data.latest_price)
            }
    
    except Exception as e:
        logger.error(f"Failed to fetch market data: {e}", exc_info=True)
        raise


def generate_daily_chart_task(**context):
    """Generate daily technical chart"""
    logger.info("Generating daily chart with technical indicators")
    
    task_instance = context.get('task_instance')
    error_context = {}
    
    try:
        
        # Retrieve market data
        market_data_json = task_instance.xcom_pull(task_ids='fetch_market_data', key='market_data')
        if not market_data_json:
            raise ValueError("No market data found in XCom. Run fetch_market_data task first.")
        market_data = MarketData.model_validate_json(market_data_json)
        
        # Calculate indicators first
        # Use shared volume for charts (accessible by both Airflow and backend)
        charts_dir = os.getenv('CHARTS_DIR', '/app/charts')
        chart_gen = ChartGenerator(output_dir=charts_dir)
        indicators = chart_gen.calculate_indicators(market_data)

        # Generate chart
        config_daily = ChartConfig(
            symbol=SYMBOL,
            timeframe=Timeframe.DAILY,
            lookback_periods=60,
            include_sma=True,
            include_rsi=True,
            include_macd=True,
            include_bollinger=True
        )

        chart_result = chart_gen.generate_chart(market_data, config_daily, indicators)
        
        logger.info(f"Generated daily chart: {chart_result.file_path}")
        logger.info(f"Indicators: {', '.join(chart_result.indicators_included)}")
        
        # Store in XCom
        task_instance.xcom_push(key='daily_chart', value=chart_result.model_dump_json())
        
        # Upload chart to MinIO
        minio_url = None
        try:
            minio_url = upload_chart_to_minio(
                file_path=chart_result.file_path,
                symbol=SYMBOL,
                timeframe='daily',
                execution_id=str(context['execution_date'])
            )
        except Exception as e:
            logger.warning(f"Failed to upload daily chart to MinIO: {e}")
        
        # Store chart artifact in database
        try:
            # Use MinIO URL if available, otherwise use local path
            image_path = minio_url if minio_url else chart_result.file_path
            store_chart_artifact(
                name=f"{SYMBOL} Daily Chart",
                symbol=SYMBOL,
                image_path=image_path,
                chart_type="daily",
                workflow_id='ibkr_trading_signal_workflow',
                execution_id=str(context['execution_date']),
                step_name='generate_daily_chart',
                dag_id=context['dag'].dag_id,
                task_id=context['task'].task_id,
                chart_data={
                    'indicators': chart_result.indicators_included,
                    'timeframe': 'daily',
                    'bars_count': market_data.bar_count,
                    'minio_url': minio_url,
                    'local_path': chart_result.file_path
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store chart artifact: {e}")
        
        return {
            'chart_path': chart_result.file_path,
            'indicators': chart_result.indicators_included
        }
    
    except TimeoutError as e:
        logger.error(f"Chart generation timed out: {e}", exc_info=True)
        error_context = {
            'error_type': 'timeout',
            'error_message': str(e),
            'task': 'generate_daily_chart'
        }
        if task_instance:
            task_instance.xcom_push(key='error_context', value=error_context)
        raise
    except Exception as e:
        logger.error(f"Failed to generate daily chart: {e}", exc_info=True)
        error_context = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'task': 'generate_daily_chart'
        }
        if task_instance:
            task_instance.xcom_push(key='error_context', value=error_context)
        raise


def generate_weekly_chart_task(**context):
    """Generate weekly technical chart for multi-timeframe confirmation"""
    logger.info("Generating weekly chart")
    
    try:
        task_instance = context['task_instance']
        
        # Retrieve market data
        market_data_json = task_instance.xcom_pull(task_ids='fetch_market_data', key='market_data')
        if not market_data_json:
            raise ValueError("No market data found in XCom. Run fetch_market_data task first.")
        market_data = MarketData.model_validate_json(market_data_json)
        
        # Resample to weekly
        # Use shared volume for charts (accessible by both Airflow and backend)
        charts_dir = os.getenv('CHARTS_DIR', '/app/charts')
        chart_gen = ChartGenerator(output_dir=charts_dir)
        weekly_data = chart_gen.resample_to_weekly(market_data)

        # Calculate indicators for weekly data
        weekly_indicators = chart_gen.calculate_indicators(weekly_data)

        # Generate chart
        config_weekly = ChartConfig(
            symbol=SYMBOL,
            timeframe=Timeframe.WEEKLY,
            lookback_periods=52,
            include_sma=True,
            include_rsi=True,
            include_macd=True,
            include_bollinger=True
        )

        chart_result = chart_gen.generate_chart(weekly_data, config_weekly, weekly_indicators)
        
        logger.info(f"Generated weekly chart: {chart_result.file_path}")
        
        # Store in XCom
        task_instance.xcom_push(key='weekly_chart', value=chart_result.model_dump_json())
        
        # Upload chart to MinIO
        minio_url = None
        try:
            minio_url = upload_chart_to_minio(
                file_path=chart_result.file_path,
                symbol=SYMBOL,
                timeframe='weekly',
                execution_id=str(context['execution_date'])
            )
        except Exception as e:
            logger.warning(f"Failed to upload weekly chart to MinIO: {e}")
        
        # Store chart artifact in database
        try:
            # Use MinIO URL if available, otherwise use local path
            image_path = minio_url if minio_url else chart_result.file_path
            store_chart_artifact(
                name=f"{SYMBOL} Weekly Chart",
                symbol=SYMBOL,
                image_path=image_path,
                chart_type="weekly",
                workflow_id='ibkr_trading_signal_workflow',
                execution_id=str(context['execution_date']),
                step_name='generate_weekly_chart',
                dag_id=context['dag'].dag_id,
                task_id=context['task'].task_id,
                chart_data={
                    'indicators': chart_result.indicators_included if hasattr(chart_result, 'indicators_included') else [],
                    'timeframe': 'weekly',
                    'bars_count': weekly_data.bar_count,
                    'minio_url': minio_url,
                    'local_path': chart_result.file_path
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store chart artifact: {e}")
        
        return {
            'chart_path': chart_result.file_path,
            'periods': chart_result.periods_shown
        }
    
    except Exception as e:
        logger.error(f"Failed to generate weekly chart: {e}", exc_info=True)
        raise


def analyze_with_llm_task(**context):
    """Analyze charts with LLM to generate trading signal"""
    logger.info(f"Analyzing charts with LLM ({LLM_PROVIDER})")
    
    try:
        task_instance = context['task_instance']
        
        # Retrieve data
        market_data_json = task_instance.xcom_pull(task_ids='fetch_market_data', key='market_data')
        daily_chart_json = task_instance.xcom_pull(task_ids='generate_daily_chart', key='daily_chart')
        weekly_chart_json = task_instance.xcom_pull(task_ids='generate_weekly_chart', key='weekly_chart')

        if not market_data_json:
            raise ValueError("No market data found in XCom. Run fetch_market_data task first.")
        if not daily_chart_json:
            raise ValueError("No daily chart found in XCom. Run generate_daily_chart task first.")
        if not weekly_chart_json:
            raise ValueError("No weekly chart found in XCom. Run generate_weekly_chart task first.")

        market_data = MarketData.model_validate_json(market_data_json)
        daily_chart = ChartResult.model_validate_json(daily_chart_json)
        weekly_chart = ChartResult.model_validate_json(weekly_chart_json)
        
        # Analyze with LLM
        analyzer = LLMSignalAnalyzer(
            provider=LLM_PROVIDER,
            model=LLM_MODEL,
            api_key=LLM_API_KEY if LLM_API_KEY else None,
            base_url=LLM_API_BASE_URL if LLM_API_BASE_URL else None
        )
        signal = analyzer.analyze_charts(
            symbol=SYMBOL,
            daily_chart=daily_chart,
            weekly_chart=weekly_chart,
            market_data=market_data
        )
        
        logger.info(f"LLM Signal: {signal.action} (Confidence: {signal.confidence} - {signal.confidence_score}%)")
        logger.info(f"Reasoning: {signal.reasoning[:200]}...")
        logger.info(f"Is Actionable: {signal.is_actionable}")
        
        if signal.risk_reward_ratio:
            logger.info(f"Risk/Reward Ratio: {signal.risk_reward_ratio}")
        
        # Store in XCom
        task_instance.xcom_push(key='trading_signal', value=signal.model_dump_json())
        
        # Store LLM artifact (prompt + response)
        try:
            prompt_text = f"Analyze {SYMBOL} daily and weekly charts with technical indicators (SMA, RSI, MACD, Bollinger Bands) and provide trading recommendation."
            store_llm_artifact(
                name=f"{SYMBOL} LLM Analysis",
                symbol=SYMBOL,
                prompt=prompt_text,
                response=signal.reasoning,
                model_name=signal.model_used or LLM_MODEL or "unknown",
                workflow_id='ibkr_trading_signal_workflow',
                execution_id=str(context['execution_date']),
                step_name='analyze_with_llm',
                dag_id=context['dag'].dag_id,
                task_id=context['task'].task_id
            )
        except Exception as e:
            logger.warning(f"Failed to store LLM artifact: {e}")
        
        # Store signal artifact
        try:
            store_signal_artifact(
                name=f"{SYMBOL} {signal.action} Signal",
                symbol=SYMBOL,
                action=str(signal.action),
                confidence=float(signal.confidence_score) / 100.0 if signal.confidence_score else 0.5,
                workflow_id='ibkr_trading_signal_workflow',
                execution_id=str(context['execution_date']),
                step_name='analyze_with_llm',
                dag_id=context['dag'].dag_id,
                task_id=context['task'].task_id,
                signal_data={
                    'confidence_level': str(signal.confidence),
                    'confidence_score': float(signal.confidence_score) if signal.confidence_score else None,
                    'reasoning': signal.reasoning,
                    'key_factors': signal.key_factors,
                    'entry_price': float(signal.suggested_entry_price) if signal.suggested_entry_price else None,
                    'stop_loss': float(signal.suggested_stop_loss) if signal.suggested_stop_loss else None,
                    'take_profit': float(signal.suggested_take_profit) if signal.suggested_take_profit else None,
                    'risk_reward_ratio': float(signal.risk_reward_ratio) if signal.risk_reward_ratio else None,
                    'is_actionable': signal.is_actionable
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store signal artifact: {e}")
        
        return {
            'action': signal.action,
            'confidence': signal.confidence,
            'is_actionable': signal.is_actionable,
            'entry_price': float(signal.suggested_entry_price) if signal.suggested_entry_price else None
        }
    
    except Exception as e:
        logger.error(f"Failed to analyze with LLM: {e}", exc_info=True)
        raise


def place_order_task(**context):
    """Place order if signal is actionable"""
    logger.info("Evaluating whether to place order")
    
    try:
        task_instance = context['task_instance']
        
        # Retrieve signal
        signal_json = task_instance.xcom_pull(task_ids='analyze_with_llm', key='trading_signal')
        signal = TradingSignal.model_validate_json(signal_json)
        
        if not signal.is_actionable:
            logger.info(f"Signal not actionable: {signal.action} with {signal.confidence} confidence")
            task_instance.xcom_push(key='order_placed', value=False)
            return {'order_placed': False, 'reason': 'Signal not actionable'}
        
        logger.info(f"Signal is actionable! Placing {signal.action} order")
        
        # Create order
        order = Order(
            symbol=SYMBOL,
            side=OrderSide.BUY if signal.action == SignalAction.BUY else OrderSide.SELL,
            quantity=POSITION_SIZE,
            order_type=OrderType.LIMIT,
            limit_price=signal.suggested_entry_price,
            signal_id=str(context['execution_date'])
        )
        
        # Place order via IBKR
        with IBKRClient(host=IBKR_HOST, port=IBKR_PORT) as client:
            order = client.place_order(order)
        
        logger.info(f"Order placed: {order.order_id}")
        logger.info(f"Side: {order.side}, Quantity: {order.quantity}, Price: ${order.limit_price}")
        
        # Store order artifact
        try:
            store_order_artifact(
                name=f"{SYMBOL} {order.side} Order",
                symbol=SYMBOL,
                order_id=str(order.order_id),
                order_type=str(order.order_type),
                side=str(order.side),
                quantity=order.quantity,
                price=float(order.limit_price) if order.limit_price else None,
                status=str(order.status),
                workflow_id='ibkr_trading_signal_workflow',
                execution_id=str(context['execution_date']),
                step_name='place_order',
                dag_id=context['dag'].dag_id,
                task_id=context['task'].task_id,
                order_data={
                    'signal_id': order.signal_id,
                    'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store order artifact: {e}")
        
        # Store in XCom
        task_instance.xcom_push(key='order', value=order.model_dump_json())
        task_instance.xcom_push(key='order_placed', value=True)
        
        return {
            'order_placed': True,
            'order_id': order.order_id,
            'side': order.side,
            'quantity': order.quantity
        }
    
    except Exception as e:
        logger.error(f"Failed to place order: {e}", exc_info=True)
        raise


def get_trades_task(**context):
    """Get trade executions from IBKR"""
    logger.info("Retrieving trade executions")
    
    try:
        task_instance = context['task_instance']
        
        # Check if order was placed
        order_placed = task_instance.xcom_pull(task_ids='place_order', key='order_placed')
        
        if not order_placed:
            logger.info("No order was placed, skipping trade retrieval")
            return {'trades_found': 0}
        
        # Retrieve order
        order_json = task_instance.xcom_pull(task_ids='place_order', key='order')
        order = Order.model_validate_json(order_json)
        
        # Get trades
        with IBKRClient(host=IBKR_HOST, port=IBKR_PORT) as client:
            trades = client.get_trades(order.order_id)
        
        logger.info(f"Retrieved {len(trades)} trade(s)")
        
        if trades:
            trade = trades[0]
            logger.info(f"Trade: {trade.total_quantity} @ ${trade.average_price}")
            logger.info(f"Total cost: ${trade.total_cost}")
            
            # Store trade artifact
            try:
                store_trade_artifact(
                    name=f"{SYMBOL} Trade Execution",
                    symbol=SYMBOL,
                    trade_id=trade.executions[0].execution_id if trade.executions else f"TRADE_{order.order_id}",
                    order_id=str(order.order_id),
                    quantity=int(trade.total_quantity),
                    price=float(trade.average_price),
                    side=str(trade.side),
                    workflow_id='ibkr_trading_signal_workflow',
                    execution_id=str(context['execution_date']),
                    step_name='get_trades',
                    dag_id=context['dag'].dag_id,
                    task_id=context['task'].task_id,
                    trade_data={
                        'total_quantity': int(trade.total_quantity),
                        'average_price': float(trade.average_price),
                        'total_commission': float(trade.total_commission),
                        'total_cost': float(trade.total_cost),
                        'first_execution_at': trade.first_execution_at.isoformat() if trade.first_execution_at else None,
                        'last_execution_at': trade.last_execution_at.isoformat() if trade.last_execution_at else None
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to store trade artifact: {e}")
            
            # Store in XCom
            task_instance.xcom_push(key='trades', value=[t.model_dump_json() for t in trades])
        
        return {
            'trades_found': len(trades),
            'total_quantity': trades[0].total_quantity if trades else 0
        }
    
    except Exception as e:
        logger.error(f"Failed to get trades: {e}", exc_info=True)
        raise


def get_portfolio_task(**context):
    """Get current portfolio status from IBKR"""
    logger.info("Retrieving portfolio status")
    
    try:
        task_instance = context['task_instance']
        
        # Get portfolio
        with IBKRClient(host=IBKR_HOST, port=IBKR_PORT) as client:
            portfolio = client.get_portfolio()
        
        logger.info(f"Portfolio: {portfolio.position_count} positions")
        logger.info(f"Total value: ${portfolio.total_value}")
        logger.info(f"Cash: ${portfolio.cash_balance}")
        logger.info(f"Unrealized P&L: ${portfolio.total_unrealized_pnl}")
        
        # Check for symbol position
        if portfolio.has_position(SYMBOL):
            position = portfolio.get_position(SYMBOL)
            logger.info(f"{SYMBOL} Position: {position.quantity} shares @ ${position.current_price}")
            logger.info(f"P&L: ${position.unrealized_pnl} ({position.unrealized_pnl_percent}%)")
        
        # Store portfolio artifact
        try:
            portfolio_positions = [
                {
                    'symbol': p.symbol,
                    'quantity': p.quantity,
                    'average_cost': float(p.average_cost),
                    'current_price': float(p.current_price),
                    'market_value': float(p.market_value),
                    'unrealized_pnl': float(p.unrealized_pnl),
                    'unrealized_pnl_percent': float(p.unrealized_pnl_percent)
                }
                for p in portfolio.positions
            ]
            store_portfolio_artifact(
                name="Portfolio Snapshot",
                account_id=portfolio.account_id,
                total_value=float(portfolio.total_value),
                cash_balance=float(portfolio.cash_balance),
                position_count=portfolio.position_count,
                workflow_id='ibkr_trading_signal_workflow',
                execution_id=str(context['execution_date']),
                step_name='get_portfolio',
                dag_id=context['dag'].dag_id,
                task_id=context['task'].task_id,
                portfolio_data={
                    'positions': portfolio_positions,
                    'total_market_value': float(portfolio.total_market_value),
                    'total_unrealized_pnl': float(portfolio.total_unrealized_pnl)
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store portfolio artifact: {e}")
        
        # Store in XCom
        task_instance.xcom_push(key='portfolio', value=portfolio.model_dump_json())
        
        return {
            'positions': portfolio.position_count,
            'total_value': float(portfolio.total_value),
            'cash': float(portfolio.cash_balance)
        }
    
    except Exception as e:
        logger.error(f"Failed to get portfolio: {e}", exc_info=True)
        raise


def log_to_mlflow_task(**context):
    """Log entire workflow to MLflow"""
    logger.info("Logging workflow to MLflow")
    
    try:
        task_instance = context['task_instance']
        execution_date = context['execution_date']
        dag_run = context['dag_run']
        
        # Retrieve all data
        market_data_json = task_instance.xcom_pull(task_ids='fetch_market_data', key='market_data')
        signal_json = task_instance.xcom_pull(task_ids='analyze_with_llm', key='trading_signal')
        daily_chart_json = task_instance.xcom_pull(task_ids='generate_daily_chart', key='daily_chart')
        weekly_chart_json = task_instance.xcom_pull(task_ids='generate_weekly_chart', key='weekly_chart')
        portfolio_json = task_instance.xcom_pull(task_ids='get_portfolio', key='portfolio')
        order_placed = task_instance.xcom_pull(task_ids='place_order', key='order_placed')
        
        market_data = MarketData.model_validate_json(market_data_json)
        signal = TradingSignal.model_validate_json(signal_json)
        daily_chart = ChartResult.model_validate_json(daily_chart_json)
        weekly_chart = ChartResult.model_validate_json(weekly_chart_json)
        portfolio = Portfolio.model_validate_json(portfolio_json)
        
        # Start MLflow run
        run_name = f"trading_signal_{SYMBOL}_{execution_date.strftime('%Y%m%d_%H%M%S')}"
        tags = {
            'workflow_type': 'trading_signal',
            'symbol': SYMBOL,
            'airflow_dag_id': context['dag'].dag_id,
            'airflow_run_id': dag_run.run_id,
            'signal_action': signal.action,
            'signal_confidence': signal.confidence,
            'order_placed': str(order_placed)
        }
        
        with mlflow_run_context(run_name=run_name, tags=tags) as tracker:
            
            # Log parameters
            tracker.log_params({
                'symbol': SYMBOL,
                'position_size': POSITION_SIZE,
                'llm_provider': LLM_PROVIDER,
                'execution_date': str(execution_date),
                'signal_action': signal.action,
                'signal_confidence': signal.confidence,
                'signal_model': signal.model_used
            })
            
            # Log metrics
            metrics = {
                'latest_price': float(market_data.latest_price),
                'confidence_score': float(signal.confidence_score),
                'bars_analyzed': market_data.bar_count,
                'portfolio_value': float(portfolio.total_value),
                'portfolio_cash': float(portfolio.cash_balance),
                'portfolio_positions': portfolio.position_count
            }
            
            if signal.risk_reward_ratio:
                metrics['risk_reward_ratio'] = float(signal.risk_reward_ratio)
            
            if order_placed:
                metrics['order_placed'] = 1
            else:
                metrics['order_placed'] = 0
            
            tracker.log_metrics(metrics)
            
            # Log artifacts
            tracker.log_artifact_dict({
                'symbol': signal.symbol,
                'action': signal.action,
                'confidence': signal.confidence,
                'confidence_score': float(signal.confidence_score),
                'reasoning': signal.reasoning,
                'key_factors': signal.key_factors,
                'entry_price': float(signal.suggested_entry_price) if signal.suggested_entry_price else None,
                'stop_loss': float(signal.suggested_stop_loss) if signal.suggested_stop_loss else None,
                'take_profit': float(signal.suggested_take_profit) if signal.suggested_take_profit else None
            }, 'trading_signal.json')
            
            # Log charts as artifacts directly from their file paths
            try:
                tracker.log_file_artifact(daily_chart.file_path)
                tracker.log_file_artifact(weekly_chart.file_path)
            except Exception as e:
                logger.warning(f"Failed to log chart artifacts: {e}")
            
            # Log portfolio
            tracker.log_artifact_dict({
                'account_id': portfolio.account_id,
                'total_value': float(portfolio.total_value),
                'cash_balance': float(portfolio.cash_balance),
                'positions': [
                    {
                        'symbol': p.symbol,
                        'quantity': p.quantity,
                        'current_price': float(p.current_price),
                        'unrealized_pnl': float(p.unrealized_pnl)
                    }
                    for p in portfolio.positions
                ]
            }, 'portfolio.json')
            
            # Log debug info if enabled
            if config.debug_mode:
                debug_info = {
                    'config': config.to_dict(),
                    'market_data_summary': {
                        'bars': market_data.bar_count,
                        'latest_price': float(market_data.latest_price),
                        'timeframe': market_data.timeframe
                    },
                    'charts': {
                        'daily': {
                            'path': daily_chart.file_path,
                            'indicators': daily_chart.indicators_included
                        },
                        'weekly': {
                            'path': weekly_chart.file_path,
                            'indicators': weekly_chart.indicators_included
                        }
                    },
                    'airflow_context': {
                        'dag_id': context['dag'].dag_id,
                        'task_id': context['task'].task_id,
                        'execution_date': str(execution_date)
                    }
                }
                tracker.log_debug_info(debug_info)
            
            logger.info(f"Successfully logged to MLflow. Run ID: {tracker.run_id}")
            
            # Update artifacts with MLflow run_id if not already set (limit to 5 to prevent timeout)
            try:
                import requests
                backend_url = os.getenv('BACKEND_API_URL', 'http://backend:8000')
                # Get recent artifacts for this symbol and update them
                response = requests.get(f"{backend_url}/api/artifacts/?symbol={SYMBOL}&limit=5", timeout=3)
                if response.status_code == 200:
                    artifacts = response.json().get('artifacts', [])
                    for artifact in artifacts[:5]:  # Limit to 5 artifacts max
                        if not artifact.get('run_id'):
                            try:
                                requests.patch(
                                    f"{backend_url}/api/artifacts/{artifact['id']}",
                                    json={'run_id': tracker.run_id},
                                    timeout=2
                                )
                            except Exception as e:
                                logger.warning(f"Failed to update artifact {artifact['id']}: {e}")
            except Exception as e:
                logger.warning(f"Failed to update artifacts with MLflow run_id: {e}")
        
        return {'mlflow_run_id': tracker.run_id}
    
    except Exception as e:
        logger.error(f"MLflow logging failed: {e}", exc_info=True)
        raise


# Define the DAG
with DAG(
    'ibkr_trading_signal_workflow',
    default_args=default_args,
    description='IBKR Trading Signal Workflow - Market Data → Charts → LLM Analysis → Order → Portfolio',
    schedule_interval=WORKFLOW_SCHEDULE,  # Configurable via WORKFLOW_SCHEDULE env var
    start_date=datetime(2023, 1, 1), # Using a fixed date as days_ago is deprecated
    catchup=False,
    tags=['ibkr', 'trading', 'llm', 'signals', 'ml', 'automated' if WORKFLOW_SCHEDULE else 'manual'],
    max_active_runs=1,
) as dag:
    
    # Task 1: Fetch market data from IBKR
    fetch_market_data = PythonOperator(
        task_id='fetch_market_data',
        python_callable=fetch_market_data_task,
        provide_context=True,
        execution_timeout=timedelta(minutes=5),  # Fail after 5 minutes
        doc_md="""
        ### Fetch Market Data
        Fetches historical market data from IBKR Gateway for the configured symbol.
        - Symbol: TSLA (configurable)
        - Duration: 200 days
        - Timeframe: Daily
        - Validates with MarketData Pydantic model
        """
    )
    
    # Task 2: Generate daily chart
    generate_daily_chart = PythonOperator(
        task_id='generate_daily_chart',
        python_callable=generate_daily_chart_task,
        provide_context=True,
        execution_timeout=timedelta(minutes=15),  # Fail after 15 minutes
        doc_md="""
        ### Generate Daily Chart
        Creates technical analysis chart with indicators:
        - Candlesticks (60 days)
        - SMA (20, 50, 200)
        - RSI (14)
        - MACD
        - Bollinger Bands
        - Volume
        """
    )
    
    # Task 3: Generate weekly chart
    generate_weekly_chart = PythonOperator(
        task_id='generate_weekly_chart',
        python_callable=generate_weekly_chart_task,
        provide_context=True,
        execution_timeout=timedelta(minutes=15),  # Fail after 15 minutes
        doc_md="""
        ### Generate Weekly Chart
        Creates weekly timeframe chart for multi-timeframe confirmation.
        - Resamples daily data to weekly
        - Same indicators as daily chart
        - 52 weeks lookback
        """
    )
    
    # Task 4: Analyze with LLM
    analyze_with_llm = PythonOperator(
        task_id='analyze_with_llm',
        python_callable=analyze_with_llm_task,
        provide_context=True,
        execution_timeout=timedelta(minutes=20),  # LLM can take time
        doc_md="""
        ### LLM Analysis
        Sends both charts to LLM (GPT-4o or Claude) for analysis.
        - Analyzes technical patterns
        - Generates BUY/SELL/HOLD signal
        - Provides confidence score
        - Suggests entry, stop loss, take profit
        - Validates with TradingSignal Pydantic model
        """
    )
    
    # Task 5: Place order
    place_order = PythonOperator(
        task_id='place_order',
        python_callable=place_order_task,
        provide_context=True,
        execution_timeout=timedelta(minutes=5),
        doc_md="""
        ### Place Order
        Places order to IBKR if signal is actionable:
        - Only executes for HIGH/MEDIUM confidence
        - Only for BUY/SELL signals (not HOLD)
        - Uses limit order at suggested entry price
        - Validates with Order Pydantic model
        """
    )
    
    # Task 6: Get trades
    get_trades = PythonOperator(
        task_id='get_trades',
        python_callable=get_trades_task,
        provide_context=True,
        execution_timeout=timedelta(minutes=5),
        doc_md="""
        ### Get Trades
        Retrieves trade executions from IBKR.
        - Fetches execution details
        - Calculates average price
        - Validates with Trade Pydantic model
        """
    )
    
    # Task 7: Get portfolio
    get_portfolio = PythonOperator(
        task_id='get_portfolio',
        python_callable=get_portfolio_task,
        provide_context=True,
        execution_timeout=timedelta(minutes=5),
        doc_md="""
        ### Get Portfolio
        Retrieves current portfolio status from IBKR.
        - All positions
        - Cash balance
        - Total value
        - Unrealized P&L
        - Validates with Portfolio Pydantic model
        """
    )
    
    # Task 8: Log to MLflow
    log_to_mlflow = PythonOperator(
        task_id='log_to_mlflow',
        python_callable=log_to_mlflow_task,
        provide_context=True,
        execution_timeout=timedelta(minutes=5),
        doc_md="""
        ### Log to MLflow
        Tracks entire workflow in MLflow:
        - All Pydantic models
        - Charts (PNG artifacts)
        - Trading signal details
        - Portfolio status
        - Debug information
        """
    )
    
    # Define task dependencies
    fetch_market_data >> [generate_daily_chart, generate_weekly_chart]
    [generate_daily_chart, generate_weekly_chart] >> analyze_with_llm
    analyze_with_llm >> place_order
    place_order >> get_trades
    get_trades >> get_portfolio
    get_portfolio >> log_to_mlflow

