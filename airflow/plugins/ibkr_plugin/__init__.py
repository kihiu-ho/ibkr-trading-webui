"""IBKR Airflow Plugin for trading workflow orchestration."""

from airflow.plugins_manager import AirflowPlugin
from ibkr_plugin.hooks.ibkr_hook import IBKRHook
from ibkr_plugin.hooks.config_loader import ConfigLoader
from ibkr_plugin.hooks.mlflow_tracker import MLflowTracker
from ibkr_plugin.operators.market_data_operator import IBKRMarketDataOperator
from ibkr_plugin.operators.signal_operator import LLMSignalGeneratorOperator
from ibkr_plugin.operators.order_operator import OrderPlacementOperator
from ibkr_plugin.sensors.market_sensor import MarketOpenSensor
from ibkr_plugin.sensors.auth_sensor import IBKRAuthSensor


class IBKRTradingPlugin(AirflowPlugin):
    """Plugin for IBKR trading workflows."""
    
    name = "ibkr_trading"
    hooks = [IBKRHook]
    operators = [
        IBKRMarketDataOperator,
        LLMSignalGeneratorOperator,
        OrderPlacementOperator,
    ]
    sensors = [MarketOpenSensor, IBKRAuthSensor]

