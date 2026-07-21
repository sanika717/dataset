from geometry.danger_zone import DangerZoneCalculator

_calculator = DangerZoneCalculator()


def check_fall_zone_violations(hook_bbox, load_bbox, worker_bboxes, track_history,
                                frame_idx, cable_length_m=None, use_calibrated=False):
    """
    Checks whether any detected worker is standing inside the suspended
    load's fall/swing danger zone this frame.

    worker_bboxes: list of (x1, y1, x2, y2) from ppe_detector.py's person detections
    track_history: hook's rolling position history from tracker.py
    use_calibrated: if True, uses GroundPlaneCalibration IPM-based calculations.
                    if False (default), uses pixel-space gravity fall-zone checks.

    Returns a list of violation dicts, empty if none.
    """
    # For gravity zone, primary reference is load, fallback is hook.
    source_bbox = load_bbox if load_bbox is not None else hook_bbox
    if source_bbox is None:
        return []

    violations = []

    if use_calibrated:
        if hook_bbox is None:
            return []
        kwargs = {}
        if cable_length_m is not None:
            kwargs["cable_length_m"] = cable_length_m

        drop_point = _calculator.compute_drop_point(hook_bbox, load_bbox, **kwargs)
        radius_m = _calculator.compute_swing_radius(track_history, **kwargs)

        for worker_bbox in worker_bboxes:
            x1, y1, x2, y2 = worker_bbox
            foot_cx, foot_cy = (x1 + x2) / 2, y2  # bottom-center = feet

            worker_ground_point = _calculator.calib.pixel_to_ground(foot_cx, foot_cy) \
                if hasattr(_calculator, "calib") else None

            if _calculator.is_point_in_danger_zone(worker_ground_point, drop_point, radius_m):
                violations.append({
                    "type": "fall_zone_violation",
                    "frame": frame_idx,
                    "drop_point_m": drop_point,
                    "radius_m": radius_m,
                    "worker_bbox": worker_bbox,
                })
    else:
        # Gravity-based pixel-space check
        zone_center, radius_px = _calculator.compute_gravity_danger_zone_pixel(load_bbox, hook_bbox)
        if zone_center is None:
            return []

        for worker_bbox in worker_bboxes:
            if _calculator.is_worker_in_gravity_danger_zone_pixel(worker_bbox, zone_center, radius_px):
                violations.append({
                    "type": "fall_zone_violation",
                    "frame": frame_idx,
                    "zone_center_px": zone_center,
                    "radius_px": radius_px,
                    "worker_bbox": worker_bbox,
                })

    return violations