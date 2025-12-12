from thermalright_lcd_control.gui.widgets.geometry_utils import (
    compute_rotation_padding,
    device_to_preview,
    preview_to_device,
)


def test_padding_roundtrip_examples():
    cases = [
        (80, 80, 1.0, 20, 30),
        (50, 100, 1.0, 15, 60),
        (80, 50, 1.5, 10, 20),
        (33, 17, 2.0, 5, 7),
        (101, 73, 1.25, 37, 53),
    ]

    for w, h, scale, dx, dy in cases:
        pad_x, pad_y = compute_rotation_padding(w, h, scale)

        # Device -> preview
        px, py = device_to_preview(dx, dy, pad_x, pad_y, scale)

        # Preview -> device
        recovered_dx, recovered_dy = preview_to_device(px, py, pad_x, pad_y, scale)

        assert recovered_dx == dx, f"X drift: {dx} -> {recovered_dx} for w={w},h={h},s={scale}"
        assert recovered_dy == dy, f"Y drift: {dy} -> {recovered_dy} for w={w},h={h},s={scale}"
