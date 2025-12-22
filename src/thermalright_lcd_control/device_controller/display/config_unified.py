"""
Unified Config Classes - Minimal config classes for unified widget system.
No legacy dependencies.
"""
from dataclasses import dataclass
from typing import Tuple, List, Optional, Any
from enum import Enum


class ShapeType(Enum):
    """Shape types for unified system"""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    ROUNDED_RECTANGLE = "rounded_rectangle"


class LabelPosition(Enum):
    """Label positions for metrics"""
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


@dataclass
class DateConfig:
    """Date widget configuration"""
    position: Tuple[int, int]
    font_size: int
    color: Tuple[int, int, int, int]  # RGBA
    enabled: bool = True
    show_weekday: bool = True
    show_year: bool = False
    date_format: str = "default"


@dataclass
class TimeConfig:
    """Time widget configuration"""
    position: Tuple[int, int]
    font_size: int
    color: Tuple[int, int, int, int]  # RGBA
    enabled: bool = True
    use_24_hour: bool = True
    show_seconds: bool = False
    show_am_pm: bool = False


@dataclass
class MetricConfig:
    """Metric widget configuration"""
    position: Tuple[int, int]
    font_size: int
    color: Tuple[int, int, int, int]  # RGBA
    enabled: bool = True
    name: str = ""
    label: str = ""
    unit: str = ""
    label_position: LabelPosition = LabelPosition.RIGHT
    label_offset_x: int = 5
    label_offset_y: int = 0
    label_font_size: Optional[int] = None
    
    def __post_init__(self):
        if self.label_font_size is None:
            self.label_font_size = self.font_size


@dataclass
class TextConfig:
    """Text widget configuration"""
    position: Tuple[int, int]
    font_size: int
    color: Tuple[int, int, int, int]  # RGBA
    enabled: bool = True
    text: str = ""


@dataclass
class BarGraphConfig:
    """Bar graph configuration"""
    position: Tuple[int, int]
    width: int
    height: int
    color: Tuple[int, int, int, int]  # RGBA
    enabled: bool = True
    min_value: float = 0.0
    max_value: float = 100.0
    show_value: bool = True
    show_label: bool = True
    label: str = ""
    # Additional attributes for full functionality
    metric_name: str = "cpu_usage"
    orientation: str = "vertical"
    rotation: int = 0
    fill_color: Optional[Tuple[int, int, int, int]] = None
    background_color: Optional[Tuple[int, int, int, int]] = None
    border_color: Optional[Tuple[int, int, int, int]] = None
    show_border: bool = True
    border_width: int = 1
    corner_radius: int = 0
    show_percentage: bool = True


@dataclass
class CircularGraphConfig:
    """Circular graph configuration"""
    position: Tuple[int, int]
    radius: int
    color: Tuple[int, int, int, int]  # RGBA
    enabled: bool = True
    min_value: float = 0.0
    max_value: float = 100.0
    show_value: bool = True
    show_label: bool = True
    label: str = ""
    # Additional attributes for full functionality
    metric_name: str = "cpu_usage"
    thickness: int = 8
    start_angle: int = 135
    sweep_angle: int = 270
    rotation: int = 0
    fill_color: Optional[Tuple[int, int, int, int]] = None
    background_color: Optional[Tuple[int, int, int, int]] = None
    border_color: Optional[Tuple[int, int, int, int]] = None
    show_border: bool = False
    border_width: int = 1
    show_percentage: bool = True


@dataclass
class ShapeConfig:
    """Shape configuration"""
    position: Tuple[int, int]
    width: int
    height: int
    shape_type: ShapeType
    color: Tuple[int, int, int, int]  # RGBA
    enabled: bool = True
    filled: bool = True
    border_color: Optional[Tuple[int, int, int, int]] = None
    border_width: int = 1
    corner_radius: int = 0
    rotation: int = 0
    
    def __post_init__(self):
        if self.border_color is None:
            self.border_color = self.color


# YAML serialization support
import yaml

def shape_type_representer(dumper, data):
    return dumper.represent_str(data.value)

def label_position_representer(dumper, data):
    return dumper.represent_str(data.value)

yaml.add_representer(ShapeType, shape_type_representer)
yaml.add_representer(LabelPosition, label_position_representer)

def shape_type_constructor(loader, node):
    value = loader.construct_scalar(node)
    return ShapeType(value)

def label_position_constructor(loader, node):
    value = loader.construct_scalar(node)
    return LabelPosition(value)

yaml.add_constructor('!ShapeType', shape_type_constructor)
yaml.add_constructor('!LabelPosition', label_position_constructor)