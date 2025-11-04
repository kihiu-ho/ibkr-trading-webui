"""Market open sensor."""
import logging
from datetime import datetime, time as dt_time
from typing import Dict, Any
import pytz
from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import apply_defaults
from ibkr_plugin.hooks.config_loader import config_loader


logger = logging.getLogger(__name__)


class MarketOpenSensor(BaseSensorOperator):
    """
    Sensor to check if the market is open.
    
    This sensor:
    1. Checks current time against market hours
    2. Validates trading day (Monday-Friday)
    3. Returns True if market is open
    """
    
    ui_color = '#2196F3'
    
    @apply_defaults
    def __init__(
        self,
        market_config: Dict[str, Any] = None,
        *args,
        **kwargs
    ):
        """
        Initialize market open sensor.
        
        Args:
            market_config: Optional market configuration.
                          Defaults to config file.
        """
        super().__init__(*args, **kwargs)
        
        if market_config is None:
            market_config = config_loader.get_market_config()
        
        self.market_config = market_config
        
        # Parse trading hours
        trading_hours = market_config.get('trading_hours', {})
        self.market_open_time = self._parse_time(trading_hours.get('start', '09:30'))
        self.market_close_time = self._parse_time(trading_hours.get('end', '16:00'))
        
        # Get timezone
        tz_str = trading_hours.get('timezone', 'America/New_York')
        self.timezone = pytz.timezone(tz_str)
        
        # Get trading days (1=Monday, 5=Friday)
        self.trading_days = market_config.get('trading_days', [1, 2, 3, 4, 5])
    
    def _parse_time(self, time_str: str) -> dt_time:
        """Parse time string to time object."""
        hour, minute = map(int, time_str.split(':'))
        return dt_time(hour, minute)
    
    def poke(self, context: Dict[str, Any]) -> bool:
        """
        Check if market is currently open.
        
        Args:
            context: Airflow context
            
        Returns:
            True if market is open, False otherwise
        """
        # Get current time in market timezone
        now = datetime.now(self.timezone)
        current_time = now.time()
        current_weekday = now.isoweekday()  # 1=Monday, 7=Sunday
        
        # Check if it's a trading day
        if current_weekday not in self.trading_days:
            logger.info(
                f"Not a trading day: {now.strftime('%A')} "
                f"(weekday {current_weekday})"
            )
            return False
        
        # Check if within trading hours
        is_open = self.market_open_time <= current_time < self.market_close_time
        
        if is_open:
            logger.info(
                f"Market is OPEN: {current_time.strftime('%H:%M')} "
                f"(hours: {self.market_open_time.strftime('%H:%M')}-"
                f"{self.market_close_time.strftime('%H:%M')})"
            )
        else:
            logger.info(
                f"Market is CLOSED: {current_time.strftime('%H:%M')} "
                f"(hours: {self.market_open_time.strftime('%H:%M')}-"
                f"{self.market_close_time.strftime('%H:%M')})"
            )
        
        return is_open

