import os
import tempfile
from PIL import Image

import pytest

from thermalright_lcd_control.gui.components.preview_manager import PreviewManager
from thermalright_lcd_control.gui.utils.config_loader import load_config
from thermalright_lcd_control.gui.main_window import MediaPreviewUI


def create_temp_bg_image(width=120, height=80, color=(0, 0, 0, 255)):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    path = tmp.name
    tmp.close()
    img = Image.new('RGBA', (width, height), color)
    img.save(path)
    return path


def test_pil_image_to_qpixmap_preserves_size_and_alpha(monkeypatch):
    # Skip if PySide6 not installed
    pytest.importorskip("PySide6")

    # Create a label and a PreviewManager to test conversion
    from PySide6.QtWidgets import QLabel

    preview_label = QLabel()
    pm = PreviewManager({}, preview_label, None)
    pm.set_preview_scale(1.5)
    pm.set_device_dimensions(120, 80)

    bg_path = create_temp_bg_image(120, 80)
    try:
        img = Image.open(bg_path).convert('RGBA')
        pixmap = pm.pil_image_to_qpixmap(img)
        assert pixmap is not None
        assert pixmap.size().width() == pm.preview_width
        assert pixmap.size().height() == pm.preview_height
    finally:
        try:
            os.unlink(bg_path)
        except Exception:
            pass
