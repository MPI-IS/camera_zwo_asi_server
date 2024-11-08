import os
import logging
from dotenv import load_dotenv
from enumeration import Enum
from contextlib import contextmanager
from typing import Optional
import cv2
from dataclasses import dataclass

class CameraType(Enum):
    dummy = 0
    webcam = 1
    zwo_asi = 2

@dataclass
class CameraConfig:
    camera_type: CameraType
    exposure: int
    gain: int
    focus: Optional[int] = None
    aperture: Optional[int] = None

@contextmanager
def webcam_camera():
    camera = cv2.VideoCapture(0)
    try:
        yield camera
    finally:
        camera.release()
    
def dummy_capture()->np.ndarray:
    return np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

def _webcam_capture(camera_config: CameraConfig)->np.ndarray:
    with webcam_camera() as camera:
        if not camera.isOpened():
            raise RuntimeError(f"failed to connect to webcam")
        ret, frame = camera.read()
        if not ret:
            raise RuntimeError('Failed to capture image with the webcam')
    return frame

    
def capture(camera_config: CameraConfig)->np.ndarray:
    if camera_config.camera_type == CameraType.dummy:
        return _dummy_capture()
    if camera_config.camera_type == CameraType.webcam:
        return _webcam_capture()
    
    
