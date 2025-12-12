"""Pure geometry helpers for widget <-> device coordinate math.

These helpers are independent of Qt/PySide so they can be unit-tested
on CI without requiring a GUI environment.
"""
import math
from typing import Tuple


def compute_rotation_padding(width: int, height: int, preview_scale: float, border_padding: int = 4) -> Tuple[int, int]:
    """Compute padding (x, y) that results from using a diagonal-bound box
    to contain a rotated element.

    Args:
        width: element width in device coords
        height: element height in device coords
        preview_scale: scale factor used by preview
        border_padding: extra padding around diagonal box

    Returns:
        (padding_x, padding_y) in preview coordinates (integers)
    """
    scaled_width = int(round(width * preview_scale))
    scaled_height = int(round(height * preview_scale))
    diagonal = int(math.ceil(math.sqrt(scaled_width**2 + scaled_height**2)))
    total_size = diagonal + border_padding * 2
    padding_x = int(round((total_size - scaled_width) / 2.0))
    padding_y = int(round((total_size - scaled_height) / 2.0))
    return padding_x, padding_y


def device_to_preview(device_x: int, device_y: int, pad_x: int, pad_y: int, preview_scale: float) -> Tuple[int, int]:
    """Convert device coordinates to preview widget top-left (apply pad and scale)."""
    px = int(round(device_x * preview_scale)) - pad_x
    py = int(round(device_y * preview_scale)) - pad_y
    return px, py


def preview_to_device(preview_x: int, preview_y: int, pad_x: int, pad_y: int, preview_scale: float) -> Tuple[int, int]:
    """Convert preview widget top-left back to device coordinates (rounding aware)."""
    dx = int(round((preview_x + pad_x) / preview_scale))
    dy = int(round((preview_y + pad_y) / preview_scale))
    return dx, dy
