# Artifact Workflow Tracking Implementation - OpenSpec 2

## Status: ✅ PHASE 1-3 COMPLETED | 🔄 PHASE 4 IN PROGRESS

### Completed Tasks

#### ✅ Phase 1: Database Schema Enhancement
- **Created `artifacts` table** with comprehensive workflow tracking fields:
  - `workflow_id` - Workflow identifier (e.g., `ibkr_trading_signal_workflow`)
  - `execution_id` - Specific workflow execution/run ID
  - `step_name` - Workflow step that generated the artifact
  - `dag_id` - Airflow DAG ID
  - `task_id` - Airflow task ID
  - Plus all existing fields (MLflow run_id, experiment_id, etc.)

- **Created indexes** for efficient querying:
  - Individual indexes on workflow_id, execution_id, step_name, dag_id
  - Composite index on (workflow_id, execution_id)
  - Indexes on type, symbol, created_at

#### ✅ Phase 2: Model & API Updates
- **Updated `Artifact` SQLAlchemy model** (`backend/models/artifact.py`):
  - Added workflow tracking columns
  - Updated `to_dict()` method to include new fields in API responses

- **Updated artifact storage utilities** (`dags/utils/artifact_storage.py`):
  - Enhanced `store_artifact()` function with workflow parameters
  - Updated all convenience functions: `store_llm_artifact()`, `store_chart_artifact()`, `store_signal_artifact()`
  - All functions now accept and propagate workflow context

#### ✅ Phase 3: Workflow Integration
- **Updated IBKR Trading Workflow** (`dags/ibkr_trading_signal_workflow.py`):
  - Daily chart artifact storage now includes workflow context
  - Weekly chart artifact storage now includes workflow context
  - LLM analysis artifact storage now includes workflow context
  - Trading signal artifact storage now includes workflow context

- Each artifact storage call now passes:
  ```python
  workflow_id='ibkr_trading_signal_workflow',
  execution_id=str(context['execution_date']),
  step_name='generate_daily_chart',  # or relevant step
  dag_id=context['dag'].dag_id,
  task_id=context['task'].task_id
  ```

#### ✅ Phase 4: Frontend Enhancement
- **Created Artifact Detail View** (`frontend/templates/artifact_detail.html`):
  - Beautiful, type-specific rendering for LLM, Chart, and Signal artifacts
  - Displays full workflow context information
  - Shows MLflow run linking
  - Raw JSON data view for debugging

- **Added frontend route** (`backend/api/frontend.py`):
  - `/artifacts/{artifact_id}` route for detail view
  - Template renders with Alpine.js for reactivity

- **Fixed `/workflows` route**:
  - Added DAG parameter support for URL highlighting
  - Updated Airflow monitor page to handle selected DAG from URL

### 🔄 In Progress Tasks

#### Dashboard Style Fix
- Quick Actions section uses proper Tailwind CSS
- Colors are vibrant with good contrast
- **Issue**: User reports text/icons not visible (potential browser caching)
- **Solution**: Ensure proper CSS loading and add meta cache-busting

#### Grouped Artifacts View
- **Design**: Group artifacts by `execution_id` in the artifacts page
- **Implementation needed**:
  - Update artifacts page to fetch grouping data
  - Create accordion/expansion view for each workflow run
  - Display workflow metadata as section headers

#### Airflow Run Details Integration
- **Design**: Link artifacts to Airflow run detail modal
- **Implementation needed**:
  - Update Airflow monitor to fetch artifacts for selected run
  - Display artifacts in "Generated Artifacts" section
  - Add direct links to artifact detail pages

### Testing Required

#### Test 1: Trigger New Workflow Run
```bash
docker-compose exec airflow-webserver airflow dags trigger ibkr_trading_signal_workflow
```
- Verify artifacts are created with workflow metadata
- Check `workflow_id`, `execution_id`, `step_name`, `dag_id`, `task_id` are populated

#### Test 2: Artifact Detail View
```bash
# Navigate to http://localhost:8000/artifacts/3
# Should see full artifact details with workflow context
```

#### Test 3: Grouped View
- Navigate to artifacts page
- Artifacts should be grouped by workflow execution
- Each group should show execution metadata

### Database Schema

```sql
CREATE TABLE artifacts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    symbol VARCHAR(50),
    
    -- MLflow Integration
    run_id VARCHAR(255),
    experiment_id VARCHAR(255),
    
    -- Workflow Tracking (NEW)
    workflow_id VARCHAR(255),
    execution_id VARCHAR(255),
    step_name VARCHAR(100),
    dag_id VARCHAR(255),
    task_id VARCHAR(255),
    
    -- Type-specific fields
    prompt TEXT,
    response TEXT,
    prompt_length INTEGER,
    response_length INTEGER,
    model_name VARCHAR(100),
    image_path TEXT,
    chart_type VARCHAR(50),
    chart_data JSONB,
    action VARCHAR(20),
    confidence DECIMAL(3,2),
    signal_data JSONB,
    artifact_metadata JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### API Response Example

```json
{
  "id": 4,
  "name": "TSLA Daily Chart",
  "type": "chart",
  "symbol": "TSLA",
  "run_id": "abc123",
  "experiment_id": "exp456",
  "workflow_id": "ibkr_trading_signal_workflow",
  "execution_id": "2025-11-08T14:30:51+00:00",
  "step_name": "generate_daily_chart",
  "dag_id": "ibkr_trading_signal_workflow",
  "task_id": "generate_daily_chart",
  "image_path": "/tmp/TSLA_1D_20251108.png",
  "chart_type": "daily",
  "chart_data": {
    "indicators": ["SMA_20", "SMA_50", "RSI", "MACD"],
    "timeframe": "daily",
    "bars_count": 200
  },
  "created_at": "2025-11-08T14:31:10Z"
}
```

### Benefits Achieved

1. **Complete Traceability**: Every artifact can be traced back to its workflow execution
2. **Debugging**: Easy to identify which workflow run generated which artifacts
3. **Lineage**: Clear data lineage from market data → charts → LLM analysis → signals
4. **Grouping**: Artifacts can be grouped and displayed by workflow run
5. **Integration**: Seamless integration with Airflow and MLflow
6. **Audit Trail**: Complete audit trail for compliance and analysis

### Next Steps

1. **Complete dashboard style fix** - Ensure Quick Actions are visible
2. **Implement grouped artifacts view** - Group by execution_id
3. **Link artifacts to Airflow monitor** - Show artifacts in run details
4. **Test workflow run** - Verify all metadata is captured
5. **Performance optimization** - Add caching for large artifact lists

### Files Modified

#### Database
- `/database/migrations/create_artifacts_table.sql` ✅

#### Backend Models
- `/backend/models/artifact.py` ✅

#### Backend API
- `/backend/api/frontend.py` ✅

#### DAGs
- `/dags/ibkr_trading_signal_workflow.py` ✅
- `/dags/utils/artifact_storage.py` ✅

#### Frontend
- `/frontend/templates/artifact_detail.html` ✅ (NEW)
- `/frontend/templates/airflow_monitor.html` ✅ (Updated)
- `/frontend/templates/artifacts.html` 🔄 (Needs grouping update)
- `/frontend/templates/dashboard.html` 🔄 (Needs style verification)

### References
- OpenSpec 2 Methodology: Design → Build → Test → Fix
- Lineage Design Document: `/docs/implementation/LINEAGE_CHART_STORAGE_DESIGN.md`

