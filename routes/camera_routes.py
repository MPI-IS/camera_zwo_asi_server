import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List

import toml
from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    send_from_directory,
)

from capture import ImageInfo, create_image

camera_bp = Blueprint("camera", __name__)

# Get the logger configured in app.py
logger = logging.getLogger(__name__)


def get_thumbnails() -> List[ImageInfo]:
    """Helper function to retrieve the list of thumbnails sorted by timestamp."""
    image_config = current_app.config["image_config"]
    thumbnails: List[ImageInfo] = ImageInfo.from_folder(Path(image_config.img_folder))
    logger.info(f"retrieved {len(thumbnails)} images")
    return thumbnails


@camera_bp.route("/", methods=["GET"])
def index():
    thumbnails = get_thumbnails()
    return render_template("index.html", images_info=thumbnails)


@camera_bp.route("/images", methods=["GET"])
def get_images():
    thumbnails = get_thumbnails()
    return jsonify({"images_info": [thumbnail.to_dict() for thumbnail in thumbnails]})


@camera_bp.route("/capture", methods=["POST"])
def capture():
    exposure = request.form.get("exposure", type=int)
    gain = request.form.get("gain", type=int)
    focus_min = request.form.get("focus_min", type=int)
    focus_max = request.form.get("focus_max", type=int)
    focus_step = request.form.get("focus_step", type=int)
    aperture = request.form.get("aperture", type=int)

    if focus_max is None or focus_step is None:
        focus_values = [focus_min]
    else:
        focus_values = np.arange(focus_min, focus_max + focus_step, focus_step)

    camera_config = current_app.config["default_camera_config"]
    image_config = current_app.config["image_config"]

    for focus in focus_values:
        camera_config.focus = focus
        camera_config.exposure = exposure
        camera_config.gain = gain
        camera_config.aperture = aperture

        try:
            create_image(camera_config, image_config)
            logger.info(
                f"Image captured successfully with focus: {focus}, exposure: {exposure}, gain: {gain}, aperture: {aperture}"
            )
        except Exception as e:
            logger.error(
                f"Failed to capture image with focus: {focus}, exposure: {exposure}, gain: {gain}, aperture: {aperture}. Error: {e}"
            )

    return jsonify({"images_info": get_thumbnails()})


@camera_bp.route("/media/<filename>")
def serve_media(filename):
    image_config = current_app.config["image_config"]
    return send_from_directory(image_config.img_folder, filename)
