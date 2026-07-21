import math
import cv2
import numpy as np


def draw_bbox(frame, bbox, label=None, color=(0, 255, 0), thickness=2):
    """Draw a bounding box and optional label onto `frame`.

    `bbox` is expected as (x1, y1, x2, y2) in pixel coordinates.
    """
    try:
        x1, y1, x2, y2 = map(int, bbox)
    except Exception:
        return frame

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

    if label:
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.5
        th = 1
        (w, h), _ = cv2.getTextSize(label, font, scale, th)
        # background box for text
        cv2.rectangle(frame, (x1, y1 - h - 6), (x1 + w + 6, y1), color, -1)
        cv2.putText(frame, label, (x1 + 3, y1 - 4), font, scale, (0, 0, 0), th, cv2.LINE_AA)
    return frame


def draw_danger_zone(frame, calib, drop_point, radius_m, color=(0, 0, 255), n_points=48):
    """
    Draws the fall/swing danger zone onto the frame. The zone is a circle
    on the ground plane, so in the tilted camera's perspective it renders
    as an ellipse — that foreshortening is expected, not an error.

    frame: the image (numpy array, BGR) to draw on, modified in place
    calib: a GroundPlaneCalibration instance
    drop_point: (X, Y) ground-plane meters, from DangerZoneCalculator
    radius_m: danger zone radius in meters
    color: BGR tuple, defaults to red so it's visually distinct from
           detection boxes (which are typically drawn in green/blue)
    """
    if drop_point is None or calib is None:
        return frame

    pts = []
    for i in range(n_points):
        angle = 2 * math.pi * i / n_points
        X = drop_point[0] + radius_m * math.cos(angle)
        Y = drop_point[1] + radius_m * math.sin(angle)
        pixel = calib.ground_to_pixel(X, Y)
        if pixel is not None:
            pts.append([int(pixel[0]), int(pixel[1])])

    if len(pts) >= 3:
        pts_arr = np.array([pts], dtype=np.int32)
        cv2.polylines(frame, pts_arr, isClosed=True, color=color, thickness=2)
        overlay = frame.copy()
        cv2.fillPoly(overlay, pts_arr, color=color)
        cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)

    return frame


def draw_gravity_fall_zone(frame, load_bbox, hook_bbox=None,
                            zone_color=(255, 0, 180), arrow_color=(255, 255, 255),
                            drop_scale=1.5, radius_scale=1.2):
    """
    Lightweight fall-zone indicator that needs no camera calibration:
    draws a downward gravity arrow from the suspended load, and a
    danger-zone circle centered where it points. Falls back to the
    hook's position if the load isn't detected this frame.

    drop_scale: how far below the load the arrow travels, as a multiple
                of the load's own bbox height
    radius_scale: danger zone radius, as a multiple of the load's bbox
                  half-width (bigger box -> bigger, closer-looking load
                  -> bigger danger zone)
    """
    source_bbox = load_bbox if load_bbox is not None else hook_bbox
    if source_bbox is None:
        return frame

    try:
        x1, y1, x2, y2 = map(int, source_bbox)
    except Exception:
        return frame

    center_x = int((x1 + x2) / 2)
    bottom_y = int(y2)
    bbox_height = y2 - y1
    bbox_half_width = (x2 - x1) / 2

    drop_distance = int(bbox_height * drop_scale)
    zone_center = (center_x, bottom_y + drop_distance)
    radius = max(int(bbox_half_width * radius_scale), 30)

    # Gravity arrow: straight down from the load's bottom edge to the zone center
    cv2.arrowedLine(frame, (center_x, bottom_y), zone_center,
                     arrow_color, thickness=2, tipLength=0.15)
    cv2.putText(frame, "g", (center_x + 8, bottom_y + drop_distance // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, arrow_color, 2)

    # Danger zone ellipse, filled with transparency + solid outline (to lie flat on the ground plane)
    rx = radius
    ry = int(radius * 0.4)
    axes = (rx, ry)
    overlay = frame.copy()
    cv2.ellipse(overlay, zone_center, axes, 0, 0, 360, zone_color, -1)
    cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
    cv2.ellipse(frame, zone_center, axes, 0, 0, 360, zone_color, 2)
    cv2.putText(frame, "fall zone", (zone_center[0] - 35, zone_center[1] + ry + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, zone_color, 2)

    return frame