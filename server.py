import numpy as np
from PIL import Image
import os
import logging
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_from_directory

# Setup logging
logging.basicConfig(level=logging.INFO)

# Mock camera module


class camera:
    @staticmethod
    def configure(exposure, gain, focus, aperture):
        # Mock configuration function
        logging.info(
            f"Configuring camera with exposure={exposure}, gain={gain}, focus={focus}, aperture={aperture}"
        )

    @staticmethod
    def capture():
        # Generate a random RGB image
        logging.info("Capturing image...")
        return np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)


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
        camera.configure(exposure, gain, focus, aperture)
        image_array = camera.capture()
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


# HTML template
index_html = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Camera Capture</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        form { margin-bottom: 20px; }
        label { display: inline-block; width: 100px; }
        input[type="number"] { width: 100px; }
        .thumbnail { display: inline-block; margin: 10px; text-align: center; position: relative; }
        .thumbnail img { border: 1px solid #ccc; cursor: pointer; }
        .config { font-size: 0.9em; color: #555; }
        .high-res {
            position: absolute;
            display: none;
            border: 2px solid #333;
            z-index: 10;
            width: 100px; /* Adjust as needed */
            height: 100px; /* Adjust as needed */
            overflow: hidden;
        }
        .high-res img {
            position: absolute;
        }
    </style>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script>
        $(document).ready(function() {
            $('form').on('submit', function(event) {
                event.preventDefault();
                $.ajax({
                    url: '/capture',
                    method: 'POST',
                    data: $(this).serialize(),
                    success: function(data) {
                        data.forEach(function(image) {
                            $('#thumbnails').append(
                                '<div class="thumbnail">' +
                                '<a href="/download/' + image.image_filename + '">' +
                                '<img src="/thumbnails/' + image.thumbnail_filename + '" alt="Thumbnail">' +
                                '</a>' +
                                '<div class="config">Exposure: ' + image.config.exposure + ', Gain: ' + image.config.gain + ', Focus: ' + image.config.focus + ', Aperture: ' + image.config.aperture + '</div>' +
                                '</div>'
                            );
                        });
                        addHoverEffect();
                    }
                });
            });

            function addHoverEffect() {
                $('.thumbnail img').hover(function(event) {
                    const thumbnail = $(this);
                    const highResImg = $('<div class="high-res"><img src="/images/' + thumbnail.parent().attr('href').split('/').pop() + '"></div>');
                    thumbnail.parent().append(highResImg);
                    highResImg.fadeIn();

                    thumbnail.on('mousemove', function(e) {
                        const offset = thumbnail.offset();
                        const x = e.pageX - offset.left;
                        const y = e.pageY - offset.top;
                        const img = highResImg.find('img');
                        const scale = img.width() / thumbnail.width();
                        img.css({
                            left: -x * scale + highResImg.width() / 2,
                            top: -y * scale + highResImg.height() / 2
                        });
                    });
                }, function() {
                    $(this).siblings('.high-res').remove();
                });
            }

            addHoverEffect();
        });
    </script>
</head>
<body>
    <h1>Camera Configuration</h1>
    <form method="post">
        <label for="exposure">Exposure:</label>
        <input type="number" name="exposure" step="0.1" required><br>
        <label for="gain">Gain:</label>
        <input type="number" name="gain" step="0.1" required><br>
        <label for="focus_min">Focus Min:</label>
        <input type="number" name="focus_min" step="0.1" required><br>
        <label for="focus_max">Focus Max (optional):</label>
        <input type="number" name="focus_max" step="0.1"><br>
        <label for="focus_step">Focus Step (optional):</label>
        <input type="number" name="focus_step" step="0.1"><br>
        <label for="aperture">Aperture:</label>
        <input type="number" name="aperture" step="0.1" required><br>
        <input type="submit" value="Capture">
    </form>
    <h2>Captured Images</h2>
    <div id="thumbnails">
        {% for image in images_info %}
            <div class="thumbnail">
                <a href="/download/{{ image.image_filename }}">
                    <img src="/thumbnails/{{ image.thumbnail_filename }}" alt="Thumbnail">
                </a>
                <div class="config">Exposure: {{ image.config.exposure }}, Gain: {{ image.config.gain }}, Focus: {{ image.config.focus }}, Aperture: {{ image.config.aperture }}</div>
            </div>
        {% endfor %}
    </div>
</body>
</html>
"""

# Save the HTML template to a file
template_dir = os.path.join(temp_dir, "templates")
os.makedirs(template_dir, exist_ok=True)
with open(os.path.join(template_dir, "index.html"), "w") as f:
    f.write(index_html)

app.template_folder = template_dir

if __name__ == "__main__":
    app.run(debug=True)
