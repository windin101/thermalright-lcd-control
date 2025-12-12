import pytest
from PySide6.QtWidgets import QApplication

from thermalright_lcd_control.gui.widgets.draggable_widget import ShapeWidget


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


@pytest.mark.parametrize("w,h,scale,dx,dy", [
    (80, 80, 1.0, 20, 30),
    (50, 100, 1.0, 15, 60),
    (80, 50, 1.5, 10, 20),
    (33, 17, 2.0, 5, 7),
    (101, 73, 1.25, 37, 53),
])
def test_shape_padding_roundtrip(qapp, w, h, scale, dx, dy):
    """Ensure that converting device -> preview -> device yields original coordinates (no drift)."""
    sw = ShapeWidget(None, widget_name="testshape")
    sw._width = w
    sw._height = h
    sw.set_preview_scale(scale)

    pad_x, pad_y = sw._get_rotation_padding()

    # Device -> preview (apply_shapes_config behavior uses round)
    preview_x = int(round(dx * scale)) - pad_x
    preview_y = int(round(dy * scale)) - pad_y

    # Now update_preview_widget_configs would compute device coords as round((preview + pad)/scale)
    recovered_dx = int(round((preview_x + pad_x) / scale))
    recovered_dy = int(round((preview_y + pad_y) / scale))

    assert recovered_dx == dx, f"X coordinate drift: {dx} -> {recovered_dx} (w={w},h={h},s={scale})"
    assert recovered_dy == dy, f"Y coordinate drift: {dy} -> {recovered_dy} (w={w},h={h},s={scale})"
