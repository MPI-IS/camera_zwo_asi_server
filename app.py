import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, send_from_directory, render_template_string

from capture import CameraConfig, CameraType, ImageConfig
from routes.camera_routes import camera_bp
from routes.images_routes import images_bp


_MEDIA_FOLDER: str = "/tmp/camera_zwo_asi_server"


def _get_default_config() -> CameraConfig:
    camera_type_ = str(os.getenv("CAMERA", "dummy"))
    has_focus = os.getenv("HAS_FOCUS", "FALSE").upper() == "TRUE"
    has_aperture = os.getenv("HAS_APERTURE", "FALSE").upper() == "TRUE"
    exposure = int(os.getenv("DEFAULT_EXPOSURE", 0))
    gain = int(os.getenv("DEFAULT_GAIN", 0))
    focus = int(os.getenv("DEFAULT_FOCUS", 400)) if has_focus else None
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
    folder = os.getenv("IMG_FOLDER", _MEDIA_FOLDER)
    Path(folder).mkdir(exist_ok=True)
    tw = int(os.getenv("THUMBNAIL_WIDTH", 200))
    th = int(os.getenv("THUMBNAIL_HEIGHT", 200))
    return ImageConfig(img_folder=folder, thumbnail=(tw, th))


def create_app() -> Flask:
    path_to_env_file = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path=path_to_env_file, override=True)
    app = Flask(__name__)
    app.config["default_camera_config"] = _get_default_config()
    print(app.config["default_camera_config"])
    app.config["image_config"] = _get_image_config()
    app.register_blueprint(images_bp)
    app.register_blueprint(camera_bp)

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Flask application starting up.")

    return app


app = create_app()

if __name__ == "__main__":
    debug = os.getenv("DEBUG", "TRUE").upper() == "TRUE"
    app.run(debug=debug)
