# IBKR Trading Workflow - Quick Reference

## 🎯 Complete Implementation Files

### Pydantic Models (`dags/models/`)
```python
# Import all models
from models import (
    # Market data
    MarketData, OHLCVBar,
    # Indicators
    TechnicalIndicators,
    # Charts
    ChartConfig, ChartResult, Timeframe,
    # Signals
    TradingSignal, SignalAction, SignalConfidence,
    # Orders
    Order, OrderType, OrderSide, OrderStatus,
    # Trades
    Trade, TradeExecution,
    # Portfolio
    Portfolio, Position
)
```

| File | Purpose | Key Classes |
|------|---------|-------------|
| `__init__.py` | Package exports | All models exported |
| `market_data.py` | Market OHLCV data | MarketData, OHLCVBar |
| `indicators.py` | Technical indicators | TechnicalIndicators |
| `chart.py` | Chart config/results | ChartConfig, ChartResult |
| `signal.py` | Trading signals | TradingSignal |
| `order.py` | Order management | Order |
| `trade.py` | Trade tracking | Trade, TradeExecution |
| `portfolio.py` | Portfolio status | Portfolio, Position |

### Utility Modules (`dags/utils/`)

| File | Purpose | Key Functions |
|------|---------|---------------|
| `ibkr_client.py` | IBKR Gateway integration | fetch_market_data(), place_order(), get_trades(), get_portfolio() |
| `chart_generator.py` | Technical chart generation | calculate_indicators(), generate_chart(), resample_to_weekly() |
| `llm_signal_analyzer.py` | LLM-based signal generation | analyze_charts() (supports OpenAI & Anthropic) |

### Main Workflow (`dags/`)

| File | Purpose |
|------|---------|
| `ibkr_trading_signal_workflow.py` | Complete 8-task Airflow DAG |

## 🚀 Quick Start

### 1. Test the Workflow (Mock Mode)

The workflow includes mock mode - works without IBKR or LLM APIs:

```bash
# Just trigger the DAG
docker compose exec airflow-scheduler airflow dags trigger ibkr_trading_signal_workflow

# Monitor execution
docker compose exec airflow-scheduler airflow dags list-runs -d ibkr_trading_signal_workflow
```

Mock mode provides:
- ✅ Realistic market data (200 days)
- ✅ Complete chart generation
- ✅ Simulated LLM signals
- ✅ Mock order placement
- ✅ Mock portfolio

### 2. Enable Real IBKR Connection

Add to `docker-compose.yml`:
```yaml
services:
  gateway:
    image: ghcr.io/gnzsnz/ib-gateway:latest
    container_name: ibkr-gateway
    environment:
      TWS_USERID: ${IB_USER}
      TWS_PASSWORD: ${IB_PASSWORD}
      TRADING_MODE: paper
    ports:
      - "4002:4002"
    networks:
      - trading-network
```

### 3. Enable Real LLM Analysis

Add to `docker-compose.yml` environment:
```yaml
environment:
  # For OpenAI
  OPENAI_API_KEY: ${OPENAI_API_KEY}
  
  # OR for Anthropic
  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
```

Then in `.env`:
```bash
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
```

## 📊 Workflow Tasks

```
fetch_market_data (MarketData)
    ↓
    ├─→ generate_daily_chart (ChartResult)
    └─→ generate_weekly_chart (ChartResult)
            ↓
    analyze_with_llm (TradingSignal)
            ↓
    place_order (Order) [only if is_actionable]
            ↓
    get_trades (Trade)
            ↓
    get_portfolio (Portfolio)
            ↓
    log_to_mlflow (All data)
```

## 🎨 Example Usage

### Check if Signal is Actionable
```python
signal = TradingSignal(
    symbol="TSLA",
    action=SignalAction.BUY,
    confidence=SignalConfidence.HIGH,
    confidence_score=Decimal("85.5"),
    ...
)

if signal.is_actionable:  # True for BUY/SELL + HIGH/MEDIUM confidence
    print(f"Action: {signal.action}")
    print(f"Entry: ${signal.suggested_entry_price}")
    print(f"Stop: ${signal.suggested_stop_loss}")
    print(f"Target: ${signal.suggested_take_profit}")
    print(f"R/R: {signal.risk_reward_ratio}")
```

### Create and Validate Order
```python
order = Order(
    symbol="TSLA",
    side=OrderSide.BUY,
    quantity=10,
    order_type=OrderType.LIMIT,
    limit_price=Decimal("250.00")
)

# Validation happens automatically
# - Ensures limit_price is set for LIMIT orders
# - Ensures stop_price is set for STOP orders
# - Ensures filled_quantity <= quantity
```

### Check Portfolio Position
```python
portfolio = Portfolio(...)

if portfolio.has_position("TSLA"):
    pos = portfolio.get_position("TSLA")
    print(f"Quantity: {pos.quantity}")
    print(f"Current: ${pos.current_price}")
    print(f"P&L: ${pos.unrealized_pnl} ({pos.unrealized_pnl_percent}%)")
    print(f"Profitable: {pos.is_profitable}")
```

## 🔧 Configuration

### Symbol Configuration
Edit `dags/ibkr_trading_signal_workflow.py`:
```python
SYMBOL = "TSLA"  # Change to any symbol
POSITION_SIZE = 10  # Number of shares to trade
```

### LLM Provider
```python
LLM_PROVIDER = "openai"  # or "anthropic"
```

### IBKR Connection
```python
IBKR_HOST = "gateway"  # Docker service name
IBKR_PORT = 4002  # Paper trading (4001 for live)
```

## 📈 MLflow Tracking

View runs at http://localhost:5500

**Parameters Logged**:
- symbol
- position_size
- llm_provider
- signal_action
- signal_confidence

**Metrics Logged**:
- latest_price
- confidence_score
- risk_reward_ratio
- portfolio_value
- order_placed

**Artifacts Logged**:
- trading_signal.json
- daily_chart.png
- weekly_chart.png
- portfolio.json

## 🛡️ Safety Features

1. **Type Safety**: All data validated with Pydantic
2. **Actionable Filter**: Only HIGH/MEDIUM confidence signals execute
3. **Risk Management**: Stop loss and take profit from LLM
4. **Portfolio Check**: Checks existing positions before trading
5. **Mock Mode**: Test without real money
6. **Paper Trading**: Use port 4002 (not 4001)

## 🐛 Debug Mode

Enable in `docker-compose.yml`:
```yaml
environment:
  DEBUG_MODE: "true"
```

Provides:
- Detailed SQL queries
- Sample data at each step
- Complete debug artifacts in MLflow
- Full execution context

## 📝 Common Tasks

### View DAG in Airflow
```bash
open http://localhost:8080
# Find: ibkr_trading_signal_workflow
```

### Trigger Manually
```bash
docker compose exec airflow-scheduler airflow dags trigger ibkr_trading_signal_workflow
```

### Check Logs
```bash
docker logs ibkr-airflow-scheduler | grep -i trading
```

### View MLflow Runs
```bash
open http://localhost:5500
# Select experiment: ibkr-stock-data or ibkr-trading-signals
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `IMPLEMENTATION_COMPLETE.md` | Complete implementation guide |
| `TRADING_SIGNAL_WORKFLOW_SUMMARY.md` | Architecture and design |
| `QUICK_REFERENCE.md` | This file - quick commands |
| `openspec/changes/add-ibkr-trading-signal-workflow/proposal.md` | OpenSpec proposal |
| `openspec/changes/add-ibkr-trading-signal-workflow/tasks.md` | All 77 implementation tasks |

## ⚡ Next Steps

1. **Test Mock Mode**: Trigger DAG and verify execution
2. **Enable IBKR**: Connect to IBKR Gateway
3. **Add LLM API**: Set OPENAI_API_KEY or ANTHROPIC_API_KEY
4. **Review Signals**: Check MLflow for signal quality
5. **Paper Trade**: Test with real market data but paper money
6. **Go Live**: Switch to port 4001 and real trading account

## 🎯 Success Checklist

- [ ] DAG appears in Airflow UI
- [ ] Can trigger DAG manually
- [ ] fetch_market_data task succeeds
- [ ] Charts generated successfully
- [ ] LLM analysis produces signal
- [ ] Signal logged to MLflow
- [ ] Charts visible in MLflow
- [ ] Portfolio tracked correctly

**You're ready to trade!** 🚀📈
