"""
Camera Feed Module
Handles video stream capture from CCTV cameras or webcams with
automatic reconnection and frame buffering.
"""

import time
import logging
import cv2
import numpy as np
from config import EdgeConfig

logger = logging.getLogger(__name__)


class CameraFeed:
    """
    Manages a video capture stream from CCTV cameras (RTSP) or local webcams.

    Features:
        - Automatic reconnection on stream failure
        - Configurable resolution and FPS
        - Frame validation and preprocessing
    """

    def __init__(self):
        self.source = EdgeConfig.camera_source_parsed()
        self.cap: cv2.VideoCapture | None = None
        self.is_connected: bool = False
        self.frame_count: int = 0
        self.retry_count: int = 0

    def connect(self) -> bool:
        """
        Establish connection to the video source.

        Returns:
            True if connection was successful, False otherwise.
        """
        logger.info(f"Connecting to camera source: {self.source}")

        try:
            if isinstance(self.source, str) and self.source.startswith("rtsp"):
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
            else:
                self.cap = cv2.VideoCapture(self.source)

            if not self.cap.isOpened():
                logger.error("Failed to open video capture device.")
                self.is_connected = False
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, EdgeConfig.CAMERA_FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, EdgeConfig.CAMERA_FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, EdgeConfig.CAMERA_FPS)

            # Reduce buffer size to minimize latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            self.is_connected = True
            self.retry_count = 0
            logger.info("Camera connection established successfully.")

            actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            logger.info(f"Resolution: {actual_w}x{actual_h} @ {actual_fps}fps")

            return True

        except Exception as e:
            logger.error(f"Camera connection error: {e}")
            self.is_connected = False
            return False

    def read_frame(self) -> np.ndarray | None:
        """
        Read a single frame from the video stream.

        Returns:
            numpy array of the frame (BGR format) or None on failure.
        """
        if not self.is_connected or self.cap is None:
            if not self._reconnect():
                return None

        ret, frame = self.cap.read()

        if not ret or frame is None:
            logger.warning("Failed to read frame from camera.")
            self.is_connected = False
            return None

        self.frame_count += 1
        return frame

    def _reconnect(self) -> bool:
        """
        Attempt to reconnect to the camera with exponential backoff.

        Returns:
            True if reconnection succeeded, False if max retries exceeded.
        """
        if self.retry_count >= EdgeConfig.CAMERA_MAX_RETRIES:
            logger.error(
                f"Max reconnection attempts ({EdgeConfig.CAMERA_MAX_RETRIES}) exceeded."
            )
            return False

        self.retry_count += 1
        delay = min(
            EdgeConfig.CAMERA_RECONNECT_DELAY_SEC * (2 ** (self.retry_count - 1)),
            60  # Cap at 60 seconds
        )
        logger.info(
            f"Reconnection attempt {self.retry_count}/{EdgeConfig.CAMERA_MAX_RETRIES} "
            f"in {delay}s..."
        )
        time.sleep(delay)
        self.release()
        return self.connect()

    def release(self) -> None:
        """Release the video capture resource."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_connected = False
        logger.info("Camera resource released.")

    @property
    def stats(self) -> dict:
        """Return current camera statistics."""
        return {
            "source": str(self.source),
            "is_connected": self.is_connected,
            "frames_captured": self.frame_count,
            "retry_count": self.retry_count
        }
