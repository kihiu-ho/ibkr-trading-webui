import os
import sys
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('dags'))

import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta
from decimal import Decimal
from airflow.exceptions import AirflowFailException

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
os.environ['IBKR_HOST'] = 'gateway'
os.environ['IBKR_PORT'] = '4002'


# Import modules that depend on the mocked environment variables
from dags.ibkr_trading_signal_workflow import (
    fetch_market_data_task, generate_daily_chart_task, generate_weekly_chart_task,
    analyze_with_llm_task, place_order_task, get_trades_task,
    get_portfolio_task, log_to_mlflow_task, SYMBOL, IBKR_HOST, IBKR_PORT, POSITION_SIZE,
    MARKET_DATA_DURATION, MARKET_DATA_BAR_SIZE, normalize_limit_price
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

    def _set_xcom_pull_mapping(self, mapping: dict):
        """Helper to route xcom_pull responses by key."""
        def _side_effect(*args, **kwargs):
            key = kwargs.get('key')
            return mapping.get(key)
        self.mock_context['task_instance'].xcom_pull.side_effect = _side_effect

    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    def test_fetch_market_data_task(self, MockIBKRClient):
        mock_client_instance = MockIBKRClient.return_value.__enter__.return_value
        mock_market_data = MarketData(
            symbol=SYMBOL,
            bars=[
                OHLCVBar(timestamp=datetime(2023, 1, 1), open=100.0, high=105.0, low=99.0, close=103.0, volume=100000),
                OHLCVBar(timestamp=datetime(2023, 1, 2), open=103.0, high=108.0, low=102.0, close=107.0, volume=120000)
            ],
            latest_price=107.0,
            timeframe='1 day'
        )
        mock_client_instance.fetch_market_data.return_value = mock_market_data
        mock_client_instance.get_metadata.return_value = {'ib_insync_version': '1.0.0', 'connection_mode': 'mock'}

        result = fetch_market_data_task(**self.mock_context)

        MockIBKRClient.assert_called_with(host=IBKR_HOST, port=IBKR_PORT, strict_mode=False)
        mock_client_instance.fetch_market_data.assert_called_once_with(
            symbol=SYMBOL, exchange="SMART", duration=MARKET_DATA_DURATION, bar_size=MARKET_DATA_BAR_SIZE
        )
        self.assertIn(
            ('market_data', mock_market_data.model_dump_json()),
            [(call.kwargs.get('key'), call.kwargs.get('value')) for call in self.mock_context['task_instance'].xcom_push.call_args_list]
        )
        metadata_calls = [
            call for call in self.mock_context['task_instance'].xcom_push.call_args_list
            if call.kwargs.get('key') == 'market_data_metadata'
        ]
        self.assertEqual(len(metadata_calls), 1)
        self.assertEqual(metadata_calls[0].kwargs['value']['bars_returned'], 2)
        self.assertEqual(result['symbol'], SYMBOL)
        self.assertEqual(result['bars'], 2)
        self.assertEqual(result['latest_price'], 107.0)

    @patch('dags.ibkr_trading_signal_workflow._capture_live_market_snapshot')
    @patch('dags.ibkr_trading_signal_workflow.IBKR_API_BASE_URL', 'https://mock-api')
    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    def test_fetch_market_data_task_stores_live_snapshot(self, MockIBKRClient, mock_capture):
        mock_client_instance = MockIBKRClient.return_value.__enter__.return_value
        mock_market_data = MarketData(
            symbol=SYMBOL,
            bars=[
                OHLCVBar(timestamp=datetime(2023, 1, 1), open=100.0, high=105.0, low=99.0, close=103.0, volume=100000),
            ],
            timeframe='1 day'
        )
        mock_client_instance.fetch_market_data.return_value = mock_market_data
        mock_client_instance.get_metadata.return_value = {'connection_mode': 'ibkr'}

        live_payload = {
            'conid': 1234,
            'last_price': 250.5,
            'fields': {'31': 250.5},
            'source': 'ibkr_client_portal',
            'timestamp': 123456789
        }

        def _mock_capture(symbol, task_instance):
            task_instance.xcom_push(key='live_market_data', value=live_payload)
            return live_payload['conid'], live_payload

        mock_capture.side_effect = _mock_capture

        fetch_market_data_task(**self.mock_context)

        # Ensure live snapshot stored in XCom
        live_pushes = [
            call for call in self.mock_context['task_instance'].xcom_push.call_args_list
            if call.kwargs.get('key') == 'live_market_data'
        ]
        self.assertEqual(len(live_pushes), 1)
        self.assertEqual(live_pushes[0].kwargs['value']['last_price'], 250.5)

        # Ensure metadata includes live snapshot context
        metadata_call = next(
            call for call in self.mock_context['task_instance'].xcom_push.call_args_list
            if call.kwargs.get('key') == 'market_data_metadata'
        )
        self.assertIn('live_snapshot', metadata_call.kwargs['value'])
        self.assertEqual(metadata_call.kwargs['value']['live_snapshot']['conid'], 1234)

    def test_normalize_limit_price_prefers_live_snapshot(self):
        signal = TradingSignal(
            symbol=SYMBOL,
            action=SignalAction.BUY,
            confidence=SignalConfidence.HIGH,
            confidence_score=80,
            reasoning="Reasoning text",
            is_actionable=True,
            suggested_entry_price=None,
            model_used='mock_model',
            timeframe_analyzed='daily'
        )
        live_snapshot = {'last_price': '199.23', 'fields': {'31': 199.23}}
        price, source = normalize_limit_price(signal, None, live_snapshot)
        self.assertEqual(price, Decimal('199.23'))
        self.assertEqual(source, 'live_market_snapshot')
    
    @patch('dags.ibkr_trading_signal_workflow.is_strict_mode', return_value=True)
    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    def test_prod_mode_requires_full_history(self, MockIBKRClient, mock_is_strict):
        mock_client_instance = MockIBKRClient.return_value.__enter__.return_value
        bars = [
            OHLCVBar(timestamp=datetime(2023, 1, 1) + timedelta(days=i), open=100.0 + i, high=105.0 + i, low=99.0 + i, close=103.0 + i, volume=100000)
            for i in range(10)
        ]
        mock_market_data = MarketData(symbol=SYMBOL, bars=bars, latest_price=bars[-1].close, timeframe='1 day')
        mock_client_instance.fetch_market_data.return_value = mock_market_data
        mock_client_instance.get_metadata.return_value = {}

        with self.assertRaises(AirflowFailException):
            fetch_market_data_task(**self.mock_context)

        mock_client_instance.fetch_market_data.assert_called_once_with(
            symbol=SYMBOL,
            exchange="SMART",
            duration='1 Y',
            bar_size='1 day'
        )

    @patch('dags.ibkr_trading_signal_workflow.ChartGenerator')
    @patch('dags.ibkr_trading_signal_workflow.upload_chart_to_minio', return_value='http://minio/daily_chart.png')
    @patch('dags.ibkr_trading_signal_workflow.store_chart_artifact')
    def test_generate_daily_chart_task(self, mock_store_chart_artifact, mock_upload_chart_to_minio, MockChartGenerator):
        mock_market_data = MarketData(
            symbol=SYMBOL,
            bars=[
                OHLCVBar(timestamp=datetime(2023, 1, 1), open=100.0, high=105.0, low=99.0, close=103.0, volume=100000),
                OHLCVBar(timestamp=datetime(2023, 1, 2), open=103.0, high=108.0, low=102.0, close=107.0, volume=120000)
            ],
            latest_price=107.0,
            timeframe='1 day'
        )
        self._set_xcom_pull_mapping({
            'market_data': mock_market_data.model_dump_json(),
            'market_data_metadata': {
                'strict_mode': True,
                'bars_requested': '1 Y',
                'bar_size': '1 day',
                'bars_returned': 2,
                'ibkr_host': 'gateway',
                'ibkr_port': 4002
            }
        })

        mock_chart_gen_instance = MockChartGenerator.return_value
        mock_chart_result = ChartResult(
            symbol=SYMBOL,
            timeframe=Timeframe.DAILY,
            file_path=os.path.join(os.getenv('CHARTS_DIR'), f"{SYMBOL}_daily_chart.png"),
            width=1920,
            height=1080,
            indicators_included=['SMA', 'RSI'],
            periods_shown=60
        )
        mock_chart_gen_instance.calculate_indicators.return_value = MagicMock()
        mock_chart_gen_instance.generate_chart.return_value = mock_chart_result

        result = generate_daily_chart_task(**self.mock_context)

        MockChartGenerator.assert_called_with(output_dir=os.getenv('CHARTS_DIR'))
        mock_chart_gen_instance.generate_chart.assert_called_once()
        self.mock_context['task_instance'].xcom_push.assert_any_call(
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
                OHLCVBar(timestamp=datetime(2023, 1, 1), open=100.0, high=105.0, low=99.0, close=103.0, volume=100000),
                OHLCVBar(timestamp=datetime(2023, 1, 2), open=103.0, high=108.0, low=102.0, close=107.0, volume=120000)
            ],
            latest_price=107.0,
            timeframe='1 day'
        )
        self._set_xcom_pull_mapping({
            'market_data': mock_market_data.model_dump_json(),
            'market_data_metadata': {
                'strict_mode': False,
                'bars_requested': '200 D',
                'bar_size': '1 day',
                'bars_returned': 2,
                'ibkr_host': 'gateway',
                'ibkr_port': 4002
            }
        })

        mock_chart_gen_instance = MockChartGenerator.return_value
        mock_weekly_data = MarketData(
            symbol=SYMBOL,
            bars=[
                OHLCVBar(timestamp=datetime(2023, 1, 1), open=100.0, high=108.0, low=99.0, close=107.0, volume=220000),
            ],
            latest_price=107.0,
            timeframe='1 week'
        )
        mock_chart_result = ChartResult(
            symbol=SYMBOL,
            timeframe=Timeframe.WEEKLY,
            file_path=os.path.join(os.getenv('CHARTS_DIR'), f"{SYMBOL}_weekly_chart.png"),
            width=1920,
            height=1080,
            indicators_included=['SMA', 'RSI'],
            periods_shown=52
        )
        mock_chart_gen_instance.resample_to_weekly.return_value = mock_weekly_data
        mock_chart_gen_instance.calculate_indicators.return_value = MagicMock()
        mock_chart_gen_instance.generate_chart.return_value = mock_chart_result

        result = generate_weekly_chart_task(**self.mock_context)

        MockChartGenerator.assert_called_with(output_dir=os.getenv('CHARTS_DIR'))
        mock_chart_gen_instance.resample_to_weekly.assert_called_once()
        resample_arg = mock_chart_gen_instance.resample_to_weekly.call_args[0][0]
        self.assertEqual(resample_arg.symbol, mock_market_data.symbol)
        mock_chart_gen_instance.generate_chart.assert_called_once()
        self.mock_context['task_instance'].xcom_push.assert_any_call(
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
            bars=[
                OHLCVBar(
                    timestamp=datetime(2023, 1, 1),
                    open=100.0,
                    high=105.0,
                    low=99.0,
                    close=103.0,
                    volume=100000
                )
            ],
            latest_price=100.0,
            timeframe='1 day'
        )
        mock_daily_chart = ChartResult(
            symbol=SYMBOL,
            timeframe=Timeframe.DAILY,
            file_path='daily.png',
            width=1920,
            height=1080,
            indicators_included=['SMA'],
            periods_shown=60
        )
        mock_weekly_chart = ChartResult(
            symbol=SYMBOL,
            timeframe=Timeframe.WEEKLY,
            file_path='weekly.png',
            width=1920,
            height=1080,
            indicators_included=['SMA'],
            periods_shown=52
        )
        mock_signal = TradingSignal(
            symbol=SYMBOL,
            action=SignalAction.BUY,
            confidence=SignalConfidence.HIGH,
            confidence_score=90,
            reasoning="Market looks good",
            is_actionable=True,
            suggested_entry_price=101.0,
            model_used='mock_model',
            timeframe_analyzed='daily'
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
        self.mock_context['task_instance'].xcom_push.assert_any_call(
            key='trading_signal', value=mock_signal.model_dump_json()
        )
        mock_store_llm_artifact.assert_called_once()
        mock_store_signal_artifact.assert_called_once()
        self.assertEqual(result['action'], SignalAction.BUY)
        self.assertEqual(result['confidence'], SignalConfidence.HIGH)
        self.assertTrue(result['is_actionable'])
        self.assertEqual(result['entry_price'], 101.0)
    
    @patch('dags.ibkr_trading_signal_workflow.update_artifact')
    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    @patch('dags.ibkr_trading_signal_workflow.store_order_artifact')
    def test_place_order_task_actionable(self, mock_store_order_artifact, MockIBKRClient, mock_update_artifact):
        mock_signal = TradingSignal(
            symbol=SYMBOL,
            action=SignalAction.BUY,
            confidence=SignalConfidence.HIGH,
            confidence_score=90,
            reasoning="Market looks good",
            is_actionable=True,
            suggested_entry_price=101.0,
            model_used='mock_model',
            timeframe_analyzed='daily'
        )
        mock_market_data = MarketData(
            symbol=SYMBOL,
            bars=[
                OHLCVBar(timestamp=datetime(2023, 1, 1), open=100.0, high=105.0, low=99.0, close=103.0, volume=100000),
            ],
            latest_price=103.0,
            timeframe='1 day'
        )
        mock_order = Order(
            symbol=SYMBOL,
            side=OrderSide.BUY,
            quantity=POSITION_SIZE,
            order_type=OrderType.LIMIT,
            limit_price=101.0,
            order_id='123',
            status=OrderStatus.SUBMITTED,
            submitted_at=datetime.now()
        )

        self._set_xcom_pull_mapping({
            'trading_signal': mock_signal.model_dump_json(),
            'signal_artifact_id': 123,
            'market_data': mock_market_data.model_dump_json(),
            'market_data_metadata': {'bars_returned': mock_market_data.bar_count, 'strict_mode': False}
        })

        mock_client_instance = MockIBKRClient.return_value.__enter__.return_value
        mock_client_instance.place_order.return_value = mock_order

        result = place_order_task(**self.mock_context)

        MockIBKRClient.assert_called_with(host=IBKR_HOST, port=IBKR_PORT, strict_mode=False)
        mock_client_instance.place_order.assert_called_once()
        self.mock_context['task_instance'].xcom_push.assert_any_call(key='order', value=mock_order.model_dump_json())
        self.mock_context['task_instance'].xcom_push.assert_any_call(key='order_placed', value=True)
        self.mock_context['task_instance'].xcom_push.assert_any_call(key='normalized_limit_price', value=float(mock_signal.suggested_entry_price))
        mock_store_order_artifact.assert_called_once()
        mock_update_artifact.assert_called()
        self.assertTrue(result['order_placed'])
        self.assertEqual(result['order_id'], '123')
    
    @patch('dags.ibkr_trading_signal_workflow.update_artifact')
    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    @patch('dags.ibkr_trading_signal_workflow.store_order_artifact')
    def test_place_order_task_uses_market_data_when_signal_missing(self, mock_store_order_artifact, MockIBKRClient, mock_update_artifact):
        mock_signal = TradingSignal(
            symbol=SYMBOL,
            action=SignalAction.BUY,
            confidence=SignalConfidence.HIGH,
            confidence_score=90,
            reasoning="Market looks strong",
            is_actionable=True,
            suggested_entry_price=None,
            model_used='mock_model',
            timeframe_analyzed='daily'
        )
        bars = [
            OHLCVBar(timestamp=datetime(2023, 1, 1) + timedelta(days=i), open=100.0 + i, high=105.0 + i, low=99.0 + i, close=110.12 + i, volume=100000)
            for i in range(3)
        ]
        mock_market_data = MarketData(symbol=SYMBOL, bars=bars, latest_price=bars[-1].close, timeframe='1 day')
        mock_order = Order(
            symbol=SYMBOL,
            side=OrderSide.BUY,
            quantity=POSITION_SIZE,
            order_type=OrderType.LIMIT,
            limit_price=Decimal('112.12'),
            order_id='456',
            status=OrderStatus.SUBMITTED,
            submitted_at=datetime.now()
        )
        self._set_xcom_pull_mapping({
            'trading_signal': mock_signal.model_dump_json(),
            'signal_artifact_id': 77,
            'market_data': mock_market_data.model_dump_json(),
            'market_data_metadata': {'bars_returned': mock_market_data.bar_count, 'strict_mode': False}
        })
        mock_client_instance = MockIBKRClient.return_value.__enter__.return_value
        mock_client_instance.place_order.return_value = mock_order

        result = place_order_task(**self.mock_context)

        placed_order = mock_client_instance.place_order.call_args[0][0]
        self.assertEqual(str(placed_order.limit_price), '112.12')
        mock_store_order_artifact.assert_called_once()
        metadata = mock_store_order_artifact.call_args.kwargs.get('metadata')
        self.assertEqual(metadata['limit_price_source'], 'market_data_close')
        self.assertTrue(result['order_placed'])
        mock_update_artifact.assert_called()
    
    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    @patch('dags.ibkr_trading_signal_workflow.store_order_artifact')
    def test_place_order_task_not_actionable(self, mock_store_order_artifact, MockIBKRClient):
        mock_signal = TradingSignal(
            symbol=SYMBOL,
            action=SignalAction.HOLD,
            confidence=SignalConfidence.MEDIUM,
            confidence_score=50,
            reasoning="Uncertain market",
            is_actionable=False,
            model_used='mock_model',
            timeframe_analyzed='daily'
        )

        self._set_xcom_pull_mapping({
            'trading_signal': mock_signal.model_dump_json(),
            'signal_artifact_id': None
        })

        result = place_order_task(**self.mock_context)

        MockIBKRClient.assert_not_called()
        mock_store_order_artifact.assert_not_called()
        self.mock_context['task_instance'].xcom_push.assert_called_once_with(key='order_placed', value=False)
        self.assertFalse(result['order_placed'])
        self.assertEqual(result['reason'], 'Signal not actionable')
    
    @patch('dags.ibkr_trading_signal_workflow.update_artifact')
    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    @patch('dags.ibkr_trading_signal_workflow.store_order_artifact')
    def test_prod_mode_rejects_when_price_invalid(self, mock_store_order_artifact, MockIBKRClient, mock_update_artifact):
        mock_signal = TradingSignal(
            symbol=SYMBOL,
            action=SignalAction.BUY,
            confidence=SignalConfidence.HIGH,
            confidence_score=90,
            reasoning="Bad data overall",
            is_actionable=True,
            suggested_entry_price=-1,
            model_used='mock_model',
            timeframe_analyzed='daily'
        )
        self._set_xcom_pull_mapping({
            'trading_signal': mock_signal.model_dump_json(),
            'signal_artifact_id': 55,
            'market_data_metadata': {}
        })

        result = place_order_task(**self.mock_context)

        MockIBKRClient.assert_not_called()
        mock_store_order_artifact.assert_not_called()
        mock_update_artifact.assert_called_once()
        self.mock_context['task_instance'].xcom_push.assert_any_call(key='order_placed', value=False)
        self.assertFalse(result['order_placed'])
        self.assertIn("Unable to compute", result['reason'])

    @patch('dags.ibkr_trading_signal_workflow.IBKRClient')
    @patch('dags.ibkr_trading_signal_workflow.store_trade_artifact')
    def test_get_trades_task_with_trades(self, mock_store_trade_artifact, MockIBKRClient):
        mock_order = Order(
            symbol=SYMBOL,
            side=OrderSide.BUY,
            quantity=POSITION_SIZE,
            order_type=OrderType.LIMIT,
            limit_price=101.0,
            order_id='123',
            status=OrderStatus.FILLED,
            submitted_at=datetime.now()
        )
        execution_time = datetime.now()
        mock_trade = Trade(
            order_id='123',
            symbol=SYMBOL,
            total_quantity=POSITION_SIZE,
            average_price=101.0,
            side=OrderSide.BUY,
            total_cost=POSITION_SIZE * 101.0,
            total_commission=1.0,
            executions=[
                TradeExecution(
                    execution_id='exec1',
                    order_id='123',
                    symbol=SYMBOL,
                    side='BUY',
                    quantity=POSITION_SIZE,
                    price=Decimal('101.0'),
                    commission=Decimal('1.0'),
                    executed_at=execution_time
                )
            ],
            first_execution_at=execution_time,
            last_execution_at=execution_time
        )

        self.mock_context['task_instance'].xcom_pull.side_effect = [
            True, # order_placed
            mock_order.model_dump_json()
        ]

        mock_client_instance = MockIBKRClient.return_value.__enter__.return_value
        mock_client_instance.get_trades.return_value = [mock_trade]

        result = get_trades_task(**self.mock_context)

        MockIBKRClient.assert_called_with(host=IBKR_HOST, port=IBKR_PORT, strict_mode=False)
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

        MockIBKRClient.assert_called_with(host=IBKR_HOST, port=IBKR_PORT, strict_mode=False)
        mock_client_instance.get_portfolio.assert_called_once()
        self.mock_context['task_instance'].xcom_push.assert_called_once_with(
            key='portfolio', value=mock_portfolio.model_dump_json()
        )
        mock_store_portfolio_artifact.assert_called_once()
        self.assertEqual(result['positions'], 1)
        self.assertEqual(result['total_value'], 100000.0)
        self.assertEqual(result['cash'], 50000.0)
    
    @patch('dags.ibkr_trading_signal_workflow.attach_artifact_lineage')
    @patch('dags.ibkr_trading_signal_workflow.mlflow_run_context')
    def test_log_to_mlflow_task(self, mock_mlflow_run_context, mock_attach_lineage):
        mock_market_data = MarketData(
            symbol=SYMBOL,
            bars=[
                OHLCVBar(timestamp=datetime(2025, 1, 1), open=100.0, high=101.0, low=99.5, close=100.5, volume=1000)
            ],
            latest_price=100.0,
            timeframe='1 day'
        )
        mock_signal = TradingSignal(
            symbol=SYMBOL, action=SignalAction.BUY, confidence=SignalConfidence.HIGH,
            confidence_score=90, reasoning="Test reasoning", is_actionable=True,
            suggested_entry_price=101.0, model_used='mock_model', timeframe_analyzed='daily'
        )
        mock_daily_chart = ChartResult(
            symbol=SYMBOL,
            timeframe=Timeframe.DAILY,
            file_path='/tmp/charts/daily.png',
            width=1920,
            height=1080,
            periods_shown=60,
            indicators_included=['SMA']
        )
        mock_weekly_chart = ChartResult(
            symbol=SYMBOL,
            timeframe=Timeframe.WEEKLY,
            file_path='/tmp/charts/weekly.png',
            width=1440,
            height=900,
            periods_shown=52,
            indicators_included=['SMA']
        )
        mock_portfolio = Portfolio(
            account_id='U1234567', total_value=100000.0, cash_balance=50000.0,
            total_market_value=50000.0, total_unrealized_pnl=1000.0, position_count=1,
            positions=[Position(symbol=SYMBOL, quantity=POSITION_SIZE, average_cost=90.0,
                                current_price=100.0, market_value=1000.0, unrealized_pnl=100.0,
                                unrealized_pnl_percent=10.0)]
        )
        def xcom_pull_side_effect(task_ids=None, key=None):
            lookup = {
                ('fetch_market_data', 'market_data'): mock_market_data.model_dump_json(),
                ('analyze_with_llm', 'trading_signal'): mock_signal.model_dump_json(),
                ('generate_daily_chart', 'daily_chart'): mock_daily_chart.model_dump_json(),
                ('generate_weekly_chart', 'weekly_chart'): mock_weekly_chart.model_dump_json(),
                ('get_portfolio', 'portfolio'): mock_portfolio.model_dump_json(),
                ('place_order', 'order_placed'): True,
                ('generate_daily_chart', 'daily_chart_artifact_id'): 201,
                ('generate_weekly_chart', 'weekly_chart_artifact_id'): 202,
                ('analyze_with_llm', 'llm_artifact_id'): 301,
                ('analyze_with_llm', 'signal_artifact_id'): 302,
            }
            return lookup.get((task_ids, key))

        self.mock_context['task_instance'].xcom_pull.side_effect = xcom_pull_side_effect

        mock_tracker = MagicMock()
        mock_tracker.run_id = 'mlflow_run_id_123'
        mock_tracker.experiment_id = 'exp_456'
        mock_mlflow_run_context.return_value.__enter__.return_value = mock_tracker

        result = log_to_mlflow_task(**self.mock_context)

        mock_mlflow_run_context.assert_called_once()
        mock_tracker.log_params.assert_called_once()
        mock_tracker.log_metrics.assert_called_once()
        self.assertGreaterEqual(mock_tracker.log_artifact_dict.call_count, 2)
        mock_attach_lineage.assert_called_once_with(
            [201, 202, 301, 302],
            'mlflow_run_id_123',
            'exp_456'
        )
        self.assertEqual(result['mlflow_run_id'], 'mlflow_run_id_123')

if __name__ == '__main__':
    unittest.main()
