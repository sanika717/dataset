import os
from ultralytics import YOLO

class PPEDetector:

    def __init__(self):
        # Fall back to yolov8n.pt if models/ppe.pt is empty or missing
        model_path = "models/ppe.pt"
        if not os.path.exists(model_path) or os.path.getsize(model_path) == 0:
            model_path = "yolov8n.pt"
        self.model = YOLO(model_path)

    def detect(self, frame):

        results = self.model.predict(
            frame,
            conf=0.4,
            verbose=False
        )

        return results[0]