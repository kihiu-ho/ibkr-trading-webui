"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.api import health, strategies, workflows, orders, market_data, frontend
from backend.core.database import engine
from backend.models import Base
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IBKR Trading Platform",
    version="1.0.0",
    description="Automated trading platform for Interactive Brokers"
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

# Include API routers
app.include_router(health.router, tags=["health"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(market_data.router, tags=["market"])

# Frontend routes
app.include_router(frontend.router, tags=["frontend"])


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
    
    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Application shutdown")
