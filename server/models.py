"""
SQLAlchemy ORM Models
Defines the database schema for intersections, detections, signal commands, and metrics.
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON,
    Enum, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class SignalPhase(str, enum.Enum):
    """Traffic signal phases."""
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    FLASHING_RED = "FLASHING_RED"


class Intersection(Base):
    """Represents a monitored traffic intersection."""

    __tablename__ = "intersections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    intersection_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    num_lanes = Column(Integer, default=4)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    detections = relationship("Detection", back_populates="intersection", cascade="all, delete")
    signal_commands = relationship(
        "SignalCommand", back_populates="intersection",
        cascade="all, delete"
    )
    metrics = relationship("TrafficMetric", back_populates="intersection", cascade="all, delete")

    def __repr__(self):
        return f"<Intersection(id={self.intersection_id}, name={self.name})>"


class Detection(Base):
    """Stores individual vehicle detection events from edge gateways."""

    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    intersection_ref = Column(
        Integer, ForeignKey("intersections.id"), nullable=False, index=True
    )
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    total_vehicles = Column(Integer, nullable=False)
    vehicle_counts = Column(JSON, nullable=False)
    detections_data = Column(JSON, nullable=True)
    inference_time_ms = Column(Float, nullable=True)
    frame_number = Column(Integer, nullable=True)

    # Relationships
    intersection = relationship("Intersection", back_populates="detections")

    def __repr__(self):
        return (
            f"<Detection(intersection={self.intersection_ref}, "
            f"vehicles={self.total_vehicles}, time={self.timestamp})>"
        )


class SignalCommand(Base):
    """Records signal change commands sent to traffic lights."""

    __tablename__ = "signal_commands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    intersection_ref = Column(
        Integer, ForeignKey("intersections.id"), nullable=False, index=True
    )
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    phase = Column(Enum(SignalPhase), nullable=False)
    duration_sec = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    vehicle_density = Column(Float, nullable=True)
    is_override = Column(Boolean, default=False)

    # Relationships
    intersection = relationship("Intersection", back_populates="signal_commands")

    def __repr__(self):
        return (
            f"<SignalCommand(intersection={self.intersection_ref}, "
            f"phase={self.phase}, duration={self.duration_sec}s)>"
        )


class TrafficMetric(Base):
    """Aggregated traffic metrics computed at regular intervals."""

    __tablename__ = "traffic_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    intersection_ref = Column(
        Integer, ForeignKey("intersections.id"), nullable=False, index=True
    )
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    period_minutes = Column(Integer, default=5)
    avg_vehicle_count = Column(Float, nullable=False)
    max_vehicle_count = Column(Integer, nullable=False)
    total_detections = Column(Integer, nullable=False)
    avg_inference_ms = Column(Float, nullable=True)
    dominant_vehicle_type = Column(String(50), nullable=True)
    congestion_level = Column(Float, nullable=True)  # 0.0 to 1.0

    # Relationships
    intersection = relationship("Intersection", back_populates="metrics")

    def __repr__(self):
        return (
            f"<TrafficMetric(intersection={self.intersection_ref}, "
            f"avg_vehicles={self.avg_vehicle_count}, "
            f"congestion={self.congestion_level})>"
        )
