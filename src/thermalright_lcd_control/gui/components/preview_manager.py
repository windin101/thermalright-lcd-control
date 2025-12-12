# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Preview manager for display generation and frame updates"""

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QLabel

from thermalright_lcd_control.device_controller.display.config import (
    DisplayConfig, BackgroundType, DateConfig, TimeConfig, MetricConfig, TextConfig, LabelPosition, BarGraphConfig, CircularGraphConfig, ShapeConfig, ShapeType
)
from thermalright_lcd_control.device_controller.display.generator import DisplayGenerator
from concurrent.futures import ThreadPoolExecutor
from threading import Lock


class PreviewManager:
    """Manages display generation and frame updates for preview"""

    def __init__(self, config, preview_label: QLabel, text_style):
        self.config = config
        self.preview_label = preview_label
        self.text_style = text_style

        # Display properties (device resolution)
        self.device_width = 320
        self.device_height = 240
        # Preview properties (scaled for display)
        self.preview_scale = 1.5
        self.preview_width = int(self.device_width * self.preview_scale)
        self.preview_height = int(self.device_height * self.preview_scale)
        
        self.current_background_path = None
        self.current_foreground_path = None
        self.background_enabled = True  # Background visibility toggle
        self.background_color = (0, 0, 0)  # Background color when image disabled
        self.background_opacity = 1.0  # Background opacity (0.0 - 1.0)
        self.foreground_enabled = True  # Foreground visibility toggle
        self.foreground_opacity = 0.5
        self.foreground_position = (0, 0)
        self.current_rotation = 0
        self.background_scale_mode = "stretch"  # Default scaling mode
        self.refresh_interval = 1.0  # LCD refresh interval in seconds

        # Widget configs for PIL rendering
        self.date_config: Optional[DateConfig] = None
        self.time_config: Optional[TimeConfig] = None
        self.metrics_configs: List[MetricConfig] = []
        self.text_configs: List[TextConfig] = []
        self.bar_configs: List[BarGraphConfig] = []
        self.circular_configs: List[CircularGraphConfig] = []
        self.shape_configs: List = []  # List[ShapeConfig]
        # Debug overlay markers (device coordinates), used to mark positions on snapshots
        self.debug_overlay_markers: List[tuple] = []

        # Components
        self.display_generator = None
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview_frame)
        # Drag/throttle controls
        self._drag_count = 0
        self._drag_render_timer = QTimer()
        self._drag_render_timer.setSingleShot(False)
        self.drag_throttle_ms = 200
        self._drag_render_timer.setInterval(self.drag_throttle_ms)  # ms - throttle during dragging
        self._drag_render_timer.timeout.connect(self._drag_throttled_update)
        # Setup logger for GUI (<get_gui_logger> is optional in non-GUI tests)
        try:
            from thermalright_lcd_control.common.logging_config import get_gui_logger
            self.logger = get_gui_logger()
        except Exception:
            self.logger = None
        # Optional callback that will be called after the preview QLabel is updated
        # (allows the GUI to re-raise overlay widgets to ensure correct stacking)
        self.on_preview_updated = None

        # Executor used to create UI snapshot diffs in the background
        self._debug_executor = ThreadPoolExecutor(max_workers=1)
        self._debug_task_lock = Lock()
        self._debug_task_pending = False

    def set_device_dimensions(self, width: int, height: int):
        """Set preview dimensions from detected device"""
        self.device_width = width
        self.device_height = height
        self.preview_width = int(width * self.preview_scale)
        self.preview_height = int(height * self.preview_scale)
    
    def set_preview_scale(self, scale: float):
        """Set the preview scale factor"""
        self.preview_scale = scale
        self.preview_width = int(self.device_width * self.preview_scale)
        self.preview_height = int(self.device_height * self.preview_scale)

    def set_preview_dimensions(self, width: int, height: int):
        """Set preview dimensions directly (called when rotation changes)"""
        self.preview_width = width
        self.preview_height = height

    def initialize_default_background(self, backgrounds_dir: str):
        """Initialize with the first background file found"""
        try:
            backgrounds_path = Path(backgrounds_dir)
            if not backgrounds_path.exists():
                self.preview_label.setText("Background directory\nnot found")
                return

            supported_formats = self.config.get('supported_formats', {})
            supported_extensions = (set(supported_formats.get('images', [])) |
                                    set(supported_formats.get('videos', [])) |
                                    set(supported_formats.get('gifs', [])))

            for file_path in backgrounds_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    self.current_background_path = str(file_path)
                    self.create_display_generator()
                    return

            self.preview_label.setText("No background files\nfound")
        except Exception as e:
            self.preview_label.setText(f"Error loading\nbackground: {e}")

    def determine_background_type(self, file_path):
        """Determine BackgroundType from file extension"""
        if not file_path:
            return BackgroundType.IMAGE

        if Path(file_path).is_dir():
            return BackgroundType.IMAGE_COLLECTION

        extension = Path(file_path).suffix.lower()
        supported_formats = self.config.get('supported_formats', {})

        if extension in supported_formats.get('videos', []):
            return BackgroundType.VIDEO
        elif extension in supported_formats.get('gifs', []):
            return BackgroundType.GIF
        return BackgroundType.IMAGE

    def create_display_generator(self):
        """Create or recreate DisplayGenerator with current settings"""
        if not self.current_background_path:
            return

        try:
            # Only pass foreground path if foreground is enabled
            foreground_path = self.current_foreground_path if self.foreground_enabled else None
            
            # Convert QColor to RGBA tuple for text effects
            def qcolor_to_rgba(qcolor):
                return (qcolor.red(), qcolor.green(), qcolor.blue(), qcolor.alpha())
            
            # Use device dimensions for generator (actual output resolution)
            display_config = DisplayConfig(
                background_path=self.current_background_path,
                background_type=self.determine_background_type(self.current_background_path),
                output_width=self.device_width,
                output_height=self.device_height,
                rotation=self.current_rotation,
                background_scale_mode=self.background_scale_mode,
                background_enabled=self.background_enabled,
                background_color=self.background_color,
                background_alpha=self.background_opacity,
                global_font_path=self.text_style.font_family,
                foreground_image_path=foreground_path,
                foreground_position=self.foreground_position,
                foreground_alpha=self.foreground_opacity,
                # Widget configs for text rendering
                date_config=self.date_config,
                time_config=self.time_config,
                metrics_configs=self.metrics_configs if self.metrics_configs else [],
                text_configs=self.text_configs if hasattr(self, 'text_configs') and self.text_configs else [],
                bar_configs=self.bar_configs if hasattr(self, 'bar_configs') and self.bar_configs else [],
                circular_configs=self.circular_configs if hasattr(self, 'circular_configs') and self.circular_configs else [],
                shape_configs=self.shape_configs if hasattr(self, 'shape_configs') and self.shape_configs else [],
                # Text effects from text_style
                shadow_enabled=self.text_style.shadow_enabled,
                shadow_color=qcolor_to_rgba(self.text_style.shadow_color),
                shadow_offset_x=self.text_style.shadow_offset_x,
                shadow_offset_y=self.text_style.shadow_offset_y,
                shadow_blur=self.text_style.shadow_blur,
                outline_enabled=self.text_style.outline_enabled,
                outline_color=qcolor_to_rgba(self.text_style.outline_color),
                outline_width=self.text_style.outline_width,
                gradient_enabled=self.text_style.gradient_enabled,
                gradient_color1=qcolor_to_rgba(self.text_style.gradient_color1),
                gradient_color2=qcolor_to_rgba(self.text_style.gradient_color2),
                gradient_direction=self.text_style.gradient_direction
            )

            if self.display_generator:
                self.display_generator.cleanup()

            self.display_generator = DisplayGenerator(display_config)
            # Log shapes at info level so they're visible in GUI launched from terminal
            try:
                from thermalright_lcd_control.common.logging_config import get_gui_logger
                logger = get_gui_logger()
                if display_config.shape_configs:
                    logger.info("Preview Manager: shapes set in DisplayConfig:")
                    for sc in display_config.shape_configs:
                        logger.info(f"  - type={getattr(sc, 'shape_type', sc)}, pos={getattr(sc, 'position', None)}, size=({getattr(sc, 'width', None)},{getattr(sc, 'height', None)}) rot={getattr(sc, 'rotation', None)}")
            except Exception:
                pass
            # Debug: log shape configs for troubleshooting alignment/scale issues
            try:
                from thermalright_lcd_control.common.logging_config import get_gui_logger
                logger = get_gui_logger()
                if display_config.shape_configs:
                    for sc in display_config.shape_configs:
                        logger.debug(f"PreviewManager: shape_config -> type={getattr(sc, 'shape_type', sc)}, pos={getattr(sc, 'position', None)}, w={getattr(sc, 'width', None)}, h={getattr(sc, 'height', None)}, rotation={getattr(sc, 'rotation', None)}")
            except Exception:
                pass
            self.update_preview_frame()
        except Exception as e:
            self.preview_label.setText(f"Error creating\nDisplayGenerator:\n{str(e)}")

    def update_preview_frame(self, save_debug_snapshot_now: bool = False):
        """Update preview with next frame from DisplayGenerator"""
        if not self.display_generator:
            return

        try:
            # Get frame WITHOUT rotation - preview shows the working dimensions (what user designs)
            # The physical screen is rotated, so the user sees their design correctly
            # Hardware rotation happens separately when sending to USB
            pil_image, duration = self.display_generator.get_frame_with_duration(apply_rotation=False)
            # Optionally save a debug snapshot showing overlay markers vs generated shapes
            try:
                import os
                if os.path.exists('/tmp/preview_debug_enabled') and (save_debug_snapshot_now or self._drag_count == 0):
                    # Save generator-marked snapshot quickly (fast)
                    self.save_debug_snapshot(pil_image, self.display_generator.config)
                    # Optionally also capture the UI/qwidget rendering and create a diff
                    # This is heavy so we perform it asynchronously to avoid blocking UI
                    ui_enabled = os.path.exists('/tmp/preview_debug_enabled_ui')
                    if ui_enabled:
                        try:
                            from PySide6.QtCore import QBuffer
                            buf = QBuffer()
                            buf.open(QBuffer.ReadWrite)
                            preview_widget = self.preview_label.parent()
                            if preview_widget:
                                qpix = preview_widget.grab()
                                qpix.save(buf, 'PNG')
                                qbytes = bytes(buf.data())
                                # Convert pil image to bytes so background task can use it
                                from io import BytesIO
                                gen_buf = BytesIO()
                                pil_image.save(gen_buf, format='PNG')
                                gen_bytes = gen_buf.getvalue()
                                # Schedule background task - ensure we have at most one pending job
                                if not self._debug_task_pending:
                                    def task(qb, gb, cfg):
                                        try:
                                            from PIL import Image
                                            import numpy as np
                                            from io import BytesIO
                                            ui_img = Image.open(BytesIO(qb)).convert('RGBA')
                                            gen_img = Image.open(BytesIO(gb)).convert('RGBA')
                                            if ui_img.size != gen_img.size:
                                                ui_img = ui_img.resize(gen_img.size)
                                            gen_arr = np.array(gen_img, dtype=np.int16)
                                            ui_arr = np.array(ui_img, dtype=np.int16)
                                            diff = np.abs(gen_arr - ui_arr).astype('uint8')
                                            from PIL import Image
                                            diff_img = Image.fromarray(diff.astype('uint8'), 'RGBA')
                                            import time, os
                                            ui_path = f"/tmp/preview_ui_{int(time.time())}.png"
                                            diff_path = f"/tmp/preview_diff_{int(time.time())}.png"
                                            ui_img.save(ui_path)
                                            diff_img.save(diff_path)
                                            try:
                                                if self.logger:
                                                    self.logger.info(f"Saved preview diff snapshot: {diff_path}")
                                            except Exception:
                                                pass
                                        finally:
                                            with self._debug_task_lock:
                                                self._debug_task_pending = False
                                    # Mark as pending and submit
                                    with self._debug_task_lock:
                                        self._debug_task_pending = True
                                    self._debug_executor.submit(task, qbytes, gen_bytes, self.display_generator.config)
                        except Exception:
                            # If UI grab fails we still continue silently
                            pass
            except Exception:
                pass
            qpixmap = self.pil_image_to_qpixmap(pil_image)

            if qpixmap and not qpixmap.isNull():
                self.preview_label.setPixmap(qpixmap)
                # Notify the UI that preview updated so it can restore overlay z-order
                # Avoid re-raising overlays while the user is dragging to prevent
                # possible reparent/focus thrashing; only call when not dragging.
                try:
                    if callable(self.on_preview_updated) and self._drag_count == 0:
                        self.on_preview_updated()
                except Exception:
                    pass
            else:
                self.preview_label.setText("Error converting\nimage")
            next_update_ms = max(int(duration * 1000), 33)
            self.preview_timer.setSingleShot(True)
            self.preview_timer.start(next_update_ms)
        except Exception as e:
            self.preview_label.setText(f"Error updating\npreview:\n{str(e)}")

    def save_debug_snapshot(self, pil_image, display_config: DisplayConfig):
        """Save debug snapshot to /tmp with overlay markers and generator shapes highlighted.

        Green small boxes: overlay UI positions (self.debug_overlay_markers)
        Blue boxes: generator shape rectangle positions (display_config.shape_configs)
        """
        try:
            from PIL import ImageDraw
            import time, os

            # Work on RGBA image for marker overlays
            if pil_image.mode != 'RGBA':
                img = pil_image.convert('RGBA')
            else:
                img = pil_image.copy()

            draw = ImageDraw.Draw(img)
            # Draw overlay markers
            for pm in getattr(self, 'debug_overlay_markers', []) or []:
                try:
                    px, py = int(pm[0]), int(pm[1])
                    draw.rectangle([px-2, py-2, px+2, py+2], outline=(0, 255, 0, 255), width=1)
                except Exception:
                    continue

            # Additionally annotate deltas between overlay markers and nearest generator shapes
            try:
                for pm in getattr(self, 'debug_overlay_markers', []) or []:
                    px, py = int(pm[0]), int(pm[1])
                    # Find nearest shape center (if any)
                    nearest = None
                    min_dist = None
                    for sc in getattr(display_config, 'shape_configs', []) or []:
                        try:
                            sx, sy = int(sc.position[0]), int(sc.position[1])
                            sw, sh = int(sc.width), int(sc.height)
                            cx = sx + sw // 2
                            cy = sy + sh // 2
                            dist = abs(px - cx) + abs(py - cy)
                            if min_dist is None or dist < min_dist:
                                min_dist = dist
                                nearest = (sx, sy, sw, sh, cx, cy)
                        except Exception:
                            continue
                    if nearest:
                        sx, sy, sw, sh, cx, cy = nearest
                        dx = px - cx
                        dy = py - cy
                        # Draw small red cross at the generator's computed center
                        draw.line([cx-3, cy, cx+3, cy], fill=(255, 0, 0, 255), width=1)
                        draw.line([cx, cy-3, cx, cy+3], fill=(255, 0, 0, 255), width=1)
                        # Draw delta text near the overlay marker
                        text = f"d={dx},{dy}"
                        draw.text((px + 4, py - 6), text, fill=(0, 255, 0, 255))
            except Exception:
                pass

            # Draw generator shape bounding rects (blue)
            for sc in getattr(display_config, 'shape_configs', []) or []:
                try:
                    sx, sy = int(sc.position[0]), int(sc.position[1])
                    sw, sh = int(sc.width), int(sc.height)
                    draw.rectangle([sx, sy, sx + sw, sy + sh], outline=(0, 0, 255, 255), width=1)
                    # Label shapes for clarity
                    draw.text((sx + 2, sy + 2), "S", fill=(0, 0, 255, 255))
                except Exception:
                    continue

            # Draw bar graph bounding rects (magenta) and label them "B"
            for bc in getattr(display_config, 'bar_configs', []) or []:
                try:
                    bx, by = int(getattr(bc, 'position', (0, 0))[0]), int(getattr(bc, 'position', (0, 0))[1])
                    bw, bh = int(getattr(bc, 'width', 0)), int(getattr(bc, 'height', 0))
                    draw.rectangle([bx, by, bx + bw, by + bh], outline=(255, 0, 255, 255), width=1)
                    draw.text((bx + 2, by + 2), "B", fill=(255, 0, 255, 255))
                except Exception:
                    continue

            # Draw circular graph bounding boxes (cyan) and label them "A" (arc)
            for ac in getattr(display_config, 'circular_configs', []) or []:
                try:
                    cx, cy = int(getattr(ac, 'position', (0, 0))[0]), int(getattr(ac, 'position', (0, 0))[1])
                    r = int(getattr(ac, 'radius', 0))
                    draw.rectangle([cx - r, cy - r, cx + r, cy + r], outline=(0, 255, 255, 255), width=1)
                    draw.text((cx - r + 2, cy - r + 2), "A", fill=(0, 255, 255, 255))
                except Exception:
                    continue

            # Mark text widget positions (red) and metrics positions (yellow)
            for tc in getattr(display_config, 'text_configs', []) or []:
                try:
                    tx, ty = int(getattr(tc, 'position', (0, 0))[0]), int(getattr(tc, 'position', (0, 0))[1])
                    draw.line([tx - 4, ty, tx + 4, ty], fill=(255, 0, 0, 255), width=1)
                    draw.line([tx, ty - 4, tx, ty + 4], fill=(255, 0, 0, 255), width=1)
                    draw.text((tx + 4, ty - 8), "T", fill=(255, 0, 0, 255))
                except Exception:
                    continue

            for mc in getattr(display_config, 'metrics_configs', []) or []:
                try:
                    mx, my = int(getattr(mc, 'position', (0, 0))[0]), int(getattr(mc, 'position', (0, 0))[1])
                    draw.line([mx - 4, my, mx + 4, my], fill=(255, 255, 0, 255), width=1)
                    draw.line([mx, my - 4, mx, my + 4], fill=(255, 255, 0, 255), width=1)
                    draw.text((mx + 4, my - 8), "M", fill=(255, 255, 0, 255))
                except Exception:
                    continue

            path = f"/tmp/preview_debug_{int(time.time())}.png"
            img.save(path)
            try:
                from thermalright_lcd_control.common.logging_config import get_gui_logger
                logger = get_gui_logger()
                logger.info(f"Saved preview debug snapshot: {path}")
            except Exception:
                pass
            # Additionally, try to capture the actual Qt preview widget rendering
            try:
                # preview_label is a QLabel inside preview_widget; grab the parent widget
                parent_widget = getattr(self.preview_label, 'parent', None)
                if parent_widget:
                    try:
                        preview_widget = self.preview_label.parent()
                        # Use grab() to capture the widget's current rendering as QPixmap
                        from PySide6.QtCore import QBuffer, QByteArray
                        from PySide6.QtGui import QPixmap
                        qpix = preview_widget.grab()
                        ui_path = f"/tmp/preview_ui_{int(time.time())}.png"
                        qpix.save(ui_path)
                        try:
                            logger.info(f"Saved preview UI snapshot: {ui_path}")
                        except Exception:
                            pass

                        # Also save a pixel-diff image between the generator image and the UI grab
                        try:
                            # Convert QPixmap to PIL via bytes
                            buf = QBuffer()
                            buf.open(QBuffer.ReadWrite)
                            qpix.save(buf, 'PNG')
                            b = bytes(buf.data())
                            from io import BytesIO
                            ui_img = Image.open(BytesIO(b)).convert('RGBA')
                            # Ensure same size as generator image
                            if ui_img.size != img.size:
                                ui_img = ui_img.resize(img.size)
                            # Compute absolute difference
                            import numpy as np
                            gen = np.array(img.convert('RGBA'), dtype=np.int16)
                            ui = np.array(ui_img.convert('RGBA'), dtype=np.int16)
                            diff = np.abs(gen - ui).astype('uint8')
                            from PIL import Image
                            diff_img = Image.fromarray(diff.astype('uint8'), 'RGBA')
                            diff_path = f"/tmp/preview_diff_{int(time.time())}.png"
                            diff_img.save(diff_path)
                            try:
                                logger.info(f"Saved preview diff snapshot: {diff_path}")
                            except Exception:
                                pass
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass
            return path
        except Exception as e:
            try:
                from thermalright_lcd_control.common.logging_config import get_gui_logger
                logger = get_gui_logger()
                logger.error(f"Failed to save debug snapshot: {e}")
            except Exception:
                pass
            return None

    def pil_image_to_qpixmap(self, pil_image):
        """Convert PIL Image to QPixmap and scale for preview

        Preserves alpha channel and scales to exact preview size to avoid
        compositing or alignment issues in the preview label.
        """
        try:
            # Ensure we have an RGBA image so alpha is preserved
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')

            # Use Pillow's Qt adapter to get a proper QImage with alpha
            try:
                from PIL.ImageQt import ImageQt
                qimage = ImageQt(pil_image)
            except Exception:
                # Fallback to manual conversion (may lose alpha on some platforms)
                width, height = pil_image.size
                image_data = pil_image.tobytes("raw", "RGBA")
                qimage = QImage(image_data, width, height, QImage.Format_RGBA8888)

            pixmap = QPixmap.fromImage(qimage)

            # Scale FORCIBLY to preview size (1:1 mapping) - ignore aspect ratio so
            # generated content matches UI overlay positions exactly (prevents auto-centering)
            if self.preview_scale != 1.0:
                from PySide6.QtCore import Qt
                pixmap = pixmap.scaled(
                    self.preview_width,
                    self.preview_height,
                    Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation,
                )

            return pixmap
        except Exception:
            return None

    def set_background(self, file_path: str):
        """Set background media"""
        self.current_background_path = file_path
        self.create_display_generator()

    def set_foreground(self, file_path: str):
        """Set foreground media"""
        self.current_foreground_path = file_path
        self.create_display_generator()

    def set_background_enabled(self, enabled: bool):
        """Enable/disable background visibility"""
        self.background_enabled = enabled
        # Update existing generator's config (frame_manager shares the same config object)
        if self.display_generator and self.display_generator.config:
            self.display_generator.config.background_enabled = enabled
        else:
            self.create_display_generator()

    def is_background_enabled(self) -> bool:
        """Check if background is enabled"""
        return self.background_enabled

    def set_background_opacity(self, opacity: int):
        """Set background opacity (0 to 100)"""
        self.background_opacity = opacity / 100.0  # Convert to 0.0 - 1.0
        # Update existing generator's config instead of recreating
        if self.display_generator and self.display_generator.config:
            self.display_generator.config.background_alpha = self.background_opacity

    def get_background_opacity(self) -> int:
        """Get background opacity (0 to 100)"""
        return int(getattr(self, 'background_opacity', 1.0) * 100)

    def set_background_color(self, color: tuple):
        """Set background color (r, g, b) used when background image is disabled"""
        self.background_color = color
        self.create_display_generator()

    def get_background_color(self) -> tuple:
        """Get background color"""
        return self.background_color

    def set_foreground_enabled(self, enabled: bool):
        """Enable/disable foreground visibility"""
        self.foreground_enabled = enabled
        self.create_display_generator()

    def is_foreground_enabled(self) -> bool:
        """Check if foreground is enabled"""
        return self.foreground_enabled

    def set_foreground_opacity(self, opacity: float):
        """Set foreground opacity (0.0 to 1.0)"""
        self.foreground_opacity = opacity
        # Update existing generator's config instead of recreating
        if self.display_generator and self.display_generator.config:
            self.display_generator.config.foreground_alpha = opacity
        else:
            self.create_display_generator()

    def set_foreground_position(self, x: int, y: int):
        """Set foreground position (x, y)"""
        self.foreground_position = (x, y)
        # Update existing generator's config instead of recreating
        if self.display_generator and self.display_generator.config:
            self.display_generator.config.foreground_position = (x, y)
        else:
            self.create_display_generator()

    def get_foreground_position(self) -> tuple:
        """Get current foreground position"""
        return self.foreground_position

    def set_rotation(self, rotation: int):
        """Set display rotation (0, 90, 180, 270)"""
        self.current_rotation = rotation
        self.create_display_generator()

    def set_background_scale_mode(self, scale_mode: str):
        """Set background scaling mode (stretch, scaled_fit, scaled_fill, centered, tiled)"""
        self.background_scale_mode = scale_mode
        self.create_display_generator()

    def get_background_scale_mode(self) -> str:
        """Get current background scaling mode"""
        return self.background_scale_mode

    def update_text_effects(self):
        """Update text effects in the display generator from current text_style"""
        if self.display_generator and self.display_generator.config:
            config = self.display_generator.config
            
            # Convert QColor to RGBA tuple
            def qcolor_to_rgba(qcolor):
                return (qcolor.red(), qcolor.green(), qcolor.blue(), qcolor.alpha())
            
            # Update shadow settings
            config.shadow_enabled = self.text_style.shadow_enabled
            config.shadow_color = qcolor_to_rgba(self.text_style.shadow_color)
            config.shadow_offset_x = self.text_style.shadow_offset_x
            config.shadow_offset_y = self.text_style.shadow_offset_y
            config.shadow_blur = self.text_style.shadow_blur
            
            # Update outline settings
            config.outline_enabled = self.text_style.outline_enabled
            config.outline_color = qcolor_to_rgba(self.text_style.outline_color)
            config.outline_width = self.text_style.outline_width
            
            # Update gradient settings
            config.gradient_enabled = self.text_style.gradient_enabled
            config.gradient_color1 = qcolor_to_rgba(self.text_style.gradient_color1)
            config.gradient_color2 = qcolor_to_rgba(self.text_style.gradient_color2)
            config.gradient_direction = self.text_style.gradient_direction
            
            # IMPORTANT: Also update the TextRenderer's display_config reference
            # The TextRenderer stores its own reference to display_config, so we need
            # to update it there as well for the effects to actually render
            if hasattr(self.display_generator, 'text_renderer'):
                self.display_generator.text_renderer.display_config = config
            
            # Trigger immediate preview refresh to show the changes
            self.update_preview_frame()
        else:
            # Recreate generator if config not available
            self.create_display_generator()

    def update_widget_configs(self, date_config: Optional[DateConfig] = None, 
                              time_config: Optional[TimeConfig] = None,
                              metrics_configs: Optional[List[MetricConfig]] = None,
                              text_configs: Optional[List[TextConfig]] = None,
                              bar_configs: Optional[List[BarGraphConfig]] = None,
                              circular_configs: Optional[List[CircularGraphConfig]] = None,
                              shape_configs: Optional[list] = None,
                              force_update: bool = True):
        """Update widget configs and refresh the preview.
        
        Args:
            date_config: Date configuration (None means disabled)
            time_config: Time configuration (None means disabled)
            metrics_configs: List of metric configurations (empty list means all disabled)
            text_configs: List of text configurations
            bar_configs: List of bar graph configurations
            circular_configs: List of circular graph configurations
            force_update: If True, always update configs even if None (for disabling widgets)
        """
        # Always update configs - None means widget is disabled
        if force_update or date_config is not None:
            self.date_config = date_config
        if force_update or time_config is not None:
            self.time_config = time_config
        if force_update or metrics_configs is not None:
            self.metrics_configs = metrics_configs if metrics_configs else []
        if force_update or text_configs is not None:
            self.text_configs = text_configs if text_configs else []
        if force_update or bar_configs is not None:
            self.bar_configs = bar_configs if bar_configs else []
        if force_update or circular_configs is not None:
            self.circular_configs = circular_configs if circular_configs else []
        if force_update or shape_configs is not None:
            # Normalize shape configs: allow dataclass ShapeConfig or dict from YAML
            normalized_shapes = []
            if shape_configs:
                for sc in shape_configs:
                    if isinstance(sc, dict):
                        # Parse likely fields: shape_type, position, width, height, rotation, filled, fill_color, border_color, border_width, corner_radius, arrow_head_size, enabled
                        def parse_color(value):
                            # Accept either tuple/list numeric or hex string like '#RRGGBBAA' or '#RRGGBB'
                            if not value:
                                return (0, 0, 0, 255)
                            if isinstance(value, (list, tuple)) and len(value) in (3, 4):
                                if len(value) == 3:
                                    return (int(value[0]), int(value[1]), int(value[2]), 255)
                                return (int(value[0]), int(value[1]), int(value[2]), int(value[3]))
                            s = str(value).lstrip('#')
                            if len(s) == 8:
                                r = int(s[0:2], 16); g = int(s[2:4], 16); b = int(s[4:6], 16); a = int(s[6:8], 16)
                                return (r, g, b, a)
                            if len(s) == 6:
                                r = int(s[0:2], 16); g = int(s[2:4], 16); b = int(s[4:6], 16)
                                return (r, g, b, 255)
                            try:
                                # fallback: try to parse as comma-separated integers
                                parts = [int(x.strip()) for x in str(value).split(',')]
                                if len(parts) == 3:
                                    return (parts[0], parts[1], parts[2], 255)
                                if len(parts) == 4:
                                    return (parts[0], parts[1], parts[2], parts[3])
                            except Exception:
                                pass
                            return (0, 0, 0, 255)

                        # Map shape type to enum if possible
                        st = sc.get('shape_type', 'rectangle')
                        try:
                            st_enum = ShapeType(st)
                        except Exception:
                            # If UI value is e.g., 'rectangle' as string, wrap into enum
                            try:
                                st_enum = ShapeType(st)
                            except Exception:
                                st_enum = ShapeType.RECTANGLE

                        pos = sc.get('position') or {}
                        if isinstance(pos, dict):
                            px = int(pos.get('x', 0))
                            py = int(pos.get('y', 0))
                        elif isinstance(pos, (list, tuple)) and len(pos) >= 2:
                            px = int(pos[0]); py = int(pos[1])
                        else:
                            px = 0; py = 0

                        normalized_shapes.append(ShapeConfig(
                            shape_type=st_enum,
                            position=(px, py),
                            width=int(sc.get('width', 100)),
                            height=int(sc.get('height', 50)),
                            rotation=int(sc.get('rotation', 0)),
                            filled=bool(sc.get('filled', True)),
                            fill_color=parse_color(sc.get('fill_color')),
                            border_color=parse_color(sc.get('border_color')),
                            border_width=int(sc.get('border_width', 2)),
                            corner_radius=int(sc.get('corner_radius', 0)),
                            arrow_head_size=int(sc.get('arrow_head_size', 10)),
                            enabled=bool(sc.get('enabled', True))
                        ))
                    elif isinstance(sc, ShapeConfig):
                        normalized_shapes.append(sc)
                    else:
                        # ignore invalid entries but keep processing
                        continue
            self.shape_configs = normalized_shapes
        
        # Update configs in existing generator
        if self.display_generator and self.display_generator.config:
            self.display_generator.config.date_config = self.date_config
            self.display_generator.config.time_config = self.time_config
            self.display_generator.config.metrics_configs = self.metrics_configs
            self.display_generator.config.text_configs = self.text_configs
            self.display_generator.config.bar_configs = self.bar_configs
            self.display_generator.config.circular_configs = self.circular_configs
            self.display_generator.config.shape_configs = self.shape_configs
            # If user is actively dragging, avoid performing a full generator update
            # on every small movement. The display_generator.config is updated so the
            # next render will reflect the changes, but we throttle rendering using
            # a timer to reduce CPU usage and provide smoother UI interaction.
            if self._drag_count > 0:
                # Ensure the throttle timer is running so we still provide occasional
                # updates while the user is dragging.
                if not self._drag_render_timer.isActive():
                    self._drag_render_timer.start()
            else:
                self.update_preview_frame()
        else:
            self.create_display_generator()

    def set_dragging(self, dragging: bool):
        """Enable or disable dragging mode to throttle heavy preview generation.

        When dragging=True we start a throttled timer which periodically renders
        the preview at a lower frequency. When False we stop the throttle and
        immediately render the final state.
        """
        try:
            if dragging:
                self._drag_count += 1
                if self._drag_count == 1 and not self._drag_render_timer.isActive():
                    self._drag_render_timer.start()
                try:
                    if self.logger:
                        self.logger.info(f"PreviewManager: drag started (count={self._drag_count})")
                except Exception:
                    pass
            else:
                if self._drag_count > 0:
                    self._drag_count -= 1
                if self._drag_count == 0 and self._drag_render_timer.isActive():
                    self._drag_render_timer.stop()
                    # After finishing dragging, force an immediate full render
                    self.update_preview_frame()
                    try:
                        if self.logger:
                            self.logger.info("PreviewManager: drag ended - forced final render")
                    except Exception:
                        pass
        except Exception:
            pass

    def set_drag_throttle_interval(self, ms: int):
        """Adjust the drag throttle interval (ms)."""
        try:
            self.drag_throttle_ms = max(1, int(ms))
            self._drag_render_timer.setInterval(self.drag_throttle_ms)
        except Exception:
            pass

    def _drag_throttled_update(self):
        """Called periodically while dragging to render a throttled preview."""
        if self._drag_count > 0 and self.display_generator:
            try:
                # Telemetry mainly for debugging - avoid spamming too much
                try:
                    if self.logger:
                        self.logger.debug(f"PreviewManager: throttled update (drag_count={self._drag_count})")
                except Exception:
                    pass
                # Perform the update (this will also optionally save a debug snapshot)
                # Use save_debug_snapshot_now=True so we capture a single throttled debug snapshot
                self.update_preview_frame(save_debug_snapshot_now=True)
                # If debug snapshot saving is enabled, log the path for easier analysis
                try:
                    import os
                    if os.path.exists('/tmp/preview_debug_enabled'):
                        # Quick check: create frame and save a snapshot to get path
                        try:
                            pil_image, _ = self.display_generator.get_frame_with_duration(apply_rotation=False)
                            path = self.save_debug_snapshot(pil_image, self.display_generator.config)
                            if path and self.logger:
                                self.logger.debug(f"PreviewManager: throttled debug snapshot saved: {path}")
                        except Exception:
                            # If snapshot creation fails we still proceed silently
                            pass
                except Exception:
                    pass
            except Exception:
                pass

    def clear_background(self, backgrounds_dir: str):
        """Clear background media"""
        self.current_background_path = None
        self.initialize_default_background(backgrounds_dir)

    def clear_foreground(self):
        """Clear foreground media"""
        self.current_foreground_path = None
        self.create_display_generator()

    def clear_all(self, backgrounds_dir: str):
        """Clear all media"""
        self.current_foreground_path = None
        self.current_background_path = None
        self.initialize_default_background(backgrounds_dir)

    def cleanup(self):
        """Cleanup resources"""
        self.preview_timer.stop()
        if self._drag_render_timer and self._drag_render_timer.isActive():
            self._drag_render_timer.stop()
        if self.display_generator:
            self.display_generator.cleanup()
