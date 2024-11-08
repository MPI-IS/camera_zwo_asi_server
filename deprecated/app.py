import os
import logging
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_from_directory
from PIL import Image
from camera import Camera

# Setup logging
logging.basicConfig(level=logging.INFO)

# Flask app setup
app = Flask(__name__)
temp_dir = "/tmp/camera_captures"
os.makedirs(temp_dir, exist_ok=True)


@app.route("/", methods=["GET"])
def index():
    # Load existing thumbnails
    thumbnails = []
    for filename in os.listdir(temp_dir):
        if filename.startswith("thumbnail_") and filename.endswith(".png"):
            focus = filename.split("_")[-1].replace(".png", "")
            thumbnails.append(
                {
                    "thumbnail_filename": filename,
                    "image_filename": filename.replace("thumbnail_", "image_"),
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


@app.route("/capture", methods=["POST"])
def capture():
    exposure = request.form.get("exposure", type=float)
    gain = request.form.get("gain", type=float)
    focus_min = request.form.get("focus_min", type=float)
    focus_max = request.form.get("focus_max", type=float)
    focus_step = request.form.get("focus_step", type=float)
    aperture = request.form.get("aperture", type=float)

    # Determine focus values
    if focus_max is None or focus_step is None:
        focus_values = [focus_min]
    else:
        focus_values = np.arange(focus_min, focus_max + focus_step, focus_step)

    images_info = []

    for focus in focus_values:
        Camera.configure(exposure, gain, focus, aperture)
        image_array = Camera.capture()
        image = Image.fromarray(image_array)

        # Generate unique file name based on current date and time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"image_{timestamp}_focus_{focus}.png"
        image_path = os.path.join(temp_dir, image_filename)
        image.save(image_path, format="PNG")
        logging.info(f"Image saved at {image_path}")

        # Save configuration
        config = {
            "exposure": exposure,
            "gain": gain,
            "focus": focus,
            "aperture": aperture,
        }

        # Create and save thumbnail
        thumbnail = image.copy()
        thumbnail.thumbnail((100, 100))
        thumbnail_filename = f"thumbnail_{timestamp}_focus_{focus}.png"
        thumbnail_path = os.path.join(temp_dir, thumbnail_filename)
        thumbnail.save(thumbnail_path, format="PNG")
        logging.info(f"Thumbnail saved at {thumbnail_path}")

        images_info.append(
            {
                "focus": focus,
                "thumbnail_filename": thumbnail_filename,
                "image_filename": image_filename,
                "config": config,
            }
        )

    return jsonify(images_info)


@app.route("/thumbnails/<filename>")
def serve_thumbnail(filename):
    return send_from_directory(temp_dir, filename)


@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(temp_dir, filename)


if __name__ == "__main__":
    app.run(debug=True)
