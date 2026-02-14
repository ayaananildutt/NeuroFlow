"""
Adaptive Traffic Controller
Calculates optimal signal timing based on real-time vehicle density data.
"""

import json
import time
import logging
from datetime import datetime
from collections import defaultdict
from sqlalchemy.orm import Session
import paho.mqtt.client as mqtt
from config import ServerConfig
from database import sync_engine
from models import SignalCommand, SignalPhase, Intersection

logger = logging.getLogger(__name__)


class TrafficController:
    """
    Adaptive traffic signal controller.

    Uses real-time vehicle density from YOLO detections to calculate
    optimal green/red durations for each intersection, bounded by
    configurable min/max values.

    Algorithm:
        1. Receive vehicle count from detection payload.
        2. Compute density ratio = vehicle_count / lane_capacity.
        3. Scale green duration: base + (density * scaling_factor).
        4. Clamp between MIN_GREEN and MAX_GREEN.
        5. Publish signal command via MQTT to the traffic light controller.
    """

    LANE_CAPACITY = 15  # Estimated max vehicles per lane at saturation

    def __init__(self):
        self.mqtt_client = mqtt.Client(
            client_id=f"{ServerConfig.MQTT_CLIENT_ID}-controller",
            protocol=mqtt.MQTTv311
        )
        self.is_connected: bool = False
        self.commands_sent: int = 0
        self.active_phases: dict = {}  # intersection_id -> current phase
        self.density_history: dict = defaultdict(list)  # Rolling density window

        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc) -> None:
        """Handle MQTT connection for command publishing."""
        if rc == 0:
            self.is_connected = True
            logger.info("Traffic Controller connected to MQTT broker.")
        else:
            logger.error(f"Controller MQTT connection failed: rc={rc}")

    def _on_disconnect(self, client, userdata, rc) -> None:
        """Handle MQTT disconnection."""
        self.is_connected = False

    def start(self) -> None:
        """Connect to the MQTT broker for publishing signal commands."""
        try:
            self.mqtt_client.connect(
                host=ServerConfig.MQTT_BROKER_HOST,
                port=ServerConfig.MQTT_BROKER_PORT,
                keepalive=60
            )
            self.mqtt_client.loop_start()
            logger.info("Traffic Controller started.")
        except Exception as e:
            logger.error(f"Failed to start Traffic Controller: {e}")

    def process_detection(self, detection: dict) -> dict | None:
        """
        Process a detection event and determine if a signal change is needed.

        Args:
            detection: Detection payload from MQTT.

        Returns:
            Signal command dict if a change was issued, None otherwise.
        """
        intersection_id = detection.get("intersection_id", "unknown")
        vehicle_count = detection.get("total_vehicles", 0)
        vehicle_counts = detection.get("vehicle_counts", {})

        # Update density history (keep last 10 readings)
        self.density_history[intersection_id].append(vehicle_count)
        if len(self.density_history[intersection_id]) > 10:
            self.density_history[intersection_id].pop(0)

        # Calculate smoothed density using moving average
        smoothed_count = sum(self.density_history[intersection_id]) / len(
            self.density_history[intersection_id]
        )

        # Compute optimal green duration
        green_duration = self._calculate_green_duration(smoothed_count)

        # Determine signal phase
        new_phase = self._determine_phase(smoothed_count)

        # Check if phase change is needed
        current_phase = self.active_phases.get(intersection_id)
        if current_phase == new_phase:
            return None  # No change needed

        # Build signal command
        command = {
            "intersection_id": intersection_id,
            "phase": new_phase.value,
            "green_duration_sec": green_duration,
            "yellow_duration_sec": ServerConfig.YELLOW_DURATION_SEC,
            "vehicle_count": vehicle_count,
            "smoothed_count": round(smoothed_count, 1),
            "density_ratio": round(smoothed_count / self.LANE_CAPACITY, 3),
            "timestamp": time.time(),
            "reason": self._generate_reason(new_phase, smoothed_count, vehicle_counts)
        }

        # Publish command
        self._publish_command(command)
        self._store_command(command)

        # Update active phase
        self.active_phases[intersection_id] = new_phase

        return command

    def _calculate_green_duration(self, vehicle_count: float) -> int:
        """
        Calculate optimal green light duration based on vehicle density.

        Uses a linear scaling model with clamping:
            duration = base + (density_ratio * scaling_factor * base)
        """
        density_ratio = min(vehicle_count / self.LANE_CAPACITY, 1.0)

        base = ServerConfig.DEFAULT_GREEN_DURATION_SEC
        scaled = base + (
            density_ratio * ServerConfig.DENSITY_SCALING_FACTOR * base
        )

        # Clamp to configured bounds
        clamped = max(
            ServerConfig.MIN_GREEN_DURATION_SEC,
            min(int(scaled), ServerConfig.MAX_GREEN_DURATION_SEC)
        )

        return clamped

    def _determine_phase(self, vehicle_count: float) -> SignalPhase:
        """Determine the appropriate signal phase based on vehicle density."""
        density_ratio = vehicle_count / self.LANE_CAPACITY

        if density_ratio >= 0.7:
            return SignalPhase.GREEN  # High traffic — extend green
        elif density_ratio >= 0.3:
            return SignalPhase.GREEN  # Moderate traffic — standard green
        else:
            return SignalPhase.RED  # Low traffic — give time to other directions

    def _generate_reason(
        self,
        phase: SignalPhase,
        count: float,
        vehicle_counts: dict
    ) -> str:
        """Generate a human-readable reason for the signal change."""
        dominant_type = max(vehicle_counts, key=vehicle_counts.get) if vehicle_counts else "N/A"
        density_pct = round((count / self.LANE_CAPACITY) * 100, 1)

        return (
            f"Phase changed to {phase.value}. "
            f"Density: {density_pct}% ({count:.0f} vehicles avg). "
            f"Dominant type: {dominant_type}."
        )

    def _publish_command(self, command: dict) -> None:
        """Publish signal command to MQTT."""
        if not self.is_connected:
            logger.warning("Controller not connected to MQTT. Command not published.")
            return

        topic = (
            f"{ServerConfig.MQTT_TOPIC_COMMANDS}"
            f"/{command['intersection_id']}"
        )
        payload = json.dumps(command)

        result = self.mqtt_client.publish(topic=topic, payload=payload, qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            self.commands_sent += 1
            logger.info(
                f"Signal command sent to {command['intersection_id']}: "
                f"{command['phase']} for {command['green_duration_sec']}s "
                f"(density: {command['density_ratio']:.1%})"
            )
        else:
            logger.error(f"Failed to publish signal command: rc={result.rc}")

    def _store_command(self, command: dict) -> None:
        """Persist signal command to the database."""
        try:
            with Session(sync_engine) as session:
                intersection = session.query(Intersection).filter_by(
                    intersection_id=command["intersection_id"]
                ).first()

                if intersection:
                    signal_cmd = SignalCommand(
                        intersection_ref=intersection.id,
                        timestamp=datetime.utcfromtimestamp(command["timestamp"]),
                        phase=SignalPhase(command["phase"]),
                        duration_sec=command["green_duration_sec"],
                        reason=command["reason"],
                        vehicle_density=command["density_ratio"],
                        is_override=False
                    )
                    session.add(signal_cmd)
                    session.commit()
        except Exception as e:
            logger.error(f"Failed to store signal command: {e}")

    def manual_override(
        self,
        intersection_id: str,
        phase: SignalPhase,
        duration_sec: int
    ) -> dict:
        """
        Manually override the signal phase for an intersection.

        Args:
            intersection_id: Target intersection.
            phase: Desired signal phase.
            duration_sec: Duration in seconds.

        Returns:
            Signal command dict.
        """
        command = {
            "intersection_id": intersection_id,
            "phase": phase.value,
            "green_duration_sec": duration_sec,
            "yellow_duration_sec": ServerConfig.YELLOW_DURATION_SEC,
            "vehicle_count": 0,
            "smoothed_count": 0,
            "density_ratio": 0,
            "timestamp": time.time(),
            "reason": f"Manual override to {phase.value} for {duration_sec}s."
        }

        self._publish_command(command)
        self._store_command(command)
        self.active_phases[intersection_id] = phase

        return command

    def stop(self) -> None:
        """Stop the traffic controller."""
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        logger.info(f"Traffic Controller stopped. Commands sent: {self.commands_sent}")

    @property
    def stats(self) -> dict:
        """Return controller statistics."""
        return {
            "is_connected": self.is_connected,
            "commands_sent": self.commands_sent,
            "active_phases": {
                k: v.value for k, v in self.active_phases.items()
            },
            "monitored_intersections": len(self.density_history)
        }
