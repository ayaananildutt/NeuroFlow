"""
Server Configuration
Loads environment variables for database, MQTT, API, and signal timing settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class ServerConfig:
    """Configuration for the Traffic Controller Server."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://neuroflow_admin:changeme@localhost:5432/neuroflow"
    )
    DATABASE_URL_SYNC: str = os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql://neuroflow_admin:changeme@localhost:5432/neuroflow"
    )

    # MQTT Settings
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_TOPIC_DETECTIONS: str = os.getenv("MQTT_TOPIC_DETECTIONS", "neuroflow/detections")
    MQTT_TOPIC_COMMANDS: str = os.getenv("MQTT_TOPIC_COMMANDS", "neuroflow/commands")
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID_SERVER", "traffic-server")

    # API Server
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # Signal Timing Parameters
    MIN_GREEN_DURATION_SEC: int = int(os.getenv("MIN_GREEN_DURATION_SEC", "15"))
    MAX_GREEN_DURATION_SEC: int = int(os.getenv("MAX_GREEN_DURATION_SEC", "90"))
    DEFAULT_GREEN_DURATION_SEC: int = int(os.getenv("DEFAULT_GREEN_DURATION_SEC", "30"))
    YELLOW_DURATION_SEC: int = int(os.getenv("YELLOW_DURATION_SEC", "5"))
    DENSITY_SCALING_FACTOR: float = float(os.getenv("DENSITY_SCALING_FACTOR", "2.5"))

    # CORS
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8080"
    ).split(",")
