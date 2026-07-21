import numpy as np

from config import CAMERA_HEIGHT_M, CAMERA_TILT_DEG, FOCAL_PX, PRINCIPAL_X, PRINCIPAL_Y


class GroundPlaneCalibration:
    """
    Maps image pixels to real-world ground-plane coordinates for a
    tilted, non-depth camera, using Inverse Perspective Mapping (IPM).
    Assumes the target point lies on the ground (z = 0) — for points
    above ground (e.g. a suspended load), correct separately using
    depth.py's estimate_load_height_above_ground().
    """

    def __init__(self,
                 camera_height_m=CAMERA_HEIGHT_M,
                 tilt_deg=CAMERA_TILT_DEG,
                 focal_px=FOCAL_PX,
                 cx=PRINCIPAL_X,
                 cy=PRINCIPAL_Y):
        self.H = camera_height_m
        self.focal_px = focal_px
        self.cx = cx
        self.cy = cy

        theta = np.radians(tilt_deg)
        self.K = np.array([
            [focal_px, 0, cx],
            [0, focal_px, cy],
            [0, 0, 1]
        ])
        self.K_inv = np.linalg.inv(self.K)

        # Rotation compensating the downward camera tilt (pitch about x-axis)
        self.R = np.array([
            [1, 0, 0],
            [0, np.cos(theta), -np.sin(theta)],
            [0, np.sin(theta), np.cos(theta)]
        ])

    def pixel_to_ground(self, u, v):
        """
        Projects a pixel (u, v) onto the ground plane (z = 0), returning
        (X, Y) in meters relative to the point directly below the camera.
        X = lateral offset, Y = forward distance. Returns None if the ray
        points above the horizon (no ground intersection).
        """
        ray_cam = self.K_inv @ np.array([u, v, 1.0])
        ray_world = self.R @ ray_cam

        if ray_world[1] <= 1e-6:
            return None

        t = self.H / ray_world[1]
        X = ray_world[0] * t
        Y = ray_world[2] * t
        return float(X), float(Y)

    def ground_to_pixel(self, X, Y):
        """
        Inverse of pixel_to_ground: projects a ground-plane point (X, Y),
        in meters relative to the point below the camera, back to an
        image pixel (u, v). Used to draw the danger-zone circle onto the
        frame — perspective will render it as an ellipse, which is correct.
        Returns None if the point falls behind the camera.
        """
        point_world = np.array([X, self.H, Y])
        ray_cam = self.R.T @ point_world  # R is a rotation, so R^T = R^-1

        if ray_cam[2] <= 1e-6:
            return None

        ray_cam_norm = ray_cam / ray_cam[2]
        pixel = self.K @ ray_cam_norm
        return float(pixel[0]), float(pixel[1])