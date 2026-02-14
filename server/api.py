"""
FastAPI REST API & WebSocket Endpoints
Provides real-time traffic data, metrics, and signal control.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from database import get_async_session
from models import (
    Intersection, Detection, SignalCommand, SignalPhase
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Traffic API"])


# ──────────────────────────────────────────
# Pydantic Schemas
# ──────────────────────────────────────────

class IntersectionResponse(BaseModel):
    id: int
    intersection_id: str
    name: str
    latitude: float | None
    longitude: float | None
    num_lanes: int
    is_active: bool

    class Config:
        from_attributes = True


class DetectionResponse(BaseModel):
    id: int
    intersection_id: str
    timestamp: datetime
    total_vehicles: int
    vehicle_counts: dict
    inference_time_ms: float | None

    class Config:
        from_attributes = True


class MetricsSummary(BaseModel):
    intersection_id: str
    avg_vehicle_count: float
    max_vehicle_count: int
    total_detections: int
    congestion_level: float
    dominant_vehicle_type: str


class SignalOverrideRequest(BaseModel):
    phase: str
    duration_sec: int


class SystemStatus(BaseModel):
    uptime_sec: float
    total_intersections: int
    total_detections: int
    total_commands: int
    active_connections: int


# ──────────────────────────────────────────
# WebSocket Connection Manager
# ──────────────────────────────────────────

class ConnectionManager:
    """Manages WebSocket connections for live dashboard updates."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        total = len(self.active_connections)
        logger.info(f"WebSocket client connected. Total: {total}")

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)
        total = len(self.active_connections)
        logger.info(f"WebSocket client disconnected. Total: {total}")

    async def broadcast(self, message: dict) -> None:
        """Send a message to all connected WebSocket clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.active_connections.remove(conn)


ws_manager = ConnectionManager()
server_start_time = time.time()

# Reference to traffic controller (set from main.py)
_traffic_controller = None


def set_traffic_controller(controller):
    """Set the traffic controller reference for signal override endpoints."""
    global _traffic_controller
    _traffic_controller = controller


# ──────────────────────────────────────────
# REST Endpoints
# ──────────────────────────────────────────

@router.get("/health")
async def health_check():
    """System health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_sec": round(time.time() - server_start_time, 1)
    }


@router.get("/intersections", response_model=List[IntersectionResponse])
async def list_intersections(
    session: AsyncSession = Depends(get_async_session)
):
    """List all monitored intersections."""
    result = await session.execute(
        select(Intersection).where(Intersection.is_active.is_(True))
    )
    intersections = result.scalars().all()
    return intersections


@router.get("/intersections/{intersection_id}")
async def get_intersection(
    intersection_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Get details for a specific intersection."""
    result = await session.execute(
        select(Intersection).where(
            Intersection.intersection_id == intersection_id
        )
    )
    intersection = result.scalar_one_or_none()
    if not intersection:
        raise HTTPException(status_code=404, detail="Intersection not found")

    return {
        "intersection": IntersectionResponse.model_validate(intersection),
        "current_phase": (
            _traffic_controller.active_phases.get(intersection_id, "UNKNOWN")
            if _traffic_controller else "UNKNOWN"
        )
    }


@router.get("/detections")
async def list_detections(
    intersection_id: str | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session)
):
    """List recent detection events, optionally filtered by intersection."""
    query = select(Detection).order_by(desc(Detection.timestamp)).limit(limit)

    if intersection_id:
        subq = select(Intersection.id).where(
            Intersection.intersection_id == intersection_id
        )
        query = query.where(Detection.intersection_ref.in_(subq))

    result = await session.execute(query)
    detections = result.scalars().all()

    return [
        {
            "id": d.id,
            "timestamp": d.timestamp.isoformat(),
            "total_vehicles": d.total_vehicles,
            "vehicle_counts": d.vehicle_counts,
            "inference_time_ms": d.inference_time_ms,
            "frame_number": d.frame_number
        }
        for d in detections
    ]


@router.get("/metrics/{intersection_id}")
async def get_metrics(
    intersection_id: str,
    period_minutes: int = 60,
    session: AsyncSession = Depends(get_async_session)
):
    """Get aggregated traffic metrics for an intersection."""
    subq = select(Intersection.id).where(
        Intersection.intersection_id == intersection_id
    )
    since = datetime.utcnow() - timedelta(minutes=period_minutes)

    result = await session.execute(
        select(
            func.avg(Detection.total_vehicles).label("avg_vehicles"),
            func.max(Detection.total_vehicles).label("max_vehicles"),
            func.count(Detection.id).label("total_detections"),
            func.avg(Detection.inference_time_ms).label("avg_inference_ms")
        ).where(
            Detection.intersection_ref.in_(subq),
            Detection.timestamp >= since
        )
    )
    row = result.one()

    return {
        "intersection_id": intersection_id,
        "period_minutes": period_minutes,
        "avg_vehicle_count": round(float(row.avg_vehicles or 0), 1),
        "max_vehicle_count": int(row.max_vehicles or 0),
        "total_detections": int(row.total_detections or 0),
        "avg_inference_ms": round(float(row.avg_inference_ms or 0), 2)
    }


@router.get("/signals/{intersection_id}/history")
async def get_signal_history(
    intersection_id: str,
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session)
):
    """Get signal command history for an intersection."""
    subq = select(Intersection.id).where(
        Intersection.intersection_id == intersection_id
    )
    result = await session.execute(
        select(SignalCommand)
        .where(SignalCommand.intersection_ref.in_(subq))
        .order_by(desc(SignalCommand.timestamp))
        .limit(limit)
    )
    commands = result.scalars().all()

    return [
        {
            "id": c.id,
            "phase": c.phase.value,
            "duration_sec": c.duration_sec,
            "reason": c.reason,
            "vehicle_density": c.vehicle_density,
            "is_override": c.is_override,
            "timestamp": c.timestamp.isoformat()
        }
        for c in commands
    ]


@router.post("/signals/{intersection_id}/override")
async def override_signal(
    intersection_id: str,
    request: SignalOverrideRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Manually override the traffic signal for an intersection."""
    if not _traffic_controller:
        raise HTTPException(status_code=503, detail="Traffic controller not available")

    try:
        phase = SignalPhase(request.phase)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid phase. Valid: "
                   f"{[p.value for p in SignalPhase]}"
        )

    command = _traffic_controller.manual_override(
        intersection_id=intersection_id,
        phase=phase,
        duration_sec=request.duration_sec
    )

    # Broadcast override to WebSocket clients
    await ws_manager.broadcast({
        "type": "signal_override",
        "data": command
    })

    return {"status": "override_applied", "command": command}


@router.get("/status", response_model=SystemStatus)
async def system_status(
    session: AsyncSession = Depends(get_async_session)
):
    """Get overall system status."""
    intersections_count = await session.execute(
        select(func.count(Intersection.id))
    )
    detections_count = await session.execute(
        select(func.count(Detection.id))
    )
    commands_count = await session.execute(
        select(func.count(SignalCommand.id))
    )

    return SystemStatus(
        uptime_sec=round(time.time() - server_start_time, 1),
        total_intersections=intersections_count.scalar() or 0,
        total_detections=detections_count.scalar() or 0,
        total_commands=commands_count.scalar() or 0,
        active_connections=len(ws_manager.active_connections)
    )


# ──────────────────────────────────────────
# WebSocket Endpoint
# ──────────────────────────────────────────

@router.websocket("/ws/live")
async def websocket_live_feed(websocket: WebSocket):
    """WebSocket endpoint for real-time detection and signal updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for client messages
            data = await websocket.receive_text()
            logger.debug(f"WebSocket received: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
