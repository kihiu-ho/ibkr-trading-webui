## Context
The current trading workflow processes a single symbol at a time. To support multi-symbol NASDAQ trading strategies (TSLA, NVDA), we need to:
- Process multiple symbols in parallel
- Generate charts for multiple timeframes (daily, weekly)
- Analyze multiple charts with LLM
- Execute orders and track portfolio
- Visualize all artifacts in a unified interface

## Goals / Non-Goals

### Goals
- Support 2+ symbols (TSLA, NVDA) in a single workflow run
- Generate daily and weekly charts with technical indicators for each symbol
- Pass multi-chart analysis to LLM for comprehensive signal generation
- Place orders, retrieve trades, and monitor portfolio via IBKR API
- Track all artifacts (inputs, outputs, charts, LLM analysis, signals, orders, trades, portfolio) in MLflow
- Visualize artifacts grouped by execution_id with Airflow integration
- Maintain full lineage from market data → charts → analysis → signals → orders → trades → portfolio

### Non-Goals
- Real-time streaming market data (batch processing only)
- Backtesting capabilities (future enhancement)
- Multi-account support (single account per workflow)
- Advanced order types beyond LMT/MKT (basic orders only)

## Decisions

### Decision: Parallel Symbol Processing
**What**: Process multiple symbols (TSLA, NVDA) in parallel using Airflow task groups
**Why**: Reduces total workflow execution time and enables independent symbol analysis
**Alternatives considered**:
- Sequential processing: Simpler but slower
- Dynamic task mapping: More flexible but complex for fixed symbol list
**Rationale**: Fixed symbol list (TSLA, NVDA) makes task groups ideal; parallel execution improves performance

### Decision: Multi-Timeframe Chart Analysis
**What**: Generate both daily and weekly charts for each symbol and pass both to LLM
**Why**: Multi-timeframe analysis provides better trading signals by considering short-term and long-term trends
**Alternatives considered**:
- Single timeframe: Simpler but less comprehensive
- More timeframes (hourly, monthly): Adds complexity without proportional benefit
**Rationale**: Daily + weekly provides optimal balance of detail and trend analysis

### Decision: Artifact Grouping by Execution ID
**What**: Group artifacts by execution_id (Airflow run) in the visualization
**Why**: Enables users to see all artifacts generated in a single workflow run together
**Alternatives considered**:
- Group by symbol: Useful but loses workflow context
- Group by type: Simple but doesn't show workflow relationships
**Rationale**: Execution_id grouping maintains workflow lineage and makes debugging easier

### Decision: MLflow for All Artifact Tracking
**What**: Use MLflow to track all workflow artifacts (not just ML models)
**Why**: Provides unified experiment tracking, lineage, and artifact storage
**Alternatives considered**:
- Database-only: Simpler but lacks experiment tracking features
- Separate artifact store: More complex, loses integration
**Rationale**: MLflow provides experiment tracking, artifact versioning, and integration with MinIO

### Decision: Airflow Run Details Integration
**What**: Display artifacts in Airflow run details modal with bidirectional navigation
**Why**: Provides seamless workflow-to-artifact navigation for debugging and analysis
**Alternatives considered**:
- Separate artifact page only: Loses workflow context
- Airflow-only view: Doesn't leverage artifact detail pages
**Rationale**: Bidirectional integration provides best user experience

## Risks / Trade-offs

### Risk: IBKR API Rate Limits
**Mitigation**: Implement exponential backoff, respect rate limits, add delays between API calls
**Trade-off**: Slower workflow execution but reliable API interaction

### Risk: LLM API Costs
**Mitigation**: Use efficient prompts, cache analysis results when possible, monitor API usage
**Trade-off**: Higher costs for comprehensive analysis but better trading signals

### Risk: Large Artifact Storage
**Mitigation**: Use MinIO for large files (charts), database for metadata only, implement cleanup policies
**Trade-off**: More storage required but better artifact management

### Risk: Workflow Complexity
**Mitigation**: Modular task design, clear error handling, comprehensive logging
**Trade-off**: More complex workflow but more powerful capabilities

## Migration Plan

### Phase 1: Multi-Symbol Support
1. Update DAG to accept symbol list parameter
2. Implement parallel market data fetching
3. Test with TSLA and NVDA

### Phase 2: Multi-Timeframe Charts
1. Extend chart generator for daily/weekly
2. Update LLM analyzer for multi-chart input
3. Test chart generation and LLM analysis

### Phase 3: IBKR Integration
1. Implement order placement service
2. Add trade retrieval and portfolio management
3. Test with paper trading account

### Phase 4: Artifact Visualization
1. Update artifacts API for grouping
2. Enhance frontend grouped view
3. Add Airflow integration
4. Test visualization and navigation

### Rollback Plan
- Keep existing single-symbol workflow as fallback
- Feature flags for multi-symbol vs single-symbol mode
- Database migrations are additive (no breaking changes)

## Open Questions
- Should we support dynamic symbol lists from configuration?
- What is the maximum number of symbols we should support per workflow?
- Should we implement artifact cleanup policies for old executions?

