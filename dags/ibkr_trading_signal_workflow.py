"""
IBKR Trading Signal Workflow
Complete end-to-end trading workflow: Market Data → Charts → LLM Analysis → Order → Portfolio Tracking
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.exceptions import AirflowFailException
from airflow.operators.python import PythonOperator
# from airflow.utils.dates import days_ago # Deprecated in Airflow 2.x+
import logging
import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Optional, Tuple, List

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
from utils.ibkr_marketdata_api import (
    IBKRMarketDataAPI,
    DEFAULT_SNAPSHOT_FIELDS,
    extract_last_price,
)
from utils.chart_generator import ChartGenerator, ensure_kaleido_available, KaleidoMissingError
from utils.llm_signal_analyzer import LLMSignalAnalyzer
from utils.mlflow_tracking import mlflow_run_context
from utils.artifact_storage import (
    store_chart_artifact,
    store_llm_artifact,
    store_signal_artifact,
    store_order_artifact,
    store_trade_artifact,
    store_portfolio_artifact,
    attach_artifact_lineage,
    update_artifact
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
IBKR_HOST = getattr(config, 'ibkr_host', 'ibkr-gateway')
IBKR_PORT = getattr(config, 'ibkr_port', 4002)
POSITION_SIZE = 10  # Number of shares
MARKET_DATA_DURATION = config.market_data_duration
MARKET_DATA_BAR_SIZE = config.market_data_bar_size
LLM_PROVIDER = config.llm_provider  # from LLM_PROVIDER env var
LLM_MODEL = config.llm_model  # from LLM_MODEL env var
LLM_API_KEY = config.llm_api_key  # from LLM_API_KEY env var
LLM_API_BASE_URL = config.llm_api_base_url  # from LLM_API_BASE_URL env var
IBKR_API_BASE_URL = getattr(config, 'ibkr_api_base_url', '')
IBKR_API_VERIFY_SSL = getattr(config, 'ibkr_api_verify_ssl', False)
IBKR_API_TIMEOUT = getattr(config, 'ibkr_api_timeout', 15)
IBKR_PRIMARY_CONID = getattr(config, 'ibkr_primary_conid', None)

# Workflow schedule configuration
# Default: None (manual trigger only)
# Examples: '@daily', '0 9 * * 1-5' (9 AM weekdays), '@hourly'
WORKFLOW_SCHEDULE = os.getenv('WORKFLOW_SCHEDULE', None) or None  # Convert empty string to None

STRICT_MIN_DAILY_BARS = 252
STRICT_MARKET_DATA_DURATION = '1 Y'
STRICT_MARKET_DATA_BAR_SIZE = '1 day'
PRICE_PRECISION = Decimal('0.01')


def _normalize_portal_period(duration: str) -> str:
    if not duration:
        return '1y'
    tokens = duration.strip().split()
    if len(tokens) == 2:
        qty, unit = tokens
        return f"{qty}{unit.lower()[0]}"
    return duration.replace(' ', '').lower()


def _normalize_portal_bar_size(bar_size: str) -> str:
    if not bar_size:
        return '1d'
    value = bar_size.strip().lower()
    replacements = {
        '1 day': '1d',
        '1d': '1d',
        '1 hour': '1h',
        '1h': '1h'
    }
    return replacements.get(value, value.replace(' ', ''))


def is_strict_mode() -> bool:
    """Return whether the workflow is currently enforcing strict IBKR mode."""
    return getattr(config, 'ibkr_strict_mode', False)


def _coerce_positive_decimal(value: Optional[Decimal]) -> Optional[Decimal]:
    """Normalize user/LLM-provided decimal inputs into positive, 2-decimal-place numbers."""
    if value is None:
        return None
    try:
        as_decimal = Decimal(value)
    except (InvalidOperation, TypeError):
        return None
    if as_decimal <= 0:
        return None
    return as_decimal.quantize(PRICE_PRECISION, rounding=ROUND_HALF_UP)


def normalize_limit_price(
    signal: TradingSignal,
    market_data: Optional[MarketData],
    live_snapshot: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[Decimal], Optional[str]]:
    """Normalize limit price using signal suggestion, live snapshot, then historical close."""
    candidate = _coerce_positive_decimal(signal.suggested_entry_price)
    if candidate:
        return candidate, 'signal'
    live_candidate = _coerce_live_snapshot_price(live_snapshot)
    if live_candidate:
        return live_candidate, 'live_market_snapshot'
    if market_data:
        fallback = _coerce_positive_decimal(market_data.latest_price)
        if fallback:
            return fallback, 'market_data_close'
    return None, None


def _build_market_data_from_history(symbol: str, bars_payload: Dict[str, Any], bar_size: str) -> Optional[MarketData]:
    data_rows = bars_payload.get('data') or bars_payload.get('bars')
    if not data_rows:
        return None
    ohlcv_bars: List[OHLCVBar] = []
    for entry in data_rows:
        try:
            timestamp = datetime.utcfromtimestamp(int(entry['t']) / 1000)
            open_p = Decimal(str(entry['o']))
            high_p = Decimal(str(entry['h']))
            low_p = Decimal(str(entry['l']))
            close_p = Decimal(str(entry['c']))
            volume = int(entry.get('v', 0) or 0)
        except (KeyError, ValueError, TypeError):
            continue
        ohlcv_bars.append(
            OHLCVBar(
                timestamp=timestamp,
                open=open_p,
                high=high_p,
                low=low_p,
                close=close_p,
                volume=volume
            )
        )
    if not ohlcv_bars:
        return None
    return MarketData(
        symbol=symbol,
        exchange='SMART',
        bars=ohlcv_bars,
        timeframe=bar_size,
        fetched_at=datetime.utcnow()
    )


def _coerce_live_snapshot_price(live_snapshot: Optional[Dict[str, Any]]) -> Optional[Decimal]:
    if not live_snapshot:
        return None
    raw_price = live_snapshot.get('last_price')
    if raw_price is None:
        raw_entry = live_snapshot.get('raw')
        if isinstance(raw_entry, dict):
            raw_price = extract_last_price(raw_entry)
    if raw_price is None:
        fields = live_snapshot.get('fields') if isinstance(live_snapshot, dict) else None
        if isinstance(fields, dict):
            for candidate_field in ('31', '84', '85'):
                if fields.get(candidate_field) is not None:
                    raw_price = fields.get(candidate_field)
                    break
    if raw_price is None:
        return None
    return _coerce_positive_decimal(raw_price)


def _capture_live_market_snapshot(symbol: str, task_instance) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    if not IBKR_API_BASE_URL:
        return None, None
    try:
        client = IBKRMarketDataAPI(
            base_url=IBKR_API_BASE_URL,
            verify_ssl=IBKR_API_VERIFY_SSL,
            timeout=IBKR_API_TIMEOUT
        )
        conid = client.resolve_conid(symbol, preferred_conid=IBKR_PRIMARY_CONID)
        if not conid:
            logger.warning("IBKR Client Portal API could not resolve a conid for %s", symbol)
            return None, None
        snapshot_response = client.get_live_snapshot(conid)
        snapshot_entry = _select_snapshot_entry(snapshot_response, conid)
        if not snapshot_entry:
            logger.warning("No live snapshot data returned for conid %s", conid)
            return conid, None
        payload = _build_live_snapshot_payload(conid, snapshot_entry)
        if payload and task_instance:
            task_instance.xcom_push(key='live_market_data', value=payload)
        return conid, payload
    except Exception as exc:
        logger.warning("Failed to fetch IBKR live snapshot via Client Portal API: %s", exc)
        return None, None


def _select_snapshot_entry(snapshot_response: Any, target_conid: Optional[int]) -> Optional[Dict[str, Any]]:
    if isinstance(snapshot_response, list):
        if not snapshot_response:
            return None
        for entry in snapshot_response:
            if _extract_conid(entry) == target_conid:
                return entry
        return snapshot_response[0]
    if isinstance(snapshot_response, dict):
        target_key = str(target_conid) if target_conid is not None else None
        if target_key and target_key in snapshot_response and isinstance(snapshot_response[target_key], dict):
            return snapshot_response[target_key]
        if 'data' in snapshot_response and isinstance(snapshot_response['data'], list):
            return snapshot_response['data'][0] if snapshot_response['data'] else None
        for value in snapshot_response.values():
            if isinstance(value, dict) and (_extract_conid(value) == target_conid or target_conid is None):
                return value
        return None
    return snapshot_response if isinstance(snapshot_response, dict) else None


def _extract_conid(entry: Any) -> Optional[int]:
    if not isinstance(entry, dict):
        return None
    for key in ('conid', 'conId', 'contractId'):
        if entry.get(key) is None:
            continue
        try:
            return int(entry[key])
        except (TypeError, ValueError):
            continue
    return None


def _build_live_snapshot_payload(conid: int, entry: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(entry, dict):
        return {'conid': conid, 'raw': entry}
    payload = {
        'conid': conid,
        'fields': {field: entry.get(field) for field in DEFAULT_SNAPSHOT_FIELDS if field in entry},
        'raw': entry,
        'last_price': extract_last_price(entry),
        'source': 'ibkr_client_portal',
        'timestamp': entry.get('time'),
        'symbol': entry.get('55') or entry.get('symbol')
    }
    return payload


def fetch_market_data_task(**context):
    """Fetch market data from IBKR"""
    logger.info("="*60)
    logger.info(f"Fetching market data for {SYMBOL}")
    logger.info("="*60)
    strict_mode = is_strict_mode()
    requested_duration = STRICT_MARKET_DATA_DURATION if strict_mode else MARKET_DATA_DURATION
    requested_bar_size = STRICT_MARKET_DATA_BAR_SIZE if strict_mode else MARKET_DATA_BAR_SIZE
    
    try:
        with IBKRClient(host=IBKR_HOST, port=IBKR_PORT, strict_mode=strict_mode) as client:
            # Fetch daily data
            logger.info(
                "Requesting %s of %s bars from IBKR for %s",
                requested_duration,
                requested_bar_size,
                SYMBOL
            )
            market_data = client.fetch_market_data(
                symbol=SYMBOL,
                exchange="SMART",
                duration=requested_duration,
                bar_size=requested_bar_size
            )
            
            logger.info(f"Fetched {market_data.bar_count} bars")
            logger.info(f"Latest price: ${market_data.latest_price}")
            if strict_mode and market_data.bar_count < STRICT_MIN_DAILY_BARS:
                message = (
                    f"Strict mode requires ≥{STRICT_MIN_DAILY_BARS} daily bars for {SYMBOL}; "
                    f"IBKR returned {market_data.bar_count}."
                )
                logger.error(message)
                raise AirflowFailException(message)
            
            # Store in XCom as dict
            task_instance = context['task_instance']
            task_instance.xcom_push(key='market_data', value=market_data.model_dump_json())
            client_metadata = client.get_metadata() if hasattr(client, 'get_metadata') else {}
            live_snapshot_info: Optional[Dict[str, Any]] = None
            live_conid: Optional[int] = None
            if IBKR_API_BASE_URL:
                live_conid, live_snapshot_info = _capture_live_market_snapshot(SYMBOL, task_instance)

            market_data_metadata = {
                'strict_mode': strict_mode,
                'bars_requested': requested_duration,
                'bar_size': requested_bar_size,
                'bars_returned': market_data.bar_count,
                'ibkr_host': IBKR_HOST,
                'ibkr_port': IBKR_PORT,
                'ib_insync_version': client_metadata.get('ib_insync_version'),
                'ibkr_connection_mode': client_metadata.get('connection_mode'),
                'requested_min_bars': STRICT_MIN_DAILY_BARS,
                'latest_price': float(market_data.latest_price),
            }
            if live_snapshot_info:
                market_data_metadata['live_snapshot'] = {
                    'conid': live_conid,
                    'last_price': live_snapshot_info.get('last_price'),
                    'fields': live_snapshot_info.get('fields'),
                    'source': live_snapshot_info.get('source'),
                    'timestamp': live_snapshot_info.get('timestamp')
                }
                logger.info(
                    "Live market snapshot fetched via Client Portal API (conid=%s, last=%s)",
                    live_conid,
                    live_snapshot_info.get('last_price')
                )
            elif live_conid:
                market_data_metadata['live_snapshot'] = {
                    'conid': live_conid,
                    'source': 'ibkr_client_portal'
                }
            task_instance.xcom_push(key='market_data_metadata', value=market_data_metadata)
            
            return {
                'symbol': market_data.symbol,
                'bars': market_data.bar_count,
                'latest_price': float(market_data.latest_price),
                'strict_mode': strict_mode
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
        market_data_metadata = task_instance.xcom_pull(task_ids='fetch_market_data', key='market_data_metadata') or {}
        
        # Ensure Kaleido dependency is ready before generating charts
        kaleido_status = 'unknown'
        try:
            ensure_kaleido_available()
            kaleido_status = 'ready'
        except KaleidoMissingError as exc:
            kaleido_status = 'missing'
            logger.error("Kaleido is unavailable: %s", exc)
            if task_instance:
                task_instance.xcom_push(key='kaleido_ready', value=kaleido_status)
            raise

        if task_instance:
            task_instance.xcom_push(key='kaleido_ready', value=kaleido_status)

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
        
        # Store chart artifact in database with market data snapshot
        chart_artifact = None
        try:
            # Use MinIO URL if available, otherwise use local path
            image_path = minio_url if minio_url else chart_result.file_path
            
            # Build market data snapshot
            market_data_snapshot = {
                'symbol': SYMBOL,
                'timeframe': 'daily',
                'fetched_at': market_data.fetched_at.isoformat() if market_data.fetched_at else None,
                'latest_price': float(market_data.latest_price),
                'bar_count': market_data.bar_count,
                'bars_requested': market_data_metadata.get('bars_requested'),
                'bar_size': market_data_metadata.get('bar_size'),
                'bars_returned': market_data_metadata.get('bars_returned', market_data.bar_count),
                'strict_mode': market_data_metadata.get('strict_mode', False),
                'ibkr_connection': {
                    'host': market_data_metadata.get('ibkr_host'),
                    'port': market_data_metadata.get('ibkr_port'),
                    'ib_insync_version': market_data_metadata.get('ib_insync_version'),
                    'mode': market_data_metadata.get('ibkr_connection_mode')
                },
                'bars': [
                    {
                        'date': bar.timestamp.isoformat(),
                        'open': float(bar.open),
                        'high': float(bar.high),
                        'low': float(bar.low),
                        'close': float(bar.close),
                        'volume': int(bar.volume)
                    }
                    for bar in market_data.bars[-50:]  # Last 50 bars
                ]
            }
            
            # Add indicator summary
            indicator_summary = {}
            if indicators:
                if indicators.sma_20 and indicators.sma_20[-1]:
                    indicator_summary['sma_20'] = float(indicators.sma_20[-1])
                if indicators.sma_50 and indicators.sma_50[-1]:
                    indicator_summary['sma_50'] = float(indicators.sma_50[-1])
                if indicators.sma_200 and indicators.sma_200[-1]:
                    indicator_summary['sma_200'] = float(indicators.sma_200[-1])
                if indicators.rsi_14 and indicators.rsi_14[-1]:
                    indicator_summary['rsi_14'] = float(indicators.rsi_14[-1])
                if indicators.macd_line and indicators.macd_line[-1]:
                    indicator_summary['macd'] = float(indicators.macd_line[-1])
                if indicators.bb_upper and indicators.bb_upper[-1]:
                    indicator_summary['bb_upper'] = float(indicators.bb_upper[-1])
                if indicators.bb_lower and indicators.bb_lower[-1]:
                    indicator_summary['bb_lower'] = float(indicators.bb_lower[-1])
            
            chart_artifact = store_chart_artifact(
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
                    'local_path': chart_result.file_path,
                    'strict_mode': market_data_metadata.get('strict_mode', False)
                },
                metadata={
                    'market_data_snapshot': market_data_snapshot,
                    'indicator_summary': indicator_summary,
                    'market_data_context': market_data_metadata
                }
            )
            
            # Store artifact ID for later enrichment
            if chart_artifact:
                task_instance.xcom_push(key='daily_chart_artifact_id', value=chart_artifact['id'])
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
        market_data_metadata = task_instance.xcom_pull(task_ids='fetch_market_data', key='market_data_metadata') or {}

        # Confirm Kaleido is ready for weekly export
        kaleido_status = 'unknown'
        try:
            ensure_kaleido_available()
            kaleido_status = 'ready'
        except KaleidoMissingError as exc:
            kaleido_status = 'missing'
            logger.error("Kaleido is unavailable for weekly chart: %s", exc)
            if task_instance:
                task_instance.xcom_push(key='kaleido_ready_weekly', value=kaleido_status)
            raise

        if task_instance:
            task_instance.xcom_push(key='kaleido_ready_weekly', value=kaleido_status)

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
        
        # Store chart artifact in database with market data snapshot
        chart_artifact = None
        try:
            # Use MinIO URL if available, otherwise use local path
            image_path = minio_url if minio_url else chart_result.file_path
            
            # Build market data snapshot for weekly
            market_data_snapshot = {
                'symbol': SYMBOL,
                'timeframe': 'weekly',
                'fetched_at': weekly_data.fetched_at.isoformat() if weekly_data.fetched_at else None,
                'latest_price': float(weekly_data.latest_price),
                'bar_count': weekly_data.bar_count,
                'bars_requested': market_data_metadata.get('bars_requested'),
                'bar_size': market_data_metadata.get('bar_size'),
                'bars_returned': market_data_metadata.get('bars_returned'),
                'strict_mode': market_data_metadata.get('strict_mode', False),
                'ibkr_connection': {
                    'host': market_data_metadata.get('ibkr_host'),
                    'port': market_data_metadata.get('ibkr_port'),
                    'ib_insync_version': market_data_metadata.get('ib_insync_version'),
                    'mode': market_data_metadata.get('ibkr_connection_mode')
                },
                'bars': [
                    {
                        'date': bar.timestamp.isoformat(),
                        'open': float(bar.open),
                        'high': float(bar.high),
                        'low': float(bar.low),
                        'close': float(bar.close),
                        'volume': int(bar.volume)
                    }
                    for bar in weekly_data.bars[-20:]  # Last 20 weeks
                ]
            }
            
            # Add indicator summary
            indicator_summary = {}
            if weekly_indicators:
                if weekly_indicators.sma_20 and weekly_indicators.sma_20[-1]:
                    indicator_summary['sma_20'] = float(weekly_indicators.sma_20[-1])
                if weekly_indicators.sma_50 and weekly_indicators.sma_50[-1]:
                    indicator_summary['sma_50'] = float(weekly_indicators.sma_50[-1])
                if weekly_indicators.rsi_14 and weekly_indicators.rsi_14[-1]:
                    indicator_summary['rsi_14'] = float(weekly_indicators.rsi_14[-1])
                if weekly_indicators.macd_line and weekly_indicators.macd_line[-1]:
                    indicator_summary['macd'] = float(weekly_indicators.macd_line[-1])
            
            chart_artifact = store_chart_artifact(
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
                    'local_path': chart_result.file_path,
                    'strict_mode': market_data_metadata.get('strict_mode', False)
                },
                metadata={
                    'market_data_snapshot': market_data_snapshot,
                    'indicator_summary': indicator_summary,
                    'market_data_context': market_data_metadata
                }
            )
            
            # Store artifact ID for later enrichment
            if chart_artifact:
                task_instance.xcom_push(key='weekly_chart_artifact_id', value=chart_artifact['id'])
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
            llm_artifact = store_llm_artifact(
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
            if llm_artifact:
                task_instance.xcom_push(key='llm_artifact_id', value=llm_artifact['id'])
        except Exception as e:
            logger.warning(f"Failed to store LLM artifact: {e}")
        
        # Update chart artifacts with LLM analysis context
        try:
            # Retrieve chart artifact IDs
            daily_artifact_id = task_instance.xcom_pull(task_ids='generate_daily_chart', key='daily_chart_artifact_id')
            weekly_artifact_id = task_instance.xcom_pull(task_ids='generate_weekly_chart', key='weekly_chart_artifact_id')
            
            # Build LLM analysis summary for metadata
            llm_analysis = {
                'action': str(signal.action),
                'confidence': str(signal.confidence),
                'confidence_score': float(signal.confidence_score) if signal.confidence_score else None,
                'reasoning_snippet': signal.reasoning[:200] + '...' if len(signal.reasoning) > 200 else signal.reasoning,
                'key_factors': signal.key_factors[:3] if signal.key_factors else [],
                'entry_price': float(signal.suggested_entry_price) if signal.suggested_entry_price else None,
                'stop_loss': float(signal.suggested_stop_loss) if signal.suggested_stop_loss else None,
                'take_profit': float(signal.suggested_take_profit) if signal.suggested_take_profit else None,
                'is_actionable': signal.is_actionable
            }
            
            # Update daily chart artifact
            if daily_artifact_id:
                update_artifact(
                    artifact_id=daily_artifact_id,
                    updates={
                        'prompt': prompt_text,
                        'response': signal.reasoning,
                        'model_name': signal.model_used or LLM_MODEL or "unknown",
                        'prompt_length': len(prompt_text),
                        'response_length': len(signal.reasoning),
                        'metadata': {
                            'llm_analysis': llm_analysis
                        }
                    }
                )
            
            # Update weekly chart artifact
            if weekly_artifact_id:
                update_artifact(
                    artifact_id=weekly_artifact_id,
                    updates={
                        'prompt': prompt_text,
                        'response': signal.reasoning,
                        'model_name': signal.model_used or LLM_MODEL or "unknown",
                        'prompt_length': len(prompt_text),
                        'response_length': len(signal.reasoning),
                        'metadata': {
                            'llm_analysis': llm_analysis
                        }
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to update chart artifacts with LLM context: {e}")
        
        # Store signal artifact
        try:
            signal_artifact = store_signal_artifact(
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
            if signal_artifact:
                task_instance.xcom_push(key='signal_artifact_id', value=signal_artifact['id'])
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
        signal_artifact_id = task_instance.xcom_pull(task_ids='analyze_with_llm', key='signal_artifact_id')
        
        if not signal.is_actionable:
            logger.info(f"Signal not actionable: {signal.action} with {signal.confidence} confidence")
            task_instance.xcom_push(key='order_placed', value=False)
            return {'order_placed': False, 'reason': 'Signal not actionable'}
        
        logger.info(f"Signal is actionable! Placing {signal.action} order")
        market_data_json = task_instance.xcom_pull(task_ids='fetch_market_data', key='market_data')
        market_data = MarketData.model_validate_json(market_data_json) if market_data_json else None
        market_data_metadata = task_instance.xcom_pull(task_ids='fetch_market_data', key='market_data_metadata') or {}
        live_market_snapshot = task_instance.xcom_pull(task_ids='fetch_market_data', key='live_market_data')
        normalized_limit_price, price_source = normalize_limit_price(signal, market_data, live_market_snapshot)
        if not normalized_limit_price:
            reason = (
                "Unable to compute a positive limit price from the LLM signal or latest market data. "
                "Marking signal as non-actionable for this run."
            )
            logger.warning(reason)
            if signal_artifact_id:
                try:
                    update_artifact(
                        artifact_id=signal_artifact_id,
                        updates={
                            'metadata': {
                                'order_status': 'rejected',
                                'order_rejection_reason': reason,
                                'strict_mode': is_strict_mode()
                            }
                        }
                    )
                except Exception as artifact_error:
                    logger.warning(f"Failed to annotate signal artifact with rejection: {artifact_error}")
            task_instance.xcom_push(key='order_placed', value=False)
            task_instance.xcom_push(key='order_rejection_reason', value=reason)
            return {'order_placed': False, 'reason': reason}
        
        task_instance.xcom_push(key='normalized_limit_price', value=float(normalized_limit_price))
        strict_mode = is_strict_mode()
        logger.info(
            "Normalized limit price for order: %s (source=%s)",
            normalized_limit_price,
            price_source
        )
        
        # Create order
        order = Order(
            symbol=SYMBOL,
            side=OrderSide.BUY if signal.action == SignalAction.BUY else OrderSide.SELL,
            quantity=POSITION_SIZE,
            order_type=OrderType.LIMIT,
            limit_price=normalized_limit_price,
            signal_id=str(context['execution_date'])
        )
        
        # Place order via IBKR
        with IBKRClient(host=IBKR_HOST, port=IBKR_PORT, strict_mode=strict_mode) as client:
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
                },
                metadata={
                    'normalized_limit_price': float(normalized_limit_price),
                    'limit_price_source': price_source,
                    'strict_mode': strict_mode,
                    'market_data_bars': market_data.bar_count if market_data else None,
                    'market_data_context': market_data_metadata,
                    'live_market_data': live_market_snapshot
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store order artifact: {e}")
        
        if signal_artifact_id:
            try:
                update_artifact(
                    artifact_id=signal_artifact_id,
                    updates={
                        'metadata': {
                            'order_status': str(order.status),
                            'normalized_limit_price': float(normalized_limit_price),
                            'limit_price_source': price_source
                        }
                    }
                )
            except Exception as artifact_error:
                logger.warning(f"Failed to annotate signal artifact with order metadata: {artifact_error}")
        
        # Store in XCom
        task_instance.xcom_push(key='order', value=order.model_dump_json())
        task_instance.xcom_push(key='order_placed', value=True)
        
        return {
            'order_placed': True,
            'order_id': order.order_id,
            'side': order.side,
            'quantity': order.quantity,
            'normalized_limit_price': float(normalized_limit_price)
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
        with IBKRClient(host=IBKR_HOST, port=IBKR_PORT, strict_mode=is_strict_mode()) as client:
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
        with IBKRClient(host=IBKR_HOST, port=IBKR_PORT, strict_mode=is_strict_mode()) as client:
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
        daily_chart_artifact_id = task_instance.xcom_pull(task_ids='generate_daily_chart', key='daily_chart_artifact_id')
        weekly_chart_artifact_id = task_instance.xcom_pull(task_ids='generate_weekly_chart', key='weekly_chart_artifact_id')
        llm_artifact_id = task_instance.xcom_pull(task_ids='analyze_with_llm', key='llm_artifact_id')
        signal_artifact_id = task_instance.xcom_pull(task_ids='analyze_with_llm', key='signal_artifact_id')
        
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
            'order_placed': str(order_placed),
            'workflow_id': 'ibkr_trading_signal_workflow',
            'execution_id': str(execution_date)
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
            
            # Log charts as artifacts - Skip file logging to prevent hangs
            # Charts are already stored in MinIO and accessible via artifacts API
            try:
                logger.info(f"Charts stored in MinIO - skipping MLflow file upload to prevent timeout")
                logger.info(f"Daily chart: {daily_chart.file_path}")
                logger.info(f"Weekly chart: {weekly_chart.file_path}")
                # tracker.log_file_artifact(daily_chart.file_path)  # Disabled - causes timeout
                # tracker.log_file_artifact(weekly_chart.file_path)  # Disabled - causes timeout
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
        
        attach_artifact_lineage(
            [
                daily_chart_artifact_id,
                weekly_chart_artifact_id,
                llm_artifact_id,
                signal_artifact_id
            ],
            tracker.run_id,
            getattr(tracker, 'experiment_id', None)
        )
        
        # Return run_id for potential downstream tasks to update artifacts
        return {'mlflow_run_id': tracker.run_id, 'symbol': SYMBOL}
    
    except Exception as e:
        logger.error(f"MLflow logging failed: {e}", exc_info=True)
        raise


# Define the DAG
with DAG(
    'ibkr_trading_signal_workflow',
    default_args=default_args,
    description='IBKR Trading Signal Workflow - Market Data → Charts → LLM Analysis → Order → Portfolio',
    schedule=WORKFLOW_SCHEDULE,  # Configurable via WORKFLOW_SCHEDULE env var
    start_date=datetime(2023, 1, 1), # Using a fixed date as days_ago is deprecated
    catchup=False,
    tags=['ibkr', 'trading', 'llm', 'signals', 'ml', 'automated' if WORKFLOW_SCHEDULE else 'manual'],
    max_active_runs=1,
) as dag:
    
    # Task 1: Fetch market data from IBKR
    fetch_market_data = PythonOperator(
        task_id='fetch_market_data',
        python_callable=fetch_market_data_task,
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
        execution_timeout=timedelta(minutes=10),
        retries=2,
        retry_delay=timedelta(seconds=30),
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
