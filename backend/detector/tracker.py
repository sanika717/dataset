from collections import defaultdict, deque

from ultralytics import YOLO

from config import SWING_HISTORY_FRAMES


class HookTracker:
    """
    Wraps ultralytics built-in ByteTrack tracking and keeps a rolling
    position history per track ID, so danger_zone.py can estimate
    horizontal swing velocity without a physics simulation.
    """

    def __init__(self, model_path="models/hook_load.pt"):
        self.model = YOLO(model_path)
        # track_id -> deque of (frame_idx, cx, cy)
        self.history = defaultdict(lambda: deque(maxlen=SWING_HISTORY_FRAMES))
        self._frame_idx = 0

    def update(self, frame):
        """
        Run tracking on one frame, update position history, and return
        the raw ultralytics Results object (same shape as detect()).
        """
        results = self.model.track(
            frame,
            persist=True,
            tracker="models/bytetrack.yaml",
            conf=0.4,
            verbose=False
        )[0]

        self._frame_idx += 1

        if results.boxes is not None and results.boxes.id is not None:
            for box, track_id in zip(results.boxes.xyxy.tolist(), results.boxes.id.tolist()):
                x1, y1, x2, y2 = box
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                self.history[int(track_id)].append((self._frame_idx, cx, cy))

        return results

    def get_history(self, track_id):
        """Returns the rolling (frame_idx, cx, cy) history for one track ID."""
        return list(self.history.get(track_id, []))