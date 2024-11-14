import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from queue import Queue
from threading import Lock, Thread
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
    waiting: bool
    error: Optional[str]
    selfpath: str
    filename_base: str

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
            "waiting": self.waiting,
            "error": self.error,
            "selfpath": self.selfpath,
            "filename_base": self.filename_base,
        }


@dataclass
class ImageInfo:
    image: Optional[str]
    thumbnail: Optional[str]
    meta: ImageMeta
    timestamp: datetime

    @classmethod
    def from_folder(
        cls, folder_path: Path, max_images: Optional[int] = 10
    ) -> List["ImageInfo"]:
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

        # If max_images is specified and there are more than max_images, delete the older images
        if max_images is not None and len(image_infos) > max_images:
            cls.cleanup(folder_path, image_infos, max_images)

        return image_infos[:max_images]

    @staticmethod
    def cleanup(
        folder_path: Path, image_infos: List["ImageInfo"], max_images: int
    ) -> None:
        for image_info in image_infos[max_images:]:
            if image_info.image:
                image_file_path = folder_path / image_info.image
                if image_file_path.exists():
                    image_file_path.unlink()
            if image_info.thumbnail:
                thumbnail_file_path = folder_path / image_info.thumbnail
                if thumbnail_file_path.exists():
                    thumbnail_file_path.unlink()
            toml_file_path = (
                folder_path
                / f"meta_{image_info.timestamp.strftime('%Y%m%d_%H%M%S')}.toml"
            )
            if toml_file_path.exists():
                toml_file_path.unlink()

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
        time.sleep(1.0)


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
    logger.info(
        f"starting zwo-asi camera capture (exposure: {camera_config.exposure*1e-6:.2f} seconds)"
    )
    img = camera.capture().get_image()
    time.sleep(1.0)
    return img


_capture_lock = Lock()


def create_image(
    camera_config: CameraConfig,
    image_config: ImageConfig,
    image_meta: ImageMeta,
    queue: Optional[Queue] = None,
) -> None:

    global _capture_lock

    with _capture_lock:
        try:
            image_array: np.ndarray
            if camera_config.camera_type == CameraType.dummy:
                image_array = _dummy_capture()
            elif camera_config.camera_type == CameraType.zwo_asi:
                image_array = _zwo_asi_capture(camera_config)
            else:
                image_array = _webcam_capture()
        except Exception as e:
            image_meta.waiting = False
            image_meta.error = str(e)
            image_meta.serialize_to_toml(Path(image_meta.selfpath))
            return

    try:
        image = Image.fromarray(image_array)
        image.save(
            Path(image_config.img_folder) / f"{image_meta.filename_base}.jpeg",
            format="JPEG",
        )
        thumbnail = image.copy()  # type: ignore
        thumbnail.thumbnail(image_config.thumbnail)
        thumbnail.save(
            Path(image_config.img_folder)
            / f"thumbnail_{image_meta.filename_base}.jpeg",
            format="JPEG",
        )
    except Exception as e:
        image_meta.waiting = False
        image_meta.error = str(e)
        image_meta.serialize_to_toml(Path(image_meta.selfpath))
        return

    image_meta.waiting = False
    image_meta.serialize_to_toml(Path(image_meta.selfpath))

    # Notify the queue when an image is created
    if queue is not None:
        queue.put("Image created")
