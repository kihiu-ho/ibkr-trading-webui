# Design Document: FastAPI Trading WebApp

## Context

This design creates a comprehensive automated trading platform that integrates IBKR's trading capabilities with AI-powered technical analysis. The system is inspired by an n8n workflow (reference/workflow/IBKR_2_Indicator_4_Prod.json) that orchestrates multi-timeframe chart analysis, AI decision-making, and automated order execution.

### Background
- Current system: Simple Flask web UI for manual trading
- Goal: Automated trading with AI-driven decisions based on technical analysis
- Reference: n8n workflow demonstrates the desired process flow
- Stakeholders: Traders who want automated, data-driven trading decisions

### Constraints
- Must work with existing IBKR Client Portal Gateway
- Must support multiple trading strategies with configurable parameters
- Must maintain audit trail of all decisions and trades
- Must enforce risk management rules before order placement
- Must support OpenAI-compatible LLM APIs (not just OpenAI)

## Goals / Non-Goals

### Goals
1. **Automated Trading Workflow**: Implement the 2-indicator workflow (daily + weekly timeframe analysis)
2. **AI Integration**: Use LLMs to analyze charts and make trading recommendations
3. **Risk Management**: Enforce R-coefficient and profit margin thresholds
4. **Data Persistence**: Store all strategies, decisions, orders, and trades
5. **Modern Architecture**: Use FastAPI for better performance and auto-documentation
6. **Scalable Design**: Support multiple strategies running in parallel
7. **Audit Trail**: Complete logging of all workflow steps and decisions

### Non-Goals
1. Real-time streaming data (use polling instead)
2. Mobile app (web-only for now)
3. Backtesting engine (future enhancement)
4. Multi-user authentication (single user for MVP)
5. Custom indicator development (use standard indicators only)

## Architectural Decisions

### 1. Technology Stack

**Backend: FastAPI**
- **Decision**: Use FastAPI instead of Flask
- **Rationale**: 
  - Automatic OpenAPI documentation
  - Native async support for better performance
  - Built-in request validation with Pydantic
  - Type hints improve code quality
  - Better suited for API-first architecture
- **Alternatives Considered**: 
  - Flask: Current solution, but lacks modern features
  - Django: Too heavy for this use case
  - Node.js: Team prefers Python

**Database: PostgreSQL**
- **Decision**: Use PostgreSQL with SQLAlchemy ORM
- **Rationale**:
  - Reliable, production-ready RDBMS
  - JSON/JSONB support for flexible data (e.g., strategy parameters)
  - Good performance for transactional workloads
  - Excellent Docker support
- **Alternatives Considered**:
  - SQLite: Not suitable for concurrent workflows
  - NocoDB: Reference uses it, but direct PostgreSQL gives more control
  - MongoDB: Overkill, relationships are mostly relational

**Frontend: Tailwind CSS**
- **Decision**: Server-side rendered HTML with Tailwind CSS
- **Rationale**:
  - Simple, fast development
  - No build step complexity
  - Modern, responsive design with utility classes
  - Jinja2 templates integrate well with FastAPI
- **Alternatives Considered**:
  - React/Vue: Overkill for this UI complexity
  - Bootstrap: Tailwind more modern and flexible
  - Plain CSS: Too much custom CSS to write

### 2. Service Architecture

**Service-Oriented Design**
```
├── api_service.py      # IBKR API wrapper
├── chart_service.py    # Chart generation with indicators
├── db_service.py       # Database operations
├── order_service.py    # Order management logic
├── storage_service.py  # MinIO/S3 operations
├── ai_service.py       # LLM integration
├── workflow_service.py # Workflow orchestration
└── risk_service.py     # Risk calculations
```

- **Decision**: Separate services with single responsibilities
- **Rationale**:
  - Clear separation of concerns
  - Easy to test each service independently
  - Services can be reused across different endpoints
  - Matches the reference architecture pattern
- **Trade-offs**: More files, but better maintainability

### 3. Workflow Orchestration

**Sequential Workflow Pattern** (based on n8n reference)
```
1. Check Authentication → 
2. Get Strategy Config → 
3. Loop Through Symbols → 
   3a. Fetch Daily Chart Data
   3b. Fetch Weekly Chart Data
   3c. Generate Charts (upload to MinIO)
   3d. Analyze Daily Chart (AI)
   3e. Analyze Weekly Chart (AI)
   3f. Merge & Consolidate Analysis (AI)
   3g. Generate Trading Decision (AI)
   3h. Validate Risk Criteria
   3i. Place Order (if valid)
   3j. Wait/Delay
4. Loop Next Symbol
```

- **Decision**: Implement workflow as a sequential service method
- **Rationale**:
  - Matches proven n8n workflow
  - Easy to understand and debug
  - Each step can be logged and monitored
  - Errors can be caught at each stage
- **Alternatives Considered**:
  - Celery tasks: Too much infrastructure complexity
  - Background threads: Harder to debug and monitor
  - Async/await: Complicates error handling for this use case

### 4. Data Model Design

**Core Entities**
1. **Strategy**: Trading strategy configuration
   - Name, type (e.g., "two_indicator")
   - Parameters as JSON (period_1, bar_1, period_2, bar_2)
   - Associated codes (symbols)

2. **Code**: Financial instrument
   - Symbol, CONID, exchange
   - Many-to-many with strategies

3. **Market Data**: Historical price/indicator data
   - CONID, period, bar, data (JSONB)
   - Cached for performance

4. **Decision**: AI-generated trading recommendation
   - Code, strategy used, current price, target price
   - Type (buy/sell/hold), profit margin, R coefficient
   - Analysis text

5. **Orders**: Order lifecycle
   - IBKR order ID, CONID, side, quantity, price
   - Status (submitted, filled, cancelled)
   - Linked to decision

6. **Trades**: Executed trades
   - Entry/exit prices, P&L
   - Linked to order

7. **Positions**: Current holdings
   - Quantity, average cost, current value
   - Unrealized P&L

- **Decision**: Normalized schema with foreign keys
- **Rationale**:
  - Clear audit trail from decision → order → trade
  - Easy to query trade history and performance
  - Can join to see which strategy generated which results
- **Note**: Schema reference in `reference/schema/*.xlsx` informs table structure, but we define SQL directly (not import Excel)

### 5. AI Integration Design

**OpenAI-Compatible API**
- **Decision**: Support any OpenAI-compatible API endpoint
- **Rationale**:
  - Not locked into OpenAI pricing
  - Can use alternatives: Gemini (via OpenAI endpoint), local models, Azure OpenAI
  - Reference workflow uses Gemini 2.0 Flash
- **Configuration**: 
  ```
  OPENAI_API_BASE=https://generativelanguage.googleapis.com/v1beta/openai/
  OPENAI_API_KEY=your-key
  OPENAI_MODEL=gemini-2.0-flash-exp
  ```

**Prompt Strategy**
1. **Daily Chart Analysis**: Detailed single-timeframe technical analysis
2. **Weekly Chart Analysis**: Medium-term trend confirmation
3. **Consolidation**: Synthesize multi-timeframe insights
4. **Decision Making**: Structured output with buy/sell/hold + risk params

- **Decision**: Use separate prompts for each analysis stage
- **Rationale**:
  - Better focus per task
  - Can optimize each prompt independently
  - Matches n8n workflow structure
  - Easier to debug when analysis fails

**Structured Output**
- **Decision**: Use JSON schema for trading decision output
- **Rationale**:
  - Guarantees parseable results
  - No regex or string parsing fragility
  - Easy to validate before order placement
- **Schema**:
  ```json
  {
    "code": "TSLA",
    "type": "buy" | "sell" | "hold",
    "current_price": 221.86,
    "target_price": 250.00,
    "stop_loss": 210.00,
    "profit_margin": 0.127,
    "R_coefficient": 2.5,
    "strategy_used": "Indicator_1Y_1D_1Y_1W"
  }
  ```

### 6. Chart Generation

**Technical Indicators**
- SuperTrend (10, 3)
- Moving Averages (20, 50, 200 SMA)
- MACD (12, 26, 9)
- RSI (14)
- Bollinger Bands (20, 2)
- Volume bars

**Library: Plotly**
- **Decision**: Use Plotly for chart generation
- **Rationale**:
  - Excellent candlestick and financial chart support
  - Can export as PNG for AI analysis
  - Interactive charts for web UI
  - Better than matplotlib for financial data
- **Alternatives Considered**:
  - matplotlib: Reference uses it, but Plotly is more modern
  - mplfinance: Limited interactivity
  - TradingView: External dependency, cost

### 8. Message Queue System

**Task Queue: Celery + Redis**
- **Decision**: Use Celery task queue with Redis broker for concurrent workflow execution
- **Rationale**:
  - Industry standard for Python async tasks
  - Redis is fast, lightweight, easy to deploy
  - Built-in retry mechanisms and error handling
  - Excellent monitoring tools (Flower)
  - Scales horizontally (add more workers)
- **Alternatives Considered**:
  - RabbitMQ: More features but heavier, harder to deploy
  - Python threading: Not scalable, no task management
  - FastAPI BackgroundTasks: Too simple, no persistence or retry
  - Apache Kafka: Overkill for this use case

**Implementation Details**:
- Celery workers run workflow tasks
- Redis stores task queue and results
- Task priority queue (high/normal/low)
- Result TTL: 24 hours (configurable)
- Max retries: 3 with exponential backoff
- Task timeout: 1 hour per workflow

### 9. Multi-Agent Framework

**Framework: Microsoft AutoGen**
- **Decision**: Integrate AutoGen for multi-agent decision-making
- **Rationale**:
  - Designed for multi-agent collaboration
  - Built-in code execution (for custom calculations)
  - Human-in-the-loop support
  - Flexible agent configuration
  - Works with any OpenAI-compatible API
  - Active development and community
- **Alternatives Considered**:
  - LangChain Agents: More complex, less focused on multi-agent collaboration
  - CrewAI: Newer, less mature
  - Custom implementation: Too much work, reinventing wheel
  - Single LLM with long prompt: Less sophisticated reasoning

**Agent Types**:
1. **TechnicalAnalystAgent**: Analyzes charts, indicators, patterns
2. **RiskManagerAgent**: Calculates position size, validates risk/reward
3. **FundamentalAgent** (optional): Analyzes news, earnings, fundamentals
4. **SentimentAgent** (optional): Analyzes market sentiment from news/social
5. **ExecutorAgent**: Consolidates inputs, makes final decision

**Conversation Flow**:
```
1. TechnicalAnalystAgent: "Chart shows bullish SuperTrend, RSI oversold"
2. RiskManagerAgent: "Stop-loss at $100, target $120, R=2.5, position size 50 shares"
3. FundamentalAgent: "Earnings beat expectations, revenue up 15%"
4. SentimentAgent: "Social sentiment positive, 70% bullish mentions"
5. ExecutorAgent: "Consensus: BUY. All factors align. Placing order."
```

**Storage: MinIO**
- **Decision**: Store chart images in MinIO (S3-compatible)
- **Rationale**:
  - Self-hosted, no cloud vendor lock-in
  - S3-compatible API
  - Easy Docker deployment
  - Reference workflow uses MinIO (S3)
- **Alternatives Considered**:
  - Local filesystem: Not scalable, hard to share
  - AWS S3: Adds cloud dependency and cost

### 7. Risk Management

**Pre-Trade Validation Rules**
1. **R-Coefficient**: Must be >= 1.0
   - Formula: `(target_price - current_price) / (stop_loss - current_price)`
   - Ensures reward exceeds risk
2. **Profit Margin**: Must be >= 5%
   - Formula: `|target_price - current_price| / current_price`
   - Ensures meaningful profit potential
3. **Signal Type**: Must be "buy" or "sell" (not "hold")

- **Decision**: Enforce rules before order placement
- **Rationale**:
  - Prevents emotional/bad AI decisions
  - Configurable thresholds
  - Audit trail shows why orders were rejected
- **Implementation**: `risk_service.validate_decision()`

**Position Limits** (Future)
- Max position size per symbol
- Max total portfolio exposure
- Max loss per trade

## Migration Plan

### Phase 1: Setup & Infrastructure
1. Create Docker Compose with all services
2. Initialize PostgreSQL database with schema
3. Configure MinIO bucket
4. Set up .env configuration
5. Test service connectivity

### Phase 2: Core Services
1. Implement database models and services
2. Build IBKR API integration
3. Create chart generation service
4. Integrate MinIO storage
5. Build AI service with prompt templates

### Phase 3: Workflow Engine
1. Implement workflow orchestration
2. Add strategy management
3. Test end-to-end workflow execution
4. Add error handling and logging

### Phase 4: API & Frontend
1. Build FastAPI endpoints
2. Create Tailwind CSS templates
3. Implement order management UI
4. Add portfolio tracking UI
5. Test complete user flows

### Phase 5: Testing & Documentation
1. Write unit and integration tests
2. Performance testing
3. Update documentation
4. Create deployment guide

### Rollback Plan
- Keep existing Flask app running on port 5056
- New FastAPI app on port 8000
- If issues arise, revert to Flask app
- Database migrations use Alembic for rollback capability

## Risks / Trade-offs

### Risks & Mitigations

**Risk 1: AI API Costs**
- Mitigation: Cache analysis results, use cheaper models (Gemini vs GPT-4), rate limiting
- Monitoring: Track API calls and costs

**Risk 2: IBKR API Rate Limits**
- Mitigation: Respect rate limits, add backoff/retry logic, queue requests
- Monitoring: Log all API calls with timestamps

**Risk 3: Bad Trading Decisions**
- Mitigation: Risk validation rules, manual approval mode (future), paper trading first
- Monitoring: Alert on unusual decisions or consecutive losses

**Risk 4: Chart Analysis Failures**
- Mitigation: Retry logic, fallback to simpler prompts, human review
- Monitoring: Log all AI responses and errors

**Risk 5: Database Locking**
- Mitigation: Use proper transaction isolation, connection pooling
- Monitoring: Slow query logging

**Risk 6: Service Dependencies**
- Mitigation: Health checks, graceful degradation, clear error messages
- Monitoring: Service uptime checks

### Trade-offs

**Simplicity vs Features**
- Chosen: Start with 2-indicator workflow, expand later
- Rationale: Proven workflow from reference, reduce initial complexity

**Real-time vs Polling**
- Chosen: Polling with configurable intervals
- Rationale: Simpler implementation, IBKR API designed for polling

**Sync vs Async**
- Chosen: Synchronous workflow execution
- Rationale: Easier debugging, matches n8n sequential flow

**Full Automation vs Manual Review**
- Chosen: Full automation with risk rules
- Rationale: Matches reference workflow, can add manual mode later

## Resolved Design Questions

### 1. Multiple Strategies Running Simultaneously

**Decision**: Implement message queue system (Redis/Celery) for concurrent workflow execution

**Implementation**:
- Use **Celery** task queue with **Redis** as message broker
- Each workflow execution becomes an asynchronous Celery task
- Multiple strategies can run concurrently, each processing symbols in parallel
- Task priorities ensure critical workflows run first
- Result backend stores task status and results
- Frontend polls for task status or uses WebSocket for real-time updates

**Benefits**:
- True concurrent execution (not just sequential with delays)
- Better resource utilization
- Scalable: can add worker nodes
- Fault tolerance: failed tasks can retry
- Task monitoring and management

**Architecture**:
```
Frontend → API → Celery Task Queue (Redis)
                       ↓
                 Worker Pool (1-N workers)
                       ↓
                 IBKR API, Database, AI Service
```

### 2. Multiple Workflows and Strategies (Frontend Configuration)

**Decision**: Allow users to define custom workflows with different analysis patterns

**Features**:
- **Workflow Templates**: Pre-defined patterns (2-indicator, 3-indicator, single-timeframe, custom)
- **Strategy Builder UI**: Visual configuration of workflow steps
- **Parameter Customization**: Timeframes, indicators, AI prompts, risk thresholds per workflow
- **Workflow Versioning**: Track changes to workflows over time
- **Clone & Modify**: Duplicate existing workflows as starting points

**Database Schema Enhancement**:
```
workflow:
  - id, name, type (template), steps (JSON), created_at, updated_at

strategy:
  - id, name, workflow_id (FK), param (JSON), codes[], active, created_at

workflow_execution:
  - id, strategy_id, workflow_id, status, started_at, completed_at, results
```

**Workflow Step Types**:
- `fetch_data`: Get historical data
- `generate_chart`: Create chart with indicators
- `ai_analyze`: Send to LLM for analysis
- `consolidate`: Merge multiple analyses
- `decide`: Generate trading decision
- `validate_risk`: Check risk criteria
- `place_order`: Execute order

### 3. Microsoft AutoGen Framework Integration

**Decision**: Integrate AutoGen for multi-agent decision-making and advanced analysis

**Use Cases**:
1. **Multi-Agent Analysis**: Different agents analyze different aspects (technical, fundamental, sentiment)
2. **Collaborative Decision**: Agents debate and reach consensus on trading decisions
3. **Risk Agent**: Dedicated agent for risk assessment and position sizing
4. **Code Execution**: AutoGen agents can write and execute Python code for custom calculations
5. **Human-in-the-Loop**: Optional human approval before order placement

**AutoGen Architecture**:
```
Workflow Trigger
    ↓
AutoGen Orchestrator
    ↓
Multiple Agents (running concurrently):
- TechnicalAnalystAgent: Analyze charts, indicators
- FundamentalAgent: Check news, fundamentals (optional)
- RiskManagerAgent: Calculate position size, validate risk
- SentimentAgent: Analyze market sentiment (optional)
- ExecutorAgent: Consolidate and make final decision
    ↓
Consensus Decision
    ↓
Order Placement
```

**Agent Configuration**:
```python
# Each agent has:
- system_prompt: Role and instructions
- model: LLM model to use (can be different per agent)
- tools: Functions agent can call
- max_iterations: Limit for agent interactions
- human_input_mode: NEVER, ALWAYS, TERMINATE
```

**Benefits**:
- More sophisticated analysis (multiple perspectives)
- Specialization (agents focus on specific domains)
- Explainability (see reasoning from each agent)
- Flexibility (add/remove agents, change prompts)
- Code interpreter (agents can compute custom metrics)

**Integration Points**:
- AutoGen workflow type: `autogen_multi_agent`
- Configuration stored in strategy.param
- Each agent's analysis logged to database
- Final consensus stored as decision

### Other Questions

4. **Should we support live trading immediately or start with paper trading?**
   - Solution: Support both via `PAPER_TRADING_MODE` flag

5. **How long to retain historical data?**
   - Solution: Keep all data, add archival job later if needed

6. **Should we notify users of trade executions?**
   - Solution: Yes, webhook/notification service (email, Telegram) - medium priority

7. **How to handle partial fills?**
   - Solution: Track order status, update trades when filled, handle partials as separate trades

## Success Criteria

The implementation is successful when:

1. ✅ Can define a trading strategy with 2 timeframes
2. ✅ Workflow executes: fetch data → generate charts → AI analysis → decision → order
3. ✅ Charts are generated with all required indicators
4. ✅ AI produces valid trading decisions with risk parameters
5. ✅ Risk rules prevent bad trades (R < 1 or profit < 5%)
6. ✅ Orders are placed automatically to IBKR
7. ✅ All steps are logged to database
8. ✅ UI allows viewing strategies, decisions, orders, and portfolio
9. ✅ Can run multiple symbols through the workflow
10. ✅ System is containerized and can be deployed with Docker Compose

