from pathlib import Path
from flask import Flask
from routes.camera_routes import camera_bp
from capture import CameraType, CameraConfig, ImageConfig
from dotenv import load_dotenv
import os


def _get_default_config() -> CameraConfig:
    load_dotenv()
    camera_type_ = str(os.getenv("CAMERA", "dummy"))
    has_focus = os.getenv("HAS_FOCUS", "FALSE").upper() == "TRUE"
    has_aperture = os.getenv("HAS_APERTURE", "FALSE").upper() == "TRUE"
    exposure = int(os.getenv("DEFAULT_EXPOSURE", 0))
    gain = int(os.getenv("DEFAULT_GAIN", 0))
    focus = int(os.getenv("DEFAULT_FOCUS", 0)) if has_focus else None
    aperture = int(os.getenv("DEFAULT_APERTURE", 0)) if has_aperture else None

    camera_type = CameraType[str(camera_type_)]

    return CameraConfig(
        camera_type=camera_type,
        exposure=exposure,
        gain=gain,
        focus=focus,
        aperture=aperture,
    )


def _get_image_config() -> ImageConfig:
    load_dotenv()
    folder = os.getenv("IMG_FOLDER", "/tmp/camera_zwo_asi_server")
    Path(folder).mkdir(exist_ok=True)
    tw = int(os.getenv("THUMBNAIL_WIDTH", 200))
    th = int(os.getenv("THUMBNAIL_HEIGHT", 200))
    return ImageConfig(img_folder=folder, thumbnail=(tw, th))


def create_app():
    app = Flask(__name__)
    app.config["default_camera_config"] = _get_default_config()
    app.config["image_config"] = _get_image_config()
    app.register_blueprint(camera_bp)
    return app


app = create_app()

if __name__ == "__main__":
    load_dotenv()
    debug = os.getenv("DEBUG", "TRUE").upper() == "TRUE"
    app.run(debug=debug)
