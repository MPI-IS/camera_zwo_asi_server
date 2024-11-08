import numpy as np
import logging

class DummyCamera:
    @staticmethod
    def configure(exposure, gain, focus, aperture):
        logging.info(f"Configuring dummy camera with exposure={exposure}, gain={gain}, focus={focus}, aperture={aperture}")

    @staticmethod
    def capture():
        logging.info("Capturing image with dummy camera...")
        return np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
