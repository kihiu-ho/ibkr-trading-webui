<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is an Interactive Brokers (IBKR) Trading WebUI with LLM-powered strategies, implementing automated trading decisions through AI analysis of technical charts. The system uses a microservices architecture with:

### Core Components
- **Backend**: FastAPI application (`backend/main.py`) serving REST APIs and web interface
- **Frontend**: Jinja2 templates with Tailwind CSS for the web UI
- **Task Queue**: Celery with Redis for background processing of trading workflows
- **Orchestration**: Airflow for workflow management and MLflow for experiment tracking
- **Storage**: PostgreSQL for data persistence, MinIO for chart/artifact storage
- **IBKR Integration**: Client Portal Gateway container for broker connectivity

### Key Architectural Patterns
- **OpenSpec Driven Development**: All changes follow OpenSpec workflow (`openspec/AGENTS.md`)
- **Multi-Container Setup**: Services orchestrated via Docker Compose with dependency health checks
- **Workflow-Based Trading**: Airflow DAGs execute multi-step trading strategies
- **Chart-Driven Analysis**: Generate technical analysis charts → LLM analysis → trading decisions
- **Artifact Storage**: All charts, analyses, and decisions stored with lineage tracking

### Database Schema
Main entities include Strategy, Decision, Order, Position, Artifact, and Market Data Cache. See `database/init.sql` for complete schema.

## Development Commands

### Environment Setup
```bash
# Copy environment template and configure required variables
cp env.example .env
# MUST configure: DATABASE_URL, OPENAI_API_KEY, IBKR_ACCOUNT_ID

# Reload environment after changes
./reload-env.sh
```

### Service Management
```bash
# Start all services
docker-compose up -d

# Quick start without rebuild
./start-webapp.sh

# Restart with rebuild (after requirements.txt changes)
./start-webapp.sh --rebuild

# Quick restart without health checks
./start-webapp.sh --fast

# Stop all services
docker-compose down
```

### Frontend Development
```bash
# Build CSS (production)
npm run build:css

# Watch CSS changes (development)
npm run watch:css
npm run dev  # alias for watch:css
```

### Testing
```bash
# Backend Python tests
cd backend && pytest -v

# E2E tests with Playwright
cd tests && npm test

# Run specific test
pytest backend/tests/test_indicator_calculator.py -v

# Test with markers
pytest -m unit  # unit tests only
pytest -m integration  # integration tests only
```

### Database Operations
```bash
# Connect to database
docker-compose exec backend python -c "from backend.core.database import engine; print(engine.url)"

# Run database migrations
cd database/migrations && ./run_migrations.sh

# Populate test data
python scripts/populate_market_cache.py
python scripts/populate_symbols_from_cache.py
```

### Service Health Checks
```bash
# Check all service status
docker-compose ps

# Backend health
curl http://localhost:8000/health

# Airflow health
curl http://localhost:8080/health

# View service logs
docker-compose logs -f backend
docker-compose logs -f airflow-webserver
docker-compose logs -f celery-worker
```

### Development Scripts
```bash
# Check IBKR authentication
./check_ibkr_auth.sh

# Test all services
./check-services.sh

# Verify LLM configuration
python check_llm_config.py

# Database schema verification
python check_db_schema.py
```

## Key Services & Ports

| Service | URL | Purpose |
|---------|-----|---------|
| Web Interface | http://localhost:8000 | Main trading dashboard |
| API Docs | http://localhost:8000/docs | FastAPI Swagger docs |
| Airflow | http://localhost:8080 | Workflow orchestration (airflow/airflow) |
| MLflow | http://localhost:5500 | Experiment tracking |
| Flower | http://localhost:5555 | Celery task monitoring |
| MinIO Console | http://localhost:9001 | Object storage (minioadmin/minioadmin) |
| IBKR Gateway | https://localhost:5055 | Interactive Brokers API |

## Trading Workflow Process

1. **Strategy Creation**: Define symbol, risk parameters, account size in web UI
2. **Data Fetching**: Airflow DAG retrieves historical market data from IBKR
3. **Chart Generation**: Create technical analysis charts with indicators (SuperTrend, SMA, RSI, MACD, Bollinger Bands)
4. **LLM Analysis**: GPT-4 analyzes daily/weekly charts and provides trading signals
5. **Decision Engine**: Algorithm determines BUY/SELL/HOLD based on R≥1.0 and profit margin≥5%
6. **Order Execution**: Submit market orders to IBKR with calculated position sizing
7. **Persistence**: Store all artifacts, decisions, and orders with full lineage tracking

## Important File Locations

### Configuration
- `docker-compose.yml` - Main service orchestration
- `backend/requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies for CSS build
- `pytest.ini` - Test configuration
- `tailwind.config.js` - CSS framework config

### Core Application
- `backend/main.py` - FastAPI app entry point
- `backend/models/` - SQLAlchemy database models
- `backend/api/` - API endpoint definitions
- `backend/services/` - Business logic services
- `dags/` - Airflow workflow definitions
- `frontend/templates/` - Jinja2 HTML templates

### Development Tools
- `openspec/AGENTS.md` - OpenSpec development workflow instructions
- `scripts/` - Utility scripts for testing and database operations
- `tests/` - Playwright E2E tests and fixtures

## Required Environment Variables

Essential variables that MUST be configured in `.env`:
```env
DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname?sslmode=require
OPENAI_API_KEY=your_openai_api_key_here
IBKR_ACCOUNT_ID=your_ibkr_account_id
```

Optional but recommended:
```env
OPENAI_API_BASE=https://api.openai.com/v1  # or TuringAI endpoint
OPENAI_MODEL=gpt-4o
DEBUG_MODE=true
CACHE_SYMBOLS=NVDA,TSLA  # for market data caching
```

## Development Workflow

1. **Changes**: Follow OpenSpec process in `openspec/AGENTS.md` for feature development
2. **Testing**: Run relevant tests before committing changes
3. **CSS**: Use `npm run watch:css` during frontend development
4. **Services**: Use health checks to verify service dependencies
5. **Debugging**: Check logs with `docker-compose logs -f [service]`
6. **Database**: Use migration scripts for schema changes

## Troubleshooting

- **IBKR Connection**: Verify gateway is running and authenticated at https://localhost:5055
- **Environment Issues**: Run `./reload-env.sh` after .env changes
- **Service Startup**: Check `docker-compose ps` and service logs for failures
- **Database**: Ensure DATABASE_URL is correctly configured for external PostgreSQL
- **CSS Changes**: Run `npm run build:css` if styles aren't updating