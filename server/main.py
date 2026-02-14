"""
NeuroFlow Traffic Controller Server — Main Entry Point
Starts the FastAPI server with MQTT subscriber and traffic controller.
"""

import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import ServerConfig
from database import init_database, shutdown_database
from mqtt_subscriber import MQTTSubscriber
from traffic_controller import TrafficController
from api import router, set_traffic_controller, ws_manager

# ──────────────────────────────────────────
# Logging
# ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("neuroflow.server")

# ──────────────────────────────────────────
# Service Instances
# ──────────────────────────────────────────
traffic_controller = TrafficController()
mqtt_subscriber = MQTTSubscriber(
    on_detection_callback=traffic_controller.process_detection
)


async def broadcast_detection(detection: dict):
    """Broadcast detection to all WebSocket clients."""
    await ws_manager.broadcast({
        "type": "detection",
        "data": detection
    })


# ──────────────────────────────────────────
# Application Lifespan
# ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage startup and shutdown of background services."""
    logger.info("=" * 50)
    logger.info("  NeuroFlow Traffic Controller Server")
    logger.info("=" * 50)

    # Startup
    await init_database()
    traffic_controller.start()
    set_traffic_controller(traffic_controller)
    mqtt_subscriber.start()

    logger.info(f"Server ready on {ServerConfig.SERVER_HOST}:{ServerConfig.SERVER_PORT}")
    logger.info("=" * 50)

    yield

    # Shutdown
    logger.info("Shutting down server...")
    mqtt_subscriber.stop()
    traffic_controller.stop()
    await shutdown_database()
    logger.info("Server stopped. Goodbye!")


# ──────────────────────────────────────────
# FastAPI Application
# ──────────────────────────────────────────
app = FastAPI(
    title="NeuroFlow Traffic Controller",
    description=(
        "Autonomous Traffic Control System — "
        "Real-time vehicle detection, adaptive signal timing, "
        "and traffic analytics API."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ServerConfig.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "NeuroFlow Traffic Controller",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }
