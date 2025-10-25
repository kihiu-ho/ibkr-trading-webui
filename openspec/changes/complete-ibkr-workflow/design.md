# Complete IBKR Trading Workflow - Detailed Design

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│  (Login → Search → Configure → Monitor → Manage Portfolio)  │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│  ┌──────────────┬──────────────┬────────────────────────┐  │
│  │ Auth Service │Symbol Service│ Strategy Service       │  │
│  ├──────────────┼──────────────┼────────────────────────┤  │
│  │Indicator Svc │  Prompt Svc  │ Chart Generator       │  │
│  ├──────────────┼──────────────┼────────────────────────┤  │
│  │  LLM Service │ Signal Gen   │ Order Manager         │  │
│  ├──────────────┼──────────────┼────────────────────────┤  │
│  │Portfolio Svc │Position Mgmt │ Risk Management       │  │
│  └──────────────┴──────────────┴────────────────────────┘  │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                      Celery Workers                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Strategy Execution Worker (Scheduled)                │  │
│  │ Chart Generation Worker                              │  │
│  │ LLM Analysis Worker                                  │  │
│  │ Order Placement Worker                               │  │
│  │ Portfolio Update Worker                              │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                    External Services                         │
│  ┌──────────┬──────────┬──────────┬──────────┬─────────┐  │
│  │ IBKR API │PostgreSQL│  Redis   │  MinIO   │ LLM API │  │
│  └──────────┴──────────┴──────────┴──────────┴─────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Complete Workflow Design

### Step 1: User Authentication & Login

**Flow**:
```
User → /ibkr/login → IBKR Gateway → Session Token → Backend → Database
```

**Components**:
- **Frontend**: `ibkr_login.html` (KEEP - already exists)
- **Backend**: `backend/api/ibkr_auth.py` (KEEP - already exists)
- **Service**: `backend/services/ibkr_service.py` (KEEP - enhance)
- **Database**: `users` table (session management)

**Implementation**:
```python
# backend/api/ibkr_auth.py
@router.post("/login")
async def login(credentials: IBKRCredentials):
    """
    1. Forward credentials to IBKR Gateway
    2. Receive session token
    3. Store token in database
    4. Return success + user info
    """
    session = await ibkr_service.authenticate(credentials)
    await db.store_session(session)
    return {"status": "authenticated", "session_id": session.id}
```

**Database Schema**:
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ibkr_session_token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
```

---

### Step 2: Symbol Search & Contract ID Lookup

**Flow**:
```
User Search → Backend → IBKR API → Search Results → Select Symbol → Get Conid
```

**Components**:
- **Frontend**: `symbols.html` (KEEP - already exists)
- **Backend**: `backend/api/symbols.py` (KEEP - enhance)
- **Service**: `backend/services/symbol_search.py` (NEW)
- **Database**: `symbols` table (cache search results)

**Implementation**:
```python
# backend/services/symbol_search.py
class SymbolSearchService:
    async def search_symbols(self, query: str) -> List[Symbol]:
        """
        Search IBKR for symbols matching query
        Returns: List of {symbol, conid, exchange, type}
        """
        # Check cache first
        cached = await self.cache.get(query)
        if cached:
            return cached
        
        # Call IBKR API
        results = await ibkr_api.search(query)
        
        # Cache results
        await self.cache.set(query, results, ttl=3600)
        
        # Store in database
        await db.upsert_symbols(results)
        
        return results
    
    async def get_contract_details(self, conid: int) -> ContractDetails:
        """
        Get full contract details from IBKR
        Returns: {conid, symbol, exchange, currency, etc.}
        """
        details = await ibkr_api.get_contract(conid)
        await db.store_contract(details)
        return details
```

**API Endpoints**:
```python
# backend/api/symbols.py
@router.get("/search")
async def search_symbols(q: str):
    """Search symbols by name/ticker"""
    return await symbol_service.search_symbols(q)

@router.get("/{conid}")
async def get_contract(conid: int):
    """Get contract details by conid"""
    return await symbol_service.get_contract_details(conid)
```

**Database Schema**:
```sql
CREATE TABLE symbols (
    id SERIAL PRIMARY KEY,
    conid INTEGER UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    name TEXT,
    exchange VARCHAR(20),
    currency VARCHAR(3),
    asset_type VARCHAR(20),
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_symbols_symbol ON symbols(symbol);
CREATE INDEX idx_symbols_conid ON symbols(conid);
```

---

### Step 3: Indicator Configuration

**Flow**:
```
User → Select Indicators → Configure Parameters → Save Configuration
```

**Components**:
- **Frontend**: `indicators.html` (KEEP - enhance)
- **Backend**: `backend/api/indicators.py` (KEEP - enhance)
- **Service**: `backend/services/indicator_service.py` (ENHANCE existing)
- **Database**: `indicators` table (already exists), `strategy_indicators` (already exists)

**Implementation**:
```python
# backend/services/indicator_service.py
class IndicatorService:
    AVAILABLE_INDICATORS = {
        "RSI": {"params": ["period"], "default": {"period": 14}},
        "MACD": {"params": ["fast", "slow", "signal"], "default": {"fast": 12, "slow": 26, "signal": 9}},
        "ATR": {"params": ["period"], "default": {"period": 14}},
        "SMA": {"params": ["period"], "default": {"period": 20}},
        "EMA": {"params": ["period"], "default": {"period": 20}},
        "BB": {"params": ["period", "std"], "default": {"period": 20, "std": 2}},
        "SUPERTREND": {"params": ["period", "multiplier"], "default": {"period": 10, "multiplier": 3}}
    }
    
    async def create_indicator_config(
        self,
        strategy_id: int,
        indicator_type: str,
        parameters: dict
    ) -> IndicatorConfig:
        """Create indicator configuration for strategy"""
        config = IndicatorConfig(
            strategy_id=strategy_id,
            indicator_type=indicator_type,
            parameters=parameters
        )
        await db.save_indicator_config(config)
        return config
    
    async def get_strategy_indicators(self, strategy_id: int) -> List[IndicatorConfig]:
        """Get all indicators configured for a strategy"""
        return await db.get_indicators_by_strategy(strategy_id)
```

**API Endpoints**:
```python
# backend/api/indicators.py
@router.get("/available")
async def list_available_indicators():
    """List all available indicators with parameters"""
    return indicator_service.AVAILABLE_INDICATORS

@router.post("/")
async def create_indicator(config: IndicatorCreate):
    """Create new indicator configuration"""
    return await indicator_service.create_indicator_config(
        strategy_id=config.strategy_id,
        indicator_type=config.type,
        parameters=config.parameters
    )

@router.get("/strategy/{strategy_id}")
async def get_strategy_indicators(strategy_id: int):
    """Get all indicators for a strategy"""
    return await indicator_service.get_strategy_indicators(strategy_id)
```

---

### Step 4: Prompt Setup

**Flow**:
```
User → Prompt Manager → Select/Create Prompt → Assign to Strategy
```

**Components**:
- **Frontend**: `prompts.html` (KEEP - Phase 8-9 implementation)
- **Backend**: `backend/api/prompts.py` (KEEP - Phase 4 implementation)
- **Service**: `backend/services/prompt_renderer.py` (KEEP - Phase 12 implementation)
- **Database**: `prompt_templates` table (KEEP - Phase 1 implementation)

**Implementation**: ✅ **Already Complete** (Phases 1-14)
- Use existing prompt system
- Strategy can reference prompt_template_id
- Supports global and strategy-specific prompts

**Integration**:
```python
# backend/models/strategy.py (enhance)
class Strategy:
    # ... existing fields ...
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"))
    prompt_template = relationship("PromptTemplate")
```

---

### Step 5: Strategy Creation

**Flow**:
```
User → Create Strategy → Select Symbol → Choose Indicators → Choose Prompt → Set Schedule → Save
```

**Components**:
- **Frontend**: `strategies.html` (KEEP - enhance)
- **Backend**: `backend/api/strategies.py` (KEEP - enhance)
- **Service**: `backend/services/strategy_service.py` (NEW)
- **Database**: `strategies` table (KEEP - enhance)

**Implementation**:
```python
# backend/services/strategy_service.py
class StrategyService:
    async def create_strategy(
        self,
        name: str,
        symbol_conid: int,
        indicator_ids: List[int],
        prompt_template_id: int,
        schedule: str,  # cron expression
        risk_params: RiskParameters
    ) -> Strategy:
        """
        Create complete trading strategy
        
        Args:
            name: Strategy name
            symbol_conid: IBKR contract ID
            indicator_ids: List of indicator configuration IDs
            prompt_template_id: Prompt template for LLM analysis
            schedule: Cron expression (e.g., "0 9 * * MON-FRI")
            risk_params: Risk management parameters
        
        Returns:
            Created strategy
        """
        strategy = Strategy(
            name=name,
            symbol_conid=symbol_conid,
            prompt_template_id=prompt_template_id,
            schedule=schedule,
            is_active=True,
            risk_params=risk_params.dict()
        )
        await db.save_strategy(strategy)
        
        # Link indicators
        for indicator_id in indicator_ids:
            await db.link_strategy_indicator(strategy.id, indicator_id)
        
        # Create Celery Beat schedule
        await self.create_celery_schedule(strategy)
        
        return strategy
    
    async def create_celery_schedule(self, strategy: Strategy):
        """Create Celery Beat schedule for strategy execution"""
        from celery import current_app
        
        current_app.conf.beat_schedule[f"strategy_{strategy.id}"] = {
            "task": "backend.tasks.execute_strategy",
            "schedule": crontab(**parse_cron(strategy.schedule)),
            "args": (strategy.id,)
        }
```

**API Endpoints**:
```python
# backend/api/strategies.py (enhance)
@router.post("/")
async def create_strategy(strategy: StrategyCreate):
    """Create new trading strategy"""
    return await strategy_service.create_strategy(
        name=strategy.name,
        symbol_conid=strategy.symbol_conid,
        indicator_ids=strategy.indicator_ids,
        prompt_template_id=strategy.prompt_template_id,
        schedule=strategy.schedule,
        risk_params=strategy.risk_params
    )

@router.get("/{strategy_id}/execution-history")
async def get_execution_history(strategy_id: int):
    """Get strategy execution history"""
    return await strategy_service.get_execution_history(strategy_id)
```

**Database Schema Enhancement**:
```sql
ALTER TABLE strategies ADD COLUMN schedule VARCHAR(100);  -- Cron expression
ALTER TABLE strategies ADD COLUMN symbol_conid INTEGER;
ALTER TABLE strategies ADD COLUMN prompt_template_id INTEGER REFERENCES prompt_templates(id);
ALTER TABLE strategies ADD COLUMN risk_params JSONB;  -- Stop loss, take profit, position size, etc.
ALTER TABLE strategies ADD COLUMN last_executed_at TIMESTAMP;
ALTER TABLE strategies ADD COLUMN next_execution_at TIMESTAMP;

CREATE INDEX idx_strategies_schedule ON strategies(next_execution_at) WHERE is_active = TRUE;
```

---

### Step 6: Scheduled Execution (Cron Jobs)

**Flow**:
```
Celery Beat → Trigger Strategy Execution → Execute Trading Logic → Record Results
```

**Components**:
- **Celery Beat**: Schedule management
- **Celery Worker**: `backend/tasks/strategy_execution.py` (NEW)
- **Service**: `backend/services/strategy_executor.py` (NEW)

**Implementation**:
```python
# backend/tasks/strategy_execution.py
from celery import shared_task

@shared_task(name="backend.tasks.execute_strategy")
def execute_strategy(strategy_id: int):
    """
    Execute a trading strategy (called by Celery Beat)
    
    Workflow:
    1. Load strategy configuration
    2. Fetch market data
    3. Generate charts
    4. Analyze with LLM
    5. Generate trading signal
    6. Place orders if signal present
    7. Update portfolio
    8. Record execution
    """
    from backend.services.strategy_executor import StrategyExecutor
    
    executor = StrategyExecutor()
    result = await executor.execute(strategy_id)
    
    return {
        "strategy_id": strategy_id,
        "executed_at": datetime.now().isoformat(),
        "signal": result.signal,
        "orders_placed": result.orders,
        "status": result.status
    }


# backend/services/strategy_executor.py
class StrategyExecutor:
    async def execute(self, strategy_id: int) -> ExecutionResult:
        """
        Execute complete strategy workflow
        """
        # 1. Load strategy
        strategy = await db.get_strategy(strategy_id)
        if not strategy.is_active:
            return ExecutionResult(status="skipped", reason="strategy_inactive")
        
        # 2. Fetch market data
        market_data = await self.fetch_market_data(strategy.symbol_conid)
        
        # 3. Calculate indicators
        indicator_values = await self.calculate_indicators(
            strategy.indicators,
            market_data
        )
        
        # 4. Generate charts
        charts = await self.generate_charts(
            market_data,
            indicator_values,
            strategy.symbol
        )
        
        # 5. Analyze with LLM
        analysis = await self.analyze_with_llm(
            charts=charts,
            prompt_template_id=strategy.prompt_template_id,
            context={
                "symbol": strategy.symbol,
                "indicators": indicator_values,
                "market_data": market_data
            }
        )
        
        # 6. Generate trading signal
        signal = await self.parse_signal(analysis)
        
        # 7. Place orders (if signal present)
        orders = []
        if signal.action == "BUY":
            order = await self.place_buy_order(strategy, signal)
            orders.append(order)
        elif signal.action == "SELL":
            order = await self.place_sell_order(strategy, signal)
            orders.append(order)
        
        # 8. Record execution
        await db.record_execution(
            strategy_id=strategy_id,
            signal=signal,
            orders=orders,
            analysis=analysis
        )
        
        # 9. Update next execution time
        await db.update_next_execution(strategy_id)
        
        return ExecutionResult(
            status="completed",
            signal=signal,
            orders=orders,
            analysis=analysis
        )
```

**Celery Beat Configuration**:
```python
# backend/celery_app.py (enhance)
from celery.schedules import crontab

app.conf.beat_schedule = {
    # ... existing schedules ...
    
    # Dynamic strategy schedules loaded from database
    # These are created when strategies are created/updated
}

# Load strategy schedules on startup
@app.on_after_configure.connect
def setup_strategy_schedules(sender, **kwargs):
    """Load all active strategy schedules from database"""
    strategies = db.get_active_strategies()
    for strategy in strategies:
        sender.add_periodic_task(
            crontab(**parse_cron(strategy.schedule)),
            execute_strategy.s(strategy.id),
            name=f"strategy_{strategy.id}"
        )
```

---

### Step 7: Chart Generation

**Flow**:
```
Market Data → Calculate Indicators → Generate Chart with mplfinance → Save to MinIO
```

**Components**:
- **Service**: `backend/services/chart_generator.py` (KEEP - enhance existing)
- **Storage**: MinIO (KEEP - already configured)

**Implementation**:
```python
# backend/services/chart_generator.py (enhance)
import mplfinance as mpf
import pandas as pd

class ChartGenerator:
    async def generate_strategy_charts(
        self,
        strategy_id: int,
        market_data: pd.DataFrame,
        indicators: Dict[str, pd.Series]
    ) -> List[str]:
        """
        Generate charts for strategy execution
        
        Returns: List of MinIO URLs for generated charts
        """
        charts = []
        
        # 1. Daily chart
        daily_chart = await self.generate_chart(
            data=market_data,
            indicators=indicators,
            timeframe="daily",
            title=f"Strategy {strategy_id} - Daily Chart"
        )
        daily_url = await self.upload_to_minio(daily_chart, f"strategy_{strategy_id}_daily.png")
        charts.append(daily_url)
        
        # 2. Weekly chart (if needed)
        if strategy.analyze_weekly:
            weekly_data = market_data.resample('W').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            })
            weekly_chart = await self.generate_chart(
                data=weekly_data,
                indicators=self.calculate_weekly_indicators(indicators),
                timeframe="weekly",
                title=f"Strategy {strategy_id} - Weekly Chart"
            )
            weekly_url = await self.upload_to_minio(weekly_chart, f"strategy_{strategy_id}_weekly.png")
            charts.append(weekly_url)
        
        return charts
    
    async def generate_chart(
        self,
        data: pd.DataFrame,
        indicators: Dict[str, pd.Series],
        timeframe: str,
        title: str
    ) -> bytes:
        """Generate chart image"""
        # Add indicators to plot
        addplot = []
        for name, series in indicators.items():
            addplot.append(mpf.make_addplot(series, panel=self._get_panel(name)))
        
        # Create chart
        fig, axes = mpf.plot(
            data,
            type='candle',
            style='charles',
            title=title,
            volume=True,
            addplot=addplot,
            returnfig=True,
            figratio=(16, 9),
            figscale=1.2
        )
        
        # Save to bytes
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        return buffer.getvalue()
```

---

### Step 8: LLM Signal Generation

**Flow**:
```
Charts → Load Prompt → Render with Context → Call LLM API → Parse Response → Generate Signal
```

**Components**:
- **Service**: `backend/services/signal_generator.py` (KEEP - Phase 7 implementation)
- **Prompt System**: Already implemented (Phases 1-14)
- **LLM Service**: `backend/services/llm_service.py` (KEEP - Phase 5 implementation)

**Implementation**: ✅ **Mostly Complete**
```python
# backend/services/signal_generator.py (enhance)
class SignalGenerator:
    async def generate_signal_from_charts(
        self,
        strategy_id: int,
        chart_urls: List[str],
        context: Dict[str, Any]
    ) -> TradingSignal:
        """
        Generate trading signal using LLM analysis of charts
        
        Workflow:
        1. Load strategy prompt template
        2. Render prompt with context
        3. Call LLM with chart images
        4. Parse LLM response
        5. Create trading signal
        6. Store signal in database
        """
        strategy = await db.get_strategy(strategy_id)
        
        # 1. Load prompt template
        prompt = await llm_service.get_prompt_for_analysis(
            template_type="analysis",
            language="en",
            strategy_id=strategy_id
        )
        
        # 2. Render prompt
        rendered_prompt = await prompt_renderer.render(
            prompt.template_content,
            context
        )
        
        # 3. Call LLM
        analysis = await llm_service.analyze_chart(
            chart_urls=chart_urls,
            prompt=rendered_prompt,
            model=strategy.llm_model or "gpt-4-vision-preview"
        )
        
        # 4. Parse signal
        signal = await self.parse_llm_response(analysis)
        
        # 5. Create trading signal
        trading_signal = TradingSignal(
            strategy_id=strategy_id,
            symbol=strategy.symbol,
            signal_type=signal.action,  # BUY, SELL, HOLD
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            target_price=signal.target_price,
            reasoning=analysis.text,
            confidence=signal.confidence,
            prompt_template_id=prompt.id,
            prompt_version=prompt.version,
            generated_at=datetime.now()
        )
        
        # 6. Store signal
        await db.save_trading_signal(trading_signal)
        
        return trading_signal
    
    async def parse_llm_response(self, analysis: str) -> ParsedSignal:
        """
        Parse LLM response to extract trading signal
        
        Expected format:
        - Signal: BUY/SELL/HOLD
        - Entry Price: $XXX.XX
        - Stop Loss: $XXX.XX
        - Target Price: $XXX.XX
        - Confidence: XX%
        """
        # Use regex or structured output parsing
        signal_match = re.search(r"Signal:\s*(BUY|SELL|HOLD)", analysis, re.IGNORECASE)
        entry_match = re.search(r"Entry Price:\s*\$?([\d.]+)", analysis)
        stop_match = re.search(r"Stop Loss:\s*\$?([\d.]+)", analysis)
        target_match = re.search(r"Target(?:\sPrice)?:\s*\$?([\d.]+)", analysis)
        confidence_match = re.search(r"Confidence:\s*([\d.]+)%?", analysis)
        
        return ParsedSignal(
            action=signal_match.group(1).upper() if signal_match else "HOLD",
            entry_price=float(entry_match.group(1)) if entry_match else None,
            stop_loss=float(stop_match.group(1)) if stop_match else None,
            target_price=float(target_match.group(1)) if target_match else None,
            confidence=float(confidence_match.group(1))/100 if confidence_match else 0.5
        )
```

---

### Step 9: Order Placement (Buy Signals)

**Flow**:
```
Buy Signal → Validate → Calculate Position Size → Place Order → Record Order
```

**Components**:
- **Service**: `backend/services/order_manager.py` (NEW)
- **IBKR Service**: `backend/services/ibkr_service.py` (ENHANCE)
- **Database**: `orders` table (KEEP - already exists)

**Implementation**:
```python
# backend/services/order_manager.py
class OrderManager:
    async def place_buy_order(
        self,
        strategy: Strategy,
        signal: TradingSignal
    ) -> Order:
        """
        Place buy order based on signal
        
        Workflow:
        1. Validate signal
        2. Check available capital
        3. Calculate position size
        4. Apply risk management
        5. Place order to IBKR
        6. Record order in database
        7. Monitor order status
        """
        # 1. Validate
        if signal.signal_type != "BUY":
            raise ValueError("Signal is not a BUY signal")
        
        # 2. Check capital
        portfolio = await self.get_portfolio()
        available_capital = portfolio.available_capital
        
        # 3. Calculate position size
        position_size = await self.calculate_position_size(
            available_capital=available_capital,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            risk_percent=strategy.risk_params["risk_per_trade"]  # e.g., 1%
        )
        
        # 4. Apply risk management
        if position_size * signal.entry_price > available_capital:
            position_size = int(available_capital / signal.entry_price)
        
        # 5. Place order to IBKR
        ibkr_order = await ibkr_service.place_order(
            conid=strategy.symbol_conid,
            side="BUY",
            quantity=position_size,
            order_type="LMT",  # Limit order
            price=signal.entry_price,
            tif="DAY"
        )
        
        # 6. Record order
        order = Order(
            strategy_id=strategy.id,
            signal_id=signal.id,
            ibkr_order_id=ibkr_order.order_id,
            symbol=signal.symbol,
            side="BUY",
            quantity=position_size,
            order_type="LMT",
            limit_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            target_price=signal.target_price,
            status="SUBMITTED",
            submitted_at=datetime.now()
        )
        await db.save_order(order)
        
        # 7. Start monitoring
        await self.start_order_monitoring(order.id)
        
        return order
    
    async def calculate_position_size(
        self,
        available_capital: float,
        entry_price: float,
        stop_loss: float,
        risk_percent: float
    ) -> int:
        """
        Calculate position size based on risk management
        
        Formula:
        Position Size = (Account Risk) / (Entry Price - Stop Loss)
        Account Risk = Available Capital * Risk Percent
        """
        account_risk = available_capital * risk_percent
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0
        
        position_size = int(account_risk / price_risk)
        
        # Minimum 1 share
        return max(1, position_size)
```

**API Endpoints**:
```python
# backend/api/orders.py (enhance)
@router.post("/")
async def place_order(order: OrderCreate):
    """Place new order"""
    return await order_manager.place_order(order)

@router.get("/{order_id}")
async def get_order(order_id: int):
    """Get order details"""
    return await order_manager.get_order(order_id)

@router.get("/{order_id}/status")
async def get_order_status(order_id: int):
    """Get real-time order status from IBKR"""
    return await order_manager.get_order_status(order_id)
```

---

### Step 10: Position Management (Sell Signals)

**Flow**:
```
Sell Signal → Check Position → Place Sell Order → Update Position → Record Trade
```

**Components**:
- **Service**: `backend/services/position_manager.py` (NEW)
- **Database**: `positions` table (KEEP - already exists)

**Implementation**:
```python
# backend/services/position_manager.py
class PositionManager:
    async def place_sell_order(
        self,
        strategy: Strategy,
        signal: TradingSignal
    ) -> Order:
        """
        Place sell order for existing position
        
        Workflow:
        1. Check if position exists
        2. Validate position quantity
        3. Place sell order
        4. Record order
        5. Update position on fill
        """
        # 1. Check position
        position = await db.get_position_by_strategy_symbol(
            strategy_id=strategy.id,
            symbol=signal.symbol
        )
        
        if not position or position.quantity <= 0:
            raise ValueError(f"No position to sell for {signal.symbol}")
        
        # 2. Validate quantity
        sell_quantity = position.quantity
        
        # 3. Place sell order
        ibkr_order = await ibkr_service.place_order(
            conid=strategy.symbol_conid,
            side="SELL",
            quantity=sell_quantity,
            order_type="LMT",
            price=signal.entry_price,  # Sell at signal price
            tif="DAY"
        )
        
        # 4. Record order
        order = Order(
            strategy_id=strategy.id,
            signal_id=signal.id,
            position_id=position.id,
            ibkr_order_id=ibkr_order.order_id,
            symbol=signal.symbol,
            side="SELL",
            quantity=sell_quantity,
            order_type="LMT",
            limit_price=signal.entry_price,
            status="SUBMITTED",
            submitted_at=datetime.now()
        )
        await db.save_order(order)
        
        # 5. Start monitoring
        await self.start_order_monitoring(order.id)
        
        return order
    
    async def check_stop_loss_targets(self):
        """
        Check all open positions for stop loss or target price hits
        (Run as scheduled task)
        """
        positions = await db.get_open_positions()
        
        for position in positions:
            current_price = await ibkr_service.get_current_price(position.symbol_conid)
            
            # Check stop loss
            if position.stop_loss and current_price <= position.stop_loss:
                await self.trigger_stop_loss_order(position, current_price)
            
            # Check target price
            elif position.target_price and current_price >= position.target_price:
                await self.trigger_take_profit_order(position, current_price)
```

---

### Step 11: Order Status Tracking

**Flow**:
```
Order Placed → Poll IBKR Status → Update Database → Notify on Fill → Update Position
```

**Components**:
- **Celery Task**: `backend/tasks/order_monitoring.py` (NEW)
- **Service**: `backend/services/order_tracker.py` (NEW)

**Implementation**:
```python
# backend/tasks/order_monitoring.py
@shared_task(name="backend.tasks.monitor_order")
def monitor_order(order_id: int):
    """
    Monitor order until filled or cancelled
    Poll every 10 seconds for up to 1 day
    """
    from backend.services.order_tracker import OrderTracker
    
    tracker = OrderTracker()
    result = await tracker.monitor_order(order_id)
    
    return result


# backend/services/order_tracker.py
class OrderTracker:
    async def monitor_order(self, order_id: int) -> OrderResult:
        """
        Monitor order until terminal state
        
        States: SUBMITTED → FILLED / CANCELLED / REJECTED
        """
        order = await db.get_order(order_id)
        max_checks = 8640  # 24 hours (10 sec intervals)
        
        for i in range(max_checks):
            # Get status from IBKR
            ibkr_status = await ibkr_service.get_order_status(order.ibkr_order_id)
            
            # Update database
            order.status = ibkr_status.status
            order.filled_quantity = ibkr_status.filled_quantity
            order.avg_fill_price = ibkr_status.avg_price
            order.updated_at = datetime.now()
            await db.update_order(order)
            
            # Check terminal states
            if ibkr_status.status == "FILLED":
                await self.handle_order_filled(order)
                return OrderResult(status="filled", order=order)
            
            elif ibkr_status.status in ["CANCELLED", "REJECTED"]:
                await self.handle_order_cancelled(order, ibkr_status.status)
                return OrderResult(status=ibkr_status.status.lower(), order=order)
            
            # Wait before next check
            await asyncio.sleep(10)
        
        # Timeout
        return OrderResult(status="timeout", order=order)
    
    async def handle_order_filled(self, order: Order):
        """Handle order fill event"""
        # 1. Update position
        if order.side == "BUY":
            await position_manager.create_or_update_position(
                strategy_id=order.strategy_id,
                symbol=order.symbol,
                quantity=order.filled_quantity,
                avg_price=order.avg_fill_price,
                stop_loss=order.stop_loss,
                target_price=order.target_price
            )
        elif order.side == "SELL":
            await position_manager.close_position(
                order.position_id,
                sell_price=order.avg_fill_price,
                sell_quantity=order.filled_quantity
            )
        
        # 2. Record trade
        trade = Trade(
            order_id=order.id,
            strategy_id=order.strategy_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.filled_quantity,
            price=order.avg_fill_price,
            executed_at=datetime.now(),
            pnl=await self.calculate_pnl(order)
        )
        await db.save_trade(trade)
        
        # 3. Update signal outcome (for performance tracking)
        if order.signal_id:
            await self.update_signal_outcome(order)
        
        # 4. Send notification
        await notification_service.send_order_filled(order)
```

---

### Step 12: Portfolio Updates

**Flow**:
```
Trade Executed → Calculate P&L → Update Portfolio → Update Statistics
```

**Components**:
- **Service**: `backend/services/portfolio_service.py` (NEW)
- **Database**: `portfolio` table (NEW)

**Implementation**:
```python
# backend/services/portfolio_service.py
class PortfolioService:
    async def update_portfolio(self, user_id: int):
        """
        Update user portfolio with latest positions and P&L
        """
        # 1. Get all positions
        positions = await db.get_user_positions(user_id)
        
        # 2. Get current prices
        portfolio_value = 0
        for position in positions:
            current_price = await ibkr_service.get_current_price(position.symbol_conid)
            position.current_price = current_price
            position.market_value = position.quantity * current_price
            position.unrealized_pnl = (current_price - position.avg_cost) * position.quantity
            portfolio_value += position.market_value
        
        # 3. Get cash balance
        cash_balance = await ibkr_service.get_cash_balance()
        
        # 4. Calculate totals
        total_value = portfolio_value + cash_balance
        
        # 5. Get closed trades P&L
        closed_trades = await db.get_closed_trades(user_id)
        realized_pnl = sum(trade.pnl for trade in closed_trades)
        
        # 6. Update portfolio
        portfolio = Portfolio(
            user_id=user_id,
            cash_balance=cash_balance,
            portfolio_value=portfolio_value,
            total_value=total_value,
            realized_pnl=realized_pnl,
            unrealized_pnl=sum(p.unrealized_pnl for p in positions),
            positions=positions,
            updated_at=datetime.now()
        )
        await db.save_portfolio(portfolio)
        
        return portfolio
    
    async def get_portfolio_statistics(self, user_id: int) -> PortfolioStats:
        """Get portfolio statistics"""
        trades = await db.get_all_trades(user_id)
        
        return PortfolioStats(
            total_trades=len(trades),
            winning_trades=len([t for t in trades if t.pnl > 0]),
            losing_trades=len([t for t in trades if t.pnl < 0]),
            win_rate=len([t for t in trades if t.pnl > 0]) / len(trades) if trades else 0,
            total_pnl=sum(t.pnl for t in trades),
            avg_win=np.mean([t.pnl for t in trades if t.pnl > 0]) if any(t.pnl > 0 for t in trades) else 0,
            avg_loss=np.mean([t.pnl for t in trades if t.pnl < 0]) if any(t.pnl < 0 for t in trades) else 0,
            largest_win=max([t.pnl for t in trades], default=0),
            largest_loss=min([t.pnl for t in trades], default=0)
        )
```

**API Endpoints**:
```python
# backend/api/portfolio.py (NEW)
@router.get("/")
async def get_portfolio(user_id: int = Depends(get_current_user_id)):
    """Get current portfolio"""
    return await portfolio_service.get_portfolio(user_id)

@router.get("/stats")
async def get_portfolio_stats(user_id: int = Depends(get_current_user_id)):
    """Get portfolio statistics"""
    return await portfolio_service.get_portfolio_statistics(user_id)

@router.post("/refresh")
async def refresh_portfolio(user_id: int = Depends(get_current_user_id)):
    """Refresh portfolio with latest data"""
    return await portfolio_service.update_portfolio(user_id)
```

**Database Schema**:
```sql
CREATE TABLE portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    cash_balance DECIMAL(18, 4),
    portfolio_value DECIMAL(18, 4),
    total_value DECIMAL(18, 4),
    realized_pnl DECIMAL(18, 4),
    unrealized_pnl DECIMAL(18, 4),
    snapshot_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_portfolio_user_date ON portfolio_snapshots(user_id, snapshot_at DESC);
```

---

### Step 13: Workflow Lineage Tracking

**Flow**:
```
Each Step → Record Input → Execute → Record Output → Store Lineage → Frontend Visualization
```

**Components**:
- **Service**: `backend/services/lineage_tracker.py` (NEW)
- **Database**: `workflow_lineage` table (NEW)
- **Frontend**: `lineage.html` (NEW) + Lineage visualization components

**Purpose**:
Track the complete input/output chain of each workflow execution for:
- 🔍 **Debugging**: Trace issues through execution history
- 📊 **Transparency**: Show users what happened at each step
- 🎯 **Audit Trail**: Complete record of all decisions
- 📈 **Performance Analysis**: Identify bottlenecks

**Implementation**:
```python
# backend/services/lineage_tracker.py
from datetime import datetime
from typing import Any, Dict, Optional
import json

class LineageTracker:
    """
    Tracks input/output lineage for each step in the trading workflow.
    """
    
    async def record_step(
        self,
        execution_id: str,  # Unique ID for this workflow run
        step_name: str,     # e.g., "fetch_market_data", "generate_chart", "llm_analysis"
        step_number: int,   # Sequential step number
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> LineageRecord:
        """
        Record a single workflow step with its input/output.
        
        Args:
            execution_id: Unique identifier for this workflow execution
            step_name: Name of the step (e.g., "chart_generation")
            step_number: Sequential order of this step (1, 2, 3...)
            input_data: Dictionary of input data for this step
            output_data: Dictionary of output data from this step
            metadata: Additional context (strategy_id, user_id, etc.)
            error: Error message if step failed
            duration_ms: Execution time in milliseconds
        
        Returns:
            LineageRecord object
        """
        record = LineageRecord(
            execution_id=execution_id,
            step_name=step_name,
            step_number=step_number,
            input_data=json.dumps(input_data, default=str),
            output_data=json.dumps(output_data, default=str),
            metadata=json.dumps(metadata or {}, default=str),
            error=error,
            duration_ms=duration_ms,
            status="error" if error else "success",
            recorded_at=datetime.now()
        )
        
        await db.save_lineage_record(record)
        return record
    
    async def get_execution_lineage(
        self,
        execution_id: str
    ) -> List[LineageRecord]:
        """
        Get complete lineage for a workflow execution.
        
        Returns records ordered by step_number.
        """
        return await db.get_lineage_by_execution(execution_id)
    
    async def get_step_lineage(
        self,
        execution_id: str,
        step_name: str
    ) -> Optional[LineageRecord]:
        """Get lineage for a specific step in an execution."""
        return await db.get_lineage_by_execution_and_step(execution_id, step_name)
    
    async def get_recent_executions(
        self,
        strategy_id: int,
        limit: int = 10
    ) -> List[str]:
        """Get recent execution IDs for a strategy."""
        return await db.get_recent_execution_ids(strategy_id, limit)


# Enhanced StrategyExecutor with lineage tracking
class StrategyExecutor:
    def __init__(self):
        self.lineage_tracker = LineageTracker()
    
    async def execute(self, strategy_id: int) -> ExecutionResult:
        """
        Execute complete strategy workflow WITH LINEAGE TRACKING
        """
        # Generate unique execution ID
        execution_id = f"{strategy_id}_{datetime.now().isoformat()}"
        
        start_time = datetime.now()
        
        try:
            # Step 1: Load strategy
            step_start = datetime.now()
            strategy = await db.get_strategy(strategy_id)
            
            await self.lineage_tracker.record_step(
                execution_id=execution_id,
                step_name="load_strategy",
                step_number=1,
                input_data={"strategy_id": strategy_id},
                output_data={
                    "strategy": strategy.to_dict(),
                    "is_active": strategy.is_active
                },
                metadata={"strategy_id": strategy_id},
                duration_ms=int((datetime.now() - step_start).total_seconds() * 1000)
            )
            
            if not strategy.is_active:
                return ExecutionResult(status="skipped", reason="strategy_inactive")
            
            # Step 2: Fetch market data
            step_start = datetime.now()
            market_data = await self.fetch_market_data(strategy.symbol_conid)
            
            await self.lineage_tracker.record_step(
                execution_id=execution_id,
                step_name="fetch_market_data",
                step_number=2,
                input_data={
                    "symbol_conid": strategy.symbol_conid,
                    "symbol": strategy.symbol
                },
                output_data={
                    "rows": len(market_data),
                    "date_range": {
                        "start": str(market_data.index[0]),
                        "end": str(market_data.index[-1])
                    },
                    "latest_price": float(market_data['close'].iloc[-1])
                },
                metadata={"strategy_id": strategy_id, "symbol": strategy.symbol},
                duration_ms=int((datetime.now() - step_start).total_seconds() * 1000)
            )
            
            # Step 3: Calculate indicators
            step_start = datetime.now()
            indicator_values = await self.calculate_indicators(
                strategy.indicators,
                market_data
            )
            
            await self.lineage_tracker.record_step(
                execution_id=execution_id,
                step_name="calculate_indicators",
                step_number=3,
                input_data={
                    "indicators": [ind.to_dict() for ind in strategy.indicators],
                    "market_data_rows": len(market_data)
                },
                output_data={
                    "calculated_indicators": {
                        name: {
                            "latest_value": float(values.iloc[-1]) if len(values) > 0 else None,
                            "count": len(values)
                        }
                        for name, values in indicator_values.items()
                    }
                },
                metadata={"strategy_id": strategy_id},
                duration_ms=int((datetime.now() - step_start).total_seconds() * 1000)
            )
            
            # Step 4: Generate charts
            step_start = datetime.now()
            charts = await self.generate_charts(
                market_data,
                indicator_values,
                strategy.symbol
            )
            
            await self.lineage_tracker.record_step(
                execution_id=execution_id,
                step_name="generate_charts",
                step_number=4,
                input_data={
                    "symbol": strategy.symbol,
                    "timeframes": ["daily", "weekly"] if strategy.analyze_weekly else ["daily"]
                },
                output_data={
                    "chart_urls": charts,
                    "chart_count": len(charts)
                },
                metadata={"strategy_id": strategy_id},
                duration_ms=int((datetime.now() - step_start).total_seconds() * 1000)
            )
            
            # Step 5: LLM Analysis
            step_start = datetime.now()
            analysis = await self.analyze_with_llm(
                charts=charts,
                prompt_template_id=strategy.prompt_template_id,
                context={
                    "symbol": strategy.symbol,
                    "indicators": {k: float(v.iloc[-1]) for k, v in indicator_values.items()},
                    "market_data": {
                        "latest_close": float(market_data['close'].iloc[-1]),
                        "volume": int(market_data['volume'].iloc[-1])
                    }
                }
            )
            
            await self.lineage_tracker.record_step(
                execution_id=execution_id,
                step_name="llm_analysis",
                step_number=5,
                input_data={
                    "chart_urls": charts,
                    "prompt_template_id": strategy.prompt_template_id,
                    "context": {
                        "symbol": strategy.symbol,
                        "latest_price": float(market_data['close'].iloc[-1])
                    }
                },
                output_data={
                    "analysis_text": analysis.text[:500] + "..." if len(analysis.text) > 500 else analysis.text,
                    "analysis_length": len(analysis.text),
                    "model_used": analysis.model
                },
                metadata={"strategy_id": strategy_id, "prompt_template_id": strategy.prompt_template_id},
                duration_ms=int((datetime.now() - step_start).total_seconds() * 1000)
            )
            
            # Step 6: Parse Signal
            step_start = datetime.now()
            signal = await self.parse_signal(analysis)
            
            await self.lineage_tracker.record_step(
                execution_id=execution_id,
                step_name="parse_signal",
                step_number=6,
                input_data={
                    "analysis_text_length": len(analysis.text)
                },
                output_data={
                    "signal": signal.action,
                    "entry_price": signal.entry_price,
                    "stop_loss": signal.stop_loss,
                    "target_price": signal.target_price,
                    "confidence": signal.confidence
                },
                metadata={"strategy_id": strategy_id},
                duration_ms=int((datetime.now() - step_start).total_seconds() * 1000)
            )
            
            # Step 7: Place Orders
            orders = []
            if signal.action in ["BUY", "SELL"]:
                step_start = datetime.now()
                
                try:
                    if signal.action == "BUY":
                        order = await self.place_buy_order(strategy, signal)
                    else:
                        order = await self.place_sell_order(strategy, signal)
                    
                    orders.append(order)
                    
                    await self.lineage_tracker.record_step(
                        execution_id=execution_id,
                        step_name="place_order",
                        step_number=7,
                        input_data={
                            "signal_action": signal.action,
                            "entry_price": signal.entry_price,
                            "quantity": order.quantity
                        },
                        output_data={
                            "order_id": order.id,
                            "ibkr_order_id": order.ibkr_order_id,
                            "status": order.status,
                            "side": order.side,
                            "quantity": order.quantity,
                            "price": order.limit_price
                        },
                        metadata={"strategy_id": strategy_id, "signal_id": signal.id},
                        duration_ms=int((datetime.now() - step_start).total_seconds() * 1000)
                    )
                    
                except Exception as e:
                    await self.lineage_tracker.record_step(
                        execution_id=execution_id,
                        step_name="place_order",
                        step_number=7,
                        input_data={
                            "signal_action": signal.action,
                            "entry_price": signal.entry_price
                        },
                        output_data={},
                        error=str(e),
                        metadata={"strategy_id": strategy_id},
                        duration_ms=int((datetime.now() - step_start).total_seconds() * 1000)
                    )
                    raise
            else:
                # No order placed (HOLD signal)
                await self.lineage_tracker.record_step(
                    execution_id=execution_id,
                    step_name="place_order",
                    step_number=7,
                    input_data={"signal_action": signal.action},
                    output_data={"reason": "HOLD signal, no order placed"},
                    metadata={"strategy_id": strategy_id},
                    duration_ms=0
                )
            
            # Step 8: Record Execution
            await db.record_execution(
                strategy_id=strategy_id,
                execution_id=execution_id,
                signal=signal,
                orders=orders,
                analysis=analysis
            )
            
            total_duration = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Final summary record
            await self.lineage_tracker.record_step(
                execution_id=execution_id,
                step_name="execution_complete",
                step_number=8,
                input_data={"execution_id": execution_id},
                output_data={
                    "status": "completed",
                    "signal": signal.action,
                    "orders_placed": len(orders),
                    "total_duration_ms": total_duration
                },
                metadata={"strategy_id": strategy_id},
                duration_ms=total_duration
            )
            
            return ExecutionResult(
                status="completed",
                execution_id=execution_id,
                signal=signal,
                orders=orders,
                analysis=analysis
            )
            
        except Exception as e:
            # Record error in lineage
            await self.lineage_tracker.record_step(
                execution_id=execution_id,
                step_name="execution_error",
                step_number=99,
                input_data={"strategy_id": strategy_id},
                output_data={},
                error=str(e),
                metadata={"strategy_id": strategy_id},
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            raise
```

**Database Schema**:
```sql
CREATE TABLE workflow_lineage (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(255) NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    step_number INTEGER NOT NULL,
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    metadata JSONB,
    error TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'success',  -- success, error
    duration_ms INTEGER,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_execution_step UNIQUE (execution_id, step_name)
);

CREATE INDEX idx_lineage_execution_id ON workflow_lineage(execution_id);
CREATE INDEX idx_lineage_step_name ON workflow_lineage(step_name);
CREATE INDEX idx_lineage_recorded_at ON workflow_lineage(recorded_at DESC);
CREATE INDEX idx_lineage_status ON workflow_lineage(status);

-- Add execution_id to strategy_executions table
ALTER TABLE strategy_executions ADD COLUMN execution_id VARCHAR(255) UNIQUE;
CREATE INDEX idx_strategy_executions_execution_id ON strategy_executions(execution_id);
```

**API Endpoints**:
```python
# backend/api/lineage.py (NEW)
from fastapi import APIRouter, Query
from typing import List, Optional

router = APIRouter(prefix="/api/lineage", tags=["lineage"])

@router.get("/execution/{execution_id}")
async def get_execution_lineage(execution_id: str):
    """
    Get complete lineage for a workflow execution.
    
    Returns list of all steps with input/output data.
    """
    lineage = await lineage_tracker.get_execution_lineage(execution_id)
    return {
        "execution_id": execution_id,
        "steps": [record.to_dict() for record in lineage],
        "total_steps": len(lineage),
        "has_errors": any(r.error for r in lineage)
    }

@router.get("/execution/{execution_id}/step/{step_name}")
async def get_step_lineage(execution_id: str, step_name: str):
    """Get lineage for a specific step in an execution."""
    record = await lineage_tracker.get_step_lineage(execution_id, step_name)
    if not record:
        raise HTTPException(status_code=404, detail="Step not found")
    return record.to_dict()

@router.get("/strategy/{strategy_id}/recent")
async def get_recent_executions(
    strategy_id: int,
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get recent execution IDs for a strategy.
    
    Returns list of execution IDs with timestamps.
    """
    executions = await lineage_tracker.get_recent_executions(strategy_id, limit)
    return {
        "strategy_id": strategy_id,
        "executions": executions,
        "count": len(executions)
    }

@router.get("/step/{step_name}/statistics")
async def get_step_statistics(
    step_name: str,
    strategy_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365)
):
    """
    Get statistics for a specific step across executions.
    
    Returns:
    - Average duration
    - Success rate
    - Common errors
    - Performance trends
    """
    stats = await db.get_step_statistics(step_name, strategy_id, days)
    return stats
```

---

## Frontend Integration

### Pages to Keep & Enhance

1. ✅ **Login** (`ibkr_login.html`) - Entry point
2. ✅ **Dashboard** (`dashboard.html`) - Overview + portfolio
3. ✅ **Symbols** (`symbols.html`) - Search symbols
4. ✅ **Indicators** (`indicators.html`) - Configure indicators
5. ✅ **Prompts** (`prompts.html`) - Manage prompts (Phase 8-9)
6. ✅ **Strategies** (`strategies.html`) - Create/manage strategies
7. ✅ **Signals** (`signals.html`) - View generated signals
8. ✅ **Charts** (`charts.html`) - View generated charts
9. ✅ **Orders** (NEW) - View and manage orders
10. ✅ **Portfolio** (NEW) - Portfolio view
11. ✅ **Lineage** (NEW) - Workflow execution lineage viewer

### Pages to Remove

- ❌ `workflows/` - Redundant with strategy execution
- ❌ `analysis.html` - Integrated into strategy execution
- ❌ `decisions/` - Integrated into signal generation
- ❌ Extra logs pages - Consolidated to one logs view

### New Frontend Components

#### Lineage Viewer UI

```html
<!-- frontend/templates/lineage.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Workflow Lineage - IBKR Trading</title>
    <!-- Bootstrap 5, Font Awesome, etc. -->
</head>
<body>
    <div class="container-fluid">
        <h1>Workflow Execution Lineage</h1>
        
        <!-- Strategy & Execution Selector -->
        <div class="row mb-4">
            <div class="col-md-6">
                <label>Strategy</label>
                <select id="strategySelect" class="form-control">
                    <!-- Populated dynamically -->
                </select>
            </div>
            <div class="col-md-6">
                <label>Execution</label>
                <select id="executionSelect" class="form-control">
                    <!-- Populated dynamically -->
                </select>
            </div>
        </div>
        
        <!-- Lineage Visualization -->
        <div id="lineageVisualization">
            <!-- Step cards will be inserted here -->
        </div>
        
        <!-- Step Detail Modal -->
        <div class="modal fade" id="stepDetailModal">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Step Details</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div id="stepDetailContent"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="/static/js/lineage-viewer.js"></script>
</body>
</html>
```

```javascript
// frontend/static/js/lineage-viewer.js
class LineageViewer {
    constructor() {
        this.currentExecutionId = null;
        this.lineageData = null;
    }
    
    async init() {
        await this.loadStrategies();
        this.bindEvents();
    }
    
    async loadStrategies() {
        const response = await fetch('/api/strategies');
        const strategies = await response.json();
        
        const select = document.getElementById('strategySelect');
        strategies.forEach(strategy => {
            const option = document.createElement('option');
            option.value = strategy.id;
            option.text = strategy.name;
            select.appendChild(option);
        });
    }
    
    async loadExecutions(strategyId) {
        const response = await fetch(`/api/lineage/strategy/${strategyId}/recent?limit=20`);
        const data = await response.json();
        
        const select = document.getElementById('executionSelect');
        select.innerHTML = '<option value="">Select Execution...</option>';
        
        data.executions.forEach(exec => {
            const option = document.createElement('option');
            option.value = exec.execution_id;
            option.text = `${new Date(exec.executed_at).toLocaleString()} - ${exec.status}`;
            select.appendChild(option);
        });
    }
    
    async loadLineage(executionId) {
        this.currentExecutionId = executionId;
        
        const response = await fetch(`/api/lineage/execution/${executionId}`);
        this.lineageData = await response.json();
        
        this.renderLineage();
    }
    
    renderLineage() {
        const container = document.getElementById('lineageVisualization');
        container.innerHTML = '';
        
        const steps = this.lineageData.steps;
        
        steps.forEach((step, index) => {
            const stepCard = this.createStepCard(step, index);
            container.appendChild(stepCard);
            
            // Add connector arrow (except for last step)
            if (index < steps.length - 1) {
                const arrow = this.createArrow();
                container.appendChild(arrow);
            }
        });
    }
    
    createStepCard(step, index) {
        const card = document.createElement('div');
        card.className = `step-card ${step.status}`;
        card.innerHTML = `
            <div class="card mb-3 ${step.error ? 'border-danger' : 'border-success'}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div>
                        <span class="badge bg-secondary">Step ${step.step_number}</span>
                        <strong>${this.formatStepName(step.step_name)}</strong>
                    </div>
                    <div>
                        <span class="badge ${step.error ? 'bg-danger' : 'bg-success'}">
                            ${step.error ? 'ERROR' : 'SUCCESS'}
                        </span>
                        <span class="text-muted">${step.duration_ms}ms</span>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-5">
                            <h6 class="text-primary">
                                <i class="fa fa-arrow-right"></i> Input
                            </h6>
                            <pre class="code-block">${this.formatJSON(step.input_data)}</pre>
                        </div>
                        <div class="col-md-2 text-center d-flex align-items-center justify-content-center">
                            <i class="fa fa-arrow-right fa-2x text-muted"></i>
                        </div>
                        <div class="col-md-5">
                            <h6 class="text-success">
                                <i class="fa fa-arrow-left"></i> Output
                            </h6>
                            ${step.error ? 
                                `<div class="alert alert-danger">${step.error}</div>` :
                                `<pre class="code-block">${this.formatJSON(step.output_data)}</pre>`
                            }
                        </div>
                    </div>
                    <div class="mt-3">
                        <button class="btn btn-sm btn-outline-primary" 
                                onclick="lineageViewer.showStepDetails(${index})">
                            View Full Details
                        </button>
                    </div>
                </div>
            </div>
        `;
        return card;
    }
    
    createArrow() {
        const arrow = document.createElement('div');
        arrow.className = 'step-connector text-center mb-3';
        arrow.innerHTML = '<i class="fa fa-arrow-down fa-2x text-primary"></i>';
        return arrow;
    }
    
    formatStepName(name) {
        return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    formatJSON(data) {
        try {
            const parsed = typeof data === 'string' ? JSON.parse(data) : data;
            return JSON.stringify(parsed, null, 2);
        } catch (e) {
            return data;
        }
    }
    
    showStepDetails(stepIndex) {
        const step = this.lineageData.steps[stepIndex];
        const modal = new bootstrap.Modal(document.getElementById('stepDetailModal'));
        
        const content = document.getElementById('stepDetailContent');
        
        // Build rich visualization based on step type
        const visualizationHtml = this.buildStepVisualization(step);
        
        content.innerHTML = `
            <div class="mb-3">
                <h5>${this.formatStepName(step.step_name)}</h5>
                <p class="text-muted">Execution ID: ${this.currentExecutionId}</p>
                <p class="text-muted">Recorded: ${new Date(step.recorded_at).toLocaleString()}</p>
                <p class="text-muted">Duration: ${step.duration_ms}ms</p>
            </div>
            
            <!-- Rich Visualization -->
            ${visualizationHtml}
            
            <!-- Collapsible Raw Data -->
            <div class="accordion mt-4" id="rawDataAccordion">
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" 
                                data-bs-toggle="collapse" data-bs-target="#rawInputData">
                            Raw Input Data (JSON)
                        </button>
                    </h2>
                    <div id="rawInputData" class="accordion-collapse collapse">
                        <div class="accordion-body">
                            <pre class="code-block">${this.formatJSON(step.input_data)}</pre>
                        </div>
                    </div>
                </div>
                
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" 
                                data-bs-toggle="collapse" data-bs-target="#rawOutputData">
                            Raw Output Data (JSON)
                        </button>
                    </h2>
                    <div id="rawOutputData" class="accordion-collapse collapse">
                        <div class="accordion-body">
                            <pre class="code-block">${this.formatJSON(step.output_data)}</pre>
                        </div>
                    </div>
                </div>
                
                ${step.metadata ? `
                    <div class="accordion-item">
                        <h2 class="accordion-header">
                            <button class="accordion-button collapsed" type="button" 
                                    data-bs-toggle="collapse" data-bs-target="#metadataData">
                                Metadata (JSON)
                            </button>
                        </h2>
                        <div id="metadataData" class="accordion-collapse collapse">
                            <div class="accordion-body">
                                <pre class="code-block">${this.formatJSON(step.metadata)}</pre>
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>
            
            ${step.error ? `
                <div class="mt-3">
                    <h6>Error Details</h6>
                    <div class="alert alert-danger">${step.error}</div>
                </div>
            ` : ''}
        `;
        
        modal.show();
    }
    
    buildStepVisualization(step) {
        /**
         * Build rich visualization based on step type
         * Returns HTML for specialized visualization
         */
        const stepName = step.step_name;
        const inputData = this.parseData(step.input_data);
        const outputData = this.parseData(step.output_data);
        
        switch(stepName) {
            case 'load_strategy':
                return this.visualizeStrategy(inputData, outputData);
            
            case 'fetch_market_data':
                return this.visualizeMarketData(inputData, outputData);
            
            case 'calculate_indicators':
                return this.visualizeIndicators(inputData, outputData);
            
            case 'generate_charts':
                return this.visualizeCharts(inputData, outputData);
            
            case 'llm_analysis':
                return this.visualizeLLMAnalysis(inputData, outputData);
            
            case 'parse_signal':
                return this.visualizeSignal(inputData, outputData);
            
            case 'place_order':
                return this.visualizeOrder(inputData, outputData);
            
            default:
                return this.visualizeGeneric(inputData, outputData);
        }
    }
    
    visualizeStrategy(input, output) {
        return `
            <h6><i class="fa fa-cog"></i> Strategy Configuration</h6>
            <div class="card">
                <div class="card-body">
                    <table class="table table-sm">
                        <tr>
                            <th>Strategy ID:</th>
                            <td>${input.strategy_id || output.strategy?.id}</td>
                        </tr>
                        <tr>
                            <th>Strategy Name:</th>
                            <td><strong>${output.strategy?.name || 'N/A'}</strong></td>
                        </tr>
                        <tr>
                            <th>Symbol:</th>
                            <td><span class="badge bg-primary">${output.strategy?.symbol || 'N/A'}</span></td>
                        </tr>
                        <tr>
                            <th>Active:</th>
                            <td>
                                ${output.is_active ? 
                                    '<span class="badge bg-success">Active</span>' : 
                                    '<span class="badge bg-secondary">Inactive</span>'}
                            </td>
                        </tr>
                        <tr>
                            <th>Schedule:</th>
                            <td><code>${output.strategy?.schedule || 'N/A'}</code></td>
                        </tr>
                    </table>
                </div>
            </div>
        `;
    }
    
    visualizeMarketData(input, output) {
        return `
            <h6><i class="fa fa-chart-line"></i> Market Data Fetched</h6>
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Input</div>
                        <div class="card-body">
                            <p><strong>Symbol:</strong> <span class="badge bg-primary">${input.symbol || 'N/A'}</span></p>
                            <p><strong>Contract ID:</strong> ${input.symbol_conid || 'N/A'}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Output</div>
                        <div class="card-body">
                            <p><strong>Rows Fetched:</strong> <span class="badge bg-info">${output.rows || 0}</span></p>
                            <p><strong>Date Range:</strong> ${output.date_range?.start || 'N/A'} to ${output.date_range?.end || 'N/A'}</p>
                            <p><strong>Latest Price:</strong> <span class="text-success fs-5">$${output.latest_price?.toFixed(2) || 'N/A'}</span></p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    visualizeIndicators(input, output) {
        const indicators = output.calculated_indicators || {};
        const indicatorList = Object.entries(indicators).map(([name, data]) => `
            <tr>
                <td><strong>${name}</strong></td>
                <td><span class="badge bg-info">${data.latest_value?.toFixed(4) || 'N/A'}</span></td>
                <td>${data.count || 0} values</td>
            </tr>
        `).join('');
        
        return `
            <h6><i class="fa fa-chart-bar"></i> Technical Indicators</h6>
            <div class="card">
                <div class="card-body">
                    <p><strong>Indicators Calculated:</strong> ${Object.keys(indicators).length}</p>
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Indicator</th>
                                <th>Latest Value</th>
                                <th>Data Points</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${indicatorList}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    visualizeCharts(input, output) {
        const chartUrls = output.chart_urls || [];
        const chartImages = chartUrls.map((url, index) => `
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-header">
                        Chart ${index + 1}: ${input.timeframes?.[index] || 'Unknown'}
                    </div>
                    <div class="card-body text-center">
                        <img src="${url}" class="img-fluid" alt="Chart ${index + 1}" 
                             style="max-height: 400px; cursor: pointer;"
                             onclick="window.open('${url}', '_blank')">
                    </div>
                </div>
            </div>
        `).join('');
        
        return `
            <h6><i class="fa fa-image"></i> Generated Charts</h6>
            <div class="row">
                ${chartImages || '<p class="text-muted">No charts generated</p>'}
            </div>
            <p class="text-muted"><small><i class="fa fa-info-circle"></i> Click chart to view full size</small></p>
        `;
    }
    
    visualizeLLMAnalysis(input, output) {
        const analysisText = output.analysis_text || 'No analysis text available';
        const model = output.model_used || input.model || 'Unknown';
        
        return `
            <h6><i class="fa fa-brain"></i> LLM Analysis</h6>
            <div class="card mb-3">
                <div class="card-header d-flex justify-content-between">
                    <span>Model Used</span>
                    <span class="badge bg-primary">${model}</span>
                </div>
                <div class="card-body">
                    <p><strong>Prompt Template ID:</strong> ${input.prompt_template_id || 'N/A'}</p>
                    <p><strong>Analysis Length:</strong> ${output.analysis_length || analysisText.length} characters</p>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <i class="fa fa-comment-alt"></i> Analysis Output
                </div>
                <div class="card-body">
                    <div class="analysis-text" style="white-space: pre-wrap; max-height: 500px; overflow-y: auto; 
                         background: #f8f9fa; padding: 15px; border-radius: 4px; font-family: 'Segoe UI', sans-serif;">
${analysisText}
                    </div>
                </div>
            </div>
        `;
    }
    
    visualizeSignal(input, output) {
        const signal = output.signal || 'HOLD';
        const signalClass = signal === 'BUY' ? 'success' : signal === 'SELL' ? 'danger' : 'secondary';
        const signalIcon = signal === 'BUY' ? 'arrow-up' : signal === 'SELL' ? 'arrow-down' : 'minus';
        
        return `
            <h6><i class="fa fa-signal"></i> Trading Signal</h6>
            <div class="card mb-3">
                <div class="card-body text-center">
                    <h2>
                        <span class="badge bg-${signalClass} fs-1">
                            <i class="fa fa-${signalIcon}"></i> ${signal}
                        </span>
                    </h2>
                    <p class="text-muted">Confidence: ${((output.confidence || 0) * 100).toFixed(0)}%</p>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body text-center">
                            <p class="text-muted mb-1">Entry Price</p>
                            <h4 class="text-primary">${output.entry_price ? '$' + output.entry_price.toFixed(2) : 'N/A'}</h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body text-center">
                            <p class="text-muted mb-1">Stop Loss</p>
                            <h4 class="text-danger">${output.stop_loss ? '$' + output.stop_loss.toFixed(2) : 'N/A'}</h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body text-center">
                            <p class="text-muted mb-1">Target Price</p>
                            <h4 class="text-success">${output.target_price ? '$' + output.target_price.toFixed(2) : 'N/A'}</h4>
                        </div>
                    </div>
                </div>
            </div>
            
            ${this.calculateRiskReward(output)}
        `;
    }
    
    visualizeOrder(input, output) {
        const side = output.side || input.signal_action || 'UNKNOWN';
        const sideClass = side === 'BUY' ? 'success' : side === 'SELL' ? 'danger' : 'secondary';
        const status = output.status || 'UNKNOWN';
        const statusClass = status === 'FILLED' ? 'success' : 
                           status === 'SUBMITTED' ? 'info' : 
                           status === 'CANCELLED' ? 'warning' : 'danger';
        
        return `
            <h6><i class="fa fa-shopping-cart"></i> Order Details</h6>
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h3>
                                <span class="badge bg-${sideClass}">${side}</span>
                                <span class="badge bg-${statusClass}">${status}</span>
                            </h3>
                        </div>
                        <div class="col-md-6 text-end">
                            <p class="mb-0"><strong>Order ID:</strong> ${output.order_id || 'N/A'}</p>
                            <p class="mb-0"><strong>IBKR Order ID:</strong> ${output.ibkr_order_id || 'N/A'}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <p class="text-muted mb-1">Quantity</p>
                            <h4>${output.quantity || input.quantity || 'N/A'}</h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <p class="text-muted mb-1">Price</p>
                            <h4>${output.price ? '$' + output.price.toFixed(2) : (input.entry_price ? '$' + input.entry_price.toFixed(2) : 'N/A')}</h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <p class="text-muted mb-1">Order Type</p>
                            <h4><span class="badge bg-secondary">${output.order_type || 'LMT'}</span></h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <p class="text-muted mb-1">Total Value</p>
                            <h4>${output.quantity && output.price ? '$' + (output.quantity * output.price).toFixed(2) : 'N/A'}</h4>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    visualizeGeneric(input, output) {
        return `
            <div class="row">
                <div class="col-md-6">
                    <h6>Input</h6>
                    <pre class="code-block">${this.formatJSON(input)}</pre>
                </div>
                <div class="col-md-6">
                    <h6>Output</h6>
                    <pre class="code-block">${this.formatJSON(output)}</pre>
                </div>
            </div>
        `;
    }
    
    calculateRiskReward(signal) {
        if (!signal.entry_price || !signal.stop_loss || !signal.target_price) {
            return '';
        }
        
        const risk = Math.abs(signal.entry_price - signal.stop_loss);
        const reward = Math.abs(signal.target_price - signal.entry_price);
        const ratio = (reward / risk).toFixed(2);
        
        return `
            <div class="card mt-3">
                <div class="card-body">
                    <h6>Risk/Reward Analysis</h6>
                    <div class="row">
                        <div class="col-md-4 text-center">
                            <p class="text-muted mb-1">Risk</p>
                            <h5 class="text-danger">$${risk.toFixed(2)}</h5>
                        </div>
                        <div class="col-md-4 text-center">
                            <p class="text-muted mb-1">Reward</p>
                            <h5 class="text-success">$${reward.toFixed(2)}</h5>
                        </div>
                        <div class="col-md-4 text-center">
                            <p class="text-muted mb-1">R:R Ratio</p>
                            <h5 class="text-primary">1:${ratio}</h5>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    parseData(data) {
        try {
            return typeof data === 'string' ? JSON.parse(data) : data;
        } catch (e) {
            return data;
        }
    }
    
    bindEvents() {
        document.getElementById('strategySelect').addEventListener('change', (e) => {
            const strategyId = e.target.value;
            if (strategyId) {
                this.loadExecutions(strategyId);
            }
        });
        
        document.getElementById('executionSelect').addEventListener('change', (e) => {
            const executionId = e.target.value;
            if (executionId) {
                this.loadLineage(executionId);
            }
        });
    }
}

// Initialize on page load
const lineageViewer = new LineageViewer();
document.addEventListener('DOMContentLoaded', () => {
    lineageViewer.init();
});
```

```css
/* frontend/static/css/lineage.css */
.step-card {
    transition: all 0.3s ease;
}

.step-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.code-block {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 12px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    max-height: 300px;
    overflow-y: auto;
}

.step-connector {
    padding: 10px 0;
}

.border-success {
    border-left: 4px solid #28a745 !important;
}

.border-danger {
    border-left: 4px solid #dc3545 !important;
}
```

#### Strategy Workflow Component

```javascript
// frontend/static/js/strategy-workflow.js
class StrategyWorkflow {
    async createStrategy() {
        // Step 1: Search symbol
        const symbol = await this.searchSymbol();
        
        // Step 2: Select indicators
        const indicators = await this.selectIndicators();
        
        // Step 3: Choose prompt
        const prompt = await this.selectPrompt();
        
        // Step 4: Set schedule
        const schedule = await this.setSchedule();
        
        // Step 5: Configure risk
        const riskParams = await this.configureRisk();
        
        // Step 6: Create strategy
        return await this.saveStrategy({
            symbol,
            indicators,
            prompt,
            schedule,
            riskParams
        });
    }
    
    async viewExecutionLineage(executionId) {
        // Navigate to lineage viewer
        window.location.href = `/lineage?execution=${executionId}`;
    }
}
```

#### Dashboard Integration

```html
<!-- Add lineage link to strategy cards in dashboard -->
<div class="strategy-card">
    <h5>{{ strategy.name }}</h5>
    <p>Symbol: {{ strategy.symbol }}</p>
    <div class="btn-group">
        <a href="/strategies/{{ strategy.id }}" class="btn btn-sm btn-primary">Edit</a>
        <a href="/lineage?strategy={{ strategy.id }}" class="btn btn-sm btn-info">
            <i class="fa fa-sitemap"></i> View Lineage
        </a>
    </div>
</div>
```

---

## Database Schema Summary

### Tables to Keep
- ✅ users
- ✅ strategies
- ✅ indicators
- ✅ prompt_templates (Phase 1)
- ✅ prompt_performance (Phase 1)
- ✅ trading_signals (Phase 7 - enhanced)
- ✅ orders
- ✅ positions
- ✅ trades

### Tables to Add
- 🆕 symbols (cache IBKR symbols)
- 🆕 strategy_executions (execution history)
- 🆕 portfolio_snapshots (portfolio over time)
- 🆕 user_sessions (IBKR sessions)
- 🆕 workflow_lineage (step-by-step execution lineage with input/output)

### Tables to Remove/Merge
- ❌ workflows → Merge into strategies
- ❌ workflow_executions → Rename to strategy_executions
- ❌ decisions → Merge into trading_signals

---

## Next Steps

1. ✅ Review and approve this design
2. 🔄 Create detailed task breakdown
3. 🔄 Identify all files to remove
4. 🔄 Create migration plan
5. 🔄 Begin implementation

---

**Total Estimated Effort**: 15-20 development days

**Dependencies**: 
- Existing prompt system (Complete ✅)
- IBKR Gateway (Exists ✅)
- Database (Exists ✅)
- Celery (Exists ✅)

**Risks**:
- Medium: IBKR API integration complexity
- Low: Breaking existing functionality
- Low: Data migration issues

