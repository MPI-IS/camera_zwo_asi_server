from flask import Flask
from routes.camera_routes import camera_bp
from camera_selector import CameraType, CameraConfig
from dotenv import load_dotenv
import os

def _get_default_config()->CameraConfig:
    load_dotenv()
    camera_type_str = os.getenv('CAMERA', 'dummy')
    has_focus = os.getenv('HAS_FOCUS', 'FALSE').upper() == 'TRUE'
    has_aperture = os.getenv('HAS_APERTURE', 'FALSE').upper() == 'TRUE'
    exposure = int(os.getenv('DEFAULT_EXPOSURE', 0))
    gain = int(os.getenv('DEFAULT_GAIN', 0))
    focus = int(os.getenv('DEFAULT_FOCUS', 0)) if has_focus else None
    aperture = int(os.getenv('DEFAULT_APERTURE', 0)) if has_aperture else None

    camera_type = CameraType[camera_type_str]

    return CameraConfig(
        camera_type=camera_type,
        exposure=exposure,
        gain=gain,
        focus=focus,
        aperture=aperture
    )

def create_app():
    app = Flask(__name__)
    app.config["default_camera_config"] = _get_default_config()
    app.register_blueprint(camera_bp)
    return app

app = create_app()

if __name__ == "__main__":
    load_dotenv()
    debug = os.getenv('DEBUG', 'TRUE').upper() == 'TRUE'
    app.run(debug=debug)
