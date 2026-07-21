import os
import json
import cv2
from datetime import datetime

class IncidentReporter:
    """
    Logs safety violations (incidents) by saving screenshot images and
    recording metadata reports.
    """
    def __init__(self, output_dir="backend/output"):
        self.output_dir = output_dir
        self.screenshots_dir = os.path.join(output_dir, "screenshots")
        self.reports_dir = os.path.join(output_dir, "reports")
        
        # Self-healing directory check: if they exist as files, remove and recreate as directories
        for path in [self.screenshots_dir, self.reports_dir]:
            if os.path.exists(path) and not os.path.isdir(path):
                print(f"[IncidentReporter] Removing file placeholder at {path}")
                os.remove(path)
            os.makedirs(path, exist_ok=True)

    def log_incident(self, frame, frame_idx, violations):
        """
        Saves a screenshot of the frame containing violations and
        records a JSON report entry.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        incident_id = f"incident_frame_{frame_idx}_{timestamp}"
        
        # Save screenshot
        screenshot_path = os.path.join(self.screenshots_dir, f"{incident_id}.png")
        cv2.imwrite(screenshot_path, frame)
        
        # Save report log
        report_path = os.path.join(self.reports_dir, f"{incident_id}.json")
        
        # Format violation coordinates for JSON serialization
        formatted_violations = []
        for v in violations:
            formatted_v = v.copy()
            if "worker_bbox" in formatted_v:
                formatted_v["worker_bbox"] = [float(coord) for coord in formatted_v["worker_bbox"]]
            if "zone_center_px" in formatted_v:
                formatted_v["zone_center_px"] = [float(c) for c in formatted_v["zone_center_px"]]
            if "radius_px" in formatted_v:
                if isinstance(formatted_v["radius_px"], (list, tuple)):
                    formatted_v["radius_px"] = [float(r) for r in formatted_v["radius_px"]]
                else:
                    formatted_v["radius_px"] = float(formatted_v["radius_px"])
            formatted_violations.append(formatted_v)

        report_data = {
            "incident_id": incident_id,
            "frame_idx": frame_idx,
            "timestamp": datetime.now().isoformat(),
            "violations": formatted_violations
        }
        
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=4)
            
        print(f"[IncidentReporter] Logged violation to: {report_path}")
        return screenshot_path
