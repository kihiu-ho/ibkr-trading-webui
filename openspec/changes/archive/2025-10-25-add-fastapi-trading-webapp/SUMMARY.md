# OpenSpec Change Proposal Summary

## Change ID: `add-fastapi-trading-webapp`

✅ **Status**: Validated and ready for implementation

## Overview

A comprehensive OpenSpec change proposal has been created to build an automated trading platform for Interactive Brokers with AI-powered technical analysis, risk management, and portfolio tracking.

## What Was Created

### 1. Core Documentation
- **`proposal.md`**: Complete change proposal explaining why, what, and impact
- **`design.md`**: Comprehensive technical design document with architectural decisions
- **`tasks.md`**: Detailed 16-phase implementation checklist with 180+ tasks
- **`README.md`**: Quick start guide and implementation overview

### 2. Specifications (8 Capabilities)

#### Database Schema (`specs/database-schema/spec.md`)
- PostgreSQL schema with 7 tables (strategy, code, market_data, decision, orders, trades, positions)
- Foreign key relationships and indexes
- Database migrations with Alembic
- 12 requirements, 28 scenarios

#### Trading Workflow (`specs/trading-workflow/spec.md`)
- Automated multi-timeframe analysis workflow
- AI-powered chart analysis (daily + weekly)
- Trading decision generation
- Risk validation and order placement
- 11 requirements, 30+ scenarios

#### Order Management (`specs/order-management/spec.md`)
- Order placement via IBKR API
- Order status tracking and lifecycle
- Order cancellation and history
- Position sizing calculations
- 6 requirements, 10 scenarios

#### Risk Management (`specs/risk-management/spec.md`)
- R-coefficient validation (min 1.0)
- Profit margin validation (min 5%)
- Stop-loss calculation
- Position sizing and portfolio limits
- 8 requirements, 14 scenarios

#### Portfolio Management (`specs/portfolio-management/spec.md`)
- Position tracking and P&L calculation
- Trade history management
- Performance metrics (win rate, profit factor, avg R)
- Position risk monitoring
- 7 requirements, 12 scenarios

#### Chart Analysis (`specs/chart-analysis/spec.md`)
- Technical indicator generation (SuperTrend, MA, MACD, RSI, Bollinger Bands)
- Chart image export to MinIO
- Interactive chart display
- Multi-timeframe comparison
- 8 requirements, 16 scenarios

#### API Backend (`specs/api-backend/spec.md`)
- FastAPI RESTful API with OpenAPI docs
- Complete CRUD endpoints for all entities
- Request validation with Pydantic
- Error handling and health checks
- 11 requirements, 27 scenarios

#### Frontend UI (`specs/frontend-ui/spec.md`)
- Tailwind CSS responsive design
- Dashboard, strategy management, orders, portfolio pages
- Interactive charts with Plotly
- Mobile-responsive design
- 8 requirements, 26 scenarios

### 3. Configuration Files

#### Environment Template (`env.template`)
Complete `.env` template with:
- IBKR configuration
- PostgreSQL database settings
- MinIO/S3 storage configuration
- OpenAI-compatible API settings (supports OpenAI, Gemini, Azure, local models)
- Risk management parameters
- Trading configuration
- Feature flags

#### Docker Compose (`docker-compose.example.yml`)
Multi-service orchestration:
- IBKR Gateway service
- PostgreSQL database
- MinIO object storage
- FastAPI backend
- Health checks and networking

## Key Features

### 1. Automated Trading Workflow
Based on the reference n8n workflow (`reference/workflow/IBKR_2_Indicator_4_Prod (1).json`):
1. Authentication check
2. Strategy configuration loading
3. Multi-symbol processing loop
4. Daily chart data fetch → chart generation → AI analysis
5. Weekly chart data fetch → chart generation → AI analysis
6. Multi-timeframe analysis consolidation
7. Structured trading decision generation
8. Risk validation (R-coefficient, profit margin)
9. Automatic order placement
10. Results logging and monitoring

### 2. AI Integration (OpenAI-Compatible)
- Support for multiple LLM providers:
  - OpenAI (GPT-4, GPT-3.5)
  - Google Gemini (via OpenAI endpoint)
  - Azure OpenAI
  - Local models (via LiteLLM)
- Four specialized prompts:
  - Daily chart technical analysis
  - Weekly chart trend confirmation
  - Multi-timeframe consolidation
  - Trading decision generation
- Structured JSON output for reliable parsing

### 3. Risk Management
- **R-Coefficient Validation**: Minimum 1.0 (reward must exceed risk)
- **Profit Margin Validation**: Minimum 5%
- **Position Sizing**: Risk-based calculation (default 1% per trade)
- **Portfolio Limits**: Maximum exposure (90%), max positions (10)
- **Stop-Loss Management**: ATR-based calculations

### 4. Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | FastAPI + Python 3.11+ | REST API with auto-docs |
| Database | PostgreSQL + SQLAlchemy | Structured data storage |
| Storage | MinIO (S3-compatible) | Chart image storage |
| Frontend | Jinja2 + Tailwind CSS | Responsive web UI |
| Charts | Plotly | Technical analysis charts |
| AI | OpenAI-compatible API | Chart analysis |
| Containers | Docker Compose | Multi-service orchestration |

## Architecture Highlights

### Service-Oriented Design
```
backend/
├── api/              # FastAPI endpoints
├── models/           # SQLAlchemy database models
├── services/         # Business logic
│   ├── api_service.py       # IBKR API wrapper
│   ├── chart_service.py     # Chart generation
│   ├── ai_service.py        # LLM integration
│   ├── workflow_service.py  # Workflow orchestration
│   ├── order_service.py     # Order management
│   ├── risk_service.py      # Risk calculations
│   ├── portfolio_service.py # Portfolio tracking
│   └── storage_service.py   # MinIO operations
├── schemas/          # Pydantic models
└── config/           # Configuration
```

### Workflow Execution Flow
```
Start
  → Check IBKR Auth
  → Get Strategy Config
  → For Each Symbol:
      → Fetch Daily Data
      → Generate Daily Chart → Upload to MinIO
      → AI Analyze Daily Chart
      → Fetch Weekly Data
      → Generate Weekly Chart → Upload to MinIO
      → AI Analyze Weekly Chart
      → AI Consolidate Analyses
      → AI Generate Trading Decision
      → Validate Risk Criteria
      → If Valid: Place Order → Store to DB
      → Wait (60 seconds)
  → Return Summary
```

## Implementation Phases

### Phase 1: Infrastructure (Week 1)
- Database schema and migrations
- Docker Compose setup
- Environment configuration
- Service connectivity testing

### Phase 2: Core Services (Week 2-3)
- Database models and ORM
- IBKR API integration
- Chart generation with indicators
- MinIO storage integration
- AI/LLM service

### Phase 3: Workflow Engine (Week 4-5)
- Strategy management
- Workflow orchestration
- Multi-timeframe analysis
- Risk validation
- Order automation

### Phase 4: API & Frontend (Week 6-7)
- FastAPI endpoints
- Tailwind CSS UI
- Dashboard and views
- Interactive charts
- Monitoring interface

### Phase 5: Testing & Docs (Week 8)
- Unit and integration tests
- End-to-end testing
- Documentation
- Deployment guide

## Validation Results

✅ **OpenSpec Validation**: Passed with strict mode
```
openspec validate add-fastapi-trading-webapp --strict
```

**Statistics**:
- Total Requirements: 75+
- Total Scenarios: 163+
- Capabilities: 8
- Tasks: 180+
- Lines of Specification: ~2,500

## Reference Files Used

The proposal was designed based on:
1. **Workflow**: `reference/workflow/IBKR_2_Indicator_4_Prod (1).json` - n8n automated trading workflow
2. **Schema**: `reference/schema/*.xlsx` - Database table structures
3. **Backend**: `reference/webapp/` - Flask application patterns
4. **Docker**: `reference/dockerfile/` - Containerization examples

## Key Design Decisions

1. **FastAPI over Flask**: Better performance, automatic OpenAPI docs, type safety
2. **PostgreSQL**: Reliable RDBMS with JSONB for flexible strategy parameters
3. **Sequential Workflow**: Matches proven n8n pattern, easier to debug
4. **OpenAI-Compatible API**: Vendor flexibility (not locked to OpenAI)
5. **Plotly for Charts**: Modern, interactive financial charts
6. **Service Architecture**: Clear separation of concerns, testable

## Next Steps

1. **Review & Approve**: Review this proposal and all specifications
2. **Setup Environment**: Copy `env.template` to `.env` and configure
3. **Start Implementation**: Follow `tasks.md` sequentially
4. **Phase 1**: Begin with database setup and Docker configuration
5. **Iterate**: Build incrementally, test thoroughly
6. **Deploy**: Use paper trading first, then live trading

## Files to Review

```bash
cd /Users/he/git/ibkr-trading-webui/openspec/changes/add-fastapi-trading-webapp/

# Read core docs
cat proposal.md
cat design.md
cat tasks.md
cat README.md

# Review all specs
cat specs/database-schema/spec.md
cat specs/trading-workflow/spec.md
cat specs/order-management/spec.md
cat specs/risk-management/spec.md
cat specs/portfolio-management/spec.md
cat specs/chart-analysis/spec.md
cat specs/api-backend/spec.md
cat specs/frontend-ui/spec.md

# Configuration
cat env.template
cat docker-compose.example.yml
```

## Commands

```bash
# Validate the proposal
openspec validate add-fastapi-trading-webapp --strict

# Show proposal
openspec show add-fastapi-trading-webapp

# View specific spec
openspec show trading-workflow --type spec

# List all capabilities
openspec list --specs
```

---

**Created**: October 19, 2025  
**Author**: AI Assistant  
**Change ID**: add-fastapi-trading-webapp  
**Status**: ✅ Validated, Ready for Approval

