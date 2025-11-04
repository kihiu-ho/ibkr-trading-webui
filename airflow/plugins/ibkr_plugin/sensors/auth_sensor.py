"""IBKR authentication sensor."""
import logging
from typing import Dict, Any
from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import apply_defaults
from ibkr_plugin.hooks.ibkr_hook import IBKRHook


logger = logging.getLogger(__name__)


class IBKRAuthSensor(BaseSensorOperator):
    """
    Sensor to check IBKR authentication status.
    
    This sensor:
    1. Checks if IBKR session is valid
    2. Attempts reauthentication if needed
    3. Returns True when authenticated
    """
    
    ui_color = '#9C27B0'
    
    @apply_defaults
    def __init__(
        self,
        attempt_reauth: bool = True,
        *args,
        **kwargs
    ):
        """
        Initialize authentication sensor.
        
        Args:
            attempt_reauth: Whether to attempt reauthentication
        """
        super().__init__(*args, **kwargs)
        self.attempt_reauth = attempt_reauth
        self._reauth_attempted = False
    
    def poke(self, context: Dict[str, Any]) -> bool:
        """
        Check authentication status.
        
        Args:
            context: Airflow context
            
        Returns:
            True if authenticated, False otherwise
        """
        ibkr_hook = IBKRHook()
        
        try:
            # Check auth status
            auth_status = ibkr_hook.check_auth_status()
            
            is_authenticated = auth_status.get('authenticated', False)
            is_connected = auth_status.get('connected', False)
            
            if is_authenticated and is_connected:
                logger.info("IBKR is authenticated and connected")
                self._reauth_attempted = False  # Reset flag
                return True
            
            logger.warning(
                f"IBKR not authenticated: "
                f"authenticated={is_authenticated}, connected={is_connected}"
            )
            
            # Attempt reauthentication if enabled and not already attempted
            if self.attempt_reauth and not self._reauth_attempted:
                logger.info("Attempting reauthentication...")
                try:
                    reauth_result = ibkr_hook.reauthenticate()
                    self._reauth_attempted = True
                    
                    if reauth_result.get('success'):
                        logger.info("Reauthentication initiated successfully")
                        # Don't return True yet, wait for next poke to verify
                    else:
                        logger.error(f"Reauthentication failed: {reauth_result}")
                        
                except Exception as e:
                    logger.error(f"Error during reauthentication: {e}")
                    self._reauth_attempted = True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking auth status: {e}")
            return False
        finally:
            ibkr_hook.close()

