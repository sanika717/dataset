"""
Detection-pipeline tuning constants.

This file was imported everywhere (tracker.py, geocalib.py, depth.py,
danger_zone.py: `from config import ...`) but was never actually part of
any uploaded phase — it's a genuine gap, not a leftover. The values
below are reasonable starting points, NOT calibrated for any real site;
tune CAMERA_HEIGHT_M / CAMERA_TILT_DEG / FOCAL_PX / PRINCIPAL_X /
PRINCIPAL_Y per camera before trusting the ground-plane (IPM) math in
geocalib.py, or leave `use_calibrated=False` in load_rules.py to stick
to the pixel-space gravity check, which needs no camera calibration.
"""

# --- Hook tracking (tracker.py) ----------------------------------------
# How many recent (frame_idx, cx, cy) samples to keep per tracked hook,
# used by danger_zone.py's compute_swing_radius() to estimate swing.
SWING_HISTORY_FRAMES = 30

# --- Danger zone geometry (danger_zone.py) ------------------------------
# Default crane cable length in meters, used when a per-camera/per-lift
# value isn't supplied.
DEFAULT_CABLE_LENGTH_M = 15.0
# Extra radius added on top of the computed swing radius, as a margin of
# error for the swing-angle estimate.
STATIC_SAFETY_MARGIN_M = 2.0

# --- Monocular distance estimate (depth.py) -----------------------------
# Real-world height of the hook object in meters (measure your actual
# hook/block assembly) and the camera's focal length in pixels, used for
# the similar-triangles distance estimate: distance = (real_size * focal) / pixel_size.
HOOK_REAL_HEIGHT_M = 0.5
FOCAL_PX = 1000.0

# --- Ground-plane calibration / IPM (geocalib.py) -----------------------
# Camera mounting height above ground, in meters.
CAMERA_HEIGHT_M = 8.0
# Downward tilt from horizontal, in degrees (0 = looking at the horizon,
# 90 = looking straight down).
CAMERA_TILT_DEG = 30.0
# Principal point (usually the image center in pixels) — update to match
# your camera's actual resolution, e.g. (width / 2, height / 2).
PRINCIPAL_X = 640.0
PRINCIPAL_Y = 360.0
