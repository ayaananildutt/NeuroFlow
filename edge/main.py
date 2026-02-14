"""
NeuroFlow Edge Gateway — Main Entry Point
Orchestrates the camera → YOLOv8 detector → MQTT publisher pipeline.
"""

import sys
import time
import signal
import logging
from config import EdgeConfig
from camera_feed import CameraFeed
from detector import VehicleDetector
from mqtt_publisher import MQTTPublisher

# ──────────────────────────────────────────
# Logging Configuration
# ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("neuroflow.edge")


class EdgeGateway:
    """
    Main edge gateway pipeline.

    Captures video frames, runs YOLOv8 vehicle detection, and publishes
    results to the MQTT broker at a configurable interval.
    """

    def __init__(self):
        self.camera = CameraFeed()
        self.detector = VehicleDetector()
        self.publisher = MQTTPublisher()
        self.running: bool = False
        self.total_detections: int = 0

    def start(self) -> None:
        """Initialize all components and start the detection pipeline."""
        EdgeConfig.log_config()

        # Load YOLOv8 model
        logger.info("Initializing YOLOv8 vehicle detector...")
        if not self.detector.load_model():
            logger.critical("Failed to load YOLOv8 model. Exiting.")
            sys.exit(1)

        # Connect to camera
        logger.info("Connecting to camera feed...")
        if not self.camera.connect():
            logger.critical("Failed to connect to camera. Exiting.")
            sys.exit(1)

        # Connect to MQTT broker
        logger.info("Connecting to MQTT broker...")
        if not self.publisher.connect():
            logger.critical("Failed to connect to MQTT broker. Exiting.")
            sys.exit(1)

        logger.info("All components initialized. Starting detection pipeline...")
        self.running = True
        self._run_pipeline()

    def _run_pipeline(self) -> None:
        """Main detection loop."""
        interval_sec = EdgeConfig.DETECTION_INTERVAL_MS / 1000.0

        while self.running:
            loop_start = time.perf_counter()

            try:
                # Capture frame
                frame = self.camera.read_frame()
                if frame is None:
                    logger.warning("No frame available. Retrying...")
                    time.sleep(1)
                    continue

                # Run detection
                result = self.detector.detect(
                    frame=frame,
                    frame_number=self.camera.frame_count
                )
                self.total_detections += 1

                # Publish to MQTT
                self.publisher.publish_detection(result.to_dict())

                # Log periodic summary
                if self.total_detections % 20 == 0:
                    self._log_summary(result)

                # Maintain target detection interval
                elapsed = time.perf_counter() - loop_start
                sleep_time = max(0, interval_sec - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received.")
                break
            except Exception as e:
                logger.error(f"Pipeline error: {e}", exc_info=True)
                time.sleep(1)

        self.stop()

    def _log_summary(self, result) -> None:
        """Log a periodic summary of detection statistics."""
        logger.info(
            f"[Summary] "
            f"Detections: {self.total_detections} | "
            f"Vehicles in frame: {result.total_vehicles} | "
            f"Counts: {result.vehicle_counts} | "
            f"Inference: {result.inference_time_ms:.1f}ms | "
            f"Avg: {self.detector.stats['avg_inference_ms']:.1f}ms | "
            f"MQTT sent: {self.publisher.stats['messages_sent']}"
        )

    def stop(self) -> None:
        """Gracefully shut down all components."""
        logger.info("Shutting down Edge Gateway...")
        self.running = False
        self.camera.release()
        self.publisher.disconnect()
        logger.info("Edge Gateway stopped. Goodbye!")

    def handle_signal(self, signum, frame) -> None:
        """Handle termination signals for graceful shutdown."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received signal {sig_name}. Initiating shutdown...")
        self.running = False


def main():
    """Entry point for the edge gateway service."""
    gateway = EdgeGateway()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, gateway.handle_signal)
    signal.signal(signal.SIGTERM, gateway.handle_signal)

    try:
        gateway.start()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        gateway.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
