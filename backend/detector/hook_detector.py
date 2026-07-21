from ultralytics import YOLO


class HookLoadDetector:

    def __init__(self):
        self.model = YOLO("models/hook_load.pt")

    def detect(self, frame):

        results = self.model.predict(
            frame,
            conf=0.25,
            verbose=False
        )

        return results[0]