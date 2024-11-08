import cv2
import logging

class Webcam:
    def __init__(self):
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            raise RuntimeError('Could not start camera.')

    def configure(self, exposure, gain, focus, aperture):
        logging.info(f"Configuring webcam with exposure={exposure}, gain={gain}, focus={focus}, aperture={aperture}")
        # Configuration for webcam can be added here if supported

    def capture(self):
        logging.info("Capturing image with webcam...")
        ret, frame = self.camera.read()
        if not ret:
            raise RuntimeError('Failed to capture image')
        return frame

    def release(self):
        self.camera.release()
