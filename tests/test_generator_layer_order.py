import os
import tempfile
from PIL import Image

from thermalright_lcd_control.device_controller.display.config import (
    DisplayConfig, BackgroundType, BarGraphConfig, TextConfig
)
from thermalright_lcd_control.device_controller.display.generator import DisplayGenerator


def create_temp_background(width=120, height=80, color=(0, 0, 0, 255)):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    path = tmp.name
    tmp.close()
    img = Image.new('RGBA', (width, height), color)
    img.save(path)
    return path


def test_text_above_bar_in_generator():
    # Create temporary background
    bg_path = create_temp_background(120, 80)

    try:
        # Base config - bar only
        cfg_bar = DisplayConfig(
            background_path=bg_path,
            background_type=BackgroundType.IMAGE,
            output_width=120,
            output_height=80,
            rotation=0,
            bar_configs=[
                BarGraphConfig(metric_name='cpu_usage', position=(20, 30), width=80, height=20,
                               fill_color=(0, 0, 255, 255), show_border=False, use_gradient=False)
            ],
            text_configs=[],
            metrics_configs=[],
            gradient_enabled=False,
            shadow_enabled=False,
            outline_enabled=False,
        )

        # config with text overlapping the bar
        cfg_with_text = DisplayConfig(
            background_path=bg_path,
            background_type=BackgroundType.IMAGE,
            output_width=120,
            output_height=80,
            rotation=0,
            bar_configs=cfg_bar.bar_configs,
            text_configs=[
                TextConfig(text='X', position=(40, 32), font_size=18, color=(255, 0, 0, 255), use_gradient=False)
            ],
            metrics_configs=[],
            gradient_enabled=False,
            shadow_enabled=False,
            outline_enabled=False,
        )

        # Ensure metrics value so bar is visible
        metrics = {'cpu_usage': 50}

        gen_bar = DisplayGenerator(cfg_bar)
        img_bar = gen_bar.generate_frame_with_metrics(metrics, apply_rotation=False)

        gen_with_text = DisplayGenerator(cfg_with_text)
        img_with_text = gen_with_text.generate_frame_with_metrics(metrics, apply_rotation=False)

        # Convert to RGBA for pixel checks
        a = img_bar.convert('RGBA')
        b = img_with_text.convert('RGBA')

        tx, ty = 40, 32
        # Check a small area around the text position for any pixel change caused by text rendering
        changed = False
        red_present = False
        for x in range(tx - 2, tx + 6):
            for y in range(ty - 2, ty + 10):
                r1, g1, b1, a1 = a.getpixel((x, y))
                r2, g2, b2, a2 = b.getpixel((x, y))
                if (r1, g1, b1) != (r2, g2, b2):
                    changed = True
                # Check for red-ish presence in generated-with-text image
                if r2 > max(g2, b2) + 10:
                    red_present = True

        assert changed, "Generated image with text should differ where text overlays the bar"
        assert red_present, "Generated image with text should contain red pixels where text is drawn"

    finally:
        try:
            os.unlink(bg_path)
        except Exception:
            pass
