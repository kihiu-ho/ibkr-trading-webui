# Quick Start Guide - IBKR Trading Platform

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Docker Desktop installed and running
- IBKR account with API access
- OpenAI API key (or compatible endpoint)

### Step 1: Configure Environment

```bash
# Copy the example environment file
cp backend/.env.example backend/.env

# Edit the .env file with your credentials
nano backend/.env
```

**Required settings to update:**
```env
# Your IBKR account ID
IBKR_ACCOUNT_ID=your_account_id_here

# Your OpenAI API key
OPENAI_API_KEY=sk-your-api-key-here

# Optional: Use different AI model
OPENAI_MODEL=gpt-4-turbo-preview

# Optional: Increase account size for position sizing
# (in strategy.param.account_size)
```

### Step 2: Start the Platform

```bash
# Build all services (first time only, may take 5-10 minutes)
docker-compose -f docker-compose.new.yml build

# Start all services
docker-compose -f docker-compose.new.yml up -d

# Check service status
docker-compose -f docker-compose.new.yml ps
```

### Step 3: Access the Platform

Once all services are running:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Web Interface** | http://localhost:8000 | No auth required |
| **API Documentation** | http://localhost:8000/docs | Interactive API docs |
| **Celery Monitor (Flower)** | http://localhost:5555 | No auth required |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |
| **IBKR Gateway** | https://localhost:5000 | Your IBKR credentials |

### Step 4: Authenticate with IBKR

1. Open https://localhost:5000 in your browser
2. Accept the self-signed certificate warning
3. Log in with your IBKR credentials
4. Complete 2FA if enabled

### Step 5: Create Your First Strategy

1. Go to http://localhost:8000/strategies
2. Click "Add Strategy"
3. Fill in the form:
   - **Name**: "AAPL Swing Trade"
   - **Symbol**: "AAPL"
   - **Workflow**: Default Workflow
   - **Account Size**: 100000
   - **Risk Per Trade**: 0.02 (2%)
4. Click "Save"

### Step 6: Execute the Strategy

1. Find your strategy in the list
2. Click the ▶️ (play) button
3. Monitor execution in the Dashboard or Flower (http://localhost:5555)

### Step 7: View Results

After execution completes (2-5 minutes):

1. **Dashboard**: View recent trading decisions
2. **Analysis Page**: See generated charts
3. **Orders Page**: Check if any orders were placed
4. **Flower**: View task execution details

## 📊 Understanding the Workflow

When you execute a strategy, the system:

1. **Searches** for the stock symbol in IBKR
2. **Fetches** 1 year of daily data and 5 years of weekly data
3. **Generates** technical analysis charts with indicators:
   - SuperTrend, SMA 20/50/200, RSI, MACD, Bollinger Bands
4. **Analyzes** charts using AI (GPT-4):
   - Daily chart analysis
   - Weekly chart analysis
   - Multi-timeframe consolidation
5. **Makes Decision**:
   - BUY: R ≥ 1.0 AND profit margin ≥ 5%
   - SELL: Same criteria for short positions
   - HOLD: Otherwise
6. **Places Order** (if BUY/SELL):
   - Calculates position size based on risk
   - Submits market order to IBKR
7. **Saves Everything**:
   - Charts to MinIO
   - Decision to database
   - Order to database

## 🛠 Common Tasks

### View Logs

```bash
# All services
docker-compose -f docker-compose.new.yml logs -f

# Specific service
docker-compose -f docker-compose.new.yml logs -f backend
docker-compose -f docker-compose.new.yml logs -f celery-worker
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose.new.yml restart

# Restart specific service
docker-compose -f docker-compose.new.yml restart backend
```

### Stop Platform

```bash
# Stop all services (preserves data)
docker-compose -f docker-compose.new.yml down

# Stop and remove volumes (clears all data)
docker-compose -f docker-compose.new.yml down -v
```

### Access Database

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.new.yml exec postgres psql -U ibkr_user -d ibkr_trading

# View strategies
SELECT * FROM strategy;

# View recent decisions
SELECT * FROM decision ORDER BY created_at DESC LIMIT 5;
```

### Monitor Task Queue

```bash
# Open Flower in browser
open http://localhost:5555

# View active workers
# View task history
# Monitor task execution times
```

## 🐛 Troubleshooting

### IBKR Connection Failed

**Problem**: Can't connect to IBKR Gateway

**Solutions**:
1. Ensure IBKR Gateway is running: https://localhost:5000
2. Log in to the gateway web interface
3. Check SSL certificate is accepted
4. Verify account ID in `.env` matches your IBKR account

### AI Analysis Failed

**Problem**: Workflow fails at AI analysis step

**Solutions**:
1. Check OpenAI API key is valid in `.env`
2. Verify API endpoint is accessible
3. Check AI request timeout (default 120s)
4. View Celery logs: `docker-compose -f docker-compose.new.yml logs celery-worker`

### No Charts Generated

**Problem**: Charts missing from analysis

**Solutions**:
1. Check MinIO is running: `docker-compose -f docker-compose.new.yml ps minio`
2. Access MinIO console: http://localhost:9001
3. Verify `ibkr-charts` bucket exists
4. Check chart service logs

### Database Connection Error

**Problem**: Backend can't connect to PostgreSQL

**Solutions**:
1. Check PostgreSQL is running: `docker-compose -f docker-compose.new.yml ps postgres`
2. Verify database credentials in `.env`
3. Wait 10 seconds after starting services for DB initialization
4. Restart backend: `docker-compose -f docker-compose.new.yml restart backend`

### Task Queue Not Processing

**Problem**: Workflows stay in "pending" state

**Solutions**:
1. Check Celery worker is running: `docker-compose -f docker-compose.new.yml ps celery-worker`
2. Check Redis is running: `docker-compose -f docker-compose.new.yml ps redis`
3. View worker logs: `docker-compose -f docker-compose.new.yml logs celery-worker`
4. Restart worker: `docker-compose -f docker-compose.new.yml restart celery-worker`

## 📝 Next Steps

Once you're comfortable with basic usage:

1. **Customize Workflows**: Modify workflow templates
2. **Adjust Risk Parameters**: Update strategy parameters
3. **Add Multiple Strategies**: Create strategies for different symbols
4. **Schedule Execution**: Use Celery Beat for periodic execution
5. **Monitor Performance**: Track P&L and decision accuracy
6. **Integrate AutoGen**: Enable multi-agent decision making (coming soon)

## 📚 More Information

- **Full Documentation**: See `README.implementation.md`
- **OpenSpec Proposal**: See `openspec/changes/add-fastapi-trading-webapp/`
- **API Reference**: http://localhost:8000/docs
- **Database Schema**: See `database/init.sql`

## 🆘 Need Help?

1. Check logs: `docker-compose -f docker-compose.new.yml logs -f`
2. Review OpenSpec documentation: `openspec/AGENTS.md`
3. Inspect service status: `docker-compose -f docker-compose.new.yml ps`
4. Verify configuration: `cat backend/.env`

---

**Happy Trading! 📈**

