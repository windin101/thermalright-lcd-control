# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Tuple


class BackgroundType(Enum):
    """Supported background types"""
    IMAGE = "image"
    GIF = "gif"
    VIDEO = "video"
    IMAGE_COLLECTION = "image_collection"


@dataclass
class TextConfig:
    """Configuration for text display"""
    text: str = ""
    position: Tuple[int, int] = (0, 0)  # (x, y)
    font_size: int = 20
    color: Tuple[int, int, int, int] = (255, 255, 255, 255)  # RGBA
    enabled: bool = True


@dataclass
class DateConfig(TextConfig):
    """Configuration for date display with format options"""
    show_weekday: bool = True
    show_year: bool = False
    date_format: str = "default"  # default, short, numeric
    
    def get_format_string(self) -> str:
        """Build strftime format string based on options"""
        if self.date_format == "numeric":
            # e.g., 09/12/2025 or 09/12
            if self.show_year:
                return "%d/%m/%Y"
            else:
                return "%d/%m"
        elif self.date_format == "short":
            # e.g., Dec 9, 2025 or Tue Dec 9
            parts = []
            if self.show_weekday:
                parts.append("%a")
            parts.append("%b %-d")
            if self.show_year:
                parts.append("%Y")
            return " ".join(parts)
        else:  # default
            # e.g., Tuesday 9 December 2025
            parts = []
            if self.show_weekday:
                parts.append("%A")
            parts.append("%-d %B")
            if self.show_year:
                parts.append("%Y")
            return " ".join(parts)


@dataclass
class TimeConfig(TextConfig):
    """Configuration for time display with format options"""
    use_24_hour: bool = True
    show_seconds: bool = False
    show_am_pm: bool = False
    
    def get_format_string(self) -> str:
        """Build strftime format string based on options"""
        if self.use_24_hour:
            if self.show_seconds:
                return "%H:%M:%S"
            else:
                return "%H:%M"
        else:
            if self.show_seconds:
                fmt = "%I:%M:%S"
            else:
                fmt = "%I:%M"
            if self.show_am_pm:
                fmt += " %p"
            return fmt


class LabelPosition(Enum):
    """Position of label relative to value - grid-based with 12 positions"""
    # Legacy positions (for backward compatibility)
    LEFT = "left"          # Alias for LEFT_CENTER
    RIGHT = "right"        # Alias for RIGHT_CENTER
    ABOVE = "above"        # Alias for ABOVE_CENTER
    BELOW = "below"        # Alias for BELOW_CENTER
    NONE = "none"          # No label, just value
    
    # Above positions (label on top)
    ABOVE_LEFT = "above-left"
    ABOVE_CENTER = "above-center"
    ABOVE_RIGHT = "above-right"
    
    # Below positions (label on bottom)
    BELOW_LEFT = "below-left"
    BELOW_CENTER = "below-center"
    BELOW_RIGHT = "below-right"
    
    # Left positions (label on left side)
    LEFT_TOP = "left-top"
    LEFT_CENTER = "left-center"
    LEFT_BOTTOM = "left-bottom"
    
    # Right positions (label on right side)
    RIGHT_TOP = "right-top"
    RIGHT_CENTER = "right-center"
    RIGHT_BOTTOM = "right-bottom"


@dataclass
class MetricConfig:
    """Configuration for metric display"""
    name: str
    label: str = ""
    position: Tuple[int, int] = (0, 0)
    font_size: int = 16
    label_font_size: Optional[int] = None  # None means use font_size
    color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    format_string: str = "{label}{value}"
    unit: str = ""
    enabled: bool = True
    label_position: LabelPosition = LabelPosition.LEFT
    label_offset_x: int = 0  # Horizontal offset for label positioning
    label_offset_y: int = 0  # Vertical offset for label positioning
    freq_format: str = "mhz"  # Frequency format: "mhz" or "ghz"
    char_limit: int = 0  # Character limit for name metrics (0 = no limit)

    def get_label_font_size(self) -> int:
        """Get label font size (individual or same as value)"""
        return self.label_font_size if self.label_font_size else self.font_size

    def format_label(self):
        return f"{self.label}: " if self.label else ""


@dataclass
class BarGraphConfig:
    """Configuration for bar graph display"""
    metric_name: str  # Which metric to display (cpu_usage, gpu_temp, etc.)
    position: Tuple[int, int] = (0, 0)  # (x, y)
    width: int = 100  # Bar width in pixels
    height: int = 16  # Bar height in pixels
    orientation: str = "horizontal"  # horizontal or vertical
    rotation: int = 0  # Rotation angle in degrees (0-359)
    
    # Colors (themeable)
    fill_color: Tuple[int, int, int, int] = (0, 255, 0, 255)  # Green fill
    background_color: Tuple[int, int, int, int] = (50, 50, 50, 255)  # Dark gray
    border_color: Tuple[int, int, int, int] = (255, 255, 255, 255)  # White border
    
    # Gradient color mode - list of (threshold, (r, g, b, a)) tuples
    # Thresholds are 0-100 percentages
    use_gradient: bool = False  # Enable threshold-based color gradient
    gradient_colors: Optional[List[Tuple[float, Tuple[int, int, int, int]]]] = None
    # Default gradient when enabled: green (0%) -> yellow (50%) -> red (100%)
    
    # Style options
    show_border: bool = True
    border_width: int = 1
    corner_radius: int = 0  # 0 = square, >0 = rounded corners
    
    # Value range for normalization
    min_value: float = 0.0
    max_value: float = 100.0
    
    enabled: bool = True
    
    def __post_init__(self):
        """Initialize default gradient colors if not provided"""
        if self.gradient_colors is None:
            self.gradient_colors = [
                (0, (0, 255, 0, 255)),      # Green at 0%
                (50, (255, 255, 0, 255)),   # Yellow at 50%
                (100, (255, 0, 0, 255))     # Red at 100%
            ]


@dataclass
class CircularGraphConfig:
    """Configuration for circular/arc graph display"""
    metric_name: str  # Which metric to display (cpu_usage, gpu_temp, etc.)
    position: Tuple[int, int] = (0, 0)  # (x, y) - center of the arc
    radius: int = 40  # Radius in pixels
    thickness: int = 8  # Arc thickness in pixels
    start_angle: int = 135  # Start angle in degrees (0 = right, 90 = bottom)
    sweep_angle: int = 270  # Sweep angle in degrees (how much arc spans)
    rotation: int = 0  # Rotation angle for the entire arc (0-359)
    
    # Colors (themeable)
    fill_color: Tuple[int, int, int, int] = (0, 255, 0, 255)  # Green fill
    background_color: Tuple[int, int, int, int] = (50, 50, 50, 255)  # Dark gray
    border_color: Tuple[int, int, int, int] = (255, 255, 255, 255)  # White border
    
    # Gradient color mode - list of (threshold, (r, g, b, a)) tuples
    # Thresholds are 0-100 percentages
    use_gradient: bool = False  # Enable threshold-based color gradient
    gradient_colors: Optional[List[Tuple[float, Tuple[int, int, int, int]]]] = None
    # Default gradient when enabled: green (0%) -> yellow (50%) -> red (100%)
    
    # Style options
    show_border: bool = False
    border_width: int = 1
    
    # Value range for normalization
    min_value: float = 0.0
    max_value: float = 100.0
    
    enabled: bool = True
    
    def __post_init__(self):
        """Initialize default gradient colors if not provided"""
        if self.gradient_colors is None:
            self.gradient_colors = [
                (0, (0, 255, 0, 255)),      # Green at 0%
                (50, (255, 255, 0, 255)),   # Yellow at 50%
                (100, (255, 0, 0, 255))     # Red at 100%
            ]


@dataclass
class DisplayConfig:
    """Complete display configuration"""
    # Background (required)
    background_path: str
    background_type: BackgroundType

    # Output dimensions
    output_width: int = 320
    output_height: int = 240

    # Display rotation (0, 90, 180, 270 degrees)
    rotation: int = 0

    # Background scaling mode (stretch, scaled_fit, scaled_fill, centered, tiled)
    background_scale_mode: str = "stretch"

    # Background enabled (when False, shows background_color instead)
    background_enabled: bool = True

    # Background color (RGB tuple) used when background_enabled is False
    background_color: Tuple[int, int, int] = (0, 0, 0)

    # Background opacity (0.0 = transparent, 1.0 = opaque)
    background_alpha: float = 1.0

    # Global font configuration (applies to all text elements)
    global_font_path: Optional[str] = None

    # Foreground image (optional)
    foreground_image_path: Optional[str] = None
    foreground_position: Tuple[int, int] = (0, 0)
    foreground_alpha: float = 1.0  # 0.0 = transparent, 1.0 = opaque

    # Metrics configuration
    metrics_configs: List[MetricConfig] = None

    # Date configuration
    date_config: Optional['DateConfig'] = None

    # Time configuration
    time_config: Optional['TimeConfig'] = None

    # Custom text configuration
    text_configs: List['TextConfig'] = None

    # Bar graph configuration
    bar_configs: List['BarGraphConfig'] = None

    # Circular graph configuration
    circular_configs: List['CircularGraphConfig'] = None

    # LCD refresh interval in seconds (how often stats update)
    refresh_interval: float = 1.0

    # Text effects configuration
    # Shadow
    shadow_enabled: bool = False
    shadow_color: Tuple[int, int, int, int] = (0, 0, 0, 128)
    shadow_offset_x: int = 2
    shadow_offset_y: int = 2
    shadow_blur: int = 3
    
    # Outline
    outline_enabled: bool = False
    outline_color: Tuple[int, int, int, int] = (0, 0, 0, 255)
    outline_width: int = 1
    
    # Gradient
    gradient_enabled: bool = False
    gradient_color1: Tuple[int, int, int, int] = (255, 255, 255, 255)
    gradient_color2: Tuple[int, int, int, int] = (100, 100, 255, 255)
    gradient_direction: str = "vertical"  # vertical, horizontal, diagonal

    def __post_init__(self):
        if self.metrics_configs is None:
            self.metrics_configs = []

    @property
    def working_width(self) -> int:
        """Get working width (swapped for 90/270 degree rotation)"""
        if self.rotation in (90, 270):
            return self.output_height
        return self.output_width

    @property
    def working_height(self) -> int:
        """Get working height (swapped for 90/270 degree rotation)"""
        if self.rotation in (90, 270):
            return self.output_width
        return self.output_height
