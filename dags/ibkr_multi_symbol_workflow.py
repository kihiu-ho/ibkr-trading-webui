"""
IBKR Multi-Symbol Trading Signal Workflow
Processes TSLA and NVDA in parallel: Market Data → Charts → LLM Analysis → Order → Portfolio Tracking
"""
from datetime import datetime, timedelta
from typing import List
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.dates import days_ago
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
# Fetch symbols dynamically from backend API
def get_enabled_symbols() -> List[str]:
    """Fetch enabled symbols from backend API."""
    try:
        import requests
        backend_url = os.getenv('BACKEND_API_URL', 'http://backend:8000')
        response = requests.get(
            f"{backend_url}/api/workflow-symbols/?enabled_only=true",
            timeout=5
        )
        if response.status_code == 200:
            symbols_data = response.json()
            # Sort by priority (descending) and extract symbols
            symbols = [s['symbol'] for s in sorted(
                symbols_data,
                key=lambda x: x.get('priority', 0),
                reverse=True
            )]
            logger.info(f"Fetched {len(symbols)} enabled symbols from backend: {symbols}")
            return symbols if symbols else ['TSLA', 'NVDA']  # Fallback
    except Exception as e:
        logger.warning(f"Failed to fetch symbols from backend: {e}")
    
    # Fallback to defaults
    return ['TSLA', 'NVDA']

SYMBOLS = get_enabled_symbols()  # NASDAQ symbols to process
IBKR_HOST = "gateway"  # Docker service name
IBKR_PORT = 4002  # Paper trading port
POSITION_SIZE = 10  # Number of shares per symbol
LLM_PROVIDER = config.llm_provider
LLM_MODEL = config.llm_model
LLM_API_KEY = config.llm_api_key
LLM_API_BASE_URL = config.llm_api_base_url

# Workflow schedule configuration
# Default: None (manual trigger only)
# Examples: '@daily', '0 9 * * 1-5' (9 AM weekdays), '@hourly'
WORKFLOW_SCHEDULE = os.getenv('WORKFLOW_SCHEDULE', None) or None  # Convert empty string to None


def fetch_market_data_task(symbol: str, **context):
    """Fetch market data from IBKR for a specific symbol"""
    logger.info("="*60)
    logger.info(f"Fetching market data for {symbol}")
    logger.info("="*60)
    
    try:
        with IBKRClient(host=IBKR_HOST, port=IBKR_PORT) as client:
            market_data = client.fetch_market_data(
                symbol=symbol,
                exchange="SMART",
                duration="200 D",
                bar_size="1 day"
            )
            
            logger.info(f"Fetched {market_data.bar_count} bars for {symbol}")
            logger.info(f"Latest price: ${market_data.latest_price}")
            
            # Store in XCom with symbol prefix
            task_instance = context['task_instance']
            task_instance.xcom_push(key=f'{symbol}_market_data', value=market_data.model_dump_json())
            
            return {
                'symbol': market_data.symbol,
                'bars': market_data.bar_count,
                'latest_price': float(market_data.latest_price)
            }
    
    except Exception as e:
        logger.error(f"Failed to fetch market data for {symbol}: {e}", exc_info=True)
        raise


def generate_daily_chart_task(symbol: str, **context):
    """Generate daily technical chart for a symbol"""
    logger.info(f"Generating daily chart for {symbol}")
    
    try:
        task_instance = context['task_instance']
        
        # Retrieve market data
        market_data_json = task_instance.xcom_pull(task_ids=f'fetch_market_data_{symbol}', key=f'{symbol}_market_data')
        if not market_data_json:
            raise ValueError(f"No market data found for {symbol}")
        market_data = MarketData.model_validate_json(market_data_json)
        
        # Calculate indicators
        # Use shared volume for charts (accessible by both Airflow and backend)
        charts_dir = os.getenv('CHARTS_DIR', '/app/charts')
        chart_gen = ChartGenerator(output_dir=charts_dir)
        indicators = chart_gen.calculate_indicators(market_data)

        # Generate chart
        config_daily = ChartConfig(
            symbol=symbol,
            timeframe=Timeframe.DAILY,
            lookback_periods=60,
            include_sma=True,
            include_rsi=True,
            include_macd=True,
            include_bollinger=True
        )

        chart_result = chart_gen.generate_chart(market_data, config_daily, indicators)
        
        logger.info(f"Generated daily chart for {symbol}: {chart_result.file_path}")
        
        # Store in XCom
        task_instance.xcom_push(key=f'{symbol}_daily_chart', value=chart_result.model_dump_json())
        
        # Store chart artifact
        try:
            store_chart_artifact(
                name=f"{symbol} Daily Chart",
                symbol=symbol,
                image_path=chart_result.file_path,
                chart_type="daily",
                workflow_id='ibkr_multi_symbol_workflow',
                execution_id=context['dag_run'].run_id if 'dag_run' in context else str(context['execution_date']),
                step_name=f'generate_daily_chart_{symbol}',
                dag_id=context['dag'].dag_id,
                task_id=context['task'].task_id,
                chart_data={
                    'indicators': chart_result.indicators_included,
                    'timeframe': 'daily',
                    'bars_count': market_data.bar_count
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store chart artifact for {symbol}: {e}")
        
        return {
            'chart_path': chart_result.file_path,
            'indicators': chart_result.indicators_included
        }
    
    except Exception as e:
        logger.error(f"Failed to generate daily chart for {symbol}: {e}", exc_info=True)
        raise


def generate_weekly_chart_task(symbol: str, **context):
    """Generate weekly technical chart for a symbol"""
    logger.info(f"Generating weekly chart for {symbol}")
    
    try:
        task_instance = context['task_instance']
        
        # Retrieve market data
        market_data_json = task_instance.xcom_pull(task_ids=f'fetch_market_data_{symbol}', key=f'{symbol}_market_data')
        if not market_data_json:
            raise ValueError(f"No market data found for {symbol}")
        market_data = MarketData.model_validate_json(market_data_json)
        
        # Resample to weekly
        # Use shared volume for charts (accessible by both Airflow and backend)
        charts_dir = os.getenv('CHARTS_DIR', '/app/charts')
        chart_gen = ChartGenerator(output_dir=charts_dir)
        weekly_data = chart_gen.resample_to_weekly(market_data)
        weekly_indicators = chart_gen.calculate_indicators(weekly_data)

        # Generate chart
        config_weekly = ChartConfig(
            symbol=symbol,
            timeframe=Timeframe.WEEKLY,
            lookback_periods=52,
            include_sma=True,
            include_rsi=True,
            include_macd=True,
            include_bollinger=True
        )

        chart_result = chart_gen.generate_chart(weekly_data, config_weekly, weekly_indicators)
        
        logger.info(f"Generated weekly chart for {symbol}: {chart_result.file_path}")
        
        # Store in XCom
        task_instance.xcom_push(key=f'{symbol}_weekly_chart', value=chart_result.model_dump_json())
        
        # Store chart artifact
        try:
            store_chart_artifact(
                name=f"{symbol} Weekly Chart",
                symbol=symbol,
                image_path=chart_result.file_path,
                chart_type="weekly",
                workflow_id='ibkr_multi_symbol_workflow',
                execution_id=context['dag_run'].run_id if 'dag_run' in context else str(context['execution_date']),
                step_name=f'generate_weekly_chart_{symbol}',
                dag_id=context['dag'].dag_id,
                task_id=context['task'].task_id,
                chart_data={
                    'indicators': chart_result.indicators_included if hasattr(chart_result, 'indicators_included') else [],
                    'timeframe': 'weekly',
                    'bars_count': weekly_data.bar_count
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store chart artifact for {symbol}: {e}")
        
        return {
            'chart_path': chart_result.file_path,
            'periods': chart_result.periods_shown
        }
    
    except Exception as e:
        logger.error(f"Failed to generate weekly chart for {symbol}: {e}", exc_info=True)
        raise


def analyze_with_llm_task(symbol: str, **context):
    """Analyze charts with LLM to generate trading signal for a symbol"""
    logger.info(f"Analyzing charts with LLM for {symbol} ({LLM_PROVIDER})")
    
    try:
        task_instance = context['task_instance']
        
        # Retrieve data
        market_data_json = task_instance.xcom_pull(task_ids=f'fetch_market_data_{symbol}', key=f'{symbol}_market_data')
        daily_chart_json = task_instance.xcom_pull(task_ids=f'generate_daily_chart_{symbol}', key=f'{symbol}_daily_chart')
        weekly_chart_json = task_instance.xcom_pull(task_ids=f'generate_weekly_chart_{symbol}', key=f'{symbol}_weekly_chart')

        if not market_data_json or not daily_chart_json or not weekly_chart_json:
            raise ValueError(f"Missing data for {symbol}")

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
            symbol=symbol,
            daily_chart=daily_chart,
            weekly_chart=weekly_chart,
            market_data=market_data
        )
        
        logger.info(f"{symbol} LLM Signal: {signal.action} (Confidence: {signal.confidence} - {signal.confidence_score}%)")
        logger.info(f"Is Actionable: {signal.is_actionable}")
        
        # Store in XCom
        task_instance.xcom_push(key=f'{symbol}_trading_signal', value=signal.model_dump_json())
        
        # Store LLM artifact
        try:
            prompt_text = f"Analyze {symbol} daily and weekly charts with technical indicators (SMA, RSI, MACD, Bollinger Bands) and provide trading recommendation."
            store_llm_artifact(
                name=f"{symbol} LLM Analysis",
                symbol=symbol,
                prompt=prompt_text,
                response=signal.reasoning,
                model_name=signal.model_used or LLM_MODEL or "unknown",
                workflow_id='ibkr_multi_symbol_workflow',
                execution_id=context['dag_run'].run_id if 'dag_run' in context else str(context['execution_date']),
                step_name=f'analyze_with_llm_{symbol}',
                dag_id=context['dag'].dag_id,
                task_id=context['task'].task_id
            )
        except Exception as e:
            logger.warning(f"Failed to store LLM artifact for {symbol}: {e}")
        
        # Store signal artifact
        try:
            store_signal_artifact(
                name=f"{symbol} {signal.action} Signal",
                symbol=symbol,
                action=str(signal.action),
                confidence=float(signal.confidence_score) / 100.0 if signal.confidence_score else 0.5,
                workflow_id='ibkr_multi_symbol_workflow',
                execution_id=context['dag_run'].run_id if 'dag_run' in context else str(context['execution_date']),
                step_name=f'analyze_with_llm_{symbol}',
                dag_id=context['dag'].dag_id,
                task_id=context['task'].task_id,
                signal_data={
                    'confidence_level': str(signal.confidence),
                    'confidence_score': signal.confidence_score,
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
            logger.warning(f"Failed to store signal artifact for {symbol}: {e}")
        
        return {
            'symbol': symbol,
            'action': signal.action,
            'confidence': signal.confidence,
            'is_actionable': signal.is_actionable
        }
    
    except Exception as e:
        logger.error(f"Failed to analyze with LLM for {symbol}: {e}", exc_info=True)
        raise


def place_order_task(symbol: str, **context):
    """Place order if signal is actionable for a symbol"""
    logger.info(f"Evaluating whether to place order for {symbol}")
    
    try:
        task_instance = context['task_instance']
        
        # Retrieve signal
        signal_json = task_instance.xcom_pull(task_ids=f'analyze_with_llm_{symbol}', key=f'{symbol}_trading_signal')
        signal = TradingSignal.model_validate_json(signal_json)
        
        if not signal.is_actionable:
            logger.info(f"{symbol}: Signal not actionable: {signal.action} with {signal.confidence} confidence")
            task_instance.xcom_push(key=f'{symbol}_order_placed', value=False)
            return {'symbol': symbol, 'order_placed': False, 'reason': 'Signal not actionable'}
        
        logger.info(f"{symbol}: Signal is actionable! Placing {signal.action} order")
        
        # Create order
        order = Order(
            symbol=symbol,
            side=OrderSide.BUY if signal.action == SignalAction.BUY else OrderSide.SELL,
            quantity=POSITION_SIZE,
            order_type=OrderType.LIMIT,
            limit_price=signal.suggested_entry_price,
            signal_id=str(context['execution_date'])
        )
        
        # Place order via IBKR
        with IBKRClient(host=IBKR_HOST, port=IBKR_PORT) as client:
            order = client.place_order(order)
        
        logger.info(f"{symbol}: Order placed: {order.order_id}")
        
        # Store order artifact
        try:
            store_order_artifact(
                name=f"{symbol} {order.side} Order",
                symbol=symbol,
                order_id=str(order.order_id),
                order_type=str(order.order_type),
                side=str(order.side),
                quantity=order.quantity,
                price=float(order.limit_price) if order.limit_price else None,
                status=str(order.status),
                workflow_id='ibkr_multi_symbol_workflow',
                execution_id=context['dag_run'].run_id if 'dag_run' in context else str(context['execution_date']),
                step_name=f'place_order_{symbol}',
                dag_id=context['dag'].dag_id,
                task_id=context['task'].task_id,
                order_data={
                    'signal_id': order.signal_id,
                    'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store order artifact for {symbol}: {e}")
        
        # Store in XCom
        task_instance.xcom_push(key=f'{symbol}_order', value=order.model_dump_json())
        task_instance.xcom_push(key=f'{symbol}_order_placed', value=True)
        
        return {
            'symbol': symbol,
            'order_placed': True,
            'order_id': order.order_id
        }
    
    except Exception as e:
        logger.error(f"Failed to place order for {symbol}: {e}", exc_info=True)
        raise


def get_trades_task(symbol: str, **context):
    """Get trade executions from IBKR for a symbol"""
    logger.info(f"Retrieving trade executions for {symbol}")
    
    try:
        task_instance = context['task_instance']
        
        # Check if order was placed
        order_placed = task_instance.xcom_pull(task_ids=f'place_order_{symbol}', key=f'{symbol}_order_placed')
        
        if not order_placed:
            logger.info(f"{symbol}: No order was placed, skipping trade retrieval")
            return {'symbol': symbol, 'trades_found': 0}
        
        # Retrieve order
        order_json = task_instance.xcom_pull(task_ids=f'place_order_{symbol}', key=f'{symbol}_order')
        order = Order.model_validate_json(order_json)
        
        # Get trades
        with IBKRClient(host=IBKR_HOST, port=IBKR_PORT) as client:
            trades = client.get_trades(order.order_id)
        
        logger.info(f"{symbol}: Retrieved {len(trades)} trade(s)")
        
        if trades:
            trade = trades[0]
            logger.info(f"{symbol}: Trade: {trade.total_quantity} @ ${trade.average_price}")
            
            # Store trade artifact
            try:
                store_trade_artifact(
                    name=f"{symbol} Trade Execution",
                    symbol=symbol,
                    trade_id=trade.executions[0].execution_id if trade.executions else f"TRADE_{order.order_id}",
                    order_id=str(order.order_id),
                    quantity=int(trade.total_quantity),
                    price=float(trade.average_price),
                    side=str(trade.side),
                    workflow_id='ibkr_multi_symbol_workflow',
                    execution_id=context['dag_run'].run_id if 'dag_run' in context else str(context['execution_date']),
                    step_name=f'get_trades_{symbol}',
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
                logger.warning(f"Failed to store trade artifact for {symbol}: {e}")
            
            # Store in XCom
            task_instance.xcom_push(key=f'{symbol}_trades', value=[t.model_dump_json() for t in trades])
        
        return {
            'symbol': symbol,
            'trades_found': len(trades)
        }
    
    except Exception as e:
        logger.error(f"Failed to get trades for {symbol}: {e}", exc_info=True)
        raise


def get_portfolio_task(**context):
    """Get current portfolio status from IBKR (once for all symbols)"""
    logger.info("Retrieving portfolio status")
    
    try:
        task_instance = context['task_instance']
        
        # Get portfolio
        with IBKRClient(host=IBKR_HOST, port=IBKR_PORT) as client:
            portfolio = client.get_portfolio()
        
        logger.info(f"Portfolio: {portfolio.position_count} positions")
        logger.info(f"Total value: ${portfolio.total_value}")
        logger.info(f"Cash: ${portfolio.cash_balance}")
        
        # Check for symbol positions
        for symbol in SYMBOLS:
            if portfolio.has_position(symbol):
                position = portfolio.get_position(symbol)
                logger.info(f"{symbol} Position: {position.quantity} shares @ ${position.current_price}")
        
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
                workflow_id='ibkr_multi_symbol_workflow',
                execution_id=context['dag_run'].run_id if 'dag_run' in context else str(context['execution_date']),
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
    """Log entire multi-symbol workflow to MLflow"""
    logger.info("Logging multi-symbol workflow to MLflow")
    
    try:
        task_instance = context['task_instance']
        execution_date = context['execution_date']
        dag_run = context['dag_run']
        
        # Collect data for all symbols
        symbols_data = {}
        for symbol in SYMBOLS:
            try:
                market_data_json = task_instance.xcom_pull(task_ids=f'fetch_market_data_{symbol}', key=f'{symbol}_market_data')
                signal_json = task_instance.xcom_pull(task_ids=f'analyze_with_llm_{symbol}', key=f'{symbol}_trading_signal')
                order_placed = task_instance.xcom_pull(task_ids=f'place_order_{symbol}', key=f'{symbol}_order_placed', default=False)
                
                if market_data_json and signal_json:
                    market_data = MarketData.model_validate_json(market_data_json)
                    signal = TradingSignal.model_validate_json(signal_json)
                    symbols_data[symbol] = {
                        'market_data': market_data,
                        'signal': signal,
                        'order_placed': order_placed
                    }
            except Exception as e:
                logger.warning(f"Failed to collect data for {symbol}: {e}")
        
        # Get portfolio
        portfolio_json = task_instance.xcom_pull(task_ids='get_portfolio', key='portfolio')
        portfolio = Portfolio.model_validate_json(portfolio_json) if portfolio_json else None
        
        # Start MLflow run
        run_name = f"multi_symbol_workflow_{execution_date.strftime('%Y%m%d_%H%M%S')}"
        tags = {
            'workflow_type': 'multi_symbol_trading',
            'symbols': ','.join(SYMBOLS),
            'airflow_dag_id': context['dag'].dag_id,
            'airflow_run_id': dag_run.run_id,
            'symbol_count': str(len(SYMBOLS))
        }
        
        with mlflow_run_context(run_name=run_name, tags=tags) as tracker:
            
            # Log parameters
            params = {
                'symbols': ','.join(SYMBOLS),
                'position_size': POSITION_SIZE,
                'llm_provider': LLM_PROVIDER,
                'llm_model': LLM_MODEL,
                'execution_date': str(execution_date),
                'dag_run_id': dag_run.run_id
            }
            tracker.log_params(params)
            
            # Log metrics for each symbol
            for symbol, data in symbols_data.items():
                market_data = data['market_data']
                signal = data['signal']
                order_placed = data['order_placed']
                
                metrics = {
                    f'{symbol}_latest_price': float(market_data.latest_price),
                    f'{symbol}_confidence_score': float(signal.confidence_score),
                    f'{symbol}_bars_analyzed': market_data.bar_count,
                    f'{symbol}_order_placed': 1 if order_placed else 0
                }
                
                if signal.risk_reward_ratio:
                    metrics[f'{symbol}_risk_reward_ratio'] = float(signal.risk_reward_ratio)
                
                tracker.log_metrics(metrics)
            
            # Log portfolio metrics
            if portfolio:
                portfolio_metrics = {
                    'portfolio_total_value': float(portfolio.total_value),
                    'portfolio_cash_balance': float(portfolio.cash_balance),
                    'portfolio_position_count': portfolio.position_count,
                    'portfolio_unrealized_pnl': float(portfolio.total_unrealized_pnl)
                }
                tracker.log_metrics(portfolio_metrics)
            
            # Log artifacts
            for symbol, data in symbols_data.items():
                signal = data['signal']
                tracker.log_artifact_dict({
                    'symbol': symbol,
                    'action': signal.action,
                    'confidence': signal.confidence,
                    'confidence_score': float(signal.confidence_score),
                    'reasoning': signal.reasoning,
                    'key_factors': signal.key_factors,
                    'entry_price': float(signal.suggested_entry_price) if signal.suggested_entry_price else None,
                    'stop_loss': float(signal.suggested_stop_loss) if signal.suggested_stop_loss else None,
                    'take_profit': float(signal.suggested_take_profit) if signal.suggested_take_profit else None,
                    'is_actionable': signal.is_actionable
                }, f'{symbol}_trading_signal.json')
            
            # Log portfolio snapshot
            if portfolio:
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
                }, 'portfolio_snapshot.json')
            
            logger.info(f"Successfully logged to MLflow. Run ID: {tracker.run_id}")
            
            return {'mlflow_run_id': tracker.run_id}
    
    except Exception as e:
        logger.error(f"MLflow logging failed: {e}", exc_info=True)
        # Don't fail the workflow if MLflow logging fails
        return {'mlflow_run_id': None, 'error': str(e)}


# Define the DAG
with DAG(
    'ibkr_multi_symbol_workflow',
    default_args=default_args,
    description='IBKR Multi-Symbol Trading Workflow - TSLA and NVDA in parallel',
    schedule_interval=WORKFLOW_SCHEDULE,
    start_date=days_ago(1),
    catchup=False,
    tags=['ibkr', 'trading', 'llm', 'signals', 'multi-symbol', 'nasdaq'],
    max_active_runs=1,
) as dag:
    
    # Create task groups for each symbol
    symbol_groups = {}
    
    for symbol in SYMBOLS:
        with TaskGroup(group_id=f'process_{symbol}') as symbol_group:
            # Fetch market data
            fetch_market_data = PythonOperator(
                task_id=f'fetch_market_data_{symbol}',
                python_callable=fetch_market_data_task,
                op_kwargs={'symbol': symbol},
                provide_context=True,
            )
            
            # Generate charts (parallel)
            generate_daily_chart = PythonOperator(
                task_id=f'generate_daily_chart_{symbol}',
                python_callable=generate_daily_chart_task,
                op_kwargs={'symbol': symbol},
                provide_context=True,
            )
            
            generate_weekly_chart = PythonOperator(
                task_id=f'generate_weekly_chart_{symbol}',
                python_callable=generate_weekly_chart_task,
                op_kwargs={'symbol': symbol},
                provide_context=True,
            )
            
            # Analyze with LLM
            analyze_with_llm = PythonOperator(
                task_id=f'analyze_with_llm_{symbol}',
                python_callable=analyze_with_llm_task,
                op_kwargs={'symbol': symbol},
                provide_context=True,
            )
            
            # Place order
            place_order = PythonOperator(
                task_id=f'place_order_{symbol}',
                python_callable=place_order_task,
                op_kwargs={'symbol': symbol},
                provide_context=True,
            )
            
            # Get trades
            get_trades = PythonOperator(
                task_id=f'get_trades_{symbol}',
                python_callable=get_trades_task,
                op_kwargs={'symbol': symbol},
                provide_context=True,
            )
            
            # Define dependencies within symbol group
            fetch_market_data >> [generate_daily_chart, generate_weekly_chart]
            [generate_daily_chart, generate_weekly_chart] >> analyze_with_llm
            analyze_with_llm >> place_order
            place_order >> get_trades
            
            symbol_groups[symbol] = symbol_group
    
    # Get portfolio (after all symbols processed)
    get_portfolio = PythonOperator(
        task_id='get_portfolio',
        python_callable=get_portfolio_task,
        provide_context=True,
    )
    
    # Log to MLflow (after portfolio)
    log_to_mlflow = PythonOperator(
        task_id='log_to_mlflow',
        python_callable=log_to_mlflow_task,
        provide_context=True,
    )
    
    # Define dependencies: all symbol groups run in parallel, then portfolio, then MLflow
    for symbol_group in symbol_groups.values():
        symbol_group >> get_portfolio
    get_portfolio >> log_to_mlflow

