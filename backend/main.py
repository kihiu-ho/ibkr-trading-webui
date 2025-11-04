"""Main FastAPI application."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.api import health, strategies, orders, market_data, market_data_cache, frontend, dashboard, ibkr_auth, indicators, signals, lineage, positions, workflows, charts, llm_analyses
from backend.core.database import engine, get_db
from backend.models import Base
from backend.models.workflow_log import WorkflowLog
import logging
import os
import asyncio
import json
from typing import Set
from sqlalchemy.orm import Session

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

# Include Core Workflow API routers
app.include_router(health.router, tags=["health"])
app.include_router(workflows.router, tags=["workflows"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(market_data.router, tags=["market"])
app.include_router(market_data_cache.router, prefix="/api/market-data", tags=["market-data-cache"])
app.include_router(indicators.router, prefix="/api/indicators", tags=["indicators"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(positions.router, tags=["positions"])
app.include_router(lineage.router, tags=["lineage"])
app.include_router(ibkr_auth.router, prefix="/api/ibkr/auth", tags=["ibkr-auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(charts.router, prefix="/api", tags=["charts"])
app.include_router(llm_analyses.router, prefix="/api", tags=["llm-analyses"])

# Frontend routes
app.include_router(frontend.router, tags=["frontend"])

# WebSocket connection manager for real-time log streaming
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.execution_subscriptions: dict[WebSocket, Set[int]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        self.execution_subscriptions[websocket] = set()
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.execution_subscriptions:
            del self.execution_subscriptions[websocket]
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    def subscribe_to_execution(self, websocket: WebSocket, execution_id: int):
        if websocket in self.execution_subscriptions:
            self.execution_subscriptions[websocket].add(execution_id)
            logger.info(f"Client subscribed to execution {execution_id}")

    def unsubscribe_from_execution(self, websocket: WebSocket, execution_id: int):
        if websocket in self.execution_subscriptions:
            self.execution_subscriptions[websocket].discard(execution_id)
            logger.info(f"Client unsubscribed from execution {execution_id}")

    async def broadcast_log(self, log_data: dict):
        """Broadcast log to all subscribers of the execution."""
        execution_id = log_data.get("workflow_execution_id")
        if not execution_id:
            return

        disconnected = set()
        for websocket in self.active_connections:
            if execution_id in self.execution_subscriptions.get(websocket, set()):
                try:
                    await websocket.send_json(log_data)
                except Exception as e:
                    logger.error(f"Error sending to WebSocket: {e}")
                    disconnected.add(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)

manager = ConnectionManager()

@app.websocket("/ws/logs")
async def websocket_logs_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming."""
    await manager.connect(websocket)
    try:
        while True:
            # Receive messages from client (subscribe/unsubscribe commands)
            data = await websocket.receive_json()
            command = data.get("command")
            execution_id = data.get("execution_id")

            if command == "subscribe" and execution_id:
                manager.subscribe_to_execution(websocket, execution_id)
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "execution_id": execution_id
                })
            elif command == "unsubscribe" and execution_id:
                manager.unsubscribe_from_execution(websocket, execution_id)
                await websocket.send_json({
                    "type": "unsubscription_confirmed",
                    "execution_id": execution_id
                })
            elif command == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


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
