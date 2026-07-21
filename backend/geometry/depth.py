from config import FOCAL_PX, HOOK_REAL_HEIGHT_M


def estimate_distance(pixel_height, real_height_m=HOOK_REAL_HEIGHT_M, focal_px=FOCAL_PX):
    """
    Monocular distance via similar triangles: distance = (real_size * focal_length) / pixel_size.
    No depth model needed — just one measured real-world reference dimension.
    """
    if pixel_height <= 0:
        return None
    return (real_height_m * focal_px) / pixel_height


def estimate_load_height_above_ground(hook_bbox, load_bbox, cable_length_m):
    """
    Estimates how high the load currently sits above the ground, using the
    pixel gap between the hook and the load as a proxy for how much cable
    is paid out vs. how much is slack. Falls back to the full cable length
    (load at cable's end, worst case for danger-zone sizing) if the load
    box isn't detected this frame.
    """
    if load_bbox is None:
        return cable_length_m

    hook_bottom = hook_bbox[3]   # y2
    load_top = load_bbox[1]      # y1

    # Larger pixel gap between hook and load roughly tracks more cable
    # played out; without a calibrated pixels-per-meter ratio at this
    # depth, use the full cable length as a conservative estimate.
    gap_px = max(load_top - hook_bottom, 0)

    return cable_length_m