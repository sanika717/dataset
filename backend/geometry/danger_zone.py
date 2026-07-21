import math

from geometry.geocalib import GroundPlaneCalibration
from geometry.depth import estimate_load_height_above_ground
from config import DEFAULT_CABLE_LENGTH_M, STATIC_SAFETY_MARGIN_M


class DangerZoneCalculator:

    def __init__(self, calib: GroundPlaneCalibration = None):
        self.calib = calib or GroundPlaneCalibration()

    def compute_drop_point(self, hook_bbox, load_bbox=None,
                            cable_length_m=DEFAULT_CABLE_LENGTH_M):
        """
        Projects the hook's pixel position to ground-plane (X, Y) meters.
        This is the point directly below the load if it were to fall now.
        """
        x1, y1, x2, y2 = hook_bbox
        hook_cx = (x1 + x2) / 2
        hook_cy = y2  # bottom of hook bbox, closest point to the load

        ground_point = self.calib.pixel_to_ground(hook_cx, hook_cy)
        if ground_point is None:
            return None

        # NOTE: load height above ground is currently a conservative
        # placeholder in depth.py (returns full cable length). Refine
        # once a calibrated pixels-per-meter ratio is available.
        estimate_load_height_above_ground(hook_bbox, load_bbox, cable_length_m)

        return ground_point

    def compute_swing_radius(self, track_history, cable_length_m=DEFAULT_CABLE_LENGTH_M):
        """
        Estimates max swing displacement from recent hook pixel-position
        history (from tracker.py). Converts peak horizontal pixel velocity
        into an angular swing estimate, then arc length L * sin(theta).
        Falls back to a small default swing angle if there isn't enough
        history yet.
        """
        if len(track_history) < 3:
            swing_angle_rad = math.radians(5)  # conservative default
        else:
            xs = [p[1] for p in track_history]
            max_dx = max(xs) - min(xs)
            # Rough mapping: larger pixel excursion -> larger swing angle,
            # capped at a reasonable physical max (30 degrees).
            swing_angle_rad = min(math.radians(30), math.radians(max_dx / 20))

        swing_radius_m = cable_length_m * math.sin(swing_angle_rad)
        return swing_radius_m + STATIC_SAFETY_MARGIN_M

    def is_point_in_danger_zone(self, worker_ground_point, drop_point, radius_m):
        """Simple circular containment test — worker's ground (X, Y) vs. drop point."""
        if worker_ground_point is None or drop_point is None:
            return False

        dx = worker_ground_point[0] - drop_point[0]
        dy = worker_ground_point[1] - drop_point[1]
        distance = math.hypot(dx, dy)

        return distance <= radius_m

    def compute_gravity_danger_zone_pixel(self, load_bbox, hook_bbox=None, drop_scale=1.5, radius_scale=1.2):
        """
        Computes the pixel-space center and radius axes (rx, ry) for the gravity-based fall zone.
        Uses Suspended Load as the primary reference, falls back to Hook if load is missing.
        """
        bbox = load_bbox if load_bbox is not None else hook_bbox
        if bbox is None:
            return None, None

        x1, y1, x2, y2 = bbox
        cx = int((x1 + x2) / 2)
        bottom_y = int(y2)
        h = y2 - y1
        bbox_half_width = (x2 - x1) / 2

        drop_distance = int(h * drop_scale)
        zone_center = (cx, bottom_y + drop_distance)
        
        rx = max(int(bbox_half_width * radius_scale), 30)
        ry = int(rx * 0.4)
        radius_axes = (rx, ry)

        return zone_center, radius_axes

    def is_worker_in_gravity_danger_zone_pixel(self, worker_bbox, zone_center, radius_axes):
        """
        Checks if a worker (using bottom-center feet coordinate) falls within the
        pixel-space danger zone (ellipse on ground plane).
        """
        if worker_bbox is None or zone_center is None or radius_axes is None:
            return False

        wx1, wy1, wx2, wy2 = worker_bbox
        w_cx = (wx1 + wx2) / 2
        w_cy = wy2  # feet bottom-center

        rx, ry = radius_axes
        if rx <= 0 or ry <= 0:
            return False

        dx = w_cx - zone_center[0]
        dy = w_cy - zone_center[1]

        return (dx / rx)**2 + (dy / ry)**2 <= 1.0