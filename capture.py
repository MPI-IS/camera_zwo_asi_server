from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple
import time
import camera_zwo_asi as zwo
import cv2
import nightskycam_focus as nf
import numpy as np
from PIL import Image


class FocusAdapter:
    initialized: bool = False

    @classmethod
    def init(cls) -> None:
        if not cls.initialized:
            nf.adapter.init_adapter()
            cls.initialized = True

    @classmethod
    def close(cls) -> None:
        if cls.initialized:
            nf.adapter.idle_adapter()

    @classmethod
    def focus(cls, focus: Optional[int]) -> None:
        if focus is not None:
            cls.init()
            nf.adapter.set_focus(focus)

    @classmethod
    def aperture(cls, aperture: Optional[int]) -> None:
        if aperture is not None:
            cls.init()
            nf.adapter.set_aperture(aperture)


class CameraType(Enum):
    dummy = 0
    webcam = 1
    zwo_asi = 2


@dataclass
class ImageConfig:
    img_folder: str
    thumbnail: Tuple[int, int]


@dataclass
class CameraConfig:
    camera_type: CameraType
    exposure: int
    gain: int
    focus: Optional[int] = None
    aperture: Optional[int] = None


@dataclass
class ImageInfo:
    filepath: Path
    thumbnail: Path
    camera_config: CameraConfig
    timestamp: str


@contextmanager
def webcam_camera():
    camera = cv2.VideoCapture(0)
    try:
        yield camera
    finally:
        camera.release()


def _dummy_capture() -> np.ndarray:
    time.sleep(1.5)
    return np.random.randint(0, 256, (960, 1280, 3), dtype=np.uint8)


def _webcam_capture() -> np.ndarray:
    with webcam_camera() as camera:
        if not camera.isOpened():
            raise RuntimeError("failed to connect to webcam")

        # Set the camera to maximum resolution
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)  # Set to maximum width
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  # Set to maximum height

        ret, frame = camera.read()
        if not ret:
            raise RuntimeError("Failed to capture image with the webcam")

        # Convert from BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    return frame


def _zwo_asi_capture(camera_config: CameraConfig) -> np.ndarray:
    camera = zwo.Camera(0)
    camera.set_control("Exposure", camera_config.exposure)
    camera.set_control("Gain", camera_config.gain)
    roi = camera.get_roi()
    roi.type = zwo.ImageType.rgb24
    camera.set_roi(roi)
    FocusAdapter.focus(camera_config.focus)
    FocusAdapter.aperture(camera_config.aperture)
    return camera.capture().get_image()


def create_thumbnail(
    image: Image, image_config: ImageConfig, filename: str  # type: ignore
) -> Path:
    thumbnail = image.copy()  # type: ignore
    thumbnail.thumbnail(image_config.thumbnail)
    thumbnail_filename = f"thumbnail_{filename}"
    thumbnail_path = Path(image_config.img_folder) / thumbnail_filename
    thumbnail.save(thumbnail_path, format="JPEG")
    return thumbnail_path


def create_image(
    camera_config: CameraConfig,
    image_config: ImageConfig,
    now: Optional[datetime] = None,
) -> ImageInfo:

    image_array: np.ndarray
    if camera_config.camera_type == CameraType.dummy:
        image_array = _dummy_capture()
    # if camera_config.camera_type == Camera2Type.webcam:
    else:
        image_array = _webcam_capture()

    if now is None:
        now = datetime.now()

    timestamp = now.strftime("%Y%m%d_%H%M%S")

    filename = f"{timestamp}.jpeg"
    filepath = Path(image_config.img_folder) / filename

    image = Image.fromarray(image_array)
    image.save(filepath, format="JPEG")

    thumbnail_path = create_thumbnail(image, image_config, filename)

    return ImageInfo(
        filepath=filepath,
        thumbnail=thumbnail_path,
        camera_config=camera_config,
        timestamp=timestamp,
    )
