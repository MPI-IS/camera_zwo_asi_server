import numpy as np
import logging


class Camera:
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
