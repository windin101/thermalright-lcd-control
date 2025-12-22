# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

from pathlib import Path
from typing import Dict, Any, Tuple

import yaml

from .config import DisplayConfig, BackgroundType, MetricConfig, TextConfig
from .config_unified import CircularGraphConfig, BarGraphConfig
from ...common.logging_config import LoggerConfig
from ...gui.utils.path_resolver import get_path_resolver


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

    def _parse_metric_config(self, metric_data: Dict[str, Any]) -> MetricConfig:
        """Parse a metric configuration from YAML data (no font_path needed)"""
        return MetricConfig(
            name=metric_data["name"],
            label=metric_data.get("label", ""),
            position=(
                metric_data["position"]["x"],
                metric_data["position"]["y"]
            ),
            font_size=metric_data["font_size"],
            color=self._hex_to_rgba(metric_data["color"]),
            format_string=metric_data.get("format_string", "{label}{value}"),
            unit=metric_data.get("unit", ""),
            enabled=metric_data.get("enabled", True)
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

    def _parse_circular_graph_config(self, graph_data: Dict[str, Any]) -> CircularGraphConfig:
        """Parse a circular graph configuration from YAML data"""
        return CircularGraphConfig(
            position=(
                graph_data["position"]["x"],
                graph_data["position"]["y"]
            ),
            radius=graph_data["radius"],
            color=self._hex_to_rgba(graph_data["color"]),
            enabled=graph_data.get("enabled", True),
            min_value=graph_data.get("min_value", 0.0),
            max_value=graph_data.get("max_value", 100.0),
            show_value=graph_data.get("show_value", True),
            show_label=graph_data.get("show_label", True),
            label=graph_data.get("label", ""),
            metric_name=graph_data.get("metric_name", "cpu_usage"),
            thickness=graph_data.get("thickness", 8),
            start_angle=graph_data.get("start_angle", 135),
            sweep_angle=graph_data.get("sweep_angle", 270),
            rotation=graph_data.get("rotation", 0),
            fill_color=self._hex_to_rgba(graph_data["fill_color"]) if "fill_color" in graph_data and graph_data["fill_color"] else None,
            background_color=self._hex_to_rgba(graph_data["background_color"]) if "background_color" in graph_data and graph_data["background_color"] else None,
            border_color=self._hex_to_rgba(graph_data["border_color"]) if "border_color" in graph_data and graph_data["border_color"] else None,
            show_border=graph_data.get("show_border", False),
            border_width=graph_data.get("border_width", 1),
            show_percentage=graph_data.get("show_percentage", True)
        )

    def _parse_bar_graph_config(self, graph_data: Dict[str, Any]) -> BarGraphConfig:
        """Parse a bar graph configuration from YAML data"""
        self.logger.debug(f"Parsing bar graph config: {graph_data}")
        try:
            config = BarGraphConfig(
                position=(
                    graph_data["position"]["x"],
                    graph_data["position"]["y"]
                ),
                width=graph_data["width"],
                height=graph_data["height"],
                color=self._hex_to_rgba(graph_data["color"]),
                enabled=graph_data.get("enabled", True),
                min_value=graph_data.get("min_value", 0.0),
                max_value=graph_data.get("max_value", 100.0),
                show_value=graph_data.get("show_value", True),
                show_label=graph_data.get("show_label", True),
                label=graph_data.get("label", ""),
                metric_name=graph_data.get("metric_name", "cpu_usage"),
                orientation=graph_data.get("orientation", "vertical"),
                fill_color=self._hex_to_rgba(graph_data["fill_color"]) if "fill_color" in graph_data and graph_data["fill_color"] else None,
                background_color=self._hex_to_rgba(graph_data["background_color"]) if "background_color" in graph_data and graph_data["background_color"] else None,
                border_color=self._hex_to_rgba(graph_data["border_color"]) if "border_color" in graph_data and graph_data["border_color"] else None,
                show_border=graph_data.get("show_border", False),
                border_width=graph_data.get("border_width", 1),
                show_percentage=graph_data.get("show_percentage", True)
            )
            self.logger.debug(f"Created BarGraphConfig: min_value={config.min_value}, max_value={config.max_value}")
            return config
        except Exception as e:
            self.logger.error(f"Error parsing bar graph config: {e}")
            raise

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
        
        # Get path resolver
        path_resolver = get_path_resolver()
        
        # Parse metrics configurations
        metrics_configs = []
        if display_data["metrics"]["enabled"]:
            for metric_data in display_data["metrics"]["configs"]:
                if metric_data.get("enabled", True):
                    metrics_configs.append(self._parse_metric_config(metric_data))
        # Parse date configuration
        date_config = None
        if display_data["date"]["enabled"]:
            date_config = self._parse_text_config(display_data["date"])
        # Parse time configuration
        time_config = None
        if display_data["time"]["enabled"]:
            time_config = self._parse_text_config(display_data["time"])

        # Parse circular graph configurations
        circular_configs = []
        if "circular_graphs" in display_data and display_data["circular_graphs"]:
            for graph_data in display_data["circular_graphs"]:
                if graph_data.get("enabled", True):
                    circular_configs.append(self._parse_circular_graph_config(graph_data))

        # Parse bar graph configurations
        bar_configs = []
        if "bar_graphs" in display_data and display_data["bar_graphs"]:
            for graph_data in display_data["bar_graphs"]:
                if graph_data.get("enabled", True):
                    bar_configs.append(self._parse_bar_graph_config(graph_data))

        # Parse foreground configuration
        foreground_path = None
        foreground_position = (0, 0)
        foreground_alpha = 1.0
        if display_data["foreground"]["enabled"]:
            foreground_path = str(display_data["foreground"]["path"]).format(
                resolution=f"{width}{height}")
            # Resolve foreground path
            foreground_path = path_resolver.resolve_foreground_path(foreground_path, f"{width}{height}")
            foreground_position = (
                display_data["foreground"]["position"]["x"],
                display_data["foreground"]["position"]["y"]
            )
            foreground_alpha = display_data["foreground"]["alpha"]

        # Resolve background path
        background_path = path_resolver.resolve_background_path(display_data["background"]["path"])

        # Get rotation
        rotation = display_data.get("rotation", 0)

        config = DisplayConfig(
            output_width=width,
            output_height=height,
            background_path=background_path,
            background_type=BackgroundType(display_data["background"]["type"]),
            background_color=display_data["background"].get("color"),
            background_enabled=display_data["background"].get("enabled", True),
            global_font_path=display_data.get("font_family"),
            foreground_image_path=foreground_path,
            foreground_position=foreground_position,
            foreground_alpha=foreground_alpha,
            metrics_configs=metrics_configs,
            date_config=date_config,
            time_config=time_config,
            circular_configs=circular_configs,
            bar_configs=bar_configs,
            rotation=rotation
        )

        return config
