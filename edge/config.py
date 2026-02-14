"""
Edge Gateway Configuration
Loads environment variables for camera, MQTT, and YOLOv8 settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class EdgeConfig:
    """Configuration for the Edge Gateway service."""

    # MQTT Settings
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_TOPIC_DETECTIONS: str = os.getenv("MQTT_TOPIC_DETECTIONS", "neuroflow/detections")
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID_EDGE", "edge-gateway-01")

    # Camera Settings
    CAMERA_SOURCE: str = os.getenv("CAMERA_SOURCE", "0")
    CAMERA_FRAME_WIDTH: int = int(os.getenv("CAMERA_FRAME_WIDTH", "1280"))
    CAMERA_FRAME_HEIGHT: int = int(os.getenv("CAMERA_FRAME_HEIGHT", "720"))
    CAMERA_FPS: int = int(os.getenv("CAMERA_FPS", "30"))
    CAMERA_RECONNECT_DELAY_SEC: int = int(os.getenv("CAMERA_RECONNECT_DELAY_SEC", "5"))
    CAMERA_MAX_RETRIES: int = int(os.getenv("CAMERA_MAX_RETRIES", "10"))

    # YOLOv8 Settings
    YOLO_MODEL_PATH: str = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
    YOLO_CONFIDENCE_THRESHOLD: float = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.5"))
    YOLO_IOU_THRESHOLD: float = float(os.getenv("YOLO_IOU_THRESHOLD", "0.45"))
    YOLO_IMG_SIZE: int = int(os.getenv("YOLO_IMG_SIZE", "640"))

    # Detection Settings
    DETECTION_INTERVAL_MS: int = int(os.getenv("DETECTION_INTERVAL_MS", "500"))
    INTERSECTION_ID: str = os.getenv("INTERSECTION_ID", "INT-001")

    # Vehicle class IDs in COCO dataset
    VEHICLE_CLASS_IDS: list = [2, 3, 5, 7]  # car, motorcycle, bus, truck
    VEHICLE_CLASS_NAMES: dict = {
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck"
    }

    @classmethod
    def camera_source_parsed(cls) -> int | str:
        """Return camera source as int (webcam index) or str (RTSP URL)."""
        try:
            return int(cls.CAMERA_SOURCE)
        except ValueError:
            return cls.CAMERA_SOURCE

    @classmethod
    def log_config(cls) -> None:
        """Print current configuration to stdout."""
        print("=" * 50)
        print("  NeuroFlow Edge Gateway — Configuration")
        print("=" * 50)
        print(f"  Intersection ID   : {cls.INTERSECTION_ID}")
        print(f"  Camera Source      : {cls.CAMERA_SOURCE}")
        print(f"  YOLO Model         : {cls.YOLO_MODEL_PATH}")
        print(f"  Confidence         : {cls.YOLO_CONFIDENCE_THRESHOLD}")
        print(f"  MQTT Broker        : {cls.MQTT_BROKER_HOST}:{cls.MQTT_BROKER_PORT}")
        print(f"  Detection Interval : {cls.DETECTION_INTERVAL_MS}ms")
        print("=" * 50)
