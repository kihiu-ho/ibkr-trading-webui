"""
IBKR Stock Data Workflow
Fetches stock data (TSLA, NVDA) from PostgreSQL and tracks runs in MLflow
Supports debug mode for detailed logging and diagnostics
"""
from datetime import datetime, timedelta
import logging
import os
import sys

# Ensure Airflow can import local `models/` and `utils/` packages regardless of how the DAG is executed.
sys.path.append(os.path.dirname(__file__))

from airflow import DAG
from airflow.operators.python import PythonOperator

try:
    from airflow.utils.dates import days_ago as _days_ago
except Exception:  # pragma: no cover - Airflow 3 compatibility
    def _days_ago(days: int) -> datetime:
        return datetime.utcnow() - timedelta(days=days)

from utils.config import config
from utils.database import db_client
from utils.mlflow_tracking import mlflow_run_context
from utils.chart_generator import ChartGenerator
from utils.llm_signal_analyzer import LLMSignalAnalyzer
from utils.artifact_storage import store_chart_artifact, store_signal_artifact
from utils.minio_upload import upload_chart_to_minio
from models.market_data import MarketData, OHLCVBar
from models.chart import Timeframe, ChartConfig

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
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}


def extract_stock_data(**context):
    """
    Extract stock data from PostgreSQL
    Stores data in XCom for downstream tasks
    """
    logger.info("="*60)
    logger.info("Starting stock data extraction")
    logger.info(f"Debug mode: {config.debug_mode}")
    logger.info(f"Symbols: {config.stock_symbols}")
    logger.info("="*60)
    
    try:
        # Check which symbols exist in database
        symbol_existence = db_client.check_symbols_exist(config.stock_symbols)
        logger.info(f"Symbol existence check: {symbol_existence}")
        
        # Identify missing symbols
        missing_symbols = [sym for sym, exists in symbol_existence.items() if not exists]
        if missing_symbols:
            logger.warning(f"Missing symbols in database: {', '.join(missing_symbols)}")
        
        # Fetch data for all requested symbols
        df = db_client.fetch_stock_data(config.stock_symbols)
        
        if df.empty:
            logger.error("No data retrieved from database!")
            raise ValueError("No stock data found for requested symbols")
        
        # Log extraction summary
        summary = {
            'total_rows': len(df),
            'symbols_found': df['symbol'].nunique() if 'symbol' in df.columns else 0,
            'date_range': {
                'start': str(df['date'].min()) if 'date' in df.columns else None,
                'end': str(df['date'].max()) if 'date' in df.columns else None,
            },
            'missing_symbols': missing_symbols,
        }
        
        logger.info(f"Extraction summary: {summary}")
        
        # Convert dates to strings for JSON serialization
        if 'date' in df.columns:
            df['date'] = df['date'].astype(str)
        if 'created_at' in df.columns:
            df['created_at'] = df['created_at'].astype(str)
        
        # Store data and summary in XCom
        context['task_instance'].xcom_push(key='stock_data', value=df.to_dict('records'))
        context['task_instance'].xcom_push(key='summary', value=summary)
        context['task_instance'].xcom_push(key='missing_symbols', value=missing_symbols)
        
        return summary
    
    except Exception as e:
        logger.error(f"Failed to extract stock data: {e}", exc_info=True)
        raise


def validate_data(**context):
    """
    Validate extracted data quality
    """
    logger.info("Starting data validation")
    
    try:
        # Retrieve data from XCom
        task_instance = context['task_instance']
        stock_data = task_instance.xcom_pull(task_ids='extract_stock_data', key='stock_data')
        
        if not stock_data:
            raise ValueError("No stock data to validate")
        
        import pandas as pd
        df = pd.DataFrame(stock_data)
        
        # Validation checks
        validation_results = {
            'total_rows': len(df),
            'checks': {}
        }
        
        # Check 1: Required columns present
        required_columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        validation_results['checks']['required_columns'] = {
            'passed': len(missing_columns) == 0,
            'missing_columns': missing_columns
        }
        
        # Check 2: No null values in critical columns
        critical_columns = ['symbol', 'date', 'close']
        null_counts = df[critical_columns].isnull().sum().to_dict()
        validation_results['checks']['null_values'] = {
            'passed': sum(null_counts.values()) == 0,
            'null_counts': null_counts
        }
        
        # Check 3: Price data validity (positive values)
        if 'close' in df.columns:
            invalid_prices = (df['close'] <= 0).sum()
            validation_results['checks']['price_validity'] = {
                'passed': invalid_prices == 0,
                'invalid_count': int(invalid_prices)
            }
        
        # Check 4: Volume data validity (non-negative)
        if 'volume' in df.columns:
            invalid_volumes = (df['volume'] < 0).sum()
            validation_results['checks']['volume_validity'] = {
                'passed': invalid_volumes == 0,
                'invalid_count': int(invalid_volumes)
            }
        
        # Overall validation status
        all_passed = all(check['passed'] for check in validation_results['checks'].values())
        validation_results['overall_status'] = 'PASSED' if all_passed else 'FAILED'
        
        logger.info(f"Validation results: {validation_results}")
        
        # Store validation results in XCom
        task_instance.xcom_push(key='validation_results', value=validation_results)
        
        if not all_passed:
            logger.error("Data validation failed!")
            raise ValueError(f"Data validation failed: {validation_results}")
        
        return validation_results
    
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise


def transform_data(**context):
    """
    Transform and enrich stock data
    """
    logger.info("Starting data transformation")
    
    try:
        task_instance = context['task_instance']
        stock_data = task_instance.xcom_pull(task_ids='extract_stock_data', key='stock_data')
        
        import pandas as pd
        df = pd.DataFrame(stock_data)
        
        # Basic transformations
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # Calculate daily returns if we have price data
        if 'close' in df.columns:
            df = df.sort_values(['symbol', 'date'])
            df['daily_return'] = df.groupby('symbol')['close'].pct_change()
        
        # Calculate price range
        if all(col in df.columns for col in ['high', 'low']):
            df['price_range'] = df['high'] - df['low']
            df['price_range_pct'] = (df['price_range'] / df['close']) * 100
        
        transformation_summary = {
            'rows_processed': len(df),
            'new_columns_added': ['daily_return', 'price_range', 'price_range_pct'],
            'symbols_processed': df['symbol'].nunique() if 'symbol' in df.columns else 0
        }
        
        logger.info(f"Transformation summary: {transformation_summary}")
        
        if config.debug_mode:
            logger.debug(f"Transformed data sample:\n{df.head(10)}")
        
        # Store transformed data - replace NaN with None for JSON serialization
        # Convert datetime columns to strings and handle NaN values
        df_clean = df.copy()
        
        # Convert date columns to strings
        for col in df_clean.columns:
            if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                df_clean[col] = df_clean[col].astype(str)
        
        # Replace NaN with None for JSON compatibility
        df_clean = df_clean.where(pd.notnull(df_clean), None)
        df_dict = df_clean.to_dict('records')
        
        task_instance.xcom_push(key='transformed_data', value=df_dict)
        task_instance.xcom_push(key='transformation_summary', value=transformation_summary)
        
        return transformation_summary
    
    except Exception as e:
        logger.error(f"Transformation failed: {e}", exc_info=True)
        raise


def log_to_mlflow(**context):
    """
    Log workflow run to MLflow with comprehensive tracking
    """
    logger.info("Starting MLflow logging")
    
    try:
        task_instance = context['task_instance']
        execution_date = context['execution_date']
        dag_run = context['dag_run']
        
        # Retrieve data from previous tasks
        summary = task_instance.xcom_pull(task_ids='extract_stock_data', key='summary')
        validation_results = task_instance.xcom_pull(task_ids='validate_data', key='validation_results')
        transformation_summary = task_instance.xcom_pull(task_ids='transform_data', key='transformation_summary')
        missing_symbols = task_instance.xcom_pull(task_ids='extract_stock_data', key='missing_symbols') or []
        transformed_data = task_instance.xcom_pull(task_ids='transform_data', key='transformed_data')
        
        import pandas as pd
        
        # Start MLflow run
        run_name = f"stock_data_{execution_date.strftime('%Y%m%d_%H%M%S')}"
        tags = {
            'airflow_dag_id': context['dag'].dag_id,
            'airflow_run_id': dag_run.run_id,
            'execution_date': str(execution_date),
            'trigger_type': 'manual' if dag_run.external_trigger else 'scheduled'
        }
        
        if missing_symbols:
            tags['missing_symbols'] = ','.join(missing_symbols)
        
        # Initialize variable to store run_id
        mlflow_run_id = None
        
        with mlflow_run_context(run_name=run_name, tags=tags) as tracker:
            
            # Log additional parameters
            tracker.log_params({
                'symbols': ','.join(config.stock_symbols),
                'execution_date': str(execution_date),
                'validation_status': validation_results['overall_status']
            })
            
            # Log metrics
            metrics = {
                'total_rows': summary['total_rows'],
                'symbols_processed': summary['symbols_found'],
                'symbols_missing': len(missing_symbols),
                'validation_checks_passed': sum(1 for c in validation_results['checks'].values() if c['passed']),
                'validation_checks_total': len(validation_results['checks']),
            }
            
            # Add transformation metrics
            if transformation_summary:
                metrics['rows_transformed'] = transformation_summary['rows_processed']
            
            tracker.log_metrics(metrics)
            
            # Log artifacts
            tracker.log_artifact_dict(summary, 'extraction_summary.json')
            tracker.log_artifact_dict(validation_results, 'validation_results.json')
            
            if transformation_summary:
                tracker.log_artifact_dict(transformation_summary, 'transformation_summary.json')
            
            # Log data sample as CSV
            if transformed_data:
                df = pd.DataFrame(transformed_data)
                # Log full dataset (or sample if too large)
                if len(df) > 10000:
                    logger.info(f"Dataset large ({len(df)} rows), logging sample")
                    sample_df = df.sample(n=min(10000, len(df)))
                    tracker.log_dataframe(sample_df, 'stock_data_sample.csv')
                else:
                    tracker.log_dataframe(df, 'stock_data_full.csv')
            
            # Log debug info if debug mode is enabled
            if config.debug_mode:
                debug_info = {
                    'config': config.to_dict(),
                    'extraction_summary': summary,
                    'validation_results': validation_results,
                    'transformation_summary': transformation_summary,
                    'airflow_context': {
                        'dag_id': context['dag'].dag_id,
                        'task_id': context['task'].task_id,
                        'execution_date': str(execution_date),
                        'run_id': dag_run.run_id,
                    }
                }
                tracker.log_debug_info(debug_info)
            
            # Capture run_id while tracker is still in scope
            mlflow_run_id = tracker.run_id
            logger.info(f"Successfully logged to MLflow. Run ID: {mlflow_run_id}")
        
        return {'mlflow_run_id': mlflow_run_id}
    
    except Exception as e:
        logger.error(f"MLflow logging failed: {e}", exc_info=True)
        raise


def generate_charts(**context):
    """
    Generate daily and weekly charts with technical indicators for each symbol
    """
    logger.info("Starting chart generation")
    
    try:
        task_instance = context['task_instance']
        dag_run = context['dag_run']
        execution_id = dag_run.run_id
        
        # Retrieve transformed data from previous task
        transformed_data = task_instance.xcom_pull(task_ids='transform_data', key='transformed_data')
        if not transformed_data:
            raise ValueError("No transformed data available for chart generation")
        
        import pandas as pd
        df = pd.DataFrame(transformed_data)
        
        # Convert date column back to datetime if it's a string
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # Initialize chart generator
        # Use shared volume for charts (accessible by both Airflow and backend)
        charts_dir = os.getenv('CHARTS_DIR', '/app/charts')
        chart_generator = ChartGenerator(output_dir=charts_dir)
        
        charts_generated = []
        
        # Generate charts for each symbol
        for symbol in df['symbol'].unique() if 'symbol' in df.columns else []:
            symbol_data = df[df['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values('date')
            
            # Convert to MarketData format
            bars = []
            for _, row in symbol_data.iterrows():
                bar = OHLCVBar(
                    timestamp=row['date'],
                    open=float(row.get('open', row.get('close', 0))),
                    high=float(row.get('high', row.get('close', 0))),
                    low=float(row.get('low', row.get('close', 0))),
                    close=float(row.get('close', 0)),
                    volume=int(row.get('volume', 0))
                )
                bars.append(bar)
            
            market_data = MarketData(symbol=symbol, bars=bars, timeframe="1D")
            
            # Generate daily chart
            try:
                daily_chart = chart_generator.generate_chart(
                    market_data=market_data,
                    config=ChartConfig(
                        symbol=symbol,
                        timeframe=Timeframe.DAILY,
                        include_sma=True,
                        include_rsi=True,
                        include_macd=True,
                        include_bollinger=True
                    )
                )
                
                if daily_chart and daily_chart.file_path:
                    # Upload chart to MinIO
                    minio_url = upload_chart_to_minio(
                        file_path=daily_chart.file_path,
                        symbol=symbol,
                        timeframe='daily',
                        execution_id=execution_id
                    )
                    
                    # Store chart artifact with MinIO URL
                    image_path = minio_url if minio_url else daily_chart.file_path
                    store_chart_artifact(
                        name=f"{symbol}_daily_chart",
                        symbol=symbol,
                        image_path=image_path,
                        chart_type="daily",
                        run_id=None,
                        execution_id=execution_id,
                        dag_id=context['dag'].dag_id,
                        task_id=context['task'].task_id,
                        chart_data={
                            'timeframe': 'daily',
                            'indicators': ['SMA', 'RSI', 'MACD', 'Bollinger Bands'],
                            'bars_count': len(bars),
                            'minio_url': minio_url,
                            'local_path': daily_chart.file_path
                        }
                    )
                    charts_generated.append({
                        'symbol': symbol, 
                        'timeframe': 'daily', 
                        'path': image_path,
                        'local_path': daily_chart.file_path,
                        'bars_count': len(bars)
                    })
                    logger.info(f"Generated daily chart for {symbol} - MinIO URL: {minio_url}")
            except Exception as e:
                logger.error(f"Failed to generate daily chart for {symbol}: {e}", exc_info=True)
            
            # Generate weekly chart
            try:
                # Create weekly market data
                weekly_market_data = MarketData(symbol=symbol, bars=bars, timeframe="1W")
                weekly_chart = chart_generator.generate_chart(
                    market_data=weekly_market_data,
                    config=ChartConfig(
                        symbol=symbol,
                        timeframe=Timeframe.WEEKLY,
                        include_sma=True,
                        include_rsi=True,
                        include_macd=True,
                        include_bollinger=True
                    )
                )
                
                if weekly_chart and weekly_chart.file_path:
                    # Upload chart to MinIO
                    minio_url = upload_chart_to_minio(
                        file_path=weekly_chart.file_path,
                        symbol=symbol,
                        timeframe='weekly',
                        execution_id=execution_id
                    )
                    
                    # Store chart artifact with MinIO URL
                    image_path = minio_url if minio_url else weekly_chart.file_path
                    store_chart_artifact(
                        name=f"{symbol}_weekly_chart",
                        symbol=symbol,
                        image_path=image_path,
                        chart_type="weekly",
                        run_id=None,
                        execution_id=execution_id,
                        dag_id=context['dag'].dag_id,
                        task_id=context['task'].task_id,
                        chart_data={
                            'timeframe': 'weekly',
                            'indicators': ['SMA', 'RSI', 'MACD', 'Bollinger Bands'],
                            'bars_count': len(bars),
                            'minio_url': minio_url,
                            'local_path': weekly_chart.file_path
                        }
                    )
                    charts_generated.append({
                        'symbol': symbol, 
                        'timeframe': 'weekly', 
                        'path': image_path,
                        'local_path': weekly_chart.file_path,
                        'bars_count': len(bars)
                    })
                    logger.info(f"Generated weekly chart for {symbol} - MinIO URL: {minio_url}")
            except Exception as e:
                logger.error(f"Failed to generate weekly chart for {symbol}: {e}", exc_info=True)
        
        # Store charts summary in XCom
        task_instance.xcom_push(key='charts_generated', value=charts_generated)
        
        logger.info(f"Chart generation complete. Generated {len(charts_generated)} charts")
        return {'charts_generated': len(charts_generated), 'charts': charts_generated}
    
    except Exception as e:
        logger.error(f"Chart generation failed: {e}", exc_info=True)
        raise


def llm_analysis(**context):
    """
    Perform LLM analysis on generated charts to generate trading signals
    """
    logger.info("Starting LLM analysis")
    
    try:
        task_instance = context['task_instance']
        dag_run = context['dag_run']
        execution_id = dag_run.run_id
        
        # Retrieve charts from previous task
        charts_generated = task_instance.xcom_pull(task_ids='generate_charts', key='charts_generated') or []
        
        if not charts_generated:
            logger.warning("No charts available for LLM analysis")
            return {'analysis_count': 0}
        
        # Initialize LLM analyzer
        llm_analyzer = LLMSignalAnalyzer()
        
        analyses = []
        
        # Group charts by symbol
        charts_by_symbol = {}
        for chart in charts_generated:
            symbol = chart['symbol']
            if symbol not in charts_by_symbol:
                charts_by_symbol[symbol] = {'daily': None, 'weekly': None}
            charts_by_symbol[symbol][chart['timeframe']] = chart['path']
        
        # Analyze each symbol
        for symbol, charts in charts_by_symbol.items():
            if not charts['daily'] or not charts['weekly']:
                logger.warning(f"Skipping {symbol} - missing daily or weekly chart")
                continue
            
            try:
                # Load chart images
                import base64
                from pathlib import Path
                import requests
                
                daily_path_str = charts['daily']
                weekly_path_str = charts['weekly']
                
                # Check if paths are MinIO URLs or local paths
                daily_path = Path(daily_path_str) if not daily_path_str.startswith('http') else None
                weekly_path = Path(weekly_path_str) if not weekly_path_str.startswith('http') else None
                
                # Read chart images as base64
                if daily_path and daily_path.exists():
                    with open(daily_path, 'rb') as f:
                        daily_image = base64.b64encode(f.read()).decode('utf-8')
                elif daily_path_str.startswith('http'):
                    # Download from MinIO URL
                    response = requests.get(daily_path_str, timeout=10)
                    response.raise_for_status()
                    daily_image = base64.b64encode(response.content).decode('utf-8')
                else:
                    logger.warning(f"Daily chart file not found for {symbol}: {daily_path_str}")
                    continue
                
                if weekly_path and weekly_path.exists():
                    with open(weekly_path, 'rb') as f:
                        weekly_image = base64.b64encode(f.read()).decode('utf-8')
                elif weekly_path_str.startswith('http'):
                    # Download from MinIO URL
                    response = requests.get(weekly_path_str, timeout=10)
                    response.raise_for_status()
                    weekly_image = base64.b64encode(response.content).decode('utf-8')
                else:
                    logger.warning(f"Weekly chart file not found for {symbol}: {weekly_path_str}")
                    continue
                
                # Get bars count from chart metadata or use default
                # Find the chart in charts_generated to get bars_count
                bars_count = 0
                for chart in charts_generated:
                    if chart['symbol'] == symbol and chart['timeframe'] == 'daily':
                        bars_count = chart.get('bars_count', 0)
                        break
                
                # If not found, try to get from weekly chart
                if bars_count == 0:
                    for chart in charts_generated:
                        if chart['symbol'] == symbol and chart['timeframe'] == 'weekly':
                            bars_count = chart.get('bars_count', 0)
                            break
                
                # Create ChartResult objects
                from models.chart import ChartResult
                # ChartResult requires file_path, width, height, periods_shown
                # We'll use defaults for missing fields
                daily_chart_result = ChartResult(
                    symbol=symbol,
                    timeframe=Timeframe.DAILY,
                    file_path=daily_path_str,
                    width=1920,
                    height=1080,
                    periods_shown=bars_count if bars_count > 0 else 100  # Default to 100 if not found
                )
                
                weekly_chart_result = ChartResult(
                    symbol=symbol,
                    timeframe=Timeframe.WEEKLY,
                    file_path=weekly_path_str,
                    width=1920,
                    height=1080,
                    periods_shown=bars_count if bars_count > 0 else 100  # Default to 100 if not found
                )
                
                # Perform LLM analysis
                signal = llm_analyzer.analyze_charts(
                    symbol=symbol,
                    daily_chart=daily_chart_result,
                    weekly_chart=weekly_chart_result
                )
                
                if signal:
                    # Store LLM analysis artifact using store_signal_artifact
                    # Extract signal data for storage
                    from utils.artifact_storage import store_signal_artifact
                    store_signal_artifact(
                        name=f"{symbol}_llm_analysis",
                        symbol=symbol,
                        action=signal.action.value if hasattr(signal.action, 'value') else str(signal.action),
                        confidence=float(signal.confidence_score) if signal.confidence_score else 0.0,
                        run_id=None,
                        execution_id=execution_id,
                        dag_id=context['dag'].dag_id,
                        task_id=context['task'].task_id,
                        signal_data={
                            'action': signal.action.value if hasattr(signal.action, 'value') else str(signal.action),
                            'confidence': signal.confidence.value if hasattr(signal.confidence, 'value') else str(signal.confidence),
                            'confidence_score': float(signal.confidence_score) if signal.confidence_score else 0.0,
                            'reasoning': signal.reasoning or '',
                            'key_factors': signal.key_factors or []
                        },
                        metadata={
                            'daily_chart': str(daily_path),
                            'weekly_chart': str(weekly_path),
                            'model_name': llm_analyzer.model if hasattr(llm_analyzer, 'model') else 'unknown',
                            'provider': llm_analyzer.provider if hasattr(llm_analyzer, 'provider') else 'unknown'
                        }
                    )
                    
                    analyses.append({
                        'symbol': symbol,
                        'action': signal.action.value if hasattr(signal.action, 'value') else str(signal.action),
                        'confidence': signal.confidence.value if hasattr(signal.confidence, 'value') else str(signal.confidence),
                        'confidence_score': float(signal.confidence_score) if signal.confidence_score else 0.0,
                        'reasoning': signal.reasoning or ''
                    })
                    logger.info(f"LLM analysis complete for {symbol}: {signal.action}")
            
            except Exception as e:
                logger.error(f"Failed LLM analysis for {symbol}: {e}", exc_info=True)
        
        # Store analysis summary in XCom
        task_instance.xcom_push(key='llm_analyses', value=analyses)
        
        logger.info(f"LLM analysis complete. Analyzed {len(analyses)} symbols")
        return {'analysis_count': len(analyses), 'analyses': analyses}
    
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}", exc_info=True)
        raise


# Define the DAG
_dag_kwargs = dict(
    dag_id='ibkr_stock_data_workflow',
    default_args=default_args,
    description='IBKR Stock Data Workflow - Fetch TSLA/NVDA data from PostgreSQL with MLflow tracking',
    start_date=_days_ago(1),
    catchup=False,  # Don't run historical DAG runs
    tags=['ibkr', 'stock-data', 'mlflow', 'postgres'],
    max_active_runs=1,  # Only one run at a time
)

# Airflow 3: uses `schedule`; Airflow 2: still supports `schedule_interval`.
try:
    dag = DAG(**_dag_kwargs, schedule=None)  # Manual trigger only (set to '@daily' or cron for scheduled runs)
except TypeError:  # pragma: no cover
    dag = DAG(**_dag_kwargs, schedule_interval=None)

with dag:
    
    # Task 1: Extract stock data from PostgreSQL
    extract_task = PythonOperator(
        task_id='extract_stock_data',
        python_callable=extract_stock_data,
        provide_context=True,
        doc_md="""
        ### Extract Stock Data
        Fetches stock data for configured symbols (TSLA, NVDA) from PostgreSQL database.
        
        **Outputs:**
        - Stock data (stored in XCom)
        - Extraction summary
        - List of missing symbols
        """
    )
    
    # Task 2: Validate data quality
    validate_task = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
        provide_context=True,
        doc_md="""
        ### Validate Data Quality
        Performs validation checks on extracted data:
        - Required columns present
        - No null values in critical fields
        - Price values are positive
        - Volume values are non-negative
        """
    )
    
    # Task 3: Transform and enrich data
    transform_task = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
        provide_context=True,
        doc_md="""
        ### Transform Data
        Applies transformations to stock data:
        - Calculate daily returns
        - Calculate price ranges
        - Add derived metrics
        """
    )
    
    # Task 4: Generate charts
    generate_charts_task = PythonOperator(
        task_id='generate_charts',
        python_callable=generate_charts,
        provide_context=True,
        doc_md="""
        ### Generate Charts
        Generates daily and weekly technical analysis charts with indicators:
        - SMA (20, 50, 200)
        - RSI (14)
        - MACD
        - Bollinger Bands
        - Volume analysis
        """
    )
    
    # Task 5: LLM Analysis
    llm_analysis_task = PythonOperator(
        task_id='llm_analysis',
        python_callable=llm_analysis,
        provide_context=True,
        doc_md="""
        ### LLM Analysis
        Analyzes generated charts using LLM to generate trading signals:
        - Action: BUY, SELL, or HOLD
        - Confidence: HIGH, MEDIUM, or LOW
        - Reasoning: Detailed analysis explanation
        """
    )
    
    # Task 6: Log to MLflow
    mlflow_task = PythonOperator(
        task_id='log_to_mlflow',
        python_callable=log_to_mlflow,
        provide_context=True,
        doc_md="""
        ### Log to MLflow
        Tracks the workflow run in MLflow:
        - Parameters (symbols, dates, configuration)
        - Metrics (row counts, validation status)
        - Artifacts (data samples, summary reports, charts, LLM analysis)
        - Debug information (if debug mode enabled)
        """
    )
    
    # Define task dependencies
    extract_task >> validate_task >> transform_task >> generate_charts_task >> llm_analysis_task >> mlflow_task
