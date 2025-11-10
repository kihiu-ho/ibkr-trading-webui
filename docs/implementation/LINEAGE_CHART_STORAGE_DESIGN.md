# Lineage & Chart Storage Design - OpenSpec 2

## Overview
Comprehensive system for tracking data lineage, storing charts, and managing ML artifacts across the IBKR trading workflow using open source tools.

## Architecture

### Core Components

#### 1. **PostgreSQL Database** (Primary Storage)
```sql
-- Workflow Lineage Table
CREATE TABLE workflow_lineage (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    execution_id VARCHAR(255) NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    step_number INTEGER NOT NULL,
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    metadata JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_workflow_execution (workflow_id, execution_id),
    INDEX idx_step_name (step_name),
    INDEX idx_created_at (created_at DESC)
);

-- Enhanced Artifacts Table
CREATE TABLE artifacts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'llm', 'chart', 'signal', 'market_data'
    symbol VARCHAR(50),
    workflow_id VARCHAR(255),
    execution_id VARCHAR(255),
    step_name VARCHAR(50),
    mlflow_run_id VARCHAR(255),
    mlflow_experiment_id VARCHAR(255),

    -- Content
    prompt TEXT,           -- For LLM artifacts
    response TEXT,         -- For LLM artifacts
    image_path TEXT,       -- For chart artifacts
    chart_data JSONB,      -- Chart configuration/data
    signal_data JSONB,     -- Trading signal details
    metadata JSONB,        -- Additional metadata

    -- Metrics
    prompt_length INTEGER,
    response_length INTEGER,
    model_name VARCHAR(100),
    confidence_score DECIMAL(3,2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_type_symbol (type, symbol),
    INDEX idx_workflow_execution (workflow_id, execution_id),
    INDEX idx_mlflow_run (mlflow_run_id)
);
```

#### 2. **MinIO Object Storage** (Chart & Binary Storage)
```
Bucket Structure:
/ml-experiments/
  └── {experiment_id}/
      ├── charts/
      │   ├── {workflow_id}_{execution_id}_daily.png
      │   ├── {workflow_id}_{execution_id}_weekly.png
      │   └── {workflow_id}_{execution_id}_indicators.json
      ├── models/
      │   └── {model_name}_{version}.pkl
      └── artifacts/
          └── {artifact_id}_{type}.{ext}

/trading-data/
  └── {symbol}/
      ├── raw/
      │   └── {date}_{source}.json
      └── processed/
          └── {date}_indicators.json
```

#### 3. **MLflow Tracking Server** (Experiment Management)
```python
# MLflow Experiment Structure
experiment_name = f"trading_workflow_{symbol}"
run_tags = {
    'workflow_type': 'trading_signal',
    'symbol': symbol,
    'dag_id': dag.dag_id,
    'airflow_run_id': dag_run.run_id,
    'signal_action': signal.action
}

# Parameters
mlflow.log_params({
    'symbol': symbol,
    'position_size': position_size,
    'llm_provider': llm_provider,
    'signal_action': signal.action,
    'signal_confidence': signal.confidence_score
})

# Metrics
mlflow.log_metrics({
    'latest_price': market_data.latest_price,
    'confidence_score': signal.confidence_score,
    'portfolio_value': portfolio.total_value,
    'order_placed': 1 if order_placed else 0
})

# Artifacts
mlflow.log_artifact('daily_chart.png')
mlflow.log_artifact('weekly_chart.png')
mlflow.log_artifact_dict(signal_data, 'trading_signal.json')
mlflow.log_artifact_dict(portfolio_data, 'portfolio.json')
```

#### 4. **Airflow XCom** (Inter-task Communication)
```python
# Store intermediate results in XCom
task_instance.xcom_push(key='market_data', value=market_data.model_dump_json())
task_instance.xcom_push(key='daily_chart', value=chart_result.model_dump_json())
task_instance.xcom_push(key='trading_signal', value=signal.model_dump_json())

# Retrieve data between tasks
market_data_json = task_instance.xcom_pull(task_ids='fetch_market_data', key='market_data')
market_data = MarketData.model_validate_json(market_data_json)
```

## Workflow Data Flow

### Phase 1: Market Data Collection
```python
# Store in lineage
store_lineage_record(
    workflow_id=workflow_id,
    execution_id=execution_id,
    step_name='fetch_market_data',
    step_number=1,
    input_data={'symbol': symbol, 'exchange': 'SMART', 'duration': '200 D'},
    output_data={
        'bars_count': market_data.bar_count,
        'latest_price': float(market_data.latest_price),
        'timeframe': market_data.timeframe
    },
    status='success',
    duration_ms=duration
)

# Store artifact
store_artifact(
    name=f"{symbol} Market Data",
    type="market_data",
    symbol=symbol,
    workflow_id=workflow_id,
    execution_id=execution_id,
    step_name='fetch_market_data',
    metadata={
        'bars_count': market_data.bar_count,
        'start_date': market_data.start_date,
        'end_date': market_data.end_date
    }
)
```

### Phase 2: Chart Generation
```python
# Store daily chart
store_artifact(
    name=f"{symbol} Daily Chart",
    type="chart",
    symbol=symbol,
    workflow_id=workflow_id,
    execution_id=execution_id,
    step_name='generate_daily_chart',
    image_path=chart_result.file_path,
    chart_data={
        'indicators': chart_result.indicators_included,
        'timeframe': 'daily',
        'bars_count': market_data.bar_count
    }
)

# Store lineage
store_lineage_record(
    workflow_id=workflow_id,
    execution_id=execution_id,
    step_name='generate_daily_chart',
    step_number=2,
    input_data={'market_data_bars': market_data.bar_count},
    output_data={
        'chart_path': chart_result.file_path,
        'indicators': chart_result.indicators_included,
        'periods_shown': chart_result.periods_shown
    }
)
```

### Phase 3: LLM Analysis
```python
# Store LLM interaction
store_artifact(
    name=f"{symbol} LLM Analysis",
    type="llm",
    symbol=symbol,
    workflow_id=workflow_id,
    execution_id=execution_id,
    step_name='analyze_with_llm',
    prompt=prompt_text,
    response=signal.reasoning,
    model_name=signal.model_used,
    confidence_score=float(signal.confidence_score) / 100.0,
    metadata={
        'signal_action': signal.action,
        'confidence_level': signal.confidence.name,
        'is_actionable': signal.is_actionable
    }
)

# Store trading signal
store_artifact(
    name=f"{symbol} {signal.action} Signal",
    type="signal",
    symbol=symbol,
    workflow_id=workflow_id,
    execution_id=execution_id,
    step_name='analyze_with_llm',
    signal_data={
        'action': signal.action,
        'confidence_score': signal.confidence_score,
        'reasoning': signal.reasoning,
        'entry_price': float(signal.suggested_entry_price) if signal.suggested_entry_price else None,
        'stop_loss': float(signal.suggested_stop_loss) if signal.suggested_stop_loss else None,
        'take_profit': float(signal.suggested_take_profit) if signal.suggested_take_profit else None,
        'risk_reward_ratio': float(signal.risk_reward_ratio) if signal.risk_reward_ratio else None
    }
)
```

## Open Source Tools Integration

### **Primary Tools**
1. **MLflow** - Experiment tracking, metrics, parameters, artifacts
2. **PostgreSQL** - Structured data, lineage tracking, metadata
3. **MinIO** - Object storage for charts, models, large files
4. **Airflow** - Workflow orchestration, XCom for inter-task data

### **Optional Advanced Tools**
1. **Marquez** - Open source data lineage and metadata collection
2. **Amundsen** - Data discovery and lineage visualization
3. **Prefect** - Enhanced workflow orchestration with lineage
4. **Great Expectations** - Data quality validation and lineage

### **Lineage Visualization**
```python
# Generate lineage graph
def generate_lineage_graph(workflow_id, execution_id):
    """Generate visual lineage graph for workflow execution"""
    lineage_records = get_lineage_records(workflow_id, execution_id)

    # Create graphviz diagram
    dot = Digraph(comment='Workflow Lineage')

    for record in lineage_records:
        # Add nodes for each step
        dot.node(record.step_name, f"{record.step_name}\n{record.status}")

        # Add edges based on data flow
        if record.step_number > 1:
            prev_step = lineage_records[record.step_number - 2]
            dot.edge(prev_step.step_name, record.step_name)

    return dot
```

## API Endpoints for Lineage

### **Lineage Query APIs**
```python
@app.get("/api/lineage/workflows/{workflow_id}")
async def get_workflow_lineage(workflow_id: str):
    """Get complete lineage for workflow"""
    return get_workflow_lineage_data(workflow_id)

@app.get("/api/lineage/executions/{execution_id}")
async def get_execution_lineage(execution_id: str):
    """Get lineage for specific execution"""
    return get_execution_lineage_data(execution_id)

@app.get("/api/lineage/steps/{step_name}")
async def get_step_lineage(step_name: str):
    """Get lineage for specific step type"""
    return get_step_lineage_data(step_name)
```

### **Artifact Management APIs**
```python
@app.get("/api/artifacts")
async def list_artifacts(
    type: str = None,
    symbol: str = None,
    workflow_id: str = None,
    limit: int = 50
):
    """List artifacts with filtering"""
    return get_filtered_artifacts(type, symbol, workflow_id, limit)

@app.get("/api/artifacts/{artifact_id}")
async def get_artifact(artifact_id: int):
    """Get detailed artifact information"""
    return get_artifact_details(artifact_id)

@app.get("/api/artifacts/lineage/{execution_id}")
async def get_execution_artifacts(execution_id: str):
    """Get all artifacts for workflow execution"""
    return get_execution_artifacts(execution_id)
```

## Monitoring & Alerting

### **Lineage Health Checks**
```python
def check_lineage_integrity():
    """Verify lineage data integrity"""
    # Check for missing steps
    # Validate data flow consistency
    # Ensure artifact references exist
    pass

def check_artifact_storage():
    """Verify artifact storage health"""
    # Check MinIO connectivity
    # Validate file references
    # Clean up orphaned artifacts
    pass
```

### **Performance Metrics**
- Lineage record count per workflow
- Artifact storage size and growth
- Query performance for lineage searches
- MLflow integration success rate

## Implementation Checklist

### ✅ **Completed**
- [x] Database schema for lineage and artifacts
- [x] MinIO storage structure
- [x] MLflow experiment tracking
- [x] Airflow XCom integration
- [x] Workflow step lineage recording
- [x] Chart and artifact storage
- [x] API endpoints for lineage queries

### 🔄 **In Progress**
- [ ] Full workflow execution with all steps
- [ ] Lineage visualization dashboard
- [ ] Advanced open source tool integration

### 📋 **Next Steps**
- [ ] Implement lineage graph visualization
- [ ] Add data quality validation
- [ ] Integrate with Marquez for advanced lineage
- [ ] Add alerting for lineage failures
- [ ] Performance optimization for large workflows

## Benefits

1. **Complete Traceability**: Track every input/output through the entire workflow
2. **Debugging Support**: Quickly identify where issues occurred in complex workflows
3. **Compliance**: Maintain audit trails for trading decisions
4. **Experimentation**: Compare different workflow runs and their outcomes
5. **Optimization**: Identify bottlenecks and performance issues
6. **Reproducibility**: Recreate exact conditions for any workflow execution

This comprehensive lineage and chart storage system provides enterprise-grade tracking and management capabilities using entirely open source tools.
