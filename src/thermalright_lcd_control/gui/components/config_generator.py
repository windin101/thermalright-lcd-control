# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Configuration YAML generator"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from thermalright_lcd_control.common.logging_config import get_gui_logger


class ConfigGenerator:
    """Generates YAML configuration files from current UI state"""

    def __init__(self, config):
        self.config = config
        self.logger = get_gui_logger()

    def generate_config_data(self, preview_manager, text_style, metric_widgets,
                             date_widget, time_widget, text_widgets=None, bar_widgets=None, 
                             arc_widgets=None) -> Optional[dict]:
        """Generate YAML configuration file based on current preview state"""
        try:
            # Get scale factor for converting preview coordinates to device coordinates
            scale = getattr(preview_manager, 'preview_scale', 1.0)
            
            foreground_path = self._add_resolution_placeholder(preview_manager.current_foreground_path,
                                                               preview_manager.device_width,
                                                               preview_manager.device_height)
            foreground_pos = preview_manager.get_foreground_position()
            # Convert foreground position from preview to device coordinates
            foreground_x = int(foreground_pos[0] / scale)
            foreground_y = int(foreground_pos[1] / scale)
            bg_color = preview_manager.get_background_color()
            config_data = {
                "display": {
                    "rotation": preview_manager.current_rotation,
                    "refresh_interval": getattr(preview_manager, 'refresh_interval', 1.0),
                    "font_family": text_style.font_family,
                    "background": {
                        "enabled": preview_manager.is_background_enabled(),
                        "path": preview_manager.current_background_path or "",
                        "type": preview_manager.determine_background_type(preview_manager.current_background_path).value,
                        "scale_mode": preview_manager.get_background_scale_mode(),
                        "color": {"r": bg_color[0], "g": bg_color[1], "b": bg_color[2]},
                        "alpha": preview_manager.background_opacity
                    },
                    "foreground": {
                        "enabled": preview_manager.is_foreground_enabled() and preview_manager.current_foreground_path is not None,
                        "path": foreground_path,
                        "position": {"x": foreground_x, "y": foreground_y},
                        "alpha": preview_manager.foreground_opacity
                    },
                    "text_effects": {
                        "shadow": {
                            "enabled": text_style.shadow_enabled,
                            "color": self._qcolor_to_hex(text_style.shadow_color),
                            "offset_x": text_style.shadow_offset_x,
                            "offset_y": text_style.shadow_offset_y,
                            "blur": text_style.shadow_blur
                        },
                        "outline": {
                            "enabled": text_style.outline_enabled,
                            "color": self._qcolor_to_hex(text_style.outline_color),
                            "width": text_style.outline_width
                        },
                        "gradient": {
                            "enabled": text_style.gradient_enabled,
                            "color1": self._qcolor_to_hex(text_style.gradient_color1),
                            "color2": self._qcolor_to_hex(text_style.gradient_color2),
                            "direction": text_style.gradient_direction
                        }
                    },
                    "metrics": {
                        "enabled": any(widget.enabled for widget in metric_widgets.values()),
                        "configs": []
                    },
                    "date": self._create_date_time_config(date_widget, 310, 15, text_style, scale),
                    "time": self._create_date_time_config(time_widget, 310, 35, text_style, scale),
                    "custom_texts": [],
                    "bar_graphs": [],
                    "circular_graphs": []
                }
            }

            # Add metric configurations
            metric_format_defaults = {
                "cpu_frequency": "{label}{value}{unit}",
                "gpu_frequency": "{label}{value}{unit}"
            }

            for metric_name, widget in metric_widgets.items():
                if widget.enabled:  # Only enabled metrics
                    label = widget.get_label()
                    unit = widget.get_unit()
                    label_position = widget.get_label_position()
                    default_format = metric_format_defaults.get(metric_name, "{label}{value}{unit}")

                    # Convert position from preview to device coordinates
                    metric_config = {
                        "name": metric_name,
                        "label": label,
                        "label_position": label_position,
                        "enabled": widget.enabled,
                        "position": {"x": int(widget.pos().x() / scale), "y": int(widget.pos().y() / scale)},
                        "font_size": widget.get_font_size(),
                        "label_font_size": widget.get_label_font_size(),
                        "color": self._qcolor_to_hex(text_style.color),
                        "format_string": default_format,
                        "unit": unit
                    }
                    # Add frequency format for frequency metrics
                    if 'frequency' in metric_name and hasattr(widget, 'get_freq_format'):
                        metric_config["freq_format"] = widget.get_freq_format()
                    
                    config_data["display"]["metrics"]["configs"].append(metric_config)

            # Add custom text configurations
            if text_widgets:
                for text_name, widget in text_widgets.items():
                    if widget.enabled:
                        # Convert position from preview to device coordinates
                        text_config = {
                            "name": text_name,
                            "text": widget.get_text(),
                            "enabled": widget.enabled,
                            "position": {"x": int(widget.pos().x() / scale), "y": int(widget.pos().y() / scale)},
                            "font_size": widget.get_font_size(),
                            "color": self._qcolor_to_hex(text_style.color)
                        }
                        config_data["display"]["custom_texts"].append(text_config)

            # Add bar graph configurations
            if bar_widgets:
                for bar_name, widget in bar_widgets.items():
                    if widget.enabled:
                        # Convert position from preview to device coordinates
                        # Use get_position() which accounts for border padding
                        pos = widget.get_position()
                        bar_config = {
                            "name": bar_name,
                            "metric_name": widget.get_metric_name(),
                            "enabled": widget.enabled,
                            "position": {"x": int(pos[0] / scale), "y": int(pos[1] / scale)},
                            "width": widget.get_width(),
                            "height": widget.get_height(),
                            "orientation": widget.get_orientation(),
                            "fill_color": self._qcolor_to_hex(widget.get_fill_color()),
                            "background_color": self._qcolor_to_hex(widget.get_background_color()),
                            "border_color": self._qcolor_to_hex(widget.get_border_color()),
                            "show_border": widget.get_show_border(),
                            "border_width": widget.get_border_width(),
                            "corner_radius": widget.get_corner_radius(),
                            "min_value": widget.get_min_value(),
                            "max_value": widget.get_max_value()
                        }
                        config_data["display"]["bar_graphs"].append(bar_config)

            # Add circular graph configurations
            if arc_widgets:
                for arc_name, widget in arc_widgets.items():
                    if widget.enabled:
                        # Convert position from preview to device coordinates
                        pos = widget.get_position()
                        arc_config = {
                            "name": arc_name,
                            "metric_name": widget.get_metric_name(),
                            "enabled": widget.enabled,
                            "position": {"x": int(pos[0] / scale), "y": int(pos[1] / scale)},
                            "radius": widget.get_radius(),
                            "thickness": widget.get_thickness(),
                            "start_angle": widget.get_start_angle(),
                            "sweep_angle": widget.get_sweep_angle(),
                            "fill_color": self._qcolor_to_hex(widget.get_fill_color()),
                            "background_color": self._qcolor_to_hex(widget.get_background_color()),
                            "border_color": self._qcolor_to_hex(widget.get_border_color()),
                            "show_border": widget.get_show_border(),
                            "border_width": widget.get_border_width(),
                            "min_value": widget.get_min_value(),
                            "max_value": widget.get_max_value()
                        }
                        config_data["display"]["circular_graphs"].append(arc_config)

            return config_data

        except Exception as e:
            self.logger.error(f"Error generating config YAML: {e}")
            return None

    def generate_config_yaml(self, preview_manager, text_style, metric_widgets,
                             date_widget, time_widget, text_widgets=None, bar_widgets=None,
                             arc_widgets=None, preview: bool = False, existing_path: str = None) -> Optional[str]:
        """Generate YAML configuration file based on current preview state
        
        Args:
            existing_path: If provided, update this file instead of creating new one
        """
        try:
            self.logger.debug(f"generate_config_yaml called with preview={preview}, existing_path={existing_path}")
            config_data = self.generate_config_data(preview_manager, text_style, metric_widgets, date_widget,
                                                    time_widget, text_widgets, bar_widgets, arc_widgets)

            # Use device dimensions, not scaled preview dimensions
            services_config_path = self._get_service_config_file_path(preview_manager.device_width,
                                                                      preview_manager.device_height)
            self.logger.debug(f"Saving service config to: {services_config_path}")
            self._save_config_file(services_config_path, config_data)

            if not preview:
                # Save configuration - use existing path or generate new
                if existing_path:
                    config_path = Path(existing_path)
                else:
                    config_path = self._get_new_config_file_path(preview_manager.device_width,
                                                                 preview_manager.device_height)
                self.logger.debug(f"Saving theme config to: {config_path}")
                self._save_config_file(config_path, config_data)
                return f"{config_path.absolute()}"

        except Exception as e:
            self.logger.error(f"Error generating config YAML: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        return None

    def _create_date_time_config(self, widget, default_x, default_y, text_style, scale=1.0):
        """Create widget configuration dictionary"""
        # Convert position from preview to device coordinates
        if widget:
            x = int(widget.pos().x() / scale)
            y = int(widget.pos().y() / scale)
        else:
            x = default_x
            y = default_y
        
        config = {
            "enabled": widget.enabled if widget else False,
            "position": {
                "x": x,
                "y": y
            },
            "font_size": widget.get_font_size() if widget else text_style.font_size,
            "color": self._qcolor_to_hex(text_style.color),
            "text": ""
        }
        
        # Add date-specific options
        if widget and hasattr(widget, 'get_show_weekday'):
            config["show_weekday"] = widget.get_show_weekday()
            config["show_year"] = widget.get_show_year()
            config["date_format"] = widget.get_date_format()
        
        # Add time-specific options
        if widget and hasattr(widget, 'get_use_24_hour'):
            config["use_24_hour"] = widget.get_use_24_hour()
            config["show_seconds"] = widget.get_show_seconds()
            config["show_am_pm"] = widget.get_show_am_pm()
        
        return config

    def _qcolor_to_hex(self, qcolor):
        """Convert QColor to hex string with alpha"""
        r, g, b, a = qcolor.getRgb()
        return f"#{r:02X}{g:02X}{b:02X}{a:02X}"

    def _get_new_config_file_path(self, dev_width, dev_height) -> Path:
        """Generate new configuration file name and path based on current timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"config_{timestamp}.yaml"
        themes_dir = Path(f"{self.config.get('paths', {}).get('themes_dir', './themes')}/{dev_width}{dev_height}")
        # Ensure the themes directory exists
        themes_dir.mkdir(parents=True, exist_ok=True)
        return themes_dir / filename

    def _get_service_config_file_path(self, dev_width, dev_height) -> Optional[Path]:
        try:
            service_config_dir = self.config.get('paths', {}).get('service_config', './config')
            service_config_path = f"{service_config_dir}/config_{dev_width}{dev_height}.yaml"
            return Path(service_config_path)
        except Exception as e:
            self.logger.error(f"Error updating service config: {e}")
            return None

    def _save_config_file(self, config_path: Path, config_data: dict) -> str:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)

        return str(config_path)

    def _add_resolution_placeholder(self, path: str, width: int, height: int) -> Optional[str]:

        return path.replace(f"/{width}{height}/", "/{resolution}/") if path is not None else None
