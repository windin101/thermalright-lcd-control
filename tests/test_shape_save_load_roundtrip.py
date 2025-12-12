from thermalright_lcd_control.gui.widgets.geometry_utils import (
    compute_rotation_padding,
    device_to_preview,
    preview_to_device,
)


def test_shape_save_load_roundtrip_examples():
    cases = [
        (80, 80, 1.0, 20, 30),
        (50, 100, 1.0, 15, 60),
        (80, 50, 1.5, 10, 20),
        (33, 17, 2.0, 5, 7),
        (101, 73, 1.25, 37, 53),
    ]

    for w, h, scale, dx, dy in cases:
        pad_x, pad_y = compute_rotation_padding(w, h, scale)

        # Simulate save: device -> preview (what widget.get_position() would be)
        preview_x, preview_y = device_to_preview(dx, dy, pad_x, pad_y, scale)

        # Save-side would compute saved_device = preview_to_device(preview_x, preview_y)
        saved_dx, saved_dy = preview_to_device(preview_x, preview_y, pad_x, pad_y, scale)
        assert saved_dx == dx and saved_dy == dy

        # Simulate load: preview move computed as round(device * scale) - pad + 1 (apply_shapes_config behavior)
        loaded_preview_x = int(round(saved_dx * scale)) - pad_x + 1
        loaded_preview_y = int(round(saved_dy * scale)) - pad_y + 1

        # After load, converting back to device coords should match saved device coords
        recovered_dx, recovered_dy = preview_to_device(loaded_preview_x, loaded_preview_y, pad_x, pad_y, scale)
        assert recovered_dx == dx, f"X roundtrip failed: {dx} -> {recovered_dx} (w={w},h={h},s={scale})"
        assert recovered_dy == dy, f"Y roundtrip failed: {dy} -> {recovered_dy} (w={w},h={h},s={scale})"
