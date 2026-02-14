"""
YOLOv8 Vehicle Detector
Runs inference on video frames to detect and count vehicles by class.
"""

import time
import logging
from dataclasses import dataclass, field
from ultralytics import YOLO
import numpy as np
from config import EdgeConfig

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Structured result from a single frame detection."""

    timestamp: float
    intersection_id: str
    total_vehicles: int
    vehicle_counts: dict = field(default_factory=dict)
    detections: list = field(default_factory=list)
    inference_time_ms: float = 0.0
    frame_number: int = 0

    def to_dict(self) -> dict:
        """Serialize to dictionary for MQTT transmission."""
        return {
            "timestamp": self.timestamp,
            "intersection_id": self.intersection_id,
            "total_vehicles": self.total_vehicles,
            "vehicle_counts": self.vehicle_counts,
            "detections": self.detections,
            "inference_time_ms": round(self.inference_time_ms, 2),
            "frame_number": self.frame_number
        }


class VehicleDetector:
    """
    YOLOv8-based vehicle detection pipeline.

    Loads a YOLOv8 model, runs inference on frames, and filters
    results to only include vehicle classes (car, motorcycle, bus, truck).
    """

    def __init__(self):
        self.model: YOLO | None = None
        self.is_loaded: bool = False
        self.total_inferences: int = 0
        self.avg_inference_ms: float = 0.0

    def load_model(self) -> bool:
        """
        Load the YOLOv8 model from disk.

        Returns:
            True if model loaded successfully, False otherwise.
        """
        try:
            logger.info(f"Loading YOLOv8 model: {EdgeConfig.YOLO_MODEL_PATH}")
            self.model = YOLO(EdgeConfig.YOLO_MODEL_PATH)

            # Warm up the model with a dummy inference
            dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model.predict(
                dummy_frame,
                conf=EdgeConfig.YOLO_CONFIDENCE_THRESHOLD,
                verbose=False
            )

            self.is_loaded = True
            logger.info("YOLOv8 model loaded and warmed up successfully.")
            return True

        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            self.is_loaded = False
            return False

    def detect(self, frame: np.ndarray, frame_number: int = 0) -> DetectionResult:
        """
        Run vehicle detection on a single frame.

        Args:
            frame: BGR image as numpy array.
            frame_number: Sequential frame counter.

        Returns:
            DetectionResult with all detected vehicles.
        """
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        start_time = time.perf_counter()

        results = self.model.predict(
            frame,
            conf=EdgeConfig.YOLO_CONFIDENCE_THRESHOLD,
            iou=EdgeConfig.YOLO_IOU_THRESHOLD,
            imgsz=EdgeConfig.YOLO_IMG_SIZE,
            classes=EdgeConfig.VEHICLE_CLASS_IDS,
            verbose=False
        )

        inference_time_ms = (time.perf_counter() - start_time) * 1000

        # Parse detections
        vehicle_counts = {name: 0 for name in EdgeConfig.VEHICLE_CLASS_NAMES.values()}
        detections = []

        if results and len(results) > 0:
            boxes = results[0].boxes

            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    class_name = EdgeConfig.VEHICLE_CLASS_NAMES.get(class_id, "unknown")
                    vehicle_counts[class_name] = vehicle_counts.get(class_name, 0) + 1

                    detections.append({
                        "class": class_name,
                        "class_id": class_id,
                        "confidence": round(confidence, 3),
                        "bbox": {
                            "x1": round(x1, 1),
                            "y1": round(y1, 1),
                            "x2": round(x2, 1),
                            "y2": round(y2, 1)
                        }
                    })

        total_vehicles = sum(vehicle_counts.values())

        # Update running average
        self.total_inferences += 1
        self.avg_inference_ms = (
            (self.avg_inference_ms * (self.total_inferences - 1) + inference_time_ms)
            / self.total_inferences
        )

        return DetectionResult(
            timestamp=time.time(),
            intersection_id=EdgeConfig.INTERSECTION_ID,
            total_vehicles=total_vehicles,
            vehicle_counts=vehicle_counts,
            detections=detections,
            inference_time_ms=inference_time_ms,
            frame_number=frame_number
        )

    @property
    def stats(self) -> dict:
        """Return detector statistics."""
        return {
            "model_path": EdgeConfig.YOLO_MODEL_PATH,
            "is_loaded": self.is_loaded,
            "total_inferences": self.total_inferences,
            "avg_inference_ms": round(self.avg_inference_ms, 2)
        }
