"""
IBKR Gateway client for market data, orders, trades, and portfolio
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal
import asyncio

try:
    import ib_insync as ib_insync_module
    from ib_insync import IB, Stock, MarketOrder, LimitOrder, util
    IB_AVAILABLE = True
    IB_VERSION = getattr(ib_insync_module, "__version__", "unknown")
except ImportError:
    IB_AVAILABLE = False
    IB_VERSION = None
    logging.warning("ib_insync not installed. IBKR integration will be mocked.")

from models.market_data import MarketData, OHLCVBar
from models.order import Order, OrderType, OrderSide, OrderStatus
from models.trade import Trade, TradeExecution
from models.portfolio import Portfolio, Position
from utils.config import config as workflow_config
from utils.ibkr_marketdata_api import IBKRMarketDataAPI

logger = logging.getLogger(__name__)
DEFAULT_STRICT_MODE = getattr(workflow_config, 'ibkr_strict_mode', False) if workflow_config else False


class IBKRClient:
    """Client for IBKR Gateway integration"""
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 4001,
        client_id: int = 1,
        strict_mode: Optional[bool] = None
    ):
        """
        Initialize IBKR client
        
        Args:
            host: IBKR Gateway host
            port: IBKR Gateway port (4001 for live, 4002 for paper)
            client_id: Client ID for connection
            strict_mode: When true, missing dependencies or connection failures raise immediately
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib: Optional[IB] = None
        self.connected = False
        self.strict_mode = DEFAULT_STRICT_MODE if strict_mode is None else strict_mode
        self.runtime_metadata = {
            'strict_mode': self.strict_mode,
            'gateway_host': self.host,
            'gateway_port': self.port,
            'ib_insync_available': IB_AVAILABLE,
            'ib_insync_version': IB_VERSION,
        }
        
        # Initialize REST client
        self.rest_client = IBKRMarketDataAPI(
            base_url=workflow_config.ibkr_api_base_url,
            verify_ssl=workflow_config.ibkr_api_verify_ssl,
            timeout=workflow_config.ibkr_api_timeout
        )
        
        if not IB_AVAILABLE:
            if self.rest_client.is_configured():
                logger.info("ib_insync not available - using IBKR REST API")
            else:
                logger.warning("Running in MOCK mode - ib_insync not available and REST API not configured")
    
    def connect(self):
        """Connect to IBKR Gateway"""
        self._ensure_dependency_available()
        if not IB_AVAILABLE:
            if self.rest_client.is_configured():
                logger.info("Using IBKR REST API (ib_insync missing)")
                self.connected = True
                self.runtime_metadata['connection_mode'] = 'rest'
                return
                
            logger.info("MOCK: Simulating IBKR connection (ib_insync missing)")
            self.connected = True
            self.runtime_metadata['connection_mode'] = 'mock'
            return
        
        try:
            self.ib = IB()
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            self.runtime_metadata['connection_mode'] = 'ibkr'
            logger.info(f"Connected to IBKR Gateway at {self.host}:{self.port}")
            if self.strict_mode:
                logger.info("Strict mode active - ib_insync version %s", IB_VERSION or "unknown")
        except Exception as e:
            logger.warning(f"Failed to connect to IBKR Gateway at {self.host}:{self.port}: {e}")
            logger.info("Falling back to MOCK mode")
            if self.strict_mode:
                raise RuntimeError(
                    f"Strict mode IBKR connection failed ({self.host}:{self.port}). "
                    "Install and configure ib_insync / IB Gateway before retrying."
                ) from e
            self.connected = True  # Enable mock mode
            self.ib = None  # Don't use real IB connection
            self.runtime_metadata['connection_mode'] = 'mock'
    
    def disconnect(self):
        """Disconnect from IBKR Gateway"""
        if self.ib and self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR Gateway")
    
    def fetch_market_data(
        self,
        symbol: str,
        exchange: str = "SMART",
        duration: str = "200 D",
        bar_size: str = "1 day"
    ) -> MarketData:
        """
        Fetch historical market data from IBKR
        
        Args:
            symbol: Stock symbol
            exchange: Exchange (SMART, NASDAQ, NYSE)
            duration: How far back to fetch (e.g., "200 D", "52 W")
            bar_size: Bar size (e.g., "1 day", "1 hour")
            
        Returns:
            MarketData with validated OHLCV bars
        """
        if not self.connected:
            self.connect()
        
        if not IB_AVAILABLE or self.ib is None:
            # Try REST API first
            if self.rest_client.is_configured():
                return self._fetch_via_rest(symbol, duration, bar_size)
                
            # Mock data for testing
            return self._mock_market_data(symbol, exchange)
        
        try:
            # Create contract
            contract = Stock(symbol, exchange, 'USD')
            
            # Request historical data
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )
            
            # Convert to OHLCVBar objects
            ohlcv_bars = []
            for bar in bars:
                ohlcv_bar = OHLCVBar(
                    timestamp=bar.date,
                    open=Decimal(str(bar.open)),
                    high=Decimal(str(bar.high)),
                    low=Decimal(str(bar.low)),
                    close=Decimal(str(bar.close)),
                    volume=int(bar.volume)
                )
                ohlcv_bars.append(ohlcv_bar)
            
            # Create and validate MarketData
            market_data = MarketData(
                symbol=symbol,
                exchange=exchange,
                bars=ohlcv_bars,
                timeframe=bar_size,
                fetched_at=datetime.utcnow()
            )
            
            logger.info(f"Fetched {len(ohlcv_bars)} bars for {symbol}")
            return market_data
        
        except Exception as e:
            logger.error(f"Failed to fetch market data for {symbol}: {e}")
            raise
    
    def _fetch_via_rest(self, symbol: str, duration: str, bar_size: str) -> MarketData:
        """Fetch market data via REST API"""
        logger.info(f"Fetching market data for {symbol} via REST API")
        
        try:
            # Resolve conid
            conid = self.rest_client.resolve_conid(symbol, preferred_conid=workflow_config.ibkr_primary_conid)
            if not conid:
                raise ValueError(f"Could not resolve conid for {symbol}")
            
            # Convert parameters
            period = self._convert_duration_to_period(duration)
            bar = self._convert_bar_size_to_bar(bar_size)
            
            # Fetch data
            response = self.rest_client.fetch_historical_bars(
                conid=conid,
                period=period,
                bar=bar
            )
            
            # Parse response
            return self._parse_rest_response(symbol, response, bar_size)
            
        except Exception as e:
            logger.error(f"Failed to fetch market data via REST: {e}")
            if self.strict_mode:
                raise
            logger.warning("Falling back to MOCK data due to REST failure")
            return self._mock_market_data(symbol, "SMART")

    def _convert_duration_to_period(self, duration: str) -> str:
        """Convert '200 D' to '1y' etc"""
        # Simple mapping for now
        d = duration.lower().replace(' ', '')
        if 'd' in d:
            days = int(''.join(filter(str.isdigit, d)))
            if days <= 1: return '1d'
            if days <= 7: return '1w'
            if days <= 30: return '1m'
            if days <= 180: return '6m'
            if days <= 365: return '1y'
            return '5y'
        if 'y' in d:
            return d
        return '1y'

    def _convert_bar_size_to_bar(self, bar_size: str) -> str:
        """Convert '1 day' to '1d' etc"""
        b = bar_size.lower().replace(' ', '')
        if 'day' in b or 'd' in b:
            return '1d'
        if 'hour' in b or 'h' in b:
            return '1h'
        if 'min' in b or 'm' in b:
            return '5min' # Default to 5min for minutes
        return '1d'

    def _parse_rest_response(self, symbol: str, response: dict, bar_size: str) -> MarketData:
        """Parse REST API response to MarketData"""
        bars = []
        data = response.get('data', []) or response.get('bars', [])
        
        for entry in data:
            try:
                # Timestamp is in ms
                ts = datetime.utcfromtimestamp(int(entry['t']) / 1000)
                
                bar = OHLCVBar(
                    timestamp=ts,
                    open=Decimal(str(entry['o'])),
                    high=Decimal(str(entry['h'])),
                    low=Decimal(str(entry['l'])),
                    close=Decimal(str(entry['c'])),
                    volume=int(float(entry.get('v', 0)))
                )
                bars.append(bar)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Skipping malformed bar: {entry} ({e})")
                continue
        
        if not bars:
            raise ValueError("No valid bars returned from REST API")
            
        return MarketData(
            symbol=symbol,
            exchange="SMART",
            bars=bars,
            timeframe=bar_size,
            fetched_at=datetime.utcnow()
        )
    
    def _mock_market_data(self, symbol: str, exchange: str) -> MarketData:
        """Generate mock market data for testing"""
        logger.info(f"MOCK: Generating market data for {symbol}")
        
        bars = []
        base_price = Decimal("250.00")
        
        for i in range(200):
            date = datetime.utcnow() - timedelta(days=200-i)
            # Simple random walk
            change = Decimal(str((i % 10 - 5) * 0.5))
            price = base_price + change
            
            bar = OHLCVBar(
                timestamp=date,
                open=price,
                high=price + Decimal("2.50"),
                low=price - Decimal("2.00"),
                close=price + Decimal("0.50"),
                volume=1000000 + (i * 10000)
            )
            bars.append(bar)
        
        return MarketData(
            symbol=symbol,
            exchange=exchange,
            bars=bars,
            timeframe="1 day",
            fetched_at=datetime.utcnow()
        )
    
    def place_order(self, order: Order) -> Order:
        """
        Place order to IBKR
        
        Args:
            order: Order to place
            
        Returns:
            Updated order with IBKR order ID and status
        """
        if not self.connected:
            self.connect()
        
        if not IB_AVAILABLE or self.ib is None:
            if self.rest_client.is_configured():
                return self._place_order_via_rest(order)
            return self._mock_place_order(order)
        
        try:
            # Create contract
            contract = Stock(order.symbol, 'SMART', 'USD')
            
            # Create IB order
            if order.order_type == OrderType.MARKET:
                ib_order = MarketOrder(
                    action=order.side.value,
                    totalQuantity=order.quantity
                )
            elif order.order_type == OrderType.LIMIT:
                ib_order = LimitOrder(
                    action=order.side.value,
                    totalQuantity=order.quantity,
                    lmtPrice=float(order.limit_price)
                )
            else:
                raise ValueError(f"Order type {order.order_type} not yet supported")
            
            # Place order
            trade = self.ib.placeOrder(contract, ib_order)
            
            # Update order
            order.order_id = str(trade.order.orderId)
            order.status = OrderStatus.SUBMITTED
            order.submitted_at = datetime.utcnow()
            
            logger.info(f"Placed {order.side} order for {order.quantity} {order.symbol} (ID: {order.order_id})")
            return order
        
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            order.status = OrderStatus.REJECTED
            raise
    
    def _place_order_via_rest(self, order: Order) -> Order:
        """Place order via REST API"""
        try:
            # Get account ID
            account_id = self._get_account_id()
            
            # Resolve conid
            conid = self.rest_client.resolve_conid(order.symbol, preferred_conid=workflow_config.ibkr_primary_conid)
            if not conid:
                raise ValueError(f"Could not resolve conid for {order.symbol}")
            
            # Construct payload
            order_payload = {
                "conid": conid,
                "orderType": order.order_type.value,
                "side": order.side.value,
                "quantity": float(order.quantity),
                "tif": "DAY",
                "outsideRTH": True
            }
            
            if order.order_type == OrderType.LIMIT:
                if not order.limit_price:
                    raise ValueError("Limit price required for LIMIT order")
                order_payload["price"] = float(order.limit_price)
            
            # Place order
            response = self.rest_client.place_order(account_id, order_payload)
            
            # Parse response (list of order status dicts)
            if response and isinstance(response, list):
                order_status = response[0]
                order.order_id = str(order_status.get("order_id") or order_status.get("id"))
                order.status = OrderStatus.SUBMITTED
                order.submitted_at = datetime.utcnow()
                logger.info(f"Placed REST order {order.order_id} for {order.symbol}")
                return order
            
            raise RuntimeError(f"Unexpected REST response: {response}")
            
        except Exception as e:
            logger.error(f"Failed to place REST order: {e}")
            order.status = OrderStatus.REJECTED
            raise

    def _get_account_id(self) -> str:
        """Helper to get first available account ID"""
        accounts = self.rest_client.get_accounts()
        if not accounts:
            raise RuntimeError("No accounts found via REST API")
        return accounts[0].get("id") or accounts[0].get("accountId")
    
    def _mock_place_order(self, order: Order) -> Order:
        """Mock order placement"""
        logger.info(f"MOCK: Placing {order.side} order for {order.quantity} {order.symbol}")
        
        order.order_id = f"MOCK_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        order.status = OrderStatus.SUBMITTED
        order.submitted_at = datetime.utcnow()
        
        return order
    
    def get_trades(self, order_id: str) -> List[Trade]:
        """
        Get trade executions for an order
        
        Args:
            order_id: Order ID to fetch trades for
            
        Returns:
            List of Trade objects
        """
        if not self.connected:
            self.connect()
        
        if not IB_AVAILABLE or self.ib is None:
            if self.rest_client.is_configured():
                return self._get_trades_via_rest(order_id)
            return self._mock_get_trades(order_id)
        
        try:
            # Get all fills
            fills = self.ib.fills()
            
            # Filter by order ID
            order_fills = [f for f in fills if str(f.contract.orderId) == order_id]
            
            if not order_fills:
                return []
            
            # Group by order
            executions = []
            for fill in order_fills:
                execution = TradeExecution(
                    execution_id=fill.execution.execId,
                    order_id=order_id,
                    symbol=fill.contract.symbol,
                    side=fill.execution.side,
                    quantity=fill.execution.shares,
                    price=Decimal(str(fill.execution.price)),
                    commission=Decimal(str(fill.commissionReport.commission)),
                    executed_at=fill.time
                )
                executions.append(execution)
            
            # Create Trade
            if executions:
                trade = Trade(
                    order_id=order_id,
                    symbol=executions[0].symbol,
                    side=executions[0].side,
                    total_quantity=sum(e.quantity for e in executions),
                    average_price=sum(e.price * Decimal(e.quantity) for e in executions) / sum(Decimal(e.quantity) for e in executions),
                    total_commission=sum(e.commission for e in executions),
                    executions=executions,
                    first_execution_at=min(e.executed_at for e in executions),
                    last_execution_at=max(e.executed_at for e in executions)
                )
                return [trade]
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get trades for order {order_id}: {e}")
            return []

    def _get_trades_via_rest(self, order_id: str) -> List[Trade]:
        """Get trades via REST API (approximated from orders)"""
        try:
            orders = self.rest_client.get_orders()
            target_order = next((o for o in orders if str(o.get("orderId")) == order_id), None)
            
            if not target_order:
                return []
            
            # Check if filled
            status = target_order.get("status")
            if status != "Filled":
                return []
            
            # Create synthetic trade execution
            # REST API orders endpoint doesn't give full execution details per fill, 
            # so we approximate from the order status
            filled_qty = Decimal(str(target_order.get("filledQuantity", 0)))
            avg_price = Decimal(str(target_order.get("avgPrice", 0)))
            
            if filled_qty == 0:
                return []
                
            execution = TradeExecution(
                execution_id=f"EXEC_{order_id}",
                order_id=order_id,
                symbol=target_order.get("symbol", ""),
                side=target_order.get("side", ""),
                quantity=float(filled_qty),
                price=avg_price,
                commission=Decimal("0"), # Commission not always available in order status
                executed_at=datetime.utcnow() # Timestamp not always available
            )
            
            trade = Trade(
                order_id=order_id,
                symbol=target_order.get("symbol", ""),
                side=target_order.get("side", ""),
                total_quantity=float(filled_qty),
                average_price=avg_price,
                total_commission=Decimal("0"),
                executions=[execution],
                first_execution_at=datetime.utcnow(),
                last_execution_at=datetime.utcnow()
            )
            
            return [trade]
            
        except Exception as e:
            logger.error(f"Failed to get trades via REST: {e}")
            return []
    
    def _mock_get_trades(self, order_id: str) -> List[Trade]:
        """Mock trade retrieval"""
        logger.info(f"MOCK: Getting trades for order {order_id}")
        
        execution = TradeExecution(
            execution_id=f"EXEC_{order_id}",
            order_id=order_id,
            symbol="TSLA",
            side="BUY",
            quantity=10,
            price=Decimal("250.50"),
            commission=Decimal("1.00"),
            executed_at=datetime.utcnow()
        )
        
        trade = Trade(
            order_id=order_id,
            symbol="TSLA",
            side="BUY",
            total_quantity=10,
            average_price=Decimal("250.50"),
            total_commission=Decimal("1.00"),
            executions=[execution],
            first_execution_at=datetime.utcnow(),
            last_execution_at=datetime.utcnow()
        )
        
        return [trade]
    
    def get_portfolio(self, account_id: Optional[str] = None) -> Portfolio:
        """
        Get current portfolio positions
        
        Args:
            account_id: Account ID (optional, uses default if not provided)
            
        Returns:
            Portfolio with current positions
        """
        if not self.connected:
            self.connect()
        
        if not IB_AVAILABLE or self.ib is None:
            if self.rest_client.is_configured():
                return self._get_portfolio_via_rest(account_id)
            return self._mock_get_portfolio(account_id or "DU123456")
        
        try:
            # Get account summary
            account_values = self.ib.accountSummary(account_id or '')
            
            # Extract cash balance and total value
            cash_balance = Decimal(0)
            total_value = Decimal(0)
            
            for item in account_values:
                if item.tag == 'TotalCashValue':
                    cash_balance = Decimal(item.value)
                elif item.tag == 'NetLiquidation':
                    total_value = Decimal(item.value)
            
            # Get positions
            positions = []
            for pos in self.ib.positions():
                # Get current price
                contract = pos.contract
                ticker = self.ib.reqMktData(contract)
                self.ib.sleep(1)  # Wait for price
                
                current_price = Decimal(str(ticker.marketPrice())) if ticker.marketPrice() else Decimal(str(pos.avgCost))
                
                market_value = Decimal(str(pos.position)) * current_price
                unrealized_pnl = market_value - (Decimal(str(pos.position)) * Decimal(str(pos.avgCost)))
                unrealized_pnl_percent = (unrealized_pnl / (Decimal(str(pos.position)) * Decimal(str(pos.avgCost)))) * Decimal(100)
                
                position = Position(
                    symbol=contract.symbol,
                    quantity=int(pos.position),
                    average_cost=Decimal(str(pos.avgCost)),
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=unrealized_pnl_percent
                )
                positions.append(position)
            
            total_market_value = sum(p.market_value for p in positions)
            total_unrealized_pnl = sum(p.unrealized_pnl for p in positions)
            
            portfolio = Portfolio(
                account_id=account_id or self.ib.wrapper.accounts[0],
                positions=positions,
                cash_balance=cash_balance,
                total_market_value=total_market_value,
                total_value=total_value,
                total_unrealized_pnl=total_unrealized_pnl
            )
            
            logger.info(f"Retrieved portfolio with {len(positions)} positions")
            return portfolio
        
        except Exception as e:
            logger.error(f"Failed to get portfolio: {e}")
            raise

    def _get_portfolio_via_rest(self, account_id: Optional[str]) -> Portfolio:
        """Get portfolio via REST API"""
        try:
            target_account = account_id or self._get_account_id()
            
            # Get summary
            summary = self.rest_client.get_portfolio_summary(target_account)
            # Get positions
            positions_data = self.rest_client.get_portfolio_positions(target_account)
            
            # Parse positions
            positions = []
            for pos in positions_data:
                try:
                    p = Position(
                        symbol=pos.get("contractDesc") or pos.get("symbol"),
                        quantity=int(float(pos.get("position", 0))),
                        average_cost=Decimal(str(pos.get("avgCost", 0))),
                        current_price=Decimal(str(pos.get("mktPrice", 0))),
                        market_value=Decimal(str(pos.get("mktValue", 0))),
                        unrealized_pnl=Decimal(str(pos.get("unrealizedPnl", 0))),
                        unrealized_pnl_percent=Decimal("0") # Not directly provided
                    )
                    positions.append(p)
                except Exception as e:
                    logger.warning(f"Skipping malformed position: {e}")
                    continue
            
            # Parse summary (simplified)
            # REST API summary structure varies, we'll try to extract key fields
            total_cash = Decimal("0")
            net_liquidation = Decimal("0")
            
            if isinstance(summary, dict):
                # This depends on the specific endpoint response structure
                # Often it's a list of keys/values or a dict
                pass 
                
            return Portfolio(
                account_id=target_account,
                positions=positions,
                cash_balance=total_cash,
                total_market_value=sum(p.market_value for p in positions),
                total_value=net_liquidation,
                total_unrealized_pnl=sum(p.unrealized_pnl for p in positions)
            )
            
        except Exception as e:
            logger.error(f"Failed to get portfolio via REST: {e}")
            raise
    
    def _mock_get_portfolio(self, account_id: str) -> Portfolio:
        """Mock portfolio retrieval"""
        logger.info(f"MOCK: Getting portfolio for {account_id}")
        
        position = Position(
            symbol="TSLA",
            quantity=10,
            average_cost=Decimal("250.50"),
            current_price=Decimal("255.00"),
            market_value=Decimal("2550.00"),
            unrealized_pnl=Decimal("45.00"),
            unrealized_pnl_percent=Decimal("1.80")
        )
        
        portfolio = Portfolio(
            account_id=account_id,
            positions=[position],
            cash_balance=Decimal("47450.00"),
            total_market_value=Decimal("2550.00"),
            total_value=Decimal("50000.00"),
            total_unrealized_pnl=Decimal("45.00")
        )
        
        return portfolio
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def _ensure_dependency_available(self) -> None:
        """Fail fast in strict mode when ib_insync is missing."""
        if self.strict_mode and not IB_AVAILABLE:
            raise RuntimeError(
                "IBKR strict mode requires ib_insync to be installed inside the Airflow runtime. "
                "Install it via airflow/requirements-airflow.txt or disable strict mode for development."
            )

    def get_metadata(self) -> dict:
        """Return runtime metadata for logging/telemetry."""
        return {**self.runtime_metadata, 'connected': self.connected}
