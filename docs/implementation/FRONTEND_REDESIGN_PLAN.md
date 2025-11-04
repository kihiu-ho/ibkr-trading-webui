# LLM Trading Frontend Redesign - Complete Plan

**Status**: 🎯 Planning Complete - Ready for Implementation  
**Date**: 2025-10-19  
**Scope**: Comprehensive frontend redesign for LLM-based trading with IBKR

## Overview

This document outlines the complete plan for redesigning the frontend to support:
1. Automatic trading with LLM decision-making
2. Real-time workflow tracing and logging
3. Dynamic parameter editing
4. Workflow lineage visualization
5. Comprehensive testing

## Phase 1: OpenSpec Proposal ✅

**Status**: COMPLETE

**Created Files**:
- `openspec/changes/add-llm-trading-frontend/proposal.md`
- `openspec/changes/add-llm-trading-frontend/tasks.md`
- `openspec/changes/add-llm-trading-frontend/specs/frontend-workflow-visualization/spec.md`

**Remaining Specs to Create**:
- `specs/frontend-logging-viewer/spec.md`
- `specs/frontend-parameter-editor/spec.md`
- `specs/frontend-dashboard/spec.md`

## Phase 2: Backend API Enhancements 🔄

### 2.1 New API Endpoints

```python
# backend/api/workflows.py
@router.post("/workflows/executions")  # Start workflow execution
@router.get("/workflows/executions/{id}")  # Get execution status
@router.get("/workflows/executions/{id}/logs")  # Get execution logs
@router.get("/workflows/executions/{id}/lineage")  # Get workflow lineage data
@router.post("/workflows/executions/{id}/stop")  # Stop execution

# backend/api/strategies.py
@router.get("/strategies")  # List strategies
@router.post("/strategies")  # Create strategy
@router.put("/strategies/{id}")  # Update strategy
@router.delete("/strategies/{id}")  # Delete strategy
@router.post("/strategies/{id}/execute")  # Execute strategy
@router.post("/strategies/{id}/validate-params")  # Validate parameters

# backend/api/logs.py
@router.get("/logs/stream")  # WebSocket/SSE for real-time logs
@router.get("/logs")  # Query logs with filters
@router.get("/logs/export")  # Export logs as JSON/CSV
```

### 2.2 WebSocket Support

Add Socket.IO or native WebSocket support for:
- Real-time log streaming
- Workflow execution status updates
- Live progress tracking

### 2.3 Required Dependencies

```txt
# Add to backend/requirements.txt
python-socketio>=5.10.0  # For WebSocket support
fastapi-socketio>=0.0.10  # FastAPI Socket.IO integration
```

## Phase 3: Frontend Architecture 🔄

### 3.1 New Frontend Structure

```
frontend/
├── templates/
│   ├── base.html (enhanced)
│   ├── dashboard.html (redesigned)
│   ├── strategies.html (enhanced)
│   ├── workflows/
│   │   ├── list.html (new)
│   │   ├── execution.html (new)
│   │   └── lineage.html (new)
│   ├── logs/
│   │   └── viewer.html (new)
│   └── parameters/
│       └── editor.html (new)
├── static/
│   ├── js/
│   │   ├── workflow-visualization.js (new)
│   │   ├── log-viewer.js (new)
│   │   ├── parameter-editor.js (new)
│   │   ├── lineage-graph.js (new)
│   │   ├── websocket-client.js (new)
│   │   └── dashboard-charts.js (new)
│   └── css/
│       ├── workflow.css (new)
│       └── components.css (enhanced)
└── components/ (Alpine.js components)
    ├── workflow-card.js
    ├── log-entry.js
    └── parameter-form.js
```

### 3.2 Key Technologies

| Technology | Purpose | Version |
|------------|---------|---------|
| Alpine.js | Reactive UI components | 3.x |
| D3.js or vis.js | Workflow DAG visualization | Latest |
| Chart.js | Performance metrics | 4.x |
| Socket.IO Client | Real-time updates | Latest |
| Tailwind CSS | Styling (already present) | Latest |

## Phase 4: Feature Implementation 🚀

### 4.1 Workflow Visualization Component

**File**: `frontend/static/js/workflow-visualization.js`

**Features**:
```javascript
class WorkflowVisualization {
    constructor(containerId, executionId) {
        this.container = document.getElementById(containerId);
        this.executionId = executionId;
        this.graph = null;
        this.data = null;
    }
    
    async init() {
        // Load execution data
        // Initialize D3/vis.js graph
        // Setup real-time updates via WebSocket
        // Render initial state
    }
    
    update(stepUpdate) {
        // Update node status
        // Update timing information
        // Highlight active nodes
    }
    
    render() {
        // Render workflow DAG
        // Add interactivity
        // Setup zoom/pan
    }
}
```

### 4.2 Log Viewer Component

**File**: `frontend/static/js/log-viewer.js`

**Features**:
```javascript
class LogViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.logs = [];
        this.filters = {
            step_type: null,
            success: null,
            code: null,
            search: ''
        };
        this.socket = null;
    }
    
    async init() {
        // Load initial logs
        // Connect to WebSocket for real-time updates
        // Setup filters UI
        // Render log entries
    }
    
    async streamLogs(executionId) {
        // Connect to log stream
        // Handle incoming log entries
        // Update UI in real-time
    }
    
    applyFilters() {
        // Filter logs based on criteria
        // Update display
    }
    
    exportLogs(format) {
        // Export as JSON or CSV
        // Download file
    }
}
```

### 4.3 Parameter Editor Component

**File**: `frontend/static/js/parameter-editor.js`

**Features**:
```javascript
class ParameterEditor {
    constructor(strategyId) {
        this.strategyId = strategyId;
        this.parameters = {};
        this.validation = {};
    }
    
    async loadParameters() {
        // Load strategy parameters
        // Load parameter schema/validation rules
        // Generate dynamic form
    }
    
    generateForm(schema) {
        // Create form fields based on parameter types
        // Add validation
        // Add help text/tooltips
    }
    
    async validateParameters() {
        // Validate against schema
        // Call backend validation API
        // Show validation errors
    }
    
    async saveParameters() {
        // Validate
        // Save to strategy
        // Show success/error
    }
}
```

### 4.4 Workflow Lineage Graph

**File**: `frontend/static/js/lineage-graph.js`

**Features**:
```javascript
class LineageGraph {
    constructor(containerId, executionId) {
        this.container = document.getElementById(containerId);
        this.executionId = executionId;
        this.data = {
            nodes: [],
            edges: []
        };
    }
    
    async loadLineageData() {
        // Fetch workflow lineage from API
        // Transform to graph format
        // Calculate layout
    }
    
    renderGraph() {
        // Render using D3.js or vis.js
        // Add node tooltips
        // Add edge labels
        // Color nodes by status
    }
    
    highlightPath(nodeId) {
        // Highlight path from start to node
        // Show dependencies
    }
}
```

## Phase 5: UI/UX Design 🎨

### 5.1 Dashboard Redesign

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Navigation Bar                                          │
├─────────────────────────────────────────────────────────┤
│  Active Strategies | Running Workflows | Recent Decisions│
│  ┌─────┐ ┌─────┐   ┌─────┐ ┌─────┐    ┌─────┐ ┌─────┐│
│  │  5  │ │ 10  │   │  3  │ │  2  │    │ 15  │ │ 80% ││
│  └─────┘ └─────┘   └─────┘ └─────┘    └─────┘ └─────┘│
├─────────────────────────────────────────────────────────┤
│  Quick Actions                                          │
│  [New Strategy] [Execute Workflow] [View Logs] [Settings]│
├─────────────────────────────────────────────────────────┤
│  Active Workflows              │  Recent Decisions      │
│  ┌──────────────────────────┐ │  ┌───────────────────┐ │
│  │ TSLA & NVDA              │ │  │ BUY TSLA @$221.86 │ │
│  │ Status: Running (60%)    │ │  │ R: 2.5 | 5% gain │ │
│  │ [View Progress] [Stop]   │ │  └───────────────────┘ │
│  └──────────────────────────┘ │                        │
│                                │  [See All Decisions]   │
├─────────────────────────────────────────────────────────┤
│  Performance Chart (Last 30 Days)                       │
│  ┌────────────────────────────────────────────────────┐ │
│  │         [Chart.js Line Chart]                      │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Workflow Execution Page

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Workflow Execution: TSLA & NVDA - Two Indicator Strategy│
├─────────────────────────────────────────────────────────┤
│ Controls: [Stop] [Pause] [Restart]    Status: Running   │
├─────────────────────────────────────────────────────────┤
│  Lineage Visualization                                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │     [Start]                                        │ │
│  │        ↓                                           │ │
│  │     [Auth Check] → [TSLA Processing] ──┐          │ │
│  │                      ↓                  │          │ │
│  │                  [Daily Data]           │          │ │
│  │                      ↓                  │          │ │
│  │                  [Weekly Data]          │          │ │
│  │                      ↓                  │          │ │
│  │                  [AI Analysis]          │          │ │
│  │                      ↓                  │          │ │
│  │                  [Decision: BUY]        │          │ │
│  │                      ↓                  │          │ │
│  │                  [Place Order]          │          │ │
│  │                      ↓                  ↓          │ │
│  │                  [60s Delay] ← [NVDA Processing]  │ │
│  │                      ↓                             │ │
│  │                  [Complete]                        │ │
│  └────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  Real-Time Logs                 │  Metrics              │
│  ┌──────────────────────────┐  │  Duration: 5m 23s     │
│  │ [INFO] Fetching TSLA...  │  │  Steps: 15/20         │
│  │ [SUCCESS] Daily chart... │  │  Success Rate: 100%   │
│  │ [INFO] Analyzing...      │  │  Decisions: 1 BUY     │
│  └──────────────────────────┘  │                       │
└─────────────────────────────────────────────────────────┘
```

### 5.3 Parameter Editor Page

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Edit Strategy Parameters: Test Multi-Code Strategy      │
├─────────────────────────────────────────────────────────┤
│  Basic Information                                      │
│  Strategy Name: [Test Multi-Code Strategy         ] │
│  Workflow:      [▼ Two Indicator Strategy         ] │
│  Status:        [✓] Active                              │
├─────────────────────────────────────────────────────────┤
│  Symbols (Multi-Select)                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │ [x] TSLA - Tesla Inc (76792991)                  │  │
│  │ [x] NVDA - NVIDIA Corp (4815747)                 │  │
│  │ [ ] AAPL - Apple Inc (265598)                    │  │
│  │ [+ Add Symbol]                                   │  │
│  └──────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│  Chart Parameters                                       │
│  Daily:   Period [1y ▼]  Bar [1d ▼]                   │
│  Weekly:  Period [5y ▼]  Bar [1w ▼]                   │
├─────────────────────────────────────────────────────────┤
│  Risk Management                                        │
│  Account Size:      [$100,000                    ]    │
│  Risk Per Trade:    [2.0                         ] %   │
│  Min R-Coefficient: [1.0                         ]    │
│  Min Profit Margin: [5.0                         ] %   │
├─────────────────────────────────────────────────────────┤
│  AI/LLM Configuration                                   │
│  Model:             [▼ gpt-4-turbo-preview        ]   │
│  Temperature:       [0.7                          ]    │
│  Max Tokens:        [4000                         ]    │
│  Timeout:           [120                          ] s  │
├─────────────────────────────────────────────────────────┤
│  Workflow Settings                                      │
│  Delay Between Symbols: [60                       ] s  │
│  Max Retries:           [3                        ]    │
│  Auto Trading:          [ ] Enable (⚠️ Use with caution)│
│  Paper Trading Mode:    [✓] Enable (Recommended)      │
├─────────────────────────────────────────────────────────┤
│  [Preview Changes] [Validate] [Save] [Cancel]          │
└─────────────────────────────────────────────────────────┘
```

## Phase 6: Testing Plan 🧪

### 6.1 Unit Tests
- Backend API endpoints
- Parameter validation logic
- Workflow lineage generation

### 6.2 Integration Tests
- Frontend-Backend API integration
- WebSocket real-time updates
- Log streaming and filtering

### 6.3 E2E Tests
```
Test Scenario: Complete Workflow Execution
1. Create new strategy with TSLA and NVDA
2. Configure parameters via parameter editor
3. Execute workflow
4. Monitor real-time progress in visualization
5. View live logs as they stream
6. Inspect workflow lineage after completion
7. Review decisions and orders
8. Export logs for analysis
```

### 6.4 Performance Tests
- Load 1000+ log entries - should render < 1s
- Real-time updates - should update UI < 100ms
- Workflow graph with 50+ nodes - should render < 2s
- Parameter form generation - should render < 500ms

## Phase 7: Implementation Priority 📋

### Immediate (Phase 1) - Core Functionality
1. ✅ Create OpenSpec proposal
2. ✅ Create task list
3. ✅ Create workflow visualization spec
4. 🔄 Create remaining specs
5. 🔄 Implement backend API endpoints
6. 🔄 Create basic frontend templates

### Short-term (Phase 2) - Basic Visualization
1. Implement workflow lineage visualization
2. Add real-time log viewer
3. Add parameter editor
4. Basic WebSocket support

### Medium-term (Phase 3) - Enhanced Features
1. Add advanced filtering and search
2. Add performance metrics
3. Add execution comparison
4. Add alert system

### Long-term (Phase 4) - Polish & Optimization
1. Performance optimization
2. Advanced visualization features
3. Customizable dashboards
4. Export and reporting

## Next Steps 🚀

**Immediate Action Items**:
1. Complete remaining OpenSpec spec files
2. Validate proposal with `openspec validate`
3. Implement backend API endpoints
4. Create basic frontend structure
5. Implement workflow visualization
6. Test with TSLA/NVDA workflow

**Estimated Timeline**:
- OpenSpec & Planning: ✅ Complete (Day 1)
- Backend APIs: 🔄 In Progress (Days 2-3)
- Frontend Core: Pending (Days 4-6)
- Testing & Polish: Pending (Days 7-8)
- Documentation: Pending (Day 9)

**Total Estimated Time**: 9 days for full implementation

## Success Criteria ✅

- [ ] All workflow executions visible in real-time
- [ ] Complete lineage visualization showing data flow
- [ ] All workflow logs accessible and filterable
- [ ] All parameters editable through UI
- [ ] Multi-symbol workflows properly displayed
- [ ] Performance meets requirements (<1s load times)
- [ ] Mobile-responsive design
- [ ] Comprehensive documentation

---

**Status**: 📋 Planning Complete - Ready to Begin Implementation  
**Next**: Create remaining spec files and begin backend API development

