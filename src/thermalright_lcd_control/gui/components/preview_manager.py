# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Preview manager for display generation and frame updates"""

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QLabel

from thermalright_lcd_control.device_controller.display.config import DisplayConfig, BackgroundType
from thermalright_lcd_control.device_controller.display.generator import DisplayGenerator


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

        # Components
        self.display_generator = None
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview_frame)

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
                foreground_alpha=self.foreground_opacity
            )

            if self.display_generator:
                self.display_generator.cleanup()

            self.display_generator = DisplayGenerator(display_config)
            self.update_preview_frame()
        except Exception as e:
            self.preview_label.setText(f"Error creating\nDisplayGenerator:\n{str(e)}")

    def update_preview_frame(self):
        """Update preview with next frame from DisplayGenerator"""
        if not self.display_generator:
            return

        try:
            # Get frame without rotation for preview (apply_rotation=False)
            pil_image, duration = self.display_generator.get_frame_with_duration(apply_rotation=False)
            qpixmap = self.pil_image_to_qpixmap(pil_image)

            if qpixmap and not qpixmap.isNull():
                self.preview_label.setPixmap(qpixmap)
            else:
                self.preview_label.setText("Error converting\nimage")
            next_update_ms = max(int(duration * 1000), 33)
            self.preview_timer.setSingleShot(True)
            self.preview_timer.start(next_update_ms)
        except Exception as e:
            self.preview_label.setText(f"Error updating\npreview:\n{str(e)}")

    def pil_image_to_qpixmap(self, pil_image):
        """Convert PIL Image to QPixmap and scale for preview"""
        try:
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            width, height = pil_image.size
            image_data = pil_image.tobytes("raw", "RGB")
            qimage = QImage(image_data, width, height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            
            # Scale for preview display
            if self.preview_scale != 1.0:
                from PySide6.QtCore import Qt
                pixmap = pixmap.scaled(
                    self.preview_width, 
                    self.preview_height, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
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
        if self.display_generator:
            self.display_generator.cleanup()
