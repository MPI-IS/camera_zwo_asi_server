import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from queue import Queue
from threading import Thread
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

from capture import FocusAdapter, ImageInfo, ImageMeta, create_image

camera_bp = Blueprint("camera", __name__)

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
        if focus_step <= 0:
            focus_values = [focus_min]
        else:
            focus_values = [
                focus_min + i * focus_step
                for i in range((focus_max - focus_min) // focus_step + 1)
            ]

    camera_config = current_app.config["default_camera_config"]
    image_config = current_app.config["image_config"]

    # Create a queue for notifications
    image_creation_queue = Queue()

    focus_meta = {}

    ts = datetime.now()
    for focus in focus_values:
        timestamp = ts.strftime("%Y%m%d_%H%M%S")
        ts = ts + timedelta(seconds=1)
        filename_base = f"{timestamp}"
        meta_filepath = Path(image_config.img_folder) / f"meta_{filename_base}.toml"
        image_meta = ImageMeta(
            focus=focus,
            aperture=aperture,
            gain=gain,
            exposure=exposure,
            waiting=True,
            error=None,
            filename_base=str(filename_base),
            selfpath=str(meta_filepath),
        )
        image_meta.serialize_to_toml(meta_filepath)
        focus_meta[focus] = image_meta

    # Define a function to run in a thread
    def background_task():
        for focus, image_meta in focus_meta.items():
            camera_config.focus = focus
            camera_config.exposure = exposure
            camera_config.gain = gain
            camera_config.aperture = aperture

            try:
                create_image(
                    camera_config, image_config, image_meta, queue=image_creation_queue
                )
                logger.info(
                    f"Image captured successfully with focus: {focus}, exposure: {exposure}, gain: {gain}, aperture: {aperture}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to capture image with focus: {focus}, exposure: {exposure}, gain: {gain}, aperture: {aperture}. Error: {e}"
                )

    # Start the background task
    thread = Thread(target=background_task)
    thread.start()

    # Return immediately
    thumbnails = get_thumbnails()
    return jsonify({"images_info": [thumbnail.to_dict() for thumbnail in thumbnails]})


@camera_bp.route("/media/<filename>")
def serve_media(filename):
    image_config = current_app.config["image_config"]
    return send_from_directory(image_config.img_folder, filename)


@camera_bp.route("/adapter/init", methods=["POST"])
def init_adapter():
    try:
        FocusAdapter.init()
        return jsonify({"message": "Adapter initialized successfully"}), 200
    except NameError:
        error = f"adapter not supported"
        logger.error(error)
        return jsonify({"message": error}), 500
    except Exception as e:
        error = f"Failed to initialize adapter ({str(type(e))}): {e}"
        logger.error(error)
        return jsonify({"message": error}), 500


@camera_bp.route("/adapter/close", methods=["POST"])
def close_adapter():
    try:
        FocusAdapter.close()
        return jsonify({"message": "Adapter closed successfully"}), 200
    except NameError:
        error = f"adapter not supported"
        logger.error(error)
        return jsonify({"message": error}), 500
    except Exception as e:
        error = f"Failed to close adapter ({str(type(e))}): {e}"
        logger.error(error)
        return jsonify({"message": error}), 500
