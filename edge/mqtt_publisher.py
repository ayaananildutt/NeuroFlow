"""
MQTT Publisher
Publishes vehicle detection results to the MQTT broker for cloud processing.
"""

import json
import time
import logging
import paho.mqtt.client as mqtt
from config import EdgeConfig

logger = logging.getLogger(__name__)


class MQTTPublisher:
    """
    Publishes detection payloads to the MQTT broker.

    Handles connection management, automatic reconnection,
    and JSON serialization of detection results.
    """

    def __init__(self):
        self.client: mqtt.Client = mqtt.Client(
            client_id=EdgeConfig.MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv311
        )
        self.is_connected: bool = False
        self.messages_sent: int = 0
        self.last_publish_time: float = 0.0

        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

        # Configure last will and testament
        self.client.will_set(
            topic=f"{EdgeConfig.MQTT_TOPIC_DETECTIONS}/status",
            payload=json.dumps({
                "intersection_id": EdgeConfig.INTERSECTION_ID,
                "status": "offline",
                "timestamp": time.time()
            }),
            qos=1,
            retain=True
        )

    def _on_connect(self, client, userdata, flags, rc) -> None:
        """Callback when connected to MQTT broker."""
        if rc == 0:
            self.is_connected = True
            logger.info(
                f"Connected to MQTT broker at "
                f"{EdgeConfig.MQTT_BROKER_HOST}:{EdgeConfig.MQTT_BROKER_PORT}"
            )
            # Publish online status
            client.publish(
                topic=f"{EdgeConfig.MQTT_TOPIC_DETECTIONS}/status",
                payload=json.dumps({
                    "intersection_id": EdgeConfig.INTERSECTION_ID,
                    "status": "online",
                    "timestamp": time.time()
                }),
                qos=1,
                retain=True
            )
        else:
            self.is_connected = False
            error_messages = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            logger.error(
                f"MQTT connection failed: {error_messages.get(rc, f'Unknown error ({rc})')}"
            )

    def _on_disconnect(self, client, userdata, rc) -> None:
        """Callback when disconnected from MQTT broker."""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection (rc={rc}). Will auto-reconnect.")
        else:
            logger.info("Disconnected from MQTT broker.")

    def _on_publish(self, client, userdata, mid) -> None:
        """Callback when a message is published."""
        self.messages_sent += 1

    def connect(self) -> bool:
        """
        Connect to the MQTT broker.

        Returns:
            True if connection initiated successfully.
        """
        try:
            logger.info(
                f"Connecting to MQTT broker: "
                f"{EdgeConfig.MQTT_BROKER_HOST}:{EdgeConfig.MQTT_BROKER_PORT}"
            )
            self.client.connect(
                host=EdgeConfig.MQTT_BROKER_HOST,
                port=EdgeConfig.MQTT_BROKER_PORT,
                keepalive=60
            )
            self.client.loop_start()

            # Wait for connection to establish
            timeout = 10
            start = time.time()
            while not self.is_connected and (time.time() - start) < timeout:
                time.sleep(0.1)

            return self.is_connected

        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            return False

    def publish_detection(self, detection_data: dict) -> bool:
        """
        Publish a detection result to the MQTT topic.

        Args:
            detection_data: Serialized detection result dictionary.

        Returns:
            True if message was published successfully.
        """
        if not self.is_connected:
            logger.warning("Not connected to MQTT broker. Skipping publish.")
            return False

        try:
            topic = (
                f"{EdgeConfig.MQTT_TOPIC_DETECTIONS}"
                f"/{detection_data.get('intersection_id', 'unknown')}"
            )
            payload = json.dumps(detection_data)

            result = self.client.publish(
                topic=topic,
                payload=payload,
                qos=1
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.last_publish_time = time.time()
                logger.debug(
                    f"Published detection to {topic} "
                    f"({len(payload)} bytes, "
                    f"{detection_data.get('total_vehicles', 0)} vehicles)"
                )
                return True
            else:
                logger.error(f"MQTT publish failed with rc={result.rc}")
                return False

        except Exception as e:
            logger.error(f"Error publishing detection: {e}")
            return False

    def disconnect(self) -> None:
        """Gracefully disconnect from the MQTT broker."""
        # Publish offline status before disconnecting
        if self.is_connected:
            self.client.publish(
                topic=f"{EdgeConfig.MQTT_TOPIC_DETECTIONS}/status",
                payload=json.dumps({
                    "intersection_id": EdgeConfig.INTERSECTION_ID,
                    "status": "offline",
                    "timestamp": time.time()
                }),
                qos=1,
                retain=True
            )
        self.client.loop_stop()
        self.client.disconnect()
        logger.info(f"MQTT disconnected. Total messages sent: {self.messages_sent}")

    @property
    def stats(self) -> dict:
        """Return publisher statistics."""
        return {
            "broker": f"{EdgeConfig.MQTT_BROKER_HOST}:{EdgeConfig.MQTT_BROKER_PORT}",
            "is_connected": self.is_connected,
            "messages_sent": self.messages_sent,
            "last_publish_time": self.last_publish_time
        }
