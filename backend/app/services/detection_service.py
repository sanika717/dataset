"""
Wires the existing detection pipeline (detector/, geometry/, rules/,
reporting/) into the database. This is the piece that was an empty stub
in every prior phase — nothing previously took a detection and turned it
into an Incident row.

Two caveats, both inherent to what was actually uploaded rather than
something introduced here:

1. Model weights (models/ppe.pt, models/hook_load.pt) are NOT included
   in this project — only the code that loads them. PPEDetector falls
   back to yolov8n.pt (a generic COCO model) if models/ppe.pt is
   missing/empty, which will detect "person" but has no concept of
   hardhats/vests, so PPE violations won't actually fire until you drop
   your trained weights into backend/models/. HookLoadDetector has no
   such fallback — it will raise on startup if models/hook_load.pt isn't
   present.

2. PPE violation class names are a guess. There's no models/ppe.pt in
   this upload to inspect, so PPE_VIOLATION_LABELS below is a best-effort
   set of common label conventions — update it to match your model's
   actual `model.names` once you can inspect it (e.g. via
   `YOLO("models/ppe.pt").names`).
"""
import logging
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from detector.ppe_detector import PPEDetector
from detector.tracker import HookTracker
from reporting.incident import IncidentReporter
from rules.load_rules import check_fall_zone_violations
from app.utils.draw import draw_bbox

logger = logging.getLogger("sitesafe.detection")

# Update to match your trained ppe.pt model's actual class names.
PPE_VIOLATION_LABELS = {
    "no_hardhat",
    "no-hardhat",
    "no_helmet",
    "no-helmet",
    "no_vest",
    "no-vest",
    "no_safety_vest",
    "without_helmet",
    "without_vest",
}
SEVERITY_BY_TYPE = {
    "ppe_violation": "medium",
    "fall_zone_violation": "critical",
}


class DetectionService:
    """
    One instance per camera stream. Owns that camera's detector/tracker
    state (track history needs to persist across frames) and the shared
    IncidentReporter for screenshot/report file output.
    """

    def __init__(self, camera_id: int, output_dir: Optional[str] = None):
        self.camera_id = camera_id
        self._frame_idx = 0

        base_dir = Path(__file__).resolve().parents[2]  # backend/
        self.reporter = IncidentReporter(
            output_dir=output_dir or str(base_dir / "output")
        )

        try:
            self.ppe_detector = PPEDetector()
        except Exception:
            logger.exception(
                "Failed to load PPE model for camera %s — PPE detection disabled "
                "for this stream.",
                camera_id,
            )
            self.ppe_detector = None

        try:
            self.hook_tracker = HookTracker()
        except Exception:
            logger.exception(
                "Failed to load hook/load model for camera %s (is "
                "models/hook_load.pt present?) — fall-zone detection "
                "disabled for this stream.",
                camera_id,
            )
            self.hook_tracker = None

    def process_frame(self, frame: np.ndarray) -> dict:
        """
        Runs one frame through whichever detectors loaded successfully,
        draws boxes onto a copy of the frame, and returns everything the
        websocket layer + incident-creation step need.

        Returns:
            {
                "annotated_frame": np.ndarray,
                "detections": [ { label, severity, box (normalized xywh) } ],
                "ppe_violations": [ ... raw boxes, for incident creation ... ],
                "fall_zone_violations": [ ... from rules.load_rules ... ],
            }
        """
        self._frame_idx += 1
        h, w = frame.shape[:2]
        annotated = frame.copy()

        detections_for_client = []
        ppe_violations = []
        worker_bboxes = []
        hook_bbox = load_bbox = None
        track_history = []

        # --- PPE + person detection ---------------------------------
        if self.ppe_detector is not None:
            try:
                results = self.ppe_detector.detect(frame)
                names = results.names or {}
                if results.boxes is not None:
                    for box, cls_id, conf in zip(
                        results.boxes.xyxy.tolist(),
                        results.boxes.cls.tolist(),
                        results.boxes.conf.tolist(),
                    ):
                        label = names.get(int(cls_id), str(int(cls_id)))
                        x1, y1, x2, y2 = box

                        if label == "person":
                            worker_bboxes.append((x1, y1, x2, y2))
                            color = (80, 200, 120)
                        elif label.lower() in PPE_VIOLATION_LABELS:
                            ppe_violations.append(
                                {"label": label, "box": (x1, y1, x2, y2), "confidence": conf}
                            )
                            color = (0, 0, 255)
                        else:
                            color = (255, 180, 0)

                        draw_bbox(annotated, (x1, y1, x2, y2), label=label, color=color)
                        detections_for_client.append(
                            {
                                "label": label,
                                "severity": "medium" if label.lower() in PPE_VIOLATION_LABELS else None,
                                "box": [x1 / w, y1 / h, (x2 - x1) / w, (y2 - y1) / h],
                            }
                        )
            except Exception:
                logger.exception("PPE detection failed on camera %s", self.camera_id)

        # --- Hook/load detection + tracking --------------------------
        if self.hook_tracker is not None:
            try:
                results = self.hook_tracker.update(frame)
                names = results.names or {}
                hook_track_id = None
                if results.boxes is not None:
                    ids = (
                        results.boxes.id.tolist()
                        if results.boxes.id is not None
                        else [None] * len(results.boxes.xyxy)
                    )
                    for box, cls_id, track_id in zip(
                        results.boxes.xyxy.tolist(), results.boxes.cls.tolist(), ids
                    ):
                        label = names.get(int(cls_id), str(int(cls_id))).lower()
                        x1, y1, x2, y2 = box

                        if "hook" in label:
                            hook_bbox = (x1, y1, x2, y2)
                            hook_track_id = int(track_id) if track_id is not None else None
                            color = (255, 255, 0)
                        elif "load" in label:
                            load_bbox = (x1, y1, x2, y2)
                            color = (0, 165, 255)
                        else:
                            color = (200, 200, 200)

                        draw_bbox(annotated, (x1, y1, x2, y2), label=label, color=color)
                        detections_for_client.append(
                            {
                                "label": label,
                                "severity": None,
                                "box": [x1 / w, y1 / h, (x2 - x1) / w, (y2 - y1) / h],
                            }
                        )

                if hook_track_id is not None:
                    track_history = self.hook_tracker.get_history(hook_track_id)
            except Exception:
                logger.exception(
                    "Hook/load detection failed on camera %s", self.camera_id
                )

        # --- Fall-zone rule check --------------------------------------
        fall_zone_violations = []
        if hook_bbox is not None or load_bbox is not None:
            try:
                fall_zone_violations = check_fall_zone_violations(
                    hook_bbox=hook_bbox,
                    load_bbox=load_bbox,
                    worker_bboxes=worker_bboxes,
                    track_history=track_history,
                    frame_idx=self._frame_idx,
                    use_calibrated=False,  # pixel-space check; flip once camera is calibrated (see backend/config.py)
                )
                for v in fall_zone_violations:
                    zone_center = v.get("zone_center_px")
                    radius = v.get("radius_px")
                    if zone_center and radius:
                        cv2.ellipse(
                            annotated,
                            (int(zone_center[0]), int(zone_center[1])),
                            (int(radius[0]), int(radius[1])),
                            0,
                            0,
                            360,
                            (0, 0, 255),
                            2,
                        )
                    detections_for_client.append(
                        {
                            "label": "fall_zone_violation",
                            "severity": "critical",
                            "box": self._bbox_to_norm(v.get("worker_bbox"), w, h),
                        }
                    )
            except Exception:
                logger.exception(
                    "Fall-zone rule check failed on camera %s", self.camera_id
                )

        return {
            "annotated_frame": annotated,
            "detections": [d for d in detections_for_client if d["box"] is not None],
            "ppe_violations": ppe_violations,
            "fall_zone_violations": fall_zone_violations,
        }

    @staticmethod
    def _bbox_to_norm(bbox, w, h):
        if not bbox:
            return None
        x1, y1, x2, y2 = bbox
        return [x1 / w, y1 / h, (x2 - x1) / w, (y2 - y1) / h]

    def build_incident_payloads(self, frame: np.ndarray, result: dict) -> List[dict]:
        """
        Turns this frame's violations into ready-to-insert Incident dicts
        (screenshot already saved to disk via IncidentReporter). Caller
        is responsible for actually writing to the DB — kept separate so
        this stays testable without a live database.
        """
        payloads = []

        if result["ppe_violations"]:
            screenshot_path = self.reporter.log_incident(
                frame, self._frame_idx, result["ppe_violations"]
            )
            for v in result["ppe_violations"]:
                payloads.append(
                    {
                        "camera_id": self.camera_id,
                        "type": "ppe_violation",
                        "title": v["label"].replace("_", " ").title(),
                        "severity": SEVERITY_BY_TYPE["ppe_violation"],
                        "confidence": v.get("confidence"),
                        "screenshot_path": screenshot_path,
                        "detection_meta": {"box": list(v["box"])},
                    }
                )

        if result["fall_zone_violations"]:
            screenshot_path = self.reporter.log_incident(
                frame, self._frame_idx, result["fall_zone_violations"]
            )
            for v in result["fall_zone_violations"]:
                payloads.append(
                    {
                        "camera_id": self.camera_id,
                        "type": "fall_zone_violation",
                        "title": "Worker in Suspended Load Fall Zone",
                        "severity": SEVERITY_BY_TYPE["fall_zone_violation"],
                        "confidence": None,
                        "screenshot_path": screenshot_path,
                        "detection_meta": {
                            k: v[k]
                            for k in ("zone_center_px", "radius_px", "worker_bbox")
                            if k in v
                        },
                    }
                )

        return payloads
