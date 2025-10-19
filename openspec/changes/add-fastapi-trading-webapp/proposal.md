# Add FastAPI Trading WebApp with AI-Driven Workflows

## Why

The current Flask-based IBKR trading interface is a simple web UI but lacks:
1. **Automated trading workflows** based on technical analysis and AI-driven decision making
2. **Structured database persistence** for trades, strategies, and market data
3. **Risk management capabilities** with position sizing and portfolio tracking
4. **AI integration** for chart analysis and trade recommendations using OpenAI-compatible models
5. **Modern API architecture** with FastAPI for better performance and automatic API documentation
6. **Multi-strategy support** allowing users to configure and run different trading strategies with customizable parameters

This change introduces a comprehensive trading platform that combines automated technical analysis workflows (daily/weekly chart analysis), AI-powered trading decisions, order management with automatic order placement, and persistent data storage.

## What Changes

### New Capabilities
- **Trading Workflow Engine**: Automated multi-timeframe technical analysis workflow based on n8n pattern (analyze daily charts → analyze weekly charts → consolidate analysis → make trading decision)
- **Message Queue System**: Celery + Redis task queue for concurrent execution of multiple workflows/strategies
- **Workflow Builder**: Visual workflow editor with templates, allowing users to create custom trading workflows from frontend
- **Microsoft AutoGen Integration**: Multi-agent collaborative decision-making with specialized agents (Technical Analyst, Risk Manager, Fundamental, Sentiment, Executor)
- **Order Management System**: Place, track, cancel, and modify IBKR orders with risk parameters
- **Risk Management**: Position sizing, stop-loss management, R-coefficient calculation, profit margin tracking
- **Portfolio Management**: Track positions, trades, P&L, and performance metrics
- **Chart Analysis Service**: Generate technical analysis charts with indicators (SuperTrend, Moving Averages, MACD, RSI, Bollinger Bands) and store to S3-compatible storage (MinIO)
- **AI Integration**: OpenAI-compatible API integration for analyzing charts and generating trading recommendations
- **Database Schema**: PostgreSQL database with tables for workflows, strategies, codes, market data, decisions, orders, trades, positions, and agent conversations
- **FastAPI Backend**: RESTful API with automatic OpenAPI documentation
- **Modern Frontend**: Tailwind CSS-based responsive UI for workflow builder, trading dashboard, order management, portfolio views, task monitoring

### Technology Stack
- **Backend**: Python 3.11+ with FastAPI, SQLAlchemy, Pydantic, Celery
- **Message Queue**: Redis (broker), Celery (task queue)
- **Multi-Agent Framework**: Microsoft AutoGen
- **Frontend**: HTML/Jinja2 templates with Tailwind CSS
- **Database**: PostgreSQL with proper schema design
- **Storage**: MinIO (S3-compatible) for chart images
- **AI**: OpenAI-compatible API for chart analysis
- **Containerization**: Docker Compose with multi-service architecture (Gateway, PostgreSQL, Redis, MinIO, Celery Workers, Backend API)

### Key Features
1. **Visual Workflow Builder**: Create and customize trading workflows from frontend with drag-and-drop interface
2. **Workflow Templates**: Pre-built templates (2-indicator, 3-indicator, AutoGen multi-agent, custom)
3. **Concurrent Execution**: Run multiple strategies simultaneously via Celery task queue
4. **Multi-Agent AI Decision**: AutoGen framework with specialized agents collaborating for sophisticated analysis
5. **Strategy Configuration**: Define trading strategies with customizable parameters and workflow associations
6. **Multi-Timeframe Analysis**: Analyze multiple timeframes (daily, weekly, monthly), consolidate findings
7. **Automated Decision Making**: AI (single or multi-agent) evaluates technical analysis and determines buy/sell/hold signals
8. **Order Execution**: Automatic order placement when conditions are met
9. **Position Tracking**: Real-time position monitoring and trade history
10. **Risk Controls**: R-coefficient validation, profit margin thresholds, stop-loss enforcement
11. **Scheduled Workflows**: Schedule periodic workflow executions with cron expressions
12. **Task Monitoring**: Real-time dashboard for monitoring task queue, workers, and execution progress

## Impact

### Affected Specs
This is a new system with the following new capabilities:
- `trading-workflow` - Automated trading workflow orchestration with concurrent execution
- `message-queue` - Celery + Redis task queue for async processing
- `workflow-builder` - Visual workflow creation and management
- `autogen-framework` - Microsoft AutoGen multi-agent decision making
- `order-management` - Order lifecycle management
- `risk-management` - Risk calculation and enforcement
- `portfolio-management` - Position and P&L tracking
- `chart-analysis` - Technical chart generation and analysis
- `database-schema` - PostgreSQL schema definition (extended with workflow tables)
- `api-backend` - FastAPI REST API (extended with workflow, task, AutoGen endpoints)
- `frontend-ui` - Tailwind CSS web interface (extended with workflow builder, monitoring)

### Affected Code
New files/directories:
- `backend/` - FastAPI application
  - `api/` - API endpoints
  - `models/` - Database models
  - `services/` - Business logic
  - `schemas/` - Pydantic models
  - `config/` - Configuration
- `frontend/` - Templates and static assets
  - `templates/` - Jinja2 HTML templates
  - `static/` - CSS/JS assets
- `database/` - Database migrations and scripts
- `docker/` - Docker configuration
- `.env` - Environment configuration template
- `docker-compose.yml` - Multi-service orchestration
- `requirements.txt` - Python dependencies

### Migration Notes
This is a new application that will coexist with the existing Flask app. The existing `webapp/` directory will remain for backward compatibility, and the new system will be in `backend/` and `frontend/` directories.

## Dependencies

### External Services
- IBKR Client Portal Gateway (port 5055)
- PostgreSQL database
- Redis (message broker and result backend)
- MinIO object storage
- OpenAI-compatible API endpoint (for AI analysis and AutoGen agents)

### Integration Points
- IBKR REST API (`/v1/api/`)
- MinIO S3 API
- OpenAI Chat Completions API
- PostgreSQL database

