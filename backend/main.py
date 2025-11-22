"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.api import health, orders, market_data, market_data_cache, frontend, dashboard, ibkr_auth, indicators, positions, charts, llm_analyses, artifacts, chart_images, workflow_symbols, schedules
from backend.app.routes import airflow_proxy, mlflow_proxy
from backend.core.database import engine, get_db
from backend.models import Base
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IBKR Trading Platform",
    version="2.0.0",
    description="Automated trading platform for Interactive Brokers with LLM-powered decision making"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
if os.path.exists("frontend/static"):
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Include Core API routers
app.include_router(health.router, tags=["health"])
app.include_router(market_data.router, tags=["market"])
app.include_router(market_data_cache.router, prefix="/api/market-data", tags=["market-data-cache"])
app.include_router(indicators.router, prefix="/api/indicators", tags=["indicators"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(positions.router, tags=["positions"])
app.include_router(ibkr_auth.router, prefix="/api/ibkr/auth", tags=["ibkr-auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(charts.router, prefix="/api", tags=["charts"])
app.include_router(llm_analyses.router, prefix="/api", tags=["llm-analyses"])
app.include_router(artifacts.router, prefix="/api/artifacts", tags=["artifacts"])
app.include_router(chart_images.router, prefix="/api/artifacts", tags=["artifacts"])
app.include_router(workflow_symbols.router, tags=["workflow-symbols"])
app.include_router(schedules.router)

# Frontend routes
app.include_router(frontend.router, tags=["frontend"])

# Airflow/MLflow proxy routes
app.include_router(airflow_proxy.router, prefix="/api/airflow", tags=["airflow"])
app.include_router(mlflow_proxy.router, prefix="/api/mlflow", tags=["mlflow"])

# WebSocket functionality removed (was used for workflow log streaming)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.warning(f"Failed to create some database tables (may have FK constraints): {e}")
        logger.info("Attempting to create tables without foreign key constraints...")
        # Try to create tables ignoring foreign key errors
        # This is a workaround for models with references to non-existent tables
        try:
            with engine.connect() as conn:
                conn.execution_options(isolation_level="AUTOCOMMIT")
                # Drop all constraints and try again
                for table in Base.metadata.tables.values():
                    try:
                        table.create(bind=engine, checkfirst=True)
                    except Exception as table_err:
                        logger.warning(f"Couldn't create table {table.name}: {table_err}")
            logger.info("Table creation attempt completed")
        except Exception as fallback_err:
            logger.error(f"Fallback table creation also failed: {fallback_err}")
    
    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Application shutdown")
