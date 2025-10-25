# FastAPI Trading WebApp Implementation

This change introduces a comprehensive automated trading platform for IBKR with AI-powered technical analysis, risk management, and portfolio tracking.

## Quick Start

1. **Review the Proposal**
   ```bash
   cat openspec/changes/add-fastapi-trading-webapp/proposal.md
   ```

2. **Review the Design**
   ```bash
   cat openspec/changes/add-fastapi-trading-webapp/design.md
   ```

3. **Review the Tasks**
   ```bash
   cat openspec/changes/add-fastapi-trading-webapp/tasks.md
   ```

4. **Review Specifications**
   - Database Schema: `specs/database-schema/spec.md`
   - Trading Workflow: `specs/trading-workflow/spec.md`
   - Order Management: `specs/order-management/spec.md`
   - Risk Management: `specs/risk-management/spec.md`
   - Portfolio Management: `specs/portfolio-management/spec.md`
   - Chart Analysis: `specs/chart-analysis/spec.md`
   - API Backend: `specs/api-backend/spec.md`
   - Frontend UI: `specs/frontend-ui/spec.md`

## Configuration Files

- **Environment Variables**: `env.template` - Copy to `.env` in project root
- **Docker Compose**: `docker-compose.example.yml` - Multi-service orchestration example

## Key Features

### Automated Trading Workflow
Based on the reference n8n workflow, the system:
1. Checks IBKR authentication
2. Fetches daily and weekly chart data
3. Generates technical analysis charts
4. Uses AI to analyze charts (multi-timeframe)
5. Consolidates analysis across timeframes
6. Generates structured trading decisions
7. Validates risk criteria (R-coefficient, profit margin)
8. Automatically places orders when criteria are met

### Technical Stack
- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL
- **Storage**: MinIO (S3-compatible)
- **AI**: OpenAI-compatible API (supports OpenAI, Gemini, Azure OpenAI, local models)
- **Frontend**: Jinja2 templates with Tailwind CSS
- **Containerization**: Docker Compose

### Risk Management
- R-coefficient validation (minimum 1.0)
- Profit margin thresholds (minimum 5%)
- Position sizing based on risk percentage
- Portfolio exposure limits
- Maximum open positions limits

## Implementation Approach

### Phase 1: Infrastructure Setup
- Database schema creation
- Docker Compose configuration
- MinIO bucket setup
- Environment configuration

### Phase 2: Core Services
- IBKR API integration
- Database models and services
- Chart generation with indicators
- MinIO storage integration
- AI/LLM integration

### Phase 3: Workflow Engine
- Strategy configuration management
- Workflow orchestration
- Multi-timeframe analysis pipeline
- Risk validation
- Order placement automation

### Phase 4: API & UI
- FastAPI REST endpoints
- Tailwind CSS responsive UI
- Dashboard and portfolio views
- Strategy management interface
- Workflow execution monitoring

## Key Decisions

1. **FastAPI over Flask**: Better performance, auto-documentation, type safety
2. **PostgreSQL**: Reliable RDBMS with JSON support for flexible data
3. **Plotly for Charts**: Modern financial charts with interactivity
4. **OpenAI-Compatible API**: Vendor flexibility (OpenAI, Gemini, Azure, local)
5. **Sequential Workflow**: Matches proven n8n pattern, easier to debug
6. **Service-Oriented Architecture**: Clear separation of concerns

## Reference Files

The implementation references existing structures:
- **Workflow**: `reference/workflow/IBKR_2_Indicator_4_Prod (1).json`
- **Schema**: `reference/schema/*.xlsx` (for table structure understanding)
- **Backend**: `reference/webapp/` (Flask app patterns)
- **Docker**: `reference/dockerfile/` (containerization patterns)

## Validation

Run OpenSpec validation:
```bash
cd /Users/he/git/ibkr-trading-webui
openspec validate add-fastapi-trading-webapp --strict
```

## Next Steps

1. Get proposal approval
2. Begin Phase 1 implementation
3. Iteratively implement features following tasks.md
4. Test thoroughly with paper trading
5. Deploy and monitor

