import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

import camera_zwo_asi as zwo
import cv2
import nightskycam_focus as nf
import numpy as np
import toml
from PIL import Image

# Get the logger configured in app.py
logger = logging.getLogger(__name__)


@dataclass
class ImageMeta:
    focus: Optional[int]
    aperture: Optional[int]
    exposure: int
    gain: int
    error: Optional[str]

    def serialize_to_toml(self, file_path: Path) -> None:
        data = {k: v for k, v in self.__dict__.items() if v is not None}
        with file_path.open("w") as f:
            toml.dump(data, f)

    @classmethod
    def from_toml(cls, file_path: Path) -> "ImageMeta":
        with file_path.open("r") as f:
            data = toml.load(f)
        for opt_attr in ("focus", "aperture", "error"):
            if opt_attr not in data:
                data[opt_attr] = None
        return cls(**data)

    def to_dict(self) -> dict:
        return {
            "focus": self.focus,
            "aperture": self.aperture,
            "exposure": self.exposure,
            "gain": self.gain,
            "error": self.error,
        }


@dataclass
class ImageInfo:
    image: Optional[str]
    thumbnail: Optional[str]
    meta: ImageMeta
    timestamp: datetime

    @classmethod
    def from_folder(cls, folder_path: Path) -> List["ImageInfo"]:
        image_infos = []

        for toml_file in folder_path.glob("meta_*.toml"):
            timestamp_str = toml_file.stem.replace("meta_", "")
            image_file = str(folder_path / f"{timestamp_str}.jpeg")
            thumbnail_file = str(folder_path / f"thumbnail_{timestamp_str}.jpeg")

            meta = ImageMeta.from_toml(toml_file)
            image_info = cls(
                image=Path(image_file).name if Path(image_file).exists() else None,
                thumbnail=(
                    Path(thumbnail_file).name if Path(thumbnail_file).exists() else None
                ),
                meta=meta,
                timestamp=datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S"),
            )
            image_infos.append(image_info)

        # Sort image_infos by timestamp
        image_infos.sort(key=lambda x: x.timestamp, reverse=True)

        return image_infos

    def to_dict(self) -> dict:
        return {
            "image": self.image,
            "thumbnail": self.thumbnail,
            "meta": self.meta.to_dict(),
            "timestamp": self.timestamp.isoformat(),
        }


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


def create_image(
    camera_config: CameraConfig,
    image_config: ImageConfig,
    now: Optional[datetime] = None,
) -> None:

    image_meta = ImageMeta(
        focus=camera_config.focus,
        aperture=camera_config.aperture,
        gain=camera_config.gain,
        exposure=camera_config.exposure,
        error=None,
    )
    if now is None:
        now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename_base = f"{timestamp}"
    meta_filepath = Path(image_config.img_folder) / f"meta_{filename_base}.toml"

    try:
        image_array: np.ndarray
        if camera_config.camera_type == CameraType.dummy:
            image_array = _dummy_capture()
        # if camera_config.camera_type == Camera2Type.webcam:
        else:
            image_array = _webcam_capture()
    except Exception as e:
        image_meta.error = str(e)
        image_meta.serialize_to_toml(meta_filepath)
        return

    try:
        image = Image.fromarray(image_array)
        image.save(
            Path(image_config.img_folder) / f"{filename_base}.jpeg", format="JPEG"
        )
        thumbnail = image.copy()  # type: ignore
        thumbnail.thumbnail(image_config.thumbnail)
        thumbnail.save(
            Path(image_config.img_folder) / f"thumbnail_{filename_base}.jpeg",
            format="JPEG",
        )
    except Exception as e:
        image_meta.error = str(e)
        image_meta.serialize_to_toml(meta_filepath)
        return

    image_meta.serialize_to_toml(meta_filepath)
