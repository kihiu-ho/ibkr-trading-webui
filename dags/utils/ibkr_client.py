"""
IBKR Gateway client for market data, orders, trades, and portfolio
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal
import asyncio

try:
    from ib_insync import IB, Stock, MarketOrder, LimitOrder, util
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    logging.warning("ib_insync not installed. IBKR integration will be mocked.")

from models.market_data import MarketData, OHLCVBar
from models.order import Order, OrderType, OrderSide, OrderStatus
from models.trade import Trade, TradeExecution
from models.portfolio import Portfolio, Position

logger = logging.getLogger(__name__)


class IBKRClient:
    """Client for IBKR Gateway integration"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 4001, client_id: int = 1):
        """
        Initialize IBKR client
        
        Args:
            host: IBKR Gateway host
            port: IBKR Gateway port (4001 for live, 4002 for paper)
            client_id: Client ID for connection
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib: Optional[IB] = None
        self.connected = False
        
        if not IB_AVAILABLE:
            logger.warning("Running in MOCK mode - ib_insync not available")
    
    def connect(self):
        """Connect to IBKR Gateway"""
        if not IB_AVAILABLE:
            logger.info("MOCK: Simulating IBKR connection")
            self.connected = True
            return
        
        try:
            self.ib = IB()
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            logger.info(f"Connected to IBKR Gateway at {self.host}:{self.port}")
        except Exception as e:
            logger.warning(f"Failed to connect to IBKR Gateway at {self.host}:{self.port}: {e}")
            logger.info("Falling back to MOCK mode")
            self.connected = True  # Enable mock mode
            self.ib = None  # Don't use real IB connection
    
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

