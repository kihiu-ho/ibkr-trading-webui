# Project Context

## Purpose
This project provides a comprehensive web-based trading platform for Interactive Brokers (IBKR) with integrated ML workflow orchestration. It combines:
- **Trading Operations**: Real-time portfolio management, order execution, and market data visualization
- **ML Workflows**: Automated trading signal generation using LLM analysis of technical charts
- **Experiment Tracking**: Full lineage tracking of data, models, and trading decisions
- **Workflow Orchestration**: Airflow-powered end-to-end trading workflows

The goal is to provide an intelligent, data-driven trading platform that combines traditional broker operations with modern ML/AI capabilities for algorithmic trading.

## Tech Stack

### Core Application
- **Backend Framework**: Python 3.11 with FastAPI
- **Frontend**: Jinja2 templates + Tailwind CSS + Alpine.js
- **HTTP Client**: httpx for async API calls
- **API Documentation**: FastAPI automatic OpenAPI/Swagger docs

### IBKR Integration
- **Gateway**: Interactive Brokers Client Portal Gateway (containerized)
- **API Version**: v1 REST API
- **Authentication**: Web-based SSO through Gateway at port 5055
- **SSL/TLS**: Self-signed certificates with verification disabled

### ML & Workflow Stack
- **Workflow Orchestration**: Apache Airflow 2.7+ with XCom for task communication
- **Experiment Tracking**: MLflow for metrics, parameters, and artifact management
- **Object Storage**: MinIO for charts, models, and large artifacts
- **LLM Integration**: OpenAI/Anthropic APIs for trading signal analysis
- **Technical Analysis**: mplfinance, pandas-ta for indicator calculation

### Data Layer
- **Primary Database**: PostgreSQL 15 (for trading data, artifacts, lineage)
- **Metadata Store**: PostgreSQL (Airflow and MLflow metadata)
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **Caching**: Redis (for Airflow Celery backend)
- **Validation**: Pydantic v2 for data models and validation

### Containerization & Orchestration
- **Container Runtime**: Docker & Docker Compose
- **Base Images**: 
  - Python: `python:3.11-slim-bookworm`
  - Airflow: Custom image based on `apache/airflow:2.7.3-python3.11`
- **Services**: 7 containers (backend, postgres, redis, minio, mlflow, airflow-webserver, airflow-scheduler, ibkr-gateway)
- **Networking**: Docker bridge network with internal DNS resolution

### Development Tools
- **Code Quality**: Black, isort, flake8, mypy
- **Testing**: pytest, pytest-cov, pytest-asyncio
- **API Testing**: Swagger UI at `/docs`, ReDoc at `/redoc`

## Project Conventions

### Code Style

#### Python
- **Style Guide**: PEP 8 with 100-character line length
- **Naming Conventions**:
  - `snake_case` for functions, variables, modules
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
- **Type Hints**: Required for function signatures
- **Docstrings**: Google-style docstrings for classes and functions
- **Async/Await**: Use for I/O-bound operations (API calls, database queries)

#### Frontend
- **Templating**: Jinja2 with `{% extends "base.html" %}`
- **CSS Framework**: Tailwind CSS 3.x (utility-first, no custom CSS)
- **JavaScript**: Alpine.js for reactivity (avoid jQuery)
- **Icons**: Font Awesome 6.x
- **Components**: Reusable partials in `templates/partials/`

### Architecture Patterns

#### Service Architecture
```
frontend (Jinja2/Tailwind) → backend (FastAPI) → IBKR Gateway (Java)
                                ↓                    ↓
                          PostgreSQL            IBKR REST API
                                ↓
                           Artifacts
                                ↓
                     ┌──────────┴──────────┐
                  Airflow              MLflow
                     ↓                    ↓
                  MinIO ← Charts/Models → MinIO
```

#### API Communication
- **Pattern**: Backend acts as proxy/aggregator for IBKR Gateway
- **Error Handling**: Graceful degradation, log warnings for non-critical failures
- **Retries**: Exponential backoff for transient failures
- **Timeouts**: 10s default for IBKR API calls, 30s for workflow operations

#### Database Design
- **Schema**: Normalized relational design with JSONB for flexible metadata
- **Migrations**: Alembic for schema versioning in `database/migrations/`
- **Indexes**: Strategic indexes on workflow_id, execution_id, symbol, created_at
- **Constraints**: Foreign keys only for critical relationships (many removed for flexibility)

#### Workflow Design
- **Pattern**: DAG-based workflows with Pydantic models for data validation
- **Data Flow**: XCom for inter-task communication, database for persistence
- **Artifacts**: Store LLM I/O, charts, signals in database with file references
- **Lineage**: Track workflow_id, execution_id, step_name for full traceability

#### Port Allocation
- `5055`: IBKR Client Portal Gateway (HTTPS)
- `8000`: FastAPI backend (HTTP)
- `5432`: PostgreSQL
- `6379`: Redis
- `9000`: MinIO (S3-compatible storage)
- `9001`: MinIO Console
- `5000`: MLflow tracking server
- `8080`: Airflow webserver

### File Structure
```
ibkr-trading-webui/
├── backend/                 # FastAPI application
│   ├── api/                # API route handlers
│   ├── app/                # Application logic
│   │   ├── routes/        # Special routes (proxies)
│   │   └── services/      # Business logic services
│   ├── core/              # Core utilities (database, config)
│   ├── models/            # SQLAlchemy models
│   └── schemas/           # Pydantic schemas
├── frontend/              # Templates and static files
│   ├── templates/         # Jinja2 HTML templates
│   │   └── partials/     # Reusable components
│   └── static/           # CSS, JS, images
├── dags/                  # Airflow DAG definitions
│   ├── models/           # Pydantic models for workflows
│   └── utils/            # Workflow utilities
├── database/             # Database scripts
│   ├── migrations/       # SQL migration scripts
│   └── init-db.sh       # Database initialization
├── scripts/              # Utility scripts
│   └── init-databases.sh # Multi-database setup
├── tests/                # Test suites
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── docs/                 # Documentation
│   ├── guides/          # How-to guides
│   ├── implementation/  # Implementation summaries
│   └── history/         # Status updates
├── openspec/             # OpenSpec specifications
│   ├── specs/           # Current specifications
│   └── changes/         # Proposed changes
├── docker-compose.yml    # Service orchestration
└── requirements.txt      # Python dependencies
  ```

### Testing Strategy
- **Unit Tests**: Test business logic in isolation with mocks
- **Integration Tests**: Test API endpoints with test database
- **Workflow Tests**: Test DAGs with Airflow test mode
- **Manual Testing**: Paper trading account for order execution tests
- **CI/CD**: Run tests on PR, lint with pre-commit hooks

### Git Workflow
- **Main Branch**: `main` for stable releases
- **Feature Branches**: `feature/description` for new capabilities
- **Fix Branches**: `fix/description` for bug fixes
- **Commits**: Conventional commits format (`feat:`, `fix:`, `docs:`)
- **Pull Requests**: Require review for merge to main
- **Releases**: Semantic versioning (v1.2.3)

### Error Handling
- **External APIs**: Try-except with specific error messages and logging
- **Database**: Transaction rollback on errors, graceful degradation
- **Workflows**: Log warnings for non-critical failures, continue execution
- **Frontend**: User-friendly error messages, toast notifications

### Logging
- **Level**: INFO for production, DEBUG for development
- **Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Handlers**: Console + file (rotate daily)
- **Sensitive Data**: Never log API keys, passwords, or tokens

## Domain Context

### IBKR Trading Concepts
- **Contract ID (conid)**: Unique identifier for financial instruments (integer)
- **Account ID**: IBKR account identifier (format: `U1234567` or `DU1234567` for paper)
- **Order Types**: 
  - `LMT`: Limit order with price
  - `MKT`: Market order
  - `STP`: Stop order with aux_price
- **Time-in-Force (TIF)**: `DAY`, `GTC`, `IOC`, `FOK`
- **Order Status**: `Submitted`, `PreSubmitted`, `Filled`, `Cancelled`, `Inactive`
- **Position**: Open position with quantity, average cost, unrealized P&L
- **Market Data**: Real-time quotes, historical bars (OHLCV)

### Technical Analysis Concepts
- **Indicators**: SMA (20/50/200), RSI (14), MACD, Bollinger Bands
- **Timeframes**: Daily (1D), Weekly (1W), Intraday (1H, 15M)
- **Chart Types**: Candlestick, line, volume
- **Signals**: BUY, SELL, HOLD with confidence levels (HIGH, MEDIUM, LOW)

### ML Workflow Concepts
- **Experiment**: Collection of runs for a specific trading strategy
- **Run**: Single execution of a workflow with logged parameters/metrics
- **Artifact**: Stored output (chart, LLM analysis, trading signal)
- **Lineage**: Traceability from market data → chart → analysis → signal → order
- **Workflow ID**: Identifier for workflow type (e.g., `ibkr_trading_signal_workflow`)
- **Execution ID**: Unique identifier for specific workflow run (timestamp-based)

### API Endpoints

#### Backend API (FastAPI)
- **Health**: `GET /health` - Service health check
- **Dashboard**: `GET /api/dashboard/stats` - Trading metrics
- **Orders**: `GET /api/orders` - List orders, `POST /api/orders` - Place order
- **Positions**: `GET /api/positions/` - Portfolio positions
- **Market Data**: `GET /api/market-data/{symbol}` - Real-time quotes
- **Artifacts**: `GET /api/artifacts/` - List artifacts, `GET /api/artifacts/{id}` - Detail
- **MLflow Proxy**: `GET /api/mlflow/*` - Proxy to MLflow tracking server
- **Airflow Proxy**: `GET /api/airflow/*` - Proxy to Airflow webserver

#### IBKR Gateway API
- **Portfolio**: `GET /v1/api/portfolio/{account}/positions`
- **Market Data**: `GET /v1/api/iserver/marketdata/snapshot`
- **Orders**: `POST /v1/api/iserver/account/{account}/orders`
- **Auth Status**: `GET /v1/api/iserver/auth/status`
- **Contract Search**: `POST /v1/api/iserver/secdef/search`

### Authentication Flow
1. User starts IBKR Gateway container (auto-started by Docker Compose)
2. Gateway requires authentication at `https://localhost:5055`
3. User logs in with IBKR credentials (supports 2FA)
4. Gateway maintains session for ~24 hours
5. Backend checks auth status via `/v1/api/iserver/auth/status`
6. Dashboard shows connection status (green = authenticated, red = disconnected)

## Important Constraints

### Technical Constraints
- **SSL Verification Disabled**: Using `verify=False` for IBKR API due to self-signed certs
- **Single Account**: Application designed for single account (configurable via env)
- **Gateway Dependency**: Backend requires authenticated Gateway to function
- **Session Timeout**: IBKR sessions expire after ~24 hours of inactivity
- **Rate Limiting**: Subject to IBKR API rate limits (varies by endpoint)
- **Market Data**: Requires market data subscriptions for certain exchanges
- **Container Memory**: Airflow workers need 2GB+ memory for DAG execution
- **Storage**: Charts and artifacts stored in `/tmp` (ephemeral) or MinIO (persistent)

### Regulatory Constraints
- **IBKR Terms**: Subject to IBKR Client Portal Gateway terms of service
- **Trading Compliance**: Users responsible for securities regulations compliance
- **Market Data**: Delayed data for non-professionals, real-time requires subscription
- **Automated Trading**: Users must comply with algorithmic trading regulations
- **Liability**: Trading decisions are user's responsibility, not the application's

### Business Constraints
- **IBKR Account Required**: Active brokerage account needed
- **Paper Trading**: Recommended for testing (free, no real money)
- **Market Hours**: Live trading limited to market hours (pre-market/after-hours available)
- **Minimum Order Size**: Subject to IBKR minimum trade sizes per instrument
- **Commission**: IBKR commission structure applies to all trades

### OpenSpec Constraints
- **Change Proposals**: Required for new features, breaking changes, architecture updates
- **Spec-First**: Write specs before implementation for complex changes
- **Validation**: Run `openspec validate --strict` before committing changes
- **Archive**: Move completed changes to `changes/archive/YYYY-MM-DD-[name]/`

## External Dependencies

### Interactive Brokers Client Portal Gateway
- **Source**: https://download2.interactivebrokers.com/portal/clientportal.gw.zip
- **Version**: Latest stable (auto-updated in Docker build)
- **Purpose**: REST API gateway for IBKR trading operations
- **Configuration**: `conf.yaml` with SSL settings, port allocation
- **Authentication**: Web-based login with 2FA support
- **Limitations**: Java-based, requires JRE 17+, memory-intensive

### IBKR REST API
- **Host**: https://api.ibkr.com (proxied through Gateway)
- **Version**: v1 (most recent stable)
- **Documentation**: https://www.interactivebrokers.com/api/doc.html
- **Environment**: Production or paper trading (configured in Gateway)
- **Rate Limits**: Varies by endpoint (portfolio: 1/sec, orders: 50/min, market data: 100/min)

### Apache Airflow
- **Version**: 2.7.3
- **Executor**: CeleryExecutor with Redis backend
- **Scheduler**: Single scheduler instance
- **Workers**: 1-2 workers for DAG execution
- **Database**: PostgreSQL for metadata
- **Purpose**: Orchestrate ML workflows, trading signal generation

### MLflow
- **Version**: 2.x (latest)
- **Backend Store**: PostgreSQL for metadata
- **Artifact Store**: MinIO (S3-compatible)
- **Tracking Server**: HTTP API on port 5000
- **Purpose**: Experiment tracking, model registry, artifact management

### MinIO
- **Version**: Latest stable
- **API**: S3-compatible REST API
- **Buckets**: `ml-experiments/`, `trading-data/`
- **Purpose**: Persistent storage for charts, models, large artifacts
- **Access**: Console at port 9001, API at port 9000

### LLM Providers
- **OpenAI**: GPT-4o, GPT-4-turbo for trading signal analysis
- **Anthropic**: Claude 3.5 Sonnet as alternative
- **Configuration**: API keys via environment variables
- **Usage**: Chart analysis, signal generation, trade reasoning
- **Cost**: ~$0.01-0.05 per workflow run (depends on model)

### Python Dependencies (Key Packages)
```
fastapi==0.104.1          # Web framework
uvicorn==0.24.0           # ASGI server
sqlalchemy==2.0.23        # ORM
pydantic==2.5.0           # Data validation
httpx==0.25.1             # Async HTTP client
pandas==2.1.3             # Data manipulation
mplfinance==0.12.10b0     # Chart generation
pandas-ta==0.3.14b        # Technical indicators
mlflow==2.8.1             # Experiment tracking
apache-airflow==2.7.3     # Workflow orchestration
redis==5.0.1              # Caching
psycopg2-binary==2.9.9    # PostgreSQL driver
alembic==1.12.1           # Database migrations
```

### System Dependencies
- **Docker Desktop**: 4.x+ for containerization
- **Python**: 3.11 for backend and Airflow
- **Java**: OpenJDK 17 JRE for IBKR Gateway
- **PostgreSQL**: 15 for data persistence
- **Redis**: 7.x for task queue
- **MinIO**: Latest for object storage

## Development Setup

### Environment Variables
```bash
# Required
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=ibkr_trading

# Optional
IBKR_ACCOUNT_ID=DU1234567       # Paper trading account
LLM_PROVIDER=openai             # or 'anthropic'
LLM_MODEL=gpt-4o                # Model name
LLM_API_KEY=sk-...              # API key
DEBUG_MODE=true                 # Enable debug logging
```

### Quick Start
```bash
# Clone repository
git clone https://github.com/yourusername/ibkr-trading-webui
cd ibkr-trading-webui

# Start all services
./start-webapp.sh

# Access applications
# Frontend: http://localhost:8000
# IBKR Gateway: https://localhost:5055
# Airflow: http://localhost:8080 (admin/admin)
# MLflow: http://localhost:5000
```

### Development Workflow
1. Create feature branch: `git checkout -b feature/my-feature`
2. Write OpenSpec proposal for significant changes
3. Implement changes with tests
4. Run linters: `black .`, `isort .`, `flake8 .`
5. Run tests: `pytest tests/`
6. Commit with conventional commits
7. Create PR for review
8. Merge to main after approval

## Monitoring & Observability

### Health Checks
- **Backend**: `GET /health` returns JSON with service status
- **IBKR Gateway**: `GET /v1/api/iserver/auth/status`
- **PostgreSQL**: Connection pooling with health checks
- **Airflow**: DAG success/failure alerts
- **MLflow**: Tracking server uptime

### Logging
- **Backend**: FastAPI logs to console, structured JSON in production
- **Airflow**: Task logs in `/logs`, viewable in UI
- **Database**: Query logs for slow queries (>1s)
- **Docker**: Centralized logging with `docker-compose logs`

### Metrics
- **Trading**: Orders placed, filled, cancelled, P&L
- **Workflows**: DAG runs, task durations, failure rates
- **ML**: Experiment count, artifact size, model performance
- **System**: Container CPU/memory, database connections

## Security Considerations

### Authentication
- **IBKR**: Handled by Gateway with IBKR SSO
- **Airflow**: Basic auth (admin/admin) - change in production
- **MLflow**: No auth by default - add reverse proxy in production
- **MinIO**: Access key/secret key authentication

### Data Privacy
- **Sensitive Data**: API keys, passwords stored in environment variables
- **Encryption**: HTTPS for IBKR API, HTTP for internal services (Docker network)
- **Credentials**: Never log or store in plaintext
- **Session Management**: IBKR Gateway handles session cookies

### Best Practices
- Use paper trading account for development
- Rotate API keys regularly
- Review order placement code carefully
- Set position size limits
- Enable transaction logging
- Monitor for unexpected trades

## Performance Considerations

### Optimization Strategies
- **Database**: Index on workflow_id, execution_id, symbol, created_at
- **API**: Cache frequently accessed data (portfolio, positions)
- **Workflows**: Parallelize independent tasks in DAGs
- **Charts**: Generate asynchronously, store in MinIO
- **Frontend**: Minimize API calls, use Alpine.js reactivity

### Scalability
- **Horizontal**: Add more Airflow workers for parallel workflows
- **Vertical**: Increase container memory for large datasets
- **Database**: Connection pooling, read replicas for analytics
- **Storage**: MinIO scales to multi-node cluster
- **Rate Limits**: Respect IBKR API limits with backoff

## Future Enhancements

### Planned Features
- **Backtesting**: Historical strategy testing with market replay
- **Portfolio Analytics**: Advanced P&L analysis, risk metrics
- **Multi-Account**: Support for multiple IBKR accounts
- **Alert System**: Notifications for orders, signals, errors
- **Strategy Builder**: Visual workflow designer for trading strategies

### Technical Improvements
- **Authentication**: OAuth2 + JWT for backend
- **Database**: Add TimescaleDB for time-series data
- **Monitoring**: Prometheus + Grafana for observability
- **Testing**: Increase coverage to 80%+
- **Documentation**: API documentation, architecture diagrams
