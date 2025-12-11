# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

import os
import subprocess

from PIL import ImageFont

from thermalright_lcd_control.device_controller.display.utils import _get_default_font_path
from thermalright_lcd_control.common.logging_config import LoggerConfig


class SystemFontManager:
    """Manager for system fonts on Ubuntu/Linux"""

    def __init__(self):
        self.logger = self.logger = LoggerConfig.setup_service_logger()
        self.font_path = _get_default_font_path()
        self._font_cache = {}  # Cache: (font_name, font_size, bold) -> ImageFont
        self._font_path_cache = {}  # Cache: (font_name, bold) -> font_path
        self._system_fonts = {}

    def get_font(self, font_size: int, font_name: str = None, bold: bool = False) -> ImageFont.ImageFont:
        """Get a font with caching, supporting both system names and file paths
        
        Args:
            font_size: Font size in points
            font_name: Font family name (e.g., "Arial", "Noto Sans"). None for default.
            bold: Whether to use bold variant
        """
        cache_key = (font_name, font_size, bold)
        
        if cache_key not in self._font_cache:
            font = self._load_font(font_size, font_name, bold)
            self._font_cache[cache_key] = font

        return self._font_cache[cache_key]

    def _get_font_path(self, font_name: str, bold: bool) -> str:
        """Get the file path for a font family using fc-match"""
        cache_key = (font_name, bold)
        
        if cache_key in self._font_path_cache:
            return self._font_path_cache[cache_key]
        
        try:
            # Build fc-match query
            query = font_name if font_name else ""
            if bold:
                query += ":weight=bold"
            
            result = subprocess.check_output(
                ["fc-match", query, "--format=%{file}"],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            
            if result and os.path.isfile(result):
                self._font_path_cache[cache_key] = result
                return result
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.warning(f"fc-match failed for font '{font_name}' bold={bold}: {e}")
        
        # Fallback to default font path
        self._font_path_cache[cache_key] = self.font_path
        return self.font_path

    def _load_font(self, font_size: int, font_name: str = None, bold: bool = False) -> ImageFont.ImageFont:
        """Load a font from system or file path"""
        # Get the font path for this family/style
        font_path = self._get_font_path(font_name, bold) if font_name else self.font_path
        
        if not font_path:
            return ImageFont.load_default()

        # Check if it's a direct file path
        if os.path.isfile(font_path):
            try:
                return ImageFont.truetype(font_path, font_size)
            except Exception as e:
                self.logger.warning(f"Could not load font from path {font_path}: {e}")
                return ImageFont.load_default(font_size)

        return ImageFont.load_default(font_size)


# Global font manager instance
_font_manager = None


def get_font_manager() -> SystemFontManager:
    """Get the global font manager instance"""
    global _font_manager
    if _font_manager is None:
        _font_manager = SystemFontManager()
    return _font_manager
