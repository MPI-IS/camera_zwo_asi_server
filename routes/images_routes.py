from flask import Blueprint, send_from_directory, render_template_string
import logging
import os

_MEDIA_FOLDER = "/tmp/camera_zwo_asi_server"

images_bp = Blueprint('images_bp', __name__)

logger = logging.getLogger(__name__)

@images_bp.route("/explore")
def list_files():
    logger.info(f"listing files in {_MEDIA_FOLDER}")
    files = os.listdir(_MEDIA_FOLDER)
    logger.info(f"found {len(files)} files")
    html_template = """
    <!doctype html>
    <title>Media Files</title>
    <h1>Media Files</h1>
    <ul>
    {% for file in files %}
      <li><a href="{{ url_for('images_bp.download_file', filename=file) }}">{{ file }}</a></li>
    {% endfor %}
    </ul>
    """
    return render_template_string(html_template, files=files)

@images_bp.route("/explore/<filename>")
def download_file(filename):
    return send_from_directory(_MEDIA_FOLDER, filename, as_attachment=True)
