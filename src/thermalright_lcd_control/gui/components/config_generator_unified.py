"""
Config Generator for Unified System
Generates YAML config from preview manager configs (not legacy widgets).
"""
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from thermalright_lcd_control.common.logging_config import get_gui_logger


class ConfigGeneratorUnified:
    """Generates YAML config from preview manager (unified system compatible)"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = get_gui_logger()
    
    def generate_config_yaml(self, preview_manager, text_style, preview: bool = False) -> Optional[str]:
        """Generate YAML config from preview manager"""
        try:
            config_data = self.generate_config_data(preview_manager, text_style)
            
            if not config_data:
                self.logger.error("generate_config_data returned None")
                return None
            
            # Save to service config path
            service_config_path = self._get_service_config_path(
                preview_manager.device_width, preview_manager.device_height
            )
            self._save_config_file(service_config_path, config_data)
            
            return str(service_config_path.absolute())
            
        except Exception as e:
            self.logger.error(f"Error generating config: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_theme_yaml(self, preview_manager, text_style, theme_name: str) -> Optional[str]:
        """Generate theme YAML file in themes directory"""
        try:
            config_data = self.generate_config_data(preview_manager, text_style)
            
            if not config_data:
                self.logger.error("generate_config_data returned None")
                return None
            
            # Convert paths to relative format for portability
            config_data = self._convert_paths_for_theme(config_data)
            
            # Save to themes directory
            theme_path = self._get_theme_config_path(
                preview_manager.device_width, preview_manager.device_height, theme_name
            )
            self._save_config_file(theme_path, config_data)
            
            return str(theme_path.absolute())
            
        except Exception as e:
            self.logger.error(f"Error generating theme: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_config_data(self, preview_manager, text_style) -> Optional[dict]:
        """Generate config dict from preview manager"""
        try:
            config_data = {
                "display": {
                    "rotation": preview_manager.current_rotation,
                    "refresh_interval": getattr(preview_manager, 'refresh_interval', 1.0),
                    "font_family": text_style.font_family,
                    "background": {
                        "enabled": preview_manager.is_background_enabled(),
                        "path": preview_manager.current_background_path or "",
                        "type": preview_manager.determine_background_type(
                            preview_manager.current_background_path
                        ).value if preview_manager.current_background_path else "color",
                        "scale_mode": preview_manager.get_background_scale_mode(),
                        "color": self._get_background_color(preview_manager),
                        "alpha": preview_manager.background_opacity
                    },
                    "foreground": {
                        "enabled": preview_manager.is_foreground_enabled() and preview_manager.current_foreground_path is not None,
                        "path": preview_manager.current_foreground_path or "",
                        "position": {"x": 0, "y": 0},
                        "alpha": preview_manager.foreground_opacity
                    },
                    "metrics": {
                        "enabled": len(preview_manager.metrics_configs) > 0,
                        "configs": []
                    },
                    "date": self._config_to_dict(preview_manager.date_config, "date") if preview_manager.date_config else {"enabled": False},
                    "time": self._config_to_dict(preview_manager.time_config, "time") if preview_manager.time_config else {"enabled": False},
                    "custom_texts": [],
                    "bar_graphs": [],
                    "circular_graphs": [],
                    "text_effects": {
                        "gradient": {
                            "enabled": getattr(text_style, 'gradient_enabled', False),
                            "color1": self._rgba_to_hex(getattr(text_style, 'gradient_color1', (255, 255, 255, 255))),
                            "color2": self._rgba_to_hex(getattr(text_style, 'gradient_color2', (107, 105, 108, 255))),
                            "direction": getattr(text_style, 'gradient_direction', 'vertical')
                        },
                        "outline": {
                            "enabled": getattr(text_style, 'outline_enabled', False),
                            "color": self._rgba_to_hex(getattr(text_style, 'outline_color', (0, 0, 0, 255))),
                            "width": getattr(text_style, 'outline_width', 1)
                        },
                        "shadow": {
                            "enabled": getattr(text_style, 'shadow_enabled', False),
                            "color": self._rgba_to_hex(getattr(text_style, 'shadow_color', (0, 0, 0, 128))),
                            "offset_x": getattr(text_style, 'shadow_offset_x', 2),
                            "offset_y": getattr(text_style, 'shadow_offset_y', 2),
                            "blur": getattr(text_style, 'shadow_blur', 3)
                        }
                    }
                }
            }
            
            # Add metrics if any
            for metric_config in preview_manager.metrics_configs:
                config_data["display"]["metrics"]["configs"].append(
                    self._config_to_dict(metric_config, "metric")
                )
            
            return config_data
            
        except Exception as e:
            self.logger.error(f"Error generating config data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _config_to_dict(self, config, config_type: str) -> dict:
        """Convert config object to dict"""
        if config_type == "date":
            return {
                "enabled": config.enabled,
                "position": {"x": config.position[0], "y": config.position[1]},
                "font_size": config.font_size,
                "color": self._rgba_to_hex(config.color),
                "show_weekday": getattr(config, 'show_weekday', True),
                "show_year": getattr(config, 'show_year', False),
                "date_format": getattr(config, 'date_format', 'default'),
                "text": ""
            }
        elif config_type == "time":
            return {
                "enabled": config.enabled,
                "position": {"x": config.position[0], "y": config.position[1]},
                "font_size": config.font_size,
                "color": self._rgba_to_hex(config.color),
                "use_24_hour": getattr(config, 'use_24_hour', True),
                "show_seconds": getattr(config, 'show_seconds', False),
                "show_am_pm": getattr(config, 'show_am_pm', False),
                "text": ""
            }
        elif config_type == "metric":
            return {
                "name": getattr(config, 'name', ''),
                "enabled": config.enabled,
                "position": {"x": config.position[0], "y": config.position[1]},
                "font_size": config.font_size,
                "color": self._rgba_to_hex(config.color),
                "label": getattr(config, 'label', ''),
                "unit": getattr(config, 'unit', ''),

                "format_string": getattr(config, 'format_string', '{label}{value}{unit}'),
                "label_position": getattr(config, 'label_position', 'right'),
                "label_offset_x": getattr(config, 'label_offset_x', 5),
                "label_offset_y": getattr(config, 'label_offset_y', 0),
                "label_font_size": getattr(config, 'label_font_size', config.font_size)
            }
        return {"enabled": False}
    
    def _rgba_to_hex(self, rgba: tuple) -> str:
        """Convert RGBA to hex string"""
        if len(rgba) == 4:
            return f"#{rgba[0]:02x}{rgba[1]:02x}{rgba[2]:02x}{rgba[3]:02x}"
        elif len(rgba) == 3:
            return f"#{rgba[0]:02x}{rgba[1]:02x}{rgba[2]:02x}"
        return "#FFFFFFFF"
    
    def _get_service_config_path(self, width: int, height: int) -> Path:
        """Get service config file path"""
        try:
            service_config_dir = self.config.get('paths', {}).get('service_config', './config')
            service_config_path = f"{service_config_dir}/config_{width}{height}.yaml"
            return Path(service_config_path)
        except Exception as e:
            self.logger.error(f"Error getting service config path: {e}")
            return Path("./config/config_320240.yaml")
    
    def _get_theme_config_path(self, width: int, height: int, theme_name: str) -> Path:
        """Get theme config file path"""
        try:
            themes_dir = self.config.get('paths', {}).get('themes_dir', './themes')
            theme_config_path = f"{themes_dir}/{width}{height}/{theme_name}.yaml"
            return Path(theme_config_path)
        except Exception as e:
            self.logger.error(f"Error getting theme config path: {e}")
            return Path(f"./themes/{width}{height}/{theme_name}.yaml")
    
    def _save_config_file(self, config_path: Path, config_data: dict):
        """Save config dict to YAML file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)

    @staticmethod
    def _get_background_color(preview_manager):
        """Get background color from preview manager"""
        # Check if preview_manager has background_color attribute
        if hasattr(preview_manager, 'background_color') and preview_manager.background_color:
            color = preview_manager.background_color
            
            # Handle different color formats
            if isinstance(color, dict):
                # Already in dict format {r: 0, g: 0, b: 0}
                return color
            elif hasattr(color, 'getRgb'):  # QColor
                r, g, b, a = color.getRgb()
                return {"r": r, "g": g, "b": b}
            elif isinstance(color, (list, tuple)) and len(color) >= 3:
                # RGB or RGBA tuple
                return {"r": color[0], "g": color[1], "b": color[2]}
        
        # Default black
        return {"r": 0, "g": 0, "b": 0}
    
    def _convert_paths_for_theme(self, config_data: dict) -> dict:
        """Convert absolute paths to relative format for theme portability"""
        from thermalright_lcd_control.gui.utils.path_resolver import get_path_resolver
        
        path_resolver = get_path_resolver()
        resources_root = path_resolver.get_resources_root()
        
        # Convert background path
        if config_data["display"]["background"]["path"]:
            bg_path = config_data["display"]["background"]["path"]
            # Convert to relative path from resources root
            try:
                bg_path_obj = Path(bg_path)
                if bg_path_obj.is_absolute() and bg_path_obj.exists():
                    # Make relative to resources root
                    relative_path = bg_path_obj.relative_to(resources_root)
                    # Convert to the standard theme format
                    config_data["display"]["background"]["path"] = f"/usr/share/thermalright-lcd-control/themes/{relative_path}"
                elif bg_path.startswith(str(resources_root)):
                    # Already relative to resources, convert to theme format
                    relative_path = bg_path.replace(str(resources_root), "").lstrip("/")
                    config_data["display"]["background"]["path"] = f"/usr/share/thermalright-lcd-control/themes/{relative_path}"
            except (ValueError, OSError):
                # Keep original path if conversion fails
                pass
        
        # Convert foreground path
        if config_data["display"]["foreground"]["path"]:
            fg_path = config_data["display"]["foreground"]["path"]
            # Convert to relative path from resources root
            try:
                fg_path_obj = Path(fg_path)
                if fg_path_obj.is_absolute() and fg_path_obj.exists():
                    # Make relative to resources root
                    relative_path = fg_path_obj.relative_to(resources_root)
                    # Convert to the standard theme format
                    config_data["display"]["foreground"]["path"] = f"/usr/share/thermalright-lcd-control/themes/{relative_path}"
                elif fg_path.startswith(str(resources_root)):
                    # Already relative to resources, convert to theme format
                    relative_path = fg_path.replace(str(resources_root), "").lstrip("/")
                    config_data["display"]["foreground"]["path"] = f"/usr/share/thermalright-lcd-control/themes/{relative_path}"
            except (ValueError, OSError):
                # Keep original path if conversion fails
                pass
        
        return config_data
