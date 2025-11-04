# IBKR Airflow Workflow Design

## Context

The IBKR trading system needs production-grade workflow orchestration for automated strategy execution. We've already integrated Airflow and MLflow into the Docker Compose setup. Now we need to design and implement the actual trading workflows as Airflow DAGs.

### Constraints
- Must use existing IBKR service APIs
- Must work with shared PostgreSQL database
- Must integrate with MLflow for tracking
- Must handle IBKR API rate limits and retries
- Must support multiple concurrent strategies

### Reference Implementation
Using the fraud detection training pipeline from `/Users/he/git/ibkr-trading-webui/reference/airflow/` as a pattern:
- YAML-based configuration
- MLflow experiment tracking
- Structured logging
- Environment validation
- Error handling with retry logic

## Goals / Non-Goals

### Goals
- ✅ Create production-ready Airflow DAGs for IBKR trading
- ✅ Integrate with existing backend services (no duplication)
- ✅ Support scheduled execution with cron syntax
- ✅ Track all executions with MLflow
- ✅ Handle failures gracefully with retries
- ✅ Provide clear monitoring and debugging

### Non-Goals
- ❌ Replace existing Celery tasks (complement, don't replace)
- ❌ Rewrite backend services (use existing APIs)
- ❌ Change frontend (backend workflow only)
- ❌ Implement new trading strategies (orchestrate existing ones)

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Airflow Scheduler                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            IBKR Trading Strategy DAG                      │   │
│  │                                                            │   │
│  │  1. Validate Environment                                  │   │
│  │  2. Check IBKR Authentication                             │   │
│  │  3. Fetch Market Data → Cache in DB                       │   │
│  │  4. Calculate Technical Indicators                        │   │
│  │  5. Generate Charts → Upload to MinIO                     │   │
│  │  6. LLM Signal Generation (with prompt system)            │   │
│  │  7. Risk Assessment                                       │   │
│  │  8. Place Orders (if signals valid)                       │   │
│  │  9. Update Portfolio                                      │   │
│  │ 10. Log to MLflow                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Services                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐         │
│  │ IBKR Service│  │ Chart Service│  │ Signal Service │         │
│  └─────────────┘  └──────────────┘  └────────────────┘         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐         │
│  │Order Service│  │Portfolio Svc │  │ Indicator Svc  │         │
│  └─────────────┘  └──────────────┘  └────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│             External Services & Storage                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────────┐         │
│  │IBKR GW  │  │MinIO    │  │MLflow   │  │PostgreSQL  │         │
│  └─────────┘  └─────────┘  └─────────┘  └────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### DAG Design Patterns

#### 1. Main Trading Strategy DAG
**Purpose**: Execute complete trading workflow for a strategy
**Schedule**: Per-strategy configuration (e.g., `0 9 * * 1-5` for 9 AM weekdays)
**Key Features**:
- Dynamic configuration from database
- MLflow experiment tracking
- Error recovery with retries
- Conditional task execution (skip if market closed)

#### 2. Market Data Collection DAG
**Purpose**: Collect and cache market data for multiple symbols
**Schedule**: Every 1 minute during market hours
**Key Features**:
- Parallel fetching for multiple symbols
- Rate limit handling
- Data validation
- Cache updates

#### 3. Portfolio Monitoring DAG
**Purpose**: Monitor positions and update portfolio state
**Schedule**: Every 5 minutes
**Key Features**:
- Position reconciliation
- P&L calculation
- Alert triggers
- Performance metrics

## Decisions

### Decision 1: Use HTTP API Calls vs Direct Database Access
**Choice**: Use HTTP API calls to backend services

**Rationale**:
- ✅ Maintains service boundaries and encapsulation
- ✅ Reuses existing authentication and validation logic
- ✅ Easier to test and debug
- ✅ Reduces database coupling
- ⚠️ Slightly higher latency (acceptable for scheduled workflows)

**Alternative Considered**: Direct database access
- ❌ Breaks service encapsulation
- ❌ Requires duplicating business logic
- ❌ Harder to maintain

### Decision 2: MLflow Tracking Granularity
**Choice**: Track at workflow execution level (DAG run)

**Rationale**:
- ✅ Complete picture of workflow performance
- ✅ Can track individual task metrics
- ✅ Easy to compare different strategy executions
- ✅ Aligns with fraud detection reference pattern

**Alternative Considered**: Track only final results
- ❌ Loses intermediate step insights
- ❌ Harder to debug failures

### Decision 3: Configuration Management
**Choice**: YAML + Database hybrid

**Rationale**:
- ✅ YAML for workflow structure (DAG definition, retry policies)
- ✅ Database for strategy-specific params (symbols, indicators)
- ✅ Separates workflow logic from business logic
- ✅ Allows dynamic strategy updates

**Alternative Considered**: All in database
- ❌ Harder to version control workflows
- ❌ More complex DAG generation

### Decision 4: Task Dependency Model
**Choice**: Linear with conditional branches

**Rationale**:
- ✅ Simple to understand and debug
- ✅ Clear execution order
- ✅ Supports skip logic for closed markets
- ⚠️ Not optimized for maximum parallelism (acceptable trade-off)

**Alternative Considered**: Fully parallelized
- ❌ Complex dependency management
- ❌ Harder to debug
- ❌ IBKR API has rate limits anyway

## Component Design

### 1. Custom Airflow Hooks

#### `IBKRHook`
```python
class IBKRHook(BaseHook):
    """Hook for IBKR API interaction via backend service."""
    
    def get_conn(self) -> httpx.AsyncClient:
        """Get HTTP client with auth."""
        
    def check_auth(self) -> bool:
        """Verify IBKR authentication status."""
        
    def get_market_data(self, symbol: str) -> Dict:
        """Fetch market data snapshot."""
        
    def place_order(self, order_params: Dict) -> Dict:
        """Place order via IBKR."""
```

### 2. Custom Operators

#### `IBKRMarketDataOperator`
```python
class IBKRMarketDataOperator(BaseOperator):
    """Fetch and cache market data for symbols."""
    
    def __init__(self, symbols: List[str], **kwargs):
        self.symbols = symbols
        
    def execute(self, context):
        # Fetch data for each symbol
        # Cache in database
        # Return summary
```

#### `LLMSignalGeneratorOperator`
```python
class LLMSignalGeneratorOperator(BaseOperator):
    """Generate trading signals using LLM analysis."""
    
    def __init__(self, strategy_id: int, **kwargs):
        self.strategy_id = strategy_id
        
    def execute(self, context):
        # Load chart from MinIO
        # Call LLM with prompt
        # Parse signal
        # Save to database
```

### 3. Sensors

#### `MarketOpenSensor`
```python
class MarketOpenSensor(BaseSensorOperator):
    """Wait for market to open before executing trades."""
    
    def poke(self, context):
        # Check if market is open
        # Return True if open, False otherwise
```

### 4. Configuration Structure

```yaml
# config/trading_workflow.yaml
workflows:
  momentum_strategy:
    dag_id: "ibkr_momentum_strategy"
    schedule: "0 9 * * 1-5"  # 9 AM weekdays
    description: "Momentum-based trading strategy"
    default_args:
      owner: "trading"
      retries: 3
      retry_delay: 300  # 5 minutes
      execution_timeout: 1800  # 30 minutes
    
    tasks:
      - name: "validate_environment"
        type: "bash"
        command: "echo 'Validating...'"
        
      - name: "check_ibkr_auth"
        type: "ibkr_auth_check"
        retry_on_failure: true
        
      - name: "fetch_market_data"
        type: "market_data"
        params:
          symbols: ["AAPL", "GOOGL", "MSFT"]
          fields: ["last", "bid", "ask", "volume"]
          
      - name: "calculate_indicators"
        type: "technical_indicators"
        depends_on: ["fetch_market_data"]
        
      - name: "generate_charts"
        type: "chart_generation"
        depends_on: ["calculate_indicators"]
        
      - name: "llm_signal_generation"
        type: "llm_signal"
        depends_on: ["generate_charts"]
        params:
          use_prompt_system: true
          
      - name: "risk_assessment"
        type: "risk_check"
        depends_on: ["llm_signal_generation"]
        
      - name: "place_orders"
        type: "order_placement"
        depends_on: ["risk_assessment"]
        trigger_rule: "all_success"
        
      - name: "update_portfolio"
        type: "portfolio_update"
        depends_on: ["place_orders"]
        
mlflow:
  tracking_uri: "http://mlflow-server:5500"
  experiment_name: "ibkr_trading_strategies"
  
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Implementation Plan

### Phase 1: Core Infrastructure (Days 1-2)
1. Create Airflow plugins directory structure
2. Implement `IBKRHook` base class
3. Set up configuration loader
4. Create base operators
5. Set up MLflow integration

### Phase 2: Operators & Sensors (Days 3-4)
1. Implement `IBKRMarketDataOperator`
2. Implement `TechnicalIndicatorOperator`
3. Implement `ChartGenerationOperator`
4. Implement `LLMSignalGeneratorOperator`
5. Implement `RiskAssessmentOperator`
6. Implement `OrderPlacementOperator`
7. Implement `MarketOpenSensor`

### Phase 3: DAG Definitions (Day 5)
1. Create main trading strategy DAG template
2. Create market data collection DAG
3. Create portfolio monitoring DAG
4. Add dynamic DAG generation from database

### Phase 4: Testing & Documentation (Day 6)
1. Unit tests for operators
2. Integration tests with backend
3. End-to-end workflow test
4. Documentation and examples
5. Deployment guide

## Risks / Trade-offs

### Risk 1: IBKR API Rate Limits
**Impact**: High - Could block workflow execution
**Mitigation**:
- Implement exponential backoff
- Cache market data aggressively
- Batch requests where possible
- Add rate limit sensor

### Risk 2: LLM Call Latency
**Impact**: Medium - Could slow workflow
**Mitigation**:
- Set reasonable timeouts
- Use async calls where possible
- Cache LLM responses for identical inputs
- Consider parallel LLM calls for multiple symbols

### Risk 3: Airflow Resource Consumption
**Impact**: Medium - Memory/CPU usage
**Mitigation**:
- Limit concurrent DAG runs
- Optimize operator memory usage
- Use pools for resource management
- Monitor with Prometheus

### Risk 4: Workflow Failure During Market Hours
**Impact**: High - Missed trading opportunities
**Mitigation**:
- Aggressive retry policies
- Alert mechanisms (email/Slack)
- Fallback execution paths
- Manual override capabilities

## Migration Plan

### Step 1: Deploy Infrastructure
- Airflow already running
- Add new DAG files to mounted volume
- No service restarts needed

### Step 2: Test with Single Strategy
- Deploy one simple strategy DAG
- Monitor execution
- Validate results
- Fix any issues

### Step 3: Gradual Rollout
- Deploy additional strategy DAGs
- Run in parallel with existing Celery tasks
- Compare results
- Migrate strategies one by one

### Step 4: Full Migration
- All strategies on Airflow
- Keep Celery for one-off tasks
- Update documentation
- Training for team

### Rollback Plan
- Keep existing Celery task system
- Can disable Airflow DAGs individually
- No destructive changes to database
- Easy to switch back

## Open Questions

1. **Should we support backtesting workflows in Airflow?**
   - Benefit: Consistent orchestration for live and backtest
   - Cost: Additional complexity
   - Decision: Phase 2 feature

2. **How to handle strategy parameter updates during active runs?**
   - Option A: Finish current run, use new params next run
   - Option B: Cancel current run, restart with new params
   - Decision: Option A (safer)

3. **Should we use Airflow XComs for inter-task data passing?**
   - Benefit: Simple, built-in mechanism
   - Cost: Limited to small data, pickle-based
   - Decision: Use for metadata only, use database for large data

4. **How to handle market holidays automatically?**
   - Option A: Sensor checks market calendar API
   - Option B: Pre-configured calendar in config
   - Decision: Option A (more flexible)

