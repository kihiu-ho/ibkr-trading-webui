"""Hook for IBKR API interaction via backend service."""
import httpx
import logging
from typing import Dict, Any, List, Optional
from airflow.hooks.base import BaseHook
from ibkr_plugin.hooks.config_loader import config_loader


logger = logging.getLogger(__name__)


class IBKRHook(BaseHook):
    """Hook for interacting with IBKR via backend API."""
    
    def __init__(self):
        """Initialize IBKR hook."""
        super().__init__()
        backend_config = config_loader.get_backend_config()
        self.base_url = backend_config.get('base_url', 'http://backend:8000')
        self.timeout = backend_config.get('timeout', 30)
        self.retry_attempts = backend_config.get('retry_attempts', 3)
        self.retry_delay = backend_config.get('retry_delay', 5)
        self.client = None
    
    def get_conn(self) -> httpx.Client:
        """Get HTTP client connection."""
        if self.client is None:
            self.client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                verify=False  # IBKR Gateway uses self-signed cert
            )
        return self.client
    
    def close(self):
        """Close HTTP client connection."""
        if self.client:
            self.client.close()
            self.client = None
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response JSON data
            
        Raises:
            httpx.HTTPError: If request fails after retries
        """
        client = self.get_conn()
        url = f"/api{endpoint}" if not endpoint.startswith('/api') else endpoint
        
        for attempt in range(self.retry_attempts):
            try:
                response = client.request(method, url, **kwargs)
                response.raise_for_status()
                
                # Handle empty responses
                if response.content:
                    return response.json()
                else:
                    return {}
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error on attempt {attempt + 1}: {e}")
                if attempt == self.retry_attempts - 1:
                    raise
                # Wait before retry
                import time
                time.sleep(self.retry_delay * (attempt + 1))
                
            except httpx.RequestError as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == self.retry_attempts - 1:
                    raise
                import time
                time.sleep(self.retry_delay * (attempt + 1))
        
        raise Exception("Max retries exceeded")
    
    # IBKR Authentication
    def check_auth_status(self) -> Dict[str, Any]:
        """Check IBKR authentication status."""
        logger.info("Checking IBKR authentication status")
        return self._request("GET", "/ibkr/auth/status")
    
    def reauthenticate(self) -> Dict[str, Any]:
        """Trigger reauthentication."""
        logger.info("Triggering IBKR reauthentication")
        return self._request("POST", "/ibkr/auth/login")
    
    # Market Data
    def get_market_data(
        self,
        symbols: List[str],
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch market data for symbols.
        
        Args:
            symbols: List of symbols to fetch
            fields: Optional list of fields to retrieve
            
        Returns:
            Market data dictionary
        """
        logger.info(f"Fetching market data for {len(symbols)} symbols")
        
        # First, search for contracts
        contracts = {}
        for symbol in symbols:
            result = self._request(
                "GET",
                "/ibkr/contracts/search",
                params={"symbol": symbol}
            )
            if result:
                contracts[symbol] = result[0] if isinstance(result, list) else result
        
        # Then fetch market data snapshots
        if fields is None:
            fields = ["31", "84", "86"]  # last, bid, ask
        
        conids = [c.get("conid") for c in contracts.values() if c.get("conid")]
        
        if not conids:
            logger.warning(f"No valid contract IDs found for symbols: {symbols}")
            return {}
        
        market_data = self._request(
            "GET",
            "/ibkr/market-data/snapshot",
            params={
                "conids": ",".join(str(c) for c in conids),
                "fields": ",".join(fields)
            }
        )
        
        return {
            "contracts": contracts,
            "market_data": market_data
        }
    
    def get_historical_data(
        self,
        symbol: str,
        period: str = "1y",
        bar: str = "1d"
    ) -> Dict[str, Any]:
        """
        Get historical market data for a symbol.
        
        Args:
            symbol: Symbol to fetch
            period: Time period (e.g., "1y", "6m")
            bar: Bar size (e.g., "1d", "1h")
            
        Returns:
            Historical data dictionary
        """
        logger.info(f"Fetching historical data for {symbol}: {period}, {bar}")
        
        # Search for contract
        contracts = self._request(
            "GET",
            "/ibkr/contracts/search",
            params={"symbol": symbol}
        )
        
        if not contracts:
            raise ValueError(f"Contract not found for symbol: {symbol}")
        
        conid = contracts[0].get("conid") if isinstance(contracts, list) else contracts.get("conid")
        
        # Fetch historical data
        historical_data = self._request(
            "GET",
            f"/ibkr/market-data/history",
            params={
                "conid": conid,
                "period": period,
                "bar": bar
            }
        )
        
        return historical_data
    
    # Orders
    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "MKT",
        price: Optional[float] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Place an order.
        
        Args:
            symbol: Symbol to trade
            side: BUY or SELL
            quantity: Order quantity
            order_type: Order type (MKT, LMT, etc.)
            price: Limit price (for LMT orders)
            account_id: Optional account ID
            
        Returns:
            Order placement response
        """
        logger.info(f"Placing {side} order: {quantity} {symbol} @ {order_type}")
        
        # Search for contract
        contracts = self._request(
            "GET",
            "/ibkr/contracts/search",
            params={"symbol": symbol}
        )
        
        if not contracts:
            raise ValueError(f"Contract not found for symbol: {symbol}")
        
        conid = contracts[0].get("conid") if isinstance(contracts, list) else contracts.get("conid")
        
        # Place order
        order_data = {
            "conid": conid,
            "side": side.upper(),
            "quantity": quantity,
            "order_type": order_type
        }
        
        if order_type == "LMT" and price is not None:
            order_data["price"] = price
        
        if account_id:
            order_data["account_id"] = account_id
        
        result = self._request(
            "POST",
            "/ibkr/orders",
            json=order_data
        )
        
        return result
    
    # Portfolio
    def get_portfolio_positions(
        self,
        account_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get portfolio positions.
        
        Args:
            account_id: Optional account ID
            
        Returns:
            List of positions
        """
        logger.info("Fetching portfolio positions")
        
        params = {}
        if account_id:
            params["account_id"] = account_id
        
        result = self._request("GET", "/ibkr/portfolio/positions", params=params)
        
        return result if isinstance(result, list) else []
    
    def get_accounts(self) -> List[str]:
        """Get list of accounts."""
        logger.info("Fetching account list")
        result = self._request("GET", "/ibkr/auth/accounts")
        
        if isinstance(result, dict):
            return result.get("accounts", [])
        elif isinstance(result, list):
            return result
        else:
            return []
    
    # Strategies
    def get_strategy(self, strategy_id: int) -> Dict[str, Any]:
        """Get strategy configuration from database."""
        logger.info(f"Fetching strategy {strategy_id}")
        return self._request("GET", f"/strategies/{strategy_id}")
    
    def get_active_strategies(self) -> List[Dict[str, Any]]:
        """Get all active strategies."""
        logger.info("Fetching active strategies")
        result = self._request("GET", "/strategies", params={"active": "true"})
        return result if isinstance(result, list) else []
    
    # Signals
    def save_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a trading signal to database."""
        logger.info(f"Saving signal for strategy {signal_data.get('strategy_id')}")
        return self._request("POST", "/signals", json=signal_data)
    
    def get_latest_signal(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """Get latest signal for a strategy."""
        logger.info(f"Fetching latest signal for strategy {strategy_id}")
        result = self._request(
            "GET",
            f"/signals/latest",
            params={"strategy_id": strategy_id}
        )
        return result if result else None

