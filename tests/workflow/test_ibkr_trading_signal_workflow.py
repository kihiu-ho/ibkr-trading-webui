import os
import sys
sys.path.append(os.path.abspath('dags'))

import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta

# Mock environment variables for configuration
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'testdb'
os.environ['POSTGRES_USER'] = 'testuser'
os.environ['POSTGRES_PASSWORD'] = 'testpass'
os.environ['MLFLOW_TRACKING_URI'] = 'http://localhost:5500'
os.environ['MLFLOW_EXPERIMENT_NAME'] = 'test-ibkr-stock-data'
os.environ['DEBUG_MODE'] = 'true'
os.environ['STOCK_SYMBOLS'] = 'TSLA'
os.environ['ENVIRONMENT'] = 'test'
os.environ['LLM_PROVIDER'] = 'mock_llm'
os.environ['LLM_API_BASE_URL'] = 'http://mock-llm:8000'
os.environ['LLM_API_KEY'] = 'mock_key'
os.environ['LLM_MODEL'] = 'mock_model'
os.environ['CHARTS_DIR'] = '/tmp/charts'
os.environ['MINIO_HOST'] = 'localhost:9000'
os.environ['MINIO_ACCESS_KEY'] = 'minioadmin'
os.environ['MINIO_SECRET_KEY'] = 'minioadmin'
os.environ['MINIO_BUCKET_NAME'] = 'charts'


# Import modules that depend on the mocked environment variables
from dags.ibkr_trading_signal_workflow import (
    fetch_market_data_task, generate_daily_chart_task, generate_weekly_chart_task,
    analyze_with_llm_task, place_order_task, get_trades_task,
    get_portfolio_task, log_to_mlflow_task, SYMBOL, IBKR_HOST, IBKR_PORT, POSITION_SIZE
)
from dags.models.market_data import MarketData, OHLCVBar
from dags.models.chart import ChartResult, ChartConfig, Timeframe
from dags.models.signal import TradingSignal, SignalAction, SignalConfidence
from dags.models.order import Order, OrderSide, OrderType, OrderStatus
from dags.models.trade import Trade, TradeExecution
from dags.models.portfolio import Portfolio, Position

class TestIBKRTradingSignalWorkflow(unittest.TestCase):

    def setUp(self):
        self.mock_context = {
            'dag_run': MagicMock(),
            'task_instance': MagicMock(),
            'execution_date': datetime.now(),
            'dag': MagicMock(dag_id='ibkr_trading_signal_workflow'),
            'task': MagicMock(task_id='mock_task')
        }
        self.mock_context['dag_run'].run_id = 'test_run_123'
        self.mock_context['task_instance'].xcom_pull.return_value = None # Default no XCom data
        
        # Ensure charts directory exists for tests
        os.makedirs(os.getenv('CHARTS_DIR'), exist_ok=True)

    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    def test_fetch_market_data_task(self, MockIBKRClient):
        mock_client_instance = MockIBKRClient.return_value.__enter__.return_value
        mock_market_data = MarketData(
            symbol=SYMBOL,
            bars=[
                OHLCVBar(date=datetime(2023, 1, 1), open=100.0, high=105.0, low=99.0, close=103.0, volume=100000),
                OHLCVBar(date=datetime(2023, 1, 2), open=103.0, high=108.0, low=102.0, close=107.0, volume=120000)
            ],
            latest_price=107.0,
            timeframe='1 day'
        )
        mock_client_instance.fetch_market_data.return_value = mock_market_data

        result = fetch_market_data_task(**self.mock_context)

        MockIBKRClient.assert_called_with(host=IBKR_HOST, port=IBKR_PORT)
        mock_client_instance.fetch_market_data.assert_called_once_with(
            symbol=SYMBOL, exchange="SMART", duration="200 D", bar_size="1 day"
        )
        self.mock_context['task_instance'].xcom_push.assert_called_once_with(
            key='market_data', value=mock_market_data.model_dump_json()
        )
        self.assertEqual(result['symbol'], SYMBOL)
        self.assertEqual(result['bars'], 2)
        self.assertEqual(result['latest_price'], 107.0)

    @patch('dags.ibkr_trading_signal_workflow.ChartGenerator')
    @patch('dags.ibkr_trading_signal_workflow.upload_chart_to_minio', return_value='http://minio/daily_chart.png')
    @patch('dags.ibkr_trading_signal_workflow.store_chart_artifact')
    def test_generate_daily_chart_task(self, mock_store_chart_artifact, mock_upload_chart_to_minio, MockChartGenerator):
        mock_market_data = MarketData(
            symbol=SYMBOL,
            bars=[
                OHLCVBar(date=datetime(2023, 1, 1), open=100.0, high=105.0, low=99.0, close=103.0, volume=100000),
                OHLCVBar(date=datetime(2023, 1, 2), open=103.0, high=108.0, low=102.0, close=107.0, volume=120000)
            ],
            latest_price=107.0,
            timeframe='1 day'
        )
        self.mock_context['task_instance'].xcom_pull.side_effect = [
            mock_market_data.model_dump_json()
        ]

        mock_chart_gen_instance = MockChartGenerator.return_value
        mock_chart_result = ChartResult(
            symbol=SYMBOL,
            timeframe=Timeframe.DAILY,
            file_path=os.path.join(os.getenv('CHARTS_DIR'), f"{SYMBOL}_daily_chart.png"),
            indicators_included=['SMA', 'RSI'],
            periods_shown=60
        )
        mock_chart_gen_instance.calculate_indicators.return_value = MagicMock()
        mock_chart_gen_instance.generate_chart.return_value = mock_chart_result

        result = generate_daily_chart_task(**self.mock_context)

        MockChartGenerator.assert_called_with(output_dir=os.getenv('CHARTS_DIR'))
        mock_chart_gen_instance.generate_chart.assert_called_once()
        self.mock_context['task_instance'].xcom_push.assert_called_once_with(
            key='daily_chart', value=mock_chart_result.model_dump_json()
        )
        mock_upload_chart_to_minio.assert_called_once()
        mock_store_chart_artifact.assert_called_once()
        self.assertEqual(result['chart_path'], mock_chart_result.file_path)
        self.assertEqual(result['indicators'], ['SMA', 'RSI'])
    
    @patch('dags.ibkr_trading_signal_workflow.ChartGenerator')
    @patch('dags.ibkr_trading_signal_workflow.upload_chart_to_minio', return_value='http://minio/weekly_chart.png')
    @patch('dags.ibkr_trading_signal_workflow.store_chart_artifact')
    def test_generate_weekly_chart_task(self, mock_store_chart_artifact, mock_upload_chart_to_minio, MockChartGenerator):
        mock_market_data = MarketData(
            symbol=SYMBOL,
            bars=[
                OHLCVBar(date=datetime(2023, 1, 1), open=100.0, high=105.0, low=99.0, close=103.0, volume=100000),
                OHLCVBar(date=datetime(2023, 1, 2), open=103.0, high=108.0, low=102.0, close=107.0, volume=120000)
            ],
            latest_price=107.0,
            timeframe='1 day'
        )
        self.mock_context['task_instance'].xcom_pull.side_effect = [
            mock_market_data.model_dump_json()
        ]

        mock_chart_gen_instance = MockChartGenerator.return_value
        mock_weekly_data = MarketData(
            symbol=SYMBOL,
            bars=[
                OHLCVBar(date=datetime(2023, 1, 1), open=100.0, high=108.0, low=99.0, close=107.0, volume=220000),
            ],
            latest_price=107.0,
            timeframe='1 week'
        )
        mock_chart_result = ChartResult(
            symbol=SYMBOL,
            timeframe=Timeframe.WEEKLY,
            file_path=os.path.join(os.getenv('CHARTS_DIR'), f"{SYMBOL}_weekly_chart.png"),
            indicators_included=['SMA', 'RSI'],
            periods_shown=52
        )
        mock_chart_gen_instance.resample_to_weekly.return_value = mock_weekly_data
        mock_chart_gen_instance.calculate_indicators.return_value = MagicMock()
        mock_chart_gen_instance.generate_chart.return_value = mock_chart_result

        result = generate_weekly_chart_task(**self.mock_context)

        MockChartGenerator.assert_called_with(output_dir=os.getenv('CHARTS_DIR'))
        mock_chart_gen_instance.resample_to_weekly.assert_called_once_with(mock_market_data)
        mock_chart_gen_instance.generate_chart.assert_called_once()
        self.mock_context['task_instance'].xcom_push.assert_called_once_with(
            key='weekly_chart', value=mock_chart_result.model_dump_json()
        )
        mock_upload_chart_to_minio.assert_called_once()
        mock_store_chart_artifact.assert_called_once()
        self.assertEqual(result['chart_path'], mock_chart_result.file_path)
        self.assertEqual(result['periods'], 52)
    
    @patch('dags.ibkr_trading_signal_workflow.LLMSignalAnalyzer')
    @patch('dags.ibkr_trading_signal_workflow.store_llm_artifact')
    @patch('dags.ibkr_trading_signal_workflow.store_signal_artifact')
    def test_analyze_with_llm_task(self, mock_store_signal_artifact, mock_store_llm_artifact, MockLLMSignalAnalyzer):
        mock_market_data = MarketData(
            symbol=SYMBOL,
            bars=[],
            latest_price=100.0,
            timeframe='1 day'
        )
        mock_daily_chart = ChartResult(
            symbol=SYMBOL,
            timeframe=Timeframe.DAILY,
            file_path='daily.png',
            indicators_included=['SMA']
        )
        mock_weekly_chart = ChartResult(
            symbol=SYMBOL,
            timeframe=Timeframe.WEEKLY,
            file_path='weekly.png',
            indicators_included=['SMA']
        )
        mock_signal = TradingSignal(
            symbol=SYMBOL,
            action=SignalAction.BUY,
            confidence=SignalConfidence.HIGH,
            confidence_score=90,
            reasoning="Market looks good",
            is_actionable=True,
            suggested_entry_price=101.0,
            model_used='mock_model'
        )

        self.mock_context['task_instance'].xcom_pull.side_effect = [
            mock_market_data.model_dump_json(),
            mock_daily_chart.model_dump_json(),
            mock_weekly_chart.model_dump_json()
        ]

        mock_analyzer_instance = MockLLMSignalAnalyzer.return_value
        mock_analyzer_instance.analyze_charts.return_value = mock_signal

        result = analyze_with_llm_task(**self.mock_context)

        MockLLMSignalAnalyzer.assert_called_with(
            provider=os.getenv('LLM_PROVIDER'),
            model=os.getenv('LLM_MODEL'),
            api_key=os.getenv('LLM_API_KEY'),
            base_url=os.getenv('LLM_API_BASE_URL')
        )
        mock_analyzer_instance.analyze_charts.assert_called_once()
        self.mock_context['task_instance'].xcom_push.assert_called_once_with(
            key='trading_signal', value=mock_signal.model_dump_json()
        )
        mock_store_llm_artifact.assert_called_once()
        mock_store_signal_artifact.assert_called_once()
        self.assertEqual(result['action'], SignalAction.BUY)
        self.assertEqual(result['confidence'], SignalConfidence.HIGH)
        self.assertTrue(result['is_actionable'])
        self.assertEqual(result['entry_price'], 101.0)
    
    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    @patch('dags.ibkr_trading_signal_workflow.store_order_artifact')
    def test_place_order_task_actionable(self, mock_store_order_artifact, MockIBKRClient):
        mock_signal = TradingSignal(
            symbol=SYMBOL,
            action=SignalAction.BUY,
            confidence=SignalConfidence.HIGH,
            confidence_score=90,
            reasoning="Market looks good",
            is_actionable=True,
            suggested_entry_price=101.0
        )
        mock_order = Order(
            symbol=SYMBOL,
            side=OrderSide.BUY,
            quantity=POSITION_SIZE,
            order_type=OrderType.LIMIT,
            limit_price=101.0,
            order_id=123,
            status=OrderStatus.SUBMITTED,
            submitted_at=datetime.now()
        )

        self.mock_context['task_instance'].xcom_pull.side_effect = [
            mock_signal.model_dump_json()
        ]

        mock_client_instance = MockIBKRClient.return_value.__enter__.return_value
        mock_client_instance.place_order.return_value = mock_order

        result = place_order_task(**self.mock_context)

        MockIBKRClient.assert_called_with(host=IBKR_HOST, port=IBKR_PORT)
        mock_client_instance.place_order.assert_called_once()
        self.mock_context['task_instance'].xcom_push.assert_any_call(key='order', value=mock_order.model_dump_json())
        self.mock_context['task_instance'].xcom_push.assert_any_call(key='order_placed', value=True)
        mock_store_order_artifact.assert_called_once()
        self.assertTrue(result['order_placed'])
        self.assertEqual(result['order_id'], 123)
    
    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    @patch('dags.ibkr_trading_signal_workflow.store_order_artifact')
    def test_place_order_task_not_actionable(self, mock_store_order_artifact, MockIBKRClient):
        mock_signal = TradingSignal(
            symbol=SYMBOL,
            action=SignalAction.HOLD,
            confidence=SignalConfidence.MEDIUM,
            confidence_score=50,
            reasoning="Uncertain market",
            is_actionable=False
        )

        self.mock_context['task_instance'].xcom_pull.side_effect = [
            mock_signal.model_dump_json()
        ]

        result = place_order_task(**self.mock_context)

        MockIBKRClient.assert_not_called()
        mock_store_order_artifact.assert_not_called()
        self.mock_context['task_instance'].xcom_push.assert_called_once_with(key='order_placed', value=False)
        self.assertFalse(result['order_placed'])
        self.assertEqual(result['reason'], 'Signal not actionable')

    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    @patch('dags.ibkr_trading_signal_workflow.store_trade_artifact')
    def test_get_trades_task_with_trades(self, mock_store_trade_artifact, MockIBKRClient):
        mock_order = Order(
            symbol=SYMBOL,
            side=OrderSide.BUY,
            quantity=POSITION_SIZE,
            order_type=OrderType.LIMIT,
            limit_price=101.0,
            order_id=123,
            status=OrderStatus.FILLED,
            submitted_at=datetime.now()
        )
        mock_trade = Trade(
            symbol=SYMBOL,
            total_quantity=POSITION_SIZE,
            average_price=101.0,
            side=OrderSide.BUY,
            total_cost=POSITION_SIZE * 101.0,
            total_commission=1.0,
            executions=[
                TradeExecution(execution_id='exec1', quantity=POSITION_SIZE, price=101.0, time=datetime.now())
            ],
            first_execution_at=datetime.now(),
            last_execution_at=datetime.now()
        )

        self.mock_context['task_instance'].xcom_pull.side_effect = [
            True, # order_placed
            mock_order.model_dump_json()
        ]

        mock_client_instance = MockIBKRClient.return_value.__enter__.return_value
        mock_client_instance.get_trades.return_value = [mock_trade]

        result = get_trades_task(**self.mock_context)

        MockIBKRClient.assert_called_with(host=IBKR_HOST, port=IBKR_PORT)
        mock_client_instance.get_trades.assert_called_once_with(mock_order.order_id)
        self.mock_context['task_instance'].xcom_push.assert_called_once_with(
            key='trades', value=[mock_trade.model_dump_json()]
        )
        mock_store_trade_artifact.assert_called_once()
        self.assertEqual(result['trades_found'], 1)
        self.assertEqual(result['total_quantity'], POSITION_SIZE)

    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    @patch('dags.ibkr_trading_signal_workflow.store_trade_artifact')
    def test_get_trades_task_no_order_placed(self, mock_store_trade_artifact, MockIBKRClient):
        self.mock_context['task_instance'].xcom_pull.side_effect = [
            False # order_placed
        ]

        result = get_trades_task(**self.mock_context)

        MockIBKRClient.assert_not_called()
        mock_store_trade_artifact.assert_not_called()
        self.assertEqual(result['trades_found'], 0)
    
    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    @patch('dags.ibkr_trading_signal_workflow.store_portfolio_artifact')
    def test_get_portfolio_task(self, mock_store_portfolio_artifact, MockIBKRClient):
        mock_portfolio = Portfolio(
            account_id='U1234567',
            total_value=100000.0,
            cash_balance=50000.0,
            total_market_value=50000.0,
            total_unrealized_pnl=1000.0,
            position_count=1,
            positions=[
                Position(
                    symbol=SYMBOL,
                    quantity=POSITION_SIZE,
                    average_cost=90.0,
                    current_price=100.0,
                    market_value=1000.0,
                    unrealized_pnl=100.0,
                    unrealized_pnl_percent=10.0
                )
            ]
        )

        mock_client_instance = MockIBKRClient.return_value.__enter__.return_value
        mock_client_instance.get_portfolio.return_value = mock_portfolio

        result = get_portfolio_task(**self.mock_context)

        MockIBKRClient.assert_called_with(host=IBKR_HOST, port=IBKR_PORT)
        mock_client_instance.get_portfolio.assert_called_once()
        self.mock_context['task_instance'].xcom_push.assert_called_once_with(
            key='portfolio', value=mock_portfolio.model_dump_json()
        )
        mock_store_portfolio_artifact.assert_called_once()
        self.assertEqual(result['positions'], 1)
        self.assertEqual(result['total_value'], 100000.0)
        self.assertEqual(result['cash'], 50000.0)
    
    @patch('dags.ibkr_trading_signal_workflow.mlflow_run_context')
    @patch('dags.ibkr_trading_signal_workflow.shutil.copy')
    @patch('dags.ibkr_trading_signal_workflow.requests')
    def test_log_to_mlflow_task(self, mock_requests, mock_shutil_copy, mock_mlflow_run_context):
        mock_market_data = MarketData(
            symbol=SYMBOL, bars=[], latest_price=100.0, timeframe='1 day'
        )
        mock_signal = TradingSignal(
            symbol=SYMBOL, action=SignalAction.BUY, confidence=SignalConfidence.HIGH,
            confidence_score=90, reasoning="Test reasoning", is_actionable=True,
            suggested_entry_price=101.0, model_used='mock_model'
        )
        mock_daily_chart = ChartResult(
            symbol=SYMBOL, timeframe=Timeframe.DAILY, file_path='/tmp/charts/daily.png',
            indicators_included=['SMA']
        )
        mock_weekly_chart = ChartResult(
            symbol=SYMBOL, timeframe=Timeframe.WEEKLY, file_path='/tmp/charts/weekly.png',
            indicators_included=['SMA']
        )
        mock_portfolio = Portfolio(
            account_id='U1234567', total_value=100000.0, cash_balance=50000.0,
            total_market_value=50000.0, total_unrealized_pnl=1000.0, position_count=1,
            positions=[Position(symbol=SYMBOL, quantity=POSITION_SIZE, average_cost=90.0,
                                current_price=100.0, market_value=1000.0, unrealized_pnl=100.0,
                                unrealized_pnl_percent=10.0)]
        )

        self.mock_context['task_instance'].xcom_pull.side_effect = [
            mock_market_data.model_dump_json(),
            mock_signal.model_dump_json(),
            mock_daily_chart.model_dump_json(),
            mock_weekly_chart.model_dump_json(),
            mock_portfolio.model_dump_json(),
            True # order_placed
        ]

        mock_tracker = MagicMock()
        mock_tracker.run_id = 'mlflow_run_id_123'
        mock_mlflow_run_context.return_value.__enter__.return_value = mock_tracker

        # Mock requests.get and requests.patch for artifact updates
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = {'artifacts': [{'id': 'artifact_id_1', 'run_id': None}]}
        mock_requests.patch.return_value.status_code = 200

        result = log_to_mlflow_task(**self.mock_context)

        mock_mlflow_run_context.assert_called_once()
        mock_tracker.log_params.assert_called_once()
        mock_tracker.log_metrics.assert_called_once()
        mock_tracker.log_artifact_dict.assert_any_call(json.loads(mock_signal.model_dump_json()), 'trading_signal.json')
        mock_shutil_copy.assert_any_call(mock_daily_chart.file_path, 'daily_chart.png')
        mock_shutil_copy.assert_any_call(mock_weekly_chart.file_path, 'weekly_chart.png')
        mock_tracker.log_artifact_dict.assert_any_call(json.loads(mock_portfolio.model_dump_json()), 'portfolio.json')
        mock_requests.get.assert_called_once_with(f"http://backend:8000/api/artifacts/?symbol={SYMBOL}&limit=10")
        mock_requests.patch.assert_called_once()
        self.assertEqual(result['mlflow_run_id'], 'mlflow_run_id_123')

if __name__ == '__main__':
    unittest.main()