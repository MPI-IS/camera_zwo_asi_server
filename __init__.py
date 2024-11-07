from flask import Flask
import os


def create_app():
    app = Flask(__name__)
    temp_dir = "/tmp/camera_captures"
    os.makedirs(temp_dir, exist_ok=True)

    with app.app_context():
        from . import app as main_app

        app.register_blueprint(main_app.bp)

    return app
