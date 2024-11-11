import logging
import os
from datetime import datetime

import numpy as np
from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    render_template,
    request,
    send_from_directory,
)

from capture import create_image

camera_bp = Blueprint("camera", __name__)


@camera_bp.route("/", methods=["GET"])
def index():
    image_config = current_app.config["image_config"]
    thumbnails = []
    for filename in os.listdir(image_config.img_folder):
        if filename.startswith("thumbnail_") and filename.endswith(".jpeg"):
            focus = filename.split("_")[-1].replace(".jpeg", "")
            thumbnails.append(
                {
                    "thumbnail_filename": filename,
                    "image_filename": filename.replace("thumbnail_", ""),
                    "focus": focus,
                    "config": {
                        "exposure": "N/A",
                        "gain": "N/A",
                        "focus": focus,
                        "aperture": "N/A",
                    },
                }
            )
    return render_template("index.html", images_info=thumbnails)


@camera_bp.route("/capture", methods=["POST"])
def capture():
    exposure = request.form.get("exposure", type=float)
    gain = request.form.get("gain", type=float)
    focus_min = request.form.get("focus_min", type=float)
    focus_max = request.form.get("focus_max", type=float)
    focus_step = request.form.get("focus_step", type=float)
    aperture = request.form.get("aperture", type=float)

    if focus_max is None or focus_step is None:
        focus_values = [focus_min]
    else:
        focus_values = np.arange(focus_min, focus_max + focus_step, focus_step)

    images_info = []

    camera_config = current_app.config["default_camera_config"]
    image_config = current_app.config["image_config"]

    for focus in focus_values:
        camera_config.focus = focus
        camera_config.exposure = exposure
        camera_config.gain = gain
        camera_config.aperture = aperture

        try:
            image_info = create_image(camera_config, image_config)
            images_info.append(
                {
                    "focus": focus,
                    "thumbnail_filename": image_info.thumbnail.name,
                    "image_filename": image_info.filepath.name,
                    "config": {
                        "exposure": exposure,
                        "gain": gain,
                        "focus": focus,
                        "aperture": aperture,
                    },
                }
            )
            logging.info(f"Image and thumbnail saved for focus {focus}")
        except Exception as e:
            logging.error(f"Failed to capture image for focus {focus}: {e}")
            images_info.append(
                {
                    "focus": focus,
                    "thumbnail_filename": None,
                    "image_filename": None,
                    "config": {
                        "exposure": exposure,
                        "gain": gain,
                        "focus": focus,
                        "aperture": aperture,
                    },
                    "error": str(e),
                }
            )

    return jsonify(images_info)


@camera_bp.route("/media/<filename>")
def serve_media(filename):
    image_config = current_app.config["image_config"]
    return send_from_directory(image_config.img_folder, filename)
