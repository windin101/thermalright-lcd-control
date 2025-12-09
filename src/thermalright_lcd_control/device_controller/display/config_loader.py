# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

from pathlib import Path
from typing import Dict, Any, Tuple

import yaml

from thermalright_lcd_control.device_controller.display.config import DisplayConfig, BackgroundType, MetricConfig, TextConfig, LabelPosition, DateConfig, TimeConfig
from thermalright_lcd_control.common.logging_config import LoggerConfig


class ConfigLoader:
    """Load and parse YAML configuration files with global font support"""

    def __init__(self):
        self.logger = LoggerConfig.setup_service_logger()

    def _hex_to_rgba(self, hex_color: str) -> Tuple[int, int, int, int]:
        """Convert hex color (#RRGGBBAA) to RGBA tuple"""
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]

        if len(hex_color) == 8:  # RRGGBBAA
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = int(hex_color[6:8], 16)
            return (r, g, b, a)
        elif len(hex_color) == 6:  # RRGGBB (assume full alpha)
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b, 255)
        else:
            raise ValueError(f"Invalid hex color format: {hex_color}")

    def _parse_label_position(self, position_str: str) -> LabelPosition:
        """Parse label position from string"""
        position_map = {
            "left": LabelPosition.LEFT,
            "right": LabelPosition.RIGHT,
            "above": LabelPosition.ABOVE,
            "below": LabelPosition.BELOW,
            "none": LabelPosition.NONE
        }
        return position_map.get(position_str.lower(), LabelPosition.LEFT)

    def _parse_metric_config(self, metric_data: Dict[str, Any]) -> MetricConfig:
        """Parse a metric configuration from YAML data (no font_path needed)"""
        label_pos_str = metric_data.get("label_position", "left")
        return MetricConfig(
            name=metric_data["name"],
            label=metric_data.get("label", ""),
            position=(
                metric_data["position"]["x"],
                metric_data["position"]["y"]
            ),
            font_size=metric_data["font_size"],
            label_font_size=metric_data.get("label_font_size"),
            color=self._hex_to_rgba(metric_data["color"]),
            format_string=metric_data.get("format_string", "{label}{value}"),
            unit=metric_data.get("unit", ""),
            enabled=metric_data.get("enabled", True),
            label_position=self._parse_label_position(label_pos_str)
        )

    def _parse_text_config(self, text_data: Dict[str, Any]) -> TextConfig:
        """Parse a text configuration from YAML data (no font_path needed)"""
        return TextConfig(
            text=text_data.get("text", ""),
            position=(
                text_data["position"]["x"],
                text_data["position"]["y"]
            ),
            font_size=text_data["font_size"],
            color=self._hex_to_rgba(text_data["color"]),
            enabled=text_data.get("enabled", True)
        )

    def _parse_date_config(self, date_data: Dict[str, Any]) -> DateConfig:
        """Parse a date configuration from YAML data with format options"""
        return DateConfig(
            text=date_data.get("text", ""),
            position=(
                date_data["position"]["x"],
                date_data["position"]["y"]
            ),
            font_size=date_data["font_size"],
            color=self._hex_to_rgba(date_data["color"]),
            enabled=date_data.get("enabled", True),
            show_weekday=date_data.get("show_weekday", True),
            show_year=date_data.get("show_year", False),
            date_format=date_data.get("date_format", "default")
        )

    def _parse_time_config(self, time_data: Dict[str, Any]) -> TimeConfig:
        """Parse a time configuration from YAML data with format options"""
        return TimeConfig(
            text=time_data.get("text", ""),
            position=(
                time_data["position"]["x"],
                time_data["position"]["y"]
            ),
            font_size=time_data["font_size"],
            color=self._hex_to_rgba(time_data["color"]),
            enabled=time_data.get("enabled", True),
            use_24_hour=time_data.get("use_24_hour", True),
            show_seconds=time_data.get("show_seconds", False),
            show_am_pm=time_data.get("show_am_pm", False)
        )

    def load_config(self, config_path: str, width: int, height: int) -> DisplayConfig:
        """Load configuration from YAML file"""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                yaml_data = yaml.safe_load(file)

            config = self.load_config_from_dict(yaml_data, width, height)
            self.logger.info(f"Configuration loaded successfully from {config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise

    def load_config_from_dict(self, yaml_data: dict, width: int, height: int) -> DisplayConfig:
        display_data = yaml_data["display"]
        # Parse metrics configurations
        metrics_configs = []
        if display_data["metrics"]["enabled"]:
            for metric_data in display_data["metrics"]["configs"]:
                if metric_data.get("enabled", True):
                    metrics_configs.append(self._parse_metric_config(metric_data))
        # Parse date configuration
        date_config = None
        if display_data["date"]["enabled"]:
            date_config = self._parse_date_config(display_data["date"])
        # Parse time configuration
        time_config = None
        if display_data["time"]["enabled"]:
            time_config = self._parse_time_config(display_data["time"])
        # Parse custom text configurations
        text_configs = []
        custom_texts = display_data.get("custom_texts", [])
        for text_data in custom_texts:
            if text_data.get("enabled", True):
                text_configs.append(self._parse_text_config(text_data))
        # Parse foreground configuration
        foreground_path = None
        foreground_position = (0, 0)
        foreground_alpha = 1.0
        if display_data["foreground"]["enabled"]:
            foreground_path = str(display_data["foreground"]["path"]).format(
                resolution=f"{width}{height}")
            foreground_position = (
                display_data["foreground"]["position"]["x"],
                display_data["foreground"]["position"]["y"]
            )
            foreground_alpha = display_data["foreground"]["alpha"]

        # Parse rotation (default to 0 if not specified)
        rotation = display_data.get("rotation", 0)
        
        # Parse background scale mode (default to stretch if not specified)
        background_scale_mode = display_data.get("background", {}).get("scale_mode", "stretch")
        
        # Parse background alpha (default to 1.0 if not specified)
        background_alpha = display_data.get("background", {}).get("alpha", 1.0)
        
        # Parse background color (default to black if not specified)
        bg_color_data = display_data.get("background", {}).get("color", {})
        background_color = (
            bg_color_data.get("r", 0),
            bg_color_data.get("g", 0),
            bg_color_data.get("b", 0)
        )

        # Parse text effects (shadow, outline, gradient)
        text_effects = display_data.get("text_effects", {})
        
        shadow_data = text_effects.get("shadow", {})
        shadow_enabled = shadow_data.get("enabled", False)
        shadow_color = self._hex_to_rgba(shadow_data.get("color", "#00000080"))
        shadow_offset_x = shadow_data.get("offset_x", 2)
        shadow_offset_y = shadow_data.get("offset_y", 2)
        shadow_blur = shadow_data.get("blur", 3)
        
        outline_data = text_effects.get("outline", {})
        outline_enabled = outline_data.get("enabled", False)
        outline_color = self._hex_to_rgba(outline_data.get("color", "#000000FF"))
        outline_width = outline_data.get("width", 1)
        
        gradient_data = text_effects.get("gradient", {})
        gradient_enabled = gradient_data.get("enabled", False)
        gradient_color1 = self._hex_to_rgba(gradient_data.get("color1", "#FFFFFFFF"))
        gradient_color2 = self._hex_to_rgba(gradient_data.get("color2", "#6464FFFF"))
        gradient_direction = gradient_data.get("direction", "vertical")

        config = DisplayConfig(
            output_width=width,
            output_height=height,
            rotation=rotation,
            background_path=display_data["background"]["path"],
            background_type=BackgroundType(display_data["background"]["type"]),
            background_scale_mode=background_scale_mode,
            background_alpha=background_alpha,
            background_color=background_color,
            foreground_image_path=foreground_path,
            foreground_position=foreground_position,
            foreground_alpha=foreground_alpha,
            metrics_configs=metrics_configs,
            date_config=date_config,
            time_config=time_config,
            text_configs=text_configs,
            shadow_enabled=shadow_enabled,
            shadow_color=shadow_color,
            shadow_offset_x=shadow_offset_x,
            shadow_offset_y=shadow_offset_y,
            shadow_blur=shadow_blur,
            outline_enabled=outline_enabled,
            outline_color=outline_color,
            outline_width=outline_width,
            gradient_enabled=gradient_enabled,
            gradient_color1=gradient_color1,
            gradient_color2=gradient_color2,
            gradient_direction=gradient_direction
        )

        return config
