"""
MQTT Subscriber
Receives vehicle detection data from edge gateways and processes it.
"""

import json
import logging
import threading
from datetime import datetime
from sqlalchemy.orm import Session
import paho.mqtt.client as mqtt
from config import ServerConfig
from database import sync_engine
from models import Detection, Intersection

logger = logging.getLogger(__name__)


class MQTTSubscriber:
    """
    Subscribes to detection topics from edge gateways.

    Parses incoming detection payloads, persists them to PostgreSQL,
    and triggers the traffic controller for signal adjustments.
    """

    def __init__(self, on_detection_callback=None):
        """
        Args:
            on_detection_callback: Optional callback function invoked with
                                   each parsed detection dict.
        """
        self.client = mqtt.Client(
            client_id=ServerConfig.MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv311
        )
        self.is_connected: bool = False
        self.messages_received: int = 0
        self.on_detection_callback = on_detection_callback
        self._thread: threading.Thread | None = None

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc) -> None:
        """Handle MQTT connection event."""
        if rc == 0:
            self.is_connected = True
            logger.info("MQTT Subscriber connected to broker.")

            # Subscribe to all detection topics
            topic = f"{ServerConfig.MQTT_TOPIC_DETECTIONS}/+"
            client.subscribe(topic, qos=1)
            logger.info(f"Subscribed to topic: {topic}")

            # Subscribe to status topics
            status_topic = f"{ServerConfig.MQTT_TOPIC_DETECTIONS}/status"
            client.subscribe(status_topic, qos=1)
        else:
            self.is_connected = False
            logger.error(f"MQTT connection failed with rc={rc}")

    def _on_disconnect(self, client, userdata, rc) -> None:
        """Handle MQTT disconnection event."""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection (rc={rc}).")
        else:
            logger.info("MQTT Subscriber disconnected.")

    def _on_message(self, client, userdata, msg) -> None:
        """Handle incoming MQTT messages."""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode("utf-8"))

            # Skip status messages
            if topic.endswith("/status"):
                logger.info(
                    f"Edge gateway status: {payload.get('intersection_id')} "
                    f"-> {payload.get('status')}"
                )
                return

            self.messages_received += 1
            intersection_id = payload.get("intersection_id", "unknown")

            logger.debug(
                f"Detection received from {intersection_id}: "
                f"{payload.get('total_vehicles', 0)} vehicles"
            )

            # Persist to database
            self._store_detection(payload)

            # Invoke callback for traffic controller
            if self.on_detection_callback:
                self.on_detection_callback(payload)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}", exc_info=True)

    def _store_detection(self, payload: dict) -> None:
        """Persist a detection record to PostgreSQL."""
        try:
            with Session(sync_engine) as session:
                intersection_id = payload.get("intersection_id", "unknown")

                # Get or create intersection
                intersection = session.query(Intersection).filter_by(
                    intersection_id=intersection_id
                ).first()

                if not intersection:
                    intersection = Intersection(
                        intersection_id=intersection_id,
                        name=f"Intersection {intersection_id}",
                        is_active=True
                    )
                    session.add(intersection)
                    session.flush()

                # Create detection record
                detection = Detection(
                    intersection_ref=intersection.id,
                    timestamp=datetime.utcfromtimestamp(payload.get("timestamp", 0)),
                    total_vehicles=payload.get("total_vehicles", 0),
                    vehicle_counts=payload.get("vehicle_counts", {}),
                    detections_data=payload.get("detections", []),
                    inference_time_ms=payload.get("inference_time_ms"),
                    frame_number=payload.get("frame_number")
                )
                session.add(detection)
                session.commit()

        except Exception as e:
            logger.error(f"Database storage error: {e}", exc_info=True)

    def start(self) -> None:
        """Connect to broker and start listening in a background thread."""
        try:
            logger.info(
                f"Connecting MQTT Subscriber to "
                f"{ServerConfig.MQTT_BROKER_HOST}:{ServerConfig.MQTT_BROKER_PORT}"
            )
            self.client.connect(
                host=ServerConfig.MQTT_BROKER_HOST,
                port=ServerConfig.MQTT_BROKER_PORT,
                keepalive=60
            )
            self._thread = threading.Thread(
                target=self.client.loop_forever,
                daemon=True,
                name="mqtt-subscriber"
            )
            self._thread.start()
            logger.info("MQTT Subscriber thread started.")

        except Exception as e:
            logger.error(f"Failed to start MQTT Subscriber: {e}")
            raise

    def stop(self) -> None:
        """Disconnect and stop the subscriber."""
        self.client.disconnect()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info(f"MQTT Subscriber stopped. Messages received: {self.messages_received}")

    @property
    def stats(self) -> dict:
        """Return subscriber statistics."""
        return {
            "is_connected": self.is_connected,
            "messages_received": self.messages_received,
            "broker": f"{ServerConfig.MQTT_BROKER_HOST}:{ServerConfig.MQTT_BROKER_PORT}"
        }
