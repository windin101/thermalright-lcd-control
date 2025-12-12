# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from PIL import ImageDraw, ImageFont, ImageFilter, Image

from thermalright_lcd_control.device_controller.display.config import TextConfig, MetricConfig, DisplayConfig, LabelPosition, DateConfig, TimeConfig, BarGraphConfig, CircularGraphConfig, ShapeConfig, ShapeType
from thermalright_lcd_control.common.logging_config import LoggerConfig

# Import font manager from current package
try:
    from .font_manager import get_font_manager
except ImportError:
    # Fallback if font_manager is not available
    class FallbackFontManager:
        def get_font(self, font_size: int) -> ImageFont.ImageFont:
            return ImageFont.load_default(font_size)


    def get_font_manager():
        return FallbackFontManager()


def _interpolate_gradient_color(normalized_value: float, gradient_colors: List[Tuple[float, Tuple[int, int, int, int]]]) -> Tuple[int, int, int, int]:
    """
    Interpolate color based on normalized value (0-1) and gradient thresholds.
    
    Args:
        normalized_value: Value between 0 and 1
        gradient_colors: List of (threshold, (r, g, b, a)) tuples, sorted by threshold
                        Thresholds are 0-100 percentages
    
    Returns:
        Interpolated (r, g, b, a) tuple
    """
    if not gradient_colors or len(gradient_colors) < 2:
        return (0, 255, 0, 255)  # Default green
    
    # Convert normalized (0-1) to percentage (0-100)
    percent = normalized_value * 100.0
    
    # Find the two colors to interpolate between
    lower_color = gradient_colors[0]
    upper_color = gradient_colors[-1]
    
    for i, (threshold, color) in enumerate(gradient_colors):
        if percent <= threshold:
            upper_color = (threshold, color)
            if i > 0:
                lower_color = gradient_colors[i - 1]
            else:
                lower_color = (threshold, color)
            break
        lower_color = (threshold, color)
    
    # If same threshold, return the color directly
    if lower_color[0] == upper_color[0]:
        c = lower_color[1]
        return (c[0], c[1], c[2], c[3] if len(c) > 3 else 255)
    
    # Linear interpolation between the two colors
    t = (percent - lower_color[0]) / (upper_color[0] - lower_color[0])
    t = max(0.0, min(1.0, t))
    
    r1, g1, b1 = lower_color[1][0], lower_color[1][1], lower_color[1][2]
    a1 = lower_color[1][3] if len(lower_color[1]) > 3 else 255
    r2, g2, b2 = upper_color[1][0], upper_color[1][1], upper_color[1][2]
    a2 = upper_color[1][3] if len(upper_color[1]) > 3 else 255
    
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    a = int(a1 + (a2 - a1) * t)
    
    return (r, g, b, a)


class TextRenderer:
    """Text rendering manager for images with global font support"""

    def __init__(self, display_config: DisplayConfig):
        self.logger = LoggerConfig.setup_service_logger()
        self.font_manager = get_font_manager()
        self._font_cache = {}
        # Store previous text bounding boxes for clearing
        self._prev_text_bounds = {}
        # Store display config for text effects
        self.display_config = display_config

    def _get_font(self, font_size: int, font_name: str = None, bold: bool = False) -> ImageFont.ImageFont:
        """Get a font with optional family name and bold style"""
        return self.font_manager.get_font(font_size, font_name, bold)

    def _draw_text_with_effects(self, draw: ImageDraw.Draw, image: Image.Image, 
                                 position: tuple, text: str, font: ImageFont.ImageFont, 
                                 fill: tuple, use_gradient: bool = True):
        """Draw text with shadow, outline, and gradient effects if enabled
        
        Args:
            use_gradient: If False, skip global gradient and use solid fill color instead
        """
        x, y = position
        
        # Draw shadow first (behind everything)
        if self.display_config.shadow_enabled:
            shadow_x = x + self.display_config.shadow_offset_x
            shadow_y = y + self.display_config.shadow_offset_y
            shadow_color = self.display_config.shadow_color
            
            if self.display_config.shadow_blur > 0:
                # Create shadow on temporary image for blur effect
                bbox = draw.textbbox(position, text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Calculate offset from position to bbox top-left
                offset_x = bbox[0] - x
                offset_y = bbox[1] - y
                
                padding = self.display_config.shadow_blur * 2 + abs(self.display_config.shadow_offset_x) + abs(self.display_config.shadow_offset_y)
                shadow_img = Image.new('RGBA', (text_width + padding * 2, text_height + padding * 2), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_img)
                # Draw text at padding offset, accounting for bbox offset
                shadow_draw.text((padding - offset_x, padding - offset_y), text, fill=shadow_color, font=font)
                shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=self.display_config.shadow_blur))
                # Paste shadow onto main image at correct position
                paste_x = shadow_x + offset_x - padding
                paste_y = shadow_y + offset_y - padding
                image.paste(shadow_img, (int(paste_x), int(paste_y)), shadow_img)
            else:
                draw.text((shadow_x, shadow_y), text, fill=shadow_color, font=font)
        
        # Draw outline (behind main text)
        if self.display_config.outline_enabled:
            outline_color = self.display_config.outline_color
            outline_width = self.display_config.outline_width
            # Draw text at multiple offsets to create outline
            for ox in range(-outline_width, outline_width + 1):
                for oy in range(-outline_width, outline_width + 1):
                    if ox != 0 or oy != 0:
                        draw.text((x + ox, y + oy), text, fill=outline_color, font=font)
        
        # Draw main text (with gradient if enabled and widget allows it)
        if self.display_config.gradient_enabled and use_gradient:
            # Create gradient text
            bbox = draw.textbbox(position, text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate offset from position to bbox top-left
            # textbbox returns absolute coordinates, so we need the offset
            offset_x = bbox[0] - x
            offset_y = bbox[1] - y
            
            if text_width > 0 and text_height > 0:
                # Create text mask - draw text at origin offset to match bbox
                padding = 4
                text_img = Image.new('RGBA', (text_width + padding, text_height + padding), (0, 0, 0, 0))
                text_draw = ImageDraw.Draw(text_img)
                # Draw text at padding/2 offset, accounting for bbox offset
                text_draw.text((padding // 2 - offset_x, padding // 2 - offset_y), text, fill=(255, 255, 255, 255), font=font, anchor=None)
                
                # Create gradient
                gradient_img = Image.new('RGBA', (text_width + padding, text_height + padding), (0, 0, 0, 0))
                c1 = self.display_config.gradient_color1
                c2 = self.display_config.gradient_color2
                
                for i in range(text_height + padding):
                    if self.display_config.gradient_direction == "vertical":
                        ratio = i / max(1, text_height + padding - 1)
                    elif self.display_config.gradient_direction == "horizontal":
                        ratio = 0.5  # Will be overridden per pixel
                    else:  # diagonal
                        ratio = i / max(1, text_height + padding - 1)
                    
                    r = int(c1[0] + (c2[0] - c1[0]) * ratio)
                    g = int(c1[1] + (c2[1] - c1[1]) * ratio)
                    b = int(c1[2] + (c2[2] - c1[2]) * ratio)
                    a = int(c1[3] + (c2[3] - c1[3]) * ratio)
                    
                    for j in range(text_width + padding):
                        if self.display_config.gradient_direction == "horizontal":
                            ratio = j / max(1, text_width + padding - 1)
                            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
                            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
                            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
                            a = int(c1[3] + (c2[3] - c1[3]) * ratio)
                        elif self.display_config.gradient_direction == "diagonal":
                            ratio = (i + j) / max(1, text_height + text_width + padding * 2 - 2)
                            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
                            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
                            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
                            a = int(c1[3] + (c2[3] - c1[3]) * ratio)
                        gradient_img.putpixel((j, i), (r, g, b, a))
                
                # Apply text as mask to gradient
                gradient_img.putalpha(text_img.split()[3])
                
                # Paste gradient text onto main image at bbox position
                paste_x = bbox[0] - padding // 2
                paste_y = bbox[1] - padding // 2
                image.paste(gradient_img, (int(paste_x), int(paste_y)), gradient_img)
            else:
                # Fallback to regular text
                draw.text(position, text, fill=fill, font=font)
        else:
            # Regular text
            draw.text(position, text, fill=fill, font=font)

    def _clear_text_area(self, draw: ImageDraw.Draw, key: str, position: tuple, text: str, font: ImageFont.ImageFont, background_color=None):
        """Clear the previous text area before drawing new text to prevent smearing"""
        # Get the bounding box for the new text
        bbox = draw.textbbox(position, text, font=font)
        # Add some padding to ensure complete clearing
        new_bounds = (bbox[0] - 1, bbox[1] - 1, bbox[2] + 2, bbox[3] + 2)
        
        # Get previous bounds for this text element
        prev_bounds = self._prev_text_bounds.get(key)
        
        if prev_bounds:
            # Calculate the union of old and new bounds to clear any remnants
            clear_bounds = (
                min(prev_bounds[0], new_bounds[0]),
                min(prev_bounds[1], new_bounds[1]),
                max(prev_bounds[2], new_bounds[2]),
                max(prev_bounds[3], new_bounds[3])
            )
            # Note: We don't actually draw here - the background is already fresh each frame
            # This tracking is for future optimization if needed
        
        # Store new bounds for next frame
        self._prev_text_bounds[key] = new_bounds

    def _safe_format_value(self, value: Any, format_string: str, metric_name: str) -> str:
        """Safely format a metric value, handling various types and potential errors"""
        if value is None:
            return "N/A"

        try:
            # Try to convert to float if it's a string representation of a number
            if isinstance(value, str):
                try:
                    value = float(value)
                except ValueError:
                    # If conversion fails, return the string as-is (e.g., cpu_name, gpu_name)
                    return value

            # If it's already a number, format based on metric type
            if isinstance(value, (int, float)):
                # Temperature and usage metrics - whole numbers
                if any(x in metric_name for x in ['temperature', 'usage', 'percent']):
                    return f"{int(round(value))}"
                # Frequency metrics - 2 decimal places (for MHz display)
                elif 'frequency' in metric_name:
                    return f"{value:.2f}"
                # RAM/VRAM total - 1 decimal place for GB
                elif metric_name in ['ram_total', 'ram_used', 'gpu_mem_total', 'gpu_mem_used']:
                    return f"{value:.1f}"
                # Check if the format string contains decimal formatting
                elif '.0f' in format_string or '.1f' in format_string or '.2f' in format_string:
                    return format_string.format(value=value)
                else:
                    # Default: convert to string
                    return str(int(value)) if value == int(value) else str(value)

            # For any other type, convert to string
            return str(value)

        except Exception as e:
            self.logger.warning(f"Error formatting value {value} for metric {metric_name}: {e}")
            return str(value) if value is not None else "N/A"

    def render_metrics(self, draw: ImageDraw.Draw, image: Image.Image, metrics: Optional[Dict[str, Any]],
                       configs: List[MetricConfig]):
        """Display metrics on the image"""
        if not metrics or not configs:
            return

        for config in configs:
            if not config.enabled:
                continue

            # Get metric value - use "N/A" if not available instead of skipping
            value = metrics.get(config.name)
            if value is None:
                value = "N/A"

            # Apply character limit for name metrics (cpu_name, gpu_name)
            char_limit = getattr(config, 'char_limit', 0)
            if char_limit > 0 and config.name in ['cpu_name', 'gpu_name']:
                value = str(value)[:char_limit]

            # Apply frequency conversion if needed (only for valid numeric values)
            is_ghz_format = 'frequency' in config.name and hasattr(config, 'freq_format') and config.freq_format == 'ghz'
            if is_ghz_format:
                try:
                    # Value is in MHz, convert to GHz
                    mhz_value = float(value)
                    value = mhz_value / 1000.0
                except (ValueError, TypeError):
                    pass

            # Get fonts - separate for value and label, using per-config font settings
            font_name = getattr(config, 'font_name', None)
            bold = getattr(config, 'bold', False)
            use_gradient = getattr(config, 'use_gradient', True)
            value_font = self._get_font(config.font_size, font_name, bold)
            label_font = self._get_font(config.get_label_font_size(), font_name, bold)
            
            # Format the value part - use 2 decimal places for GHz
            if is_ghz_format and isinstance(value, float):
                formatted_value = f"{value:.2f}"
            else:
                formatted_value = self._safe_format_value(value, "{value}", config.name)
            value_text = f"{formatted_value}{config.unit}"
            label_text = config.label if config.label else ""
            
            # Get label position and offsets
            label_pos = getattr(config, 'label_position', LabelPosition.LEFT)
            offset_x = getattr(config, 'label_offset_x', 0)
            offset_y = getattr(config, 'label_offset_y', 0)
            
            # Calculate text dimensions
            label_bbox = draw.textbbox((0, 0), label_text, font=label_font) if label_text else (0, 0, 0, 0)
            value_bbox = draw.textbbox((0, 0), value_text, font=value_font)
            label_width = label_bbox[2] - label_bbox[0]
            label_height = label_bbox[3] - label_bbox[1]
            value_width = value_bbox[2] - value_bbox[0]
            value_height = value_bbox[3] - value_bbox[1]
            
            # Base position
            base_x, base_y = config.position
            
            # Render based on label position
            if label_pos == LabelPosition.NONE or not label_text:
                # Just render value with unit
                self._draw_text_with_effects(draw, image, config.position, value_text, value_font, config.color, use_gradient)
            
            # === ABOVE positions (label on top, value below) ===
            elif label_pos in (LabelPosition.ABOVE, LabelPosition.ABOVE_CENTER):
                # Center alignment
                max_width = max(label_width, value_width)
                label_x = base_x + (max_width - label_width) // 2 + offset_x
                value_x = base_x + (max_width - value_width) // 2
                self._draw_text_with_effects(draw, image, (label_x, base_y + offset_y), label_text, label_font, config.color, use_gradient)
                self._draw_text_with_effects(draw, image, (value_x, base_y + label_height + 2), value_text, value_font, config.color, use_gradient)
            
            elif label_pos == LabelPosition.ABOVE_LEFT:
                # Left alignment
                label_x = base_x + offset_x
                value_x = base_x
                self._draw_text_with_effects(draw, image, (label_x, base_y + offset_y), label_text, label_font, config.color, use_gradient)
                self._draw_text_with_effects(draw, image, (value_x, base_y + label_height + 2), value_text, value_font, config.color, use_gradient)
            
            elif label_pos == LabelPosition.ABOVE_RIGHT:
                # Right alignment
                max_width = max(label_width, value_width)
                label_x = base_x + max_width - label_width + offset_x
                value_x = base_x + max_width - value_width
                self._draw_text_with_effects(draw, image, (label_x, base_y + offset_y), label_text, label_font, config.color, use_gradient)
                self._draw_text_with_effects(draw, image, (value_x, base_y + label_height + 2), value_text, value_font, config.color, use_gradient)
            
            # === BELOW positions (value on top, label below) ===
            elif label_pos in (LabelPosition.BELOW, LabelPosition.BELOW_CENTER):
                # Center alignment
                max_width = max(label_width, value_width)
                value_x = base_x + (max_width - value_width) // 2
                label_x = base_x + (max_width - label_width) // 2 + offset_x
                self._draw_text_with_effects(draw, image, (value_x, base_y), value_text, value_font, config.color, use_gradient)
                self._draw_text_with_effects(draw, image, (label_x, base_y + value_height + 2 + offset_y), label_text, label_font, config.color, use_gradient)
            
            elif label_pos == LabelPosition.BELOW_LEFT:
                # Left alignment
                value_x = base_x
                label_x = base_x + offset_x
                self._draw_text_with_effects(draw, image, (value_x, base_y), value_text, value_font, config.color, use_gradient)
                self._draw_text_with_effects(draw, image, (label_x, base_y + value_height + 2 + offset_y), label_text, label_font, config.color, use_gradient)
            
            elif label_pos == LabelPosition.BELOW_RIGHT:
                # Right alignment
                max_width = max(label_width, value_width)
                value_x = base_x + max_width - value_width
                label_x = base_x + max_width - label_width + offset_x
                self._draw_text_with_effects(draw, image, (value_x, base_y), value_text, value_font, config.color, use_gradient)
                self._draw_text_with_effects(draw, image, (label_x, base_y + value_height + 2 + offset_y), label_text, label_font, config.color, use_gradient)
            
            # === LEFT positions (label on left, value on right) ===
            elif label_pos in (LabelPosition.LEFT, LabelPosition.LEFT_CENTER):
                # Vertically centered
                max_height = max(label_height, value_height)
                label_y = base_y + (max_height - label_height) // 2 + offset_y
                value_y = base_y + (max_height - value_height) // 2
                label_with_colon = f"{label_text}: "
                label_colon_bbox = draw.textbbox((0, 0), label_with_colon, font=label_font)
                label_colon_width = label_colon_bbox[2] - label_colon_bbox[0]
                self._draw_text_with_effects(draw, image, (base_x + offset_x, label_y), label_with_colon, label_font, config.color, use_gradient)
                self._draw_text_with_effects(draw, image, (base_x + label_colon_width + offset_x, value_y), value_text, value_font, config.color, use_gradient)
            
            elif label_pos == LabelPosition.LEFT_TOP:
                # Top aligned
                label_with_colon = f"{label_text}: "
                label_colon_bbox = draw.textbbox((0, 0), label_with_colon, font=label_font)
                label_colon_width = label_colon_bbox[2] - label_colon_bbox[0]
                self._draw_text_with_effects(draw, image, (base_x + offset_x, base_y + offset_y), label_with_colon, label_font, config.color, use_gradient)
                self._draw_text_with_effects(draw, image, (base_x + label_colon_width + offset_x, base_y), value_text, value_font, config.color, use_gradient)
            
            elif label_pos == LabelPosition.LEFT_BOTTOM:
                # Bottom aligned
                max_height = max(label_height, value_height)
                label_y = base_y + max_height - label_height + offset_y
                value_y = base_y + max_height - value_height
                label_with_colon = f"{label_text}: "
                label_colon_bbox = draw.textbbox((0, 0), label_with_colon, font=label_font)
                label_colon_width = label_colon_bbox[2] - label_colon_bbox[0]
                self._draw_text_with_effects(draw, image, (base_x + offset_x, label_y), label_with_colon, label_font, config.color, use_gradient)
                self._draw_text_with_effects(draw, image, (base_x + label_colon_width + offset_x, value_y), value_text, value_font, config.color, use_gradient)
            
            # === RIGHT positions (value on left, label on right) ===
            elif label_pos in (LabelPosition.RIGHT, LabelPosition.RIGHT_CENTER):
                # Vertically centered
                max_height = max(label_height, value_height)
                value_y = base_y + (max_height - value_height) // 2
                label_y = base_y + (max_height - label_height) // 2 + offset_y
                self._draw_text_with_effects(draw, image, (base_x, value_y), value_text, value_font, config.color, use_gradient)
                self._draw_text_with_effects(draw, image, (base_x + value_width + offset_x, label_y), f" :{label_text}", label_font, config.color, use_gradient)
            
            elif label_pos == LabelPosition.RIGHT_TOP:
                # Top aligned
                self._draw_text_with_effects(draw, image, (base_x, base_y), value_text, value_font, config.color, use_gradient)
                self._draw_text_with_effects(draw, image, (base_x + value_width + offset_x, base_y + offset_y), f" :{label_text}", label_font, config.color, use_gradient)
            
            elif label_pos == LabelPosition.RIGHT_BOTTOM:
                # Bottom aligned
                max_height = max(label_height, value_height)
                value_y = base_y + max_height - value_height
                label_y = base_y + max_height - label_height + offset_y
                self._draw_text_with_effects(draw, image, (base_x, value_y), value_text, value_font, config.color, use_gradient)
                self._draw_text_with_effects(draw, image, (base_x + value_width + offset_x, label_y), f" :{label_text}", label_font, config.color, use_gradient)
            
            else:
                # Fallback - use old format string method with value font
                try:
                    text = config.format_string.format(
                        label=config.format_label(),
                        value=formatted_value,
                        unit=config.unit
                    )
                except Exception as e:
                    self.logger.warning(f"Error formatting metric {config.name}: {e}")
                    text = f"{label_text}: {value_text}"
                self._draw_text_with_effects(draw, image, config.position, text, value_font, config.color, use_gradient)

    def render_date(self, draw: ImageDraw.Draw, image: Image.Image, config: Optional[DateConfig], now: datetime = None):
        """Display current date with configurable format"""
        if not config or not config.enabled:
            return

        # Use provided datetime to avoid multiple calls
        if now is None:
            now = datetime.now()
        
        # Get format string from config (supports DateConfig or fallback for TextConfig)
        if hasattr(config, 'get_format_string'):
            format_str = config.get_format_string()
        else:
            format_str = "%A %-d %B"  # Default format
        
        current_date = now.strftime(format_str)

        # Get font using per-widget font configuration
        font_name = getattr(config, 'font_name', None)
        bold = getattr(config, 'bold', False)
        font = self._get_font(config.font_size, font_name, bold)

        # Check if widget wants to use gradient (default True for backward compat)
        use_gradient = getattr(config, 'use_gradient', True)

        # Draw text with effects
        self._draw_text_with_effects(draw, image, config.position, current_date, font, config.color, use_gradient)

    def render_time(self, draw: ImageDraw.Draw, image: Image.Image, config: Optional[TimeConfig], now: datetime = None):
        """Display current time with configurable format"""
        if not config or not config.enabled:
            return

        # Use provided datetime to avoid multiple calls
        if now is None:
            now = datetime.now()
        
        # Get format string from config (supports TimeConfig or fallback for TextConfig)
        if hasattr(config, 'get_format_string'):
            format_str = config.get_format_string()
        else:
            format_str = "%H:%M"  # Default format
        
        current_time = now.strftime(format_str)

        # Get font using per-widget font configuration
        font_name = getattr(config, 'font_name', None)
        bold = getattr(config, 'bold', False)
        font = self._get_font(config.font_size, font_name, bold)

        # Check if widget wants to use gradient (default True for backward compat)
        use_gradient = getattr(config, 'use_gradient', True)

        # Draw text with effects
        self._draw_text_with_effects(draw, image, config.position, current_time, font, config.color, use_gradient)

    def render_custom_text(self, draw: ImageDraw.Draw, image: Image.Image, config: TextConfig):
        """Display custom text"""
        if not config.enabled or not config.text:
            return

        # Get font using per-widget font configuration
        font_name = getattr(config, 'font_name', None)
        bold = getattr(config, 'bold', False)
        font = self._get_font(config.font_size, font_name, bold)

        # Check if widget wants to use gradient (default True for backward compat)
        use_gradient = getattr(config, 'use_gradient', True)

        # Draw text with effects
        self._draw_text_with_effects(draw, image, config.position, config.text, font, config.color, use_gradient)

    def render_bar_graphs(self, draw: ImageDraw.Draw, image: Image.Image, 
                          metrics: Optional[Dict[str, Any]], configs: List[BarGraphConfig]):
        """Render bar graphs for metrics"""
        if not metrics or not configs:
            return

        for config in configs:
            if not config.enabled:
                continue

            # Get metric value
            value = metrics.get(config.metric_name)
            if value is None:
                continue

            # Normalize value to 0-1 range
            try:
                normalized = (float(value) - config.min_value) / (config.max_value - config.min_value)
                normalized = max(0.0, min(1.0, normalized))  # Clamp to 0-1
            except (ValueError, ZeroDivisionError):
                normalized = 0.0

            x, y = config.position
            w, h = config.width, config.height
            rotation = getattr(config, 'rotation', 0)

            # If rotation is non-zero, render to a temp image and rotate
            if rotation != 0:
                self._render_rotated_bar(image, config, normalized, x, y, w, h, rotation)
            else:
                self._render_bar_direct(draw, config, normalized, x, y, w, h)

    def _render_bar_direct(self, draw: ImageDraw.Draw, config: BarGraphConfig,
                           normalized: float, x: int, y: int, w: int, h: int):
        """Render bar graph directly (no rotation)"""
        # Draw background
        if config.corner_radius > 0:
            self._draw_rounded_rect(draw, x, y, w, h, config.corner_radius, config.background_color)
        else:
            draw.rectangle([x, y, x + w, y + h], fill=config.background_color)

        # Determine fill color (use gradient if enabled)
        if config.use_gradient and config.gradient_colors:
            fill_color = _interpolate_gradient_color(normalized, config.gradient_colors)
        else:
            fill_color = config.fill_color

        # Draw filled portion
        if normalized > 0:
            if config.orientation == "horizontal":
                fill_width = int(w * normalized)
                if fill_width > 0:
                    if config.corner_radius > 0:
                        self._draw_rounded_rect(draw, x, y, fill_width, h, 
                                               min(config.corner_radius, fill_width // 2), 
                                               fill_color)
                    else:
                        draw.rectangle([x, y, x + fill_width, y + h], fill=fill_color)
            else:  # vertical
                fill_height = int(h * normalized)
                if fill_height > 0:
                    fill_y = y + h - fill_height  # Fill from bottom
                    if config.corner_radius > 0:
                        self._draw_rounded_rect(draw, x, fill_y, w, fill_height,
                                               min(config.corner_radius, fill_height // 2),
                                               fill_color)
                    else:
                        draw.rectangle([x, fill_y, x + w, y + h], fill=fill_color)

        # Draw border
        if config.show_border:
            if config.corner_radius > 0:
                self._draw_rounded_rect_outline(draw, x, y, w, h, config.corner_radius,
                                                config.border_color, config.border_width)
            else:
                draw.rectangle([x, y, x + w, y + h], outline=config.border_color, 
                              width=config.border_width)

    def _render_rotated_bar(self, image: Image.Image, config: BarGraphConfig,
                            normalized: float, x: int, y: int, w: int, h: int, rotation: int):
        """Render a rotated bar graph by drawing to temp image and pasting"""
        import math
        
        # Create temp image for the bar (with transparency)
        bar_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        bar_draw = ImageDraw.Draw(bar_img)
        
        # Draw the bar at origin (0, 0)
        # Background
        if config.corner_radius > 0:
            self._draw_rounded_rect(bar_draw, 0, 0, w, h, config.corner_radius, config.background_color)
        else:
            bar_draw.rectangle([0, 0, w, h], fill=config.background_color)
        
        # Determine fill color
        if config.use_gradient and config.gradient_colors:
            fill_color = _interpolate_gradient_color(normalized, config.gradient_colors)
        else:
            fill_color = config.fill_color
        
        # Draw filled portion
        if normalized > 0:
            if config.orientation == "horizontal":
                fill_width = int(w * normalized)
                if fill_width > 0:
                    if config.corner_radius > 0:
                        self._draw_rounded_rect(bar_draw, 0, 0, fill_width, h,
                                               min(config.corner_radius, fill_width // 2),
                                               fill_color)
                    else:
                        bar_draw.rectangle([0, 0, fill_width, h], fill=fill_color)
            else:  # vertical
                fill_height = int(h * normalized)
                if fill_height > 0:
                    fill_y = h - fill_height
                    if config.corner_radius > 0:
                        self._draw_rounded_rect(bar_draw, 0, fill_y, w, fill_height,
                                               min(config.corner_radius, fill_height // 2),
                                               fill_color)
                    else:
                        bar_draw.rectangle([0, fill_y, w, h], fill=fill_color)
        
        # Draw border
        if config.show_border:
            if config.corner_radius > 0:
                self._draw_rounded_rect_outline(bar_draw, 0, 0, w, h, config.corner_radius,
                                                config.border_color, config.border_width)
            else:
                bar_draw.rectangle([0, 0, w, h], outline=config.border_color,
                                  width=config.border_width)
        
        # Rotate the bar image
        rotated = bar_img.rotate(-rotation, expand=True, resample=Image.BICUBIC)
        
        # Calculate paste position (center the rotated image at the original position)
        rot_w, rot_h = rotated.size
        paste_x = x - (rot_w - w) // 2
        paste_y = y - (rot_h - h) // 2
        
        # Paste onto main image using alpha channel as mask
        image.paste(rotated, (paste_x, paste_y), rotated)

    def _draw_rounded_rect(self, draw: ImageDraw.Draw, x: int, y: int, w: int, h: int, 
                           radius: int, fill_color: tuple):
        """Draw a rounded rectangle"""
        radius = min(radius, w // 2, h // 2)  # Ensure radius doesn't exceed dimensions
        if radius <= 0:
            draw.rectangle([x, y, x + w, y + h], fill=fill_color)
            return
        
        # Draw rounded rectangle using pieslices for corners and rectangles for sides
        # Top-left corner
        draw.pieslice([x, y, x + 2 * radius, y + 2 * radius], 180, 270, fill=fill_color)
        # Top-right corner
        draw.pieslice([x + w - 2 * radius, y, x + w, y + 2 * radius], 270, 360, fill=fill_color)
        # Bottom-left corner
        draw.pieslice([x, y + h - 2 * radius, x + 2 * radius, y + h], 90, 180, fill=fill_color)
        # Bottom-right corner
        draw.pieslice([x + w - 2 * radius, y + h - 2 * radius, x + w, y + h], 0, 90, fill=fill_color)
        
        # Fill rectangles
        # Top
        draw.rectangle([x + radius, y, x + w - radius, y + radius], fill=fill_color)
        # Middle
        draw.rectangle([x, y + radius, x + w, y + h - radius], fill=fill_color)
        # Bottom
        draw.rectangle([x + radius, y + h - radius, x + w - radius, y + h], fill=fill_color)

    def _draw_rounded_rect_outline(self, draw: ImageDraw.Draw, x: int, y: int, w: int, h: int,
                                   radius: int, outline_color: tuple, width: int = 1):
        """Draw a rounded rectangle outline"""
        radius = min(radius, w // 2, h // 2)
        if radius <= 0:
            draw.rectangle([x, y, x + w, y + h], outline=outline_color, width=width)
            return
        
        # Draw arcs for corners
        draw.arc([x, y, x + 2 * radius, y + 2 * radius], 180, 270, fill=outline_color, width=width)
        draw.arc([x + w - 2 * radius, y, x + w, y + 2 * radius], 270, 360, fill=outline_color, width=width)
        draw.arc([x, y + h - 2 * radius, x + 2 * radius, y + h], 90, 180, fill=outline_color, width=width)
        draw.arc([x + w - 2 * radius, y + h - 2 * radius, x + w, y + h], 0, 90, fill=outline_color, width=width)
        
        # Draw lines for sides
        draw.line([x + radius, y, x + w - radius, y], fill=outline_color, width=width)  # Top
        draw.line([x + radius, y + h, x + w - radius, y + h], fill=outline_color, width=width)  # Bottom
        draw.line([x, y + radius, x, y + h - radius], fill=outline_color, width=width)  # Left
        draw.line([x + w, y + radius, x + w, y + h - radius], fill=outline_color, width=width)  # Right

    def render_circular_graphs(self, draw: ImageDraw.Draw, image: Image.Image,
                               metrics: Optional[Dict[str, Any]], configs: List[CircularGraphConfig]):
        """Render circular/arc graphs for metrics"""
        if not metrics or not configs:
            return

        for config in configs:
            if not config.enabled:
                continue

            # Get metric value
            value = metrics.get(config.metric_name)
            if value is None:
                continue

            # Normalize value to 0-1 range
            try:
                normalized = (float(value) - config.min_value) / (config.max_value - config.min_value)
                normalized = max(0.0, min(1.0, normalized))  # Clamp to 0-1
            except (ValueError, ZeroDivisionError):
                normalized = 0.0

            rotation = getattr(config, 'rotation', 0)
            
            # If rotation is non-zero, render to a temp image and rotate
            if rotation != 0:
                self._render_rotated_arc(image, config, normalized, rotation)
            else:
                self._render_arc_direct(draw, config, normalized)

    def _render_arc_direct(self, draw: ImageDraw.Draw, config: CircularGraphConfig, normalized: float):
        """Render arc directly (no rotation)"""
        cx, cy = config.position  # Center of arc
        radius = config.radius
        thickness = config.thickness
        
        # Calculate bounding box for the arc
        bbox = [
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius
        ]
        
        # Qt uses counter-clockwise angles (positive = CCW from 3 o'clock)
        # PIL uses clockwise angles (because y increases downward in images)
        pil_start = -config.start_angle
        pil_end = -(config.start_angle + config.sweep_angle)
        
        # Draw background arc (full sweep)
        draw.arc(bbox, pil_end, pil_start, fill=config.background_color, width=thickness)
        
        # Determine fill color (use gradient if enabled)
        if config.use_gradient and config.gradient_colors:
            fill_color = _interpolate_gradient_color(normalized, config.gradient_colors)
        else:
            fill_color = config.fill_color
        
        # Draw filled arc (proportional to value)
        if normalized > 0:
            filled_sweep = config.sweep_angle * normalized
            pil_filled_end = -(config.start_angle + filled_sweep)
            draw.arc(bbox, pil_filled_end, pil_start, fill=fill_color, width=thickness)
        
        # Draw border arc if enabled
        if config.show_border:
            border_width = config.border_width
            outer_bbox = [
                cx - radius - thickness // 2 - border_width,
                cy - radius - thickness // 2 - border_width,
                cx + radius + thickness // 2 + border_width,
                cy + radius + thickness // 2 + border_width
            ]
            draw.arc(outer_bbox, pil_end, pil_start, fill=config.border_color, width=border_width)
            inner_bbox = [
                cx - radius + thickness // 2 + border_width,
                cy - radius + thickness // 2 + border_width,
                cx + radius - thickness // 2 - border_width,
                cy + radius - thickness // 2 - border_width
            ]
            draw.arc(inner_bbox, pil_end, pil_start, fill=config.border_color, width=border_width)

    def _render_rotated_arc(self, image: Image.Image, config: CircularGraphConfig,
                            normalized: float, rotation: int):
        """Render a rotated arc by drawing to temp image and pasting"""
        import math
        
        radius = config.radius
        thickness = config.thickness
        
        # Calculate base size (same formula as GUI)
        border_padding = 4
        diameter = radius * 2
        base_size = diameter + thickness + border_padding * 2
        
        # Calculate total size accounting for rotation (must match GUI's get_position)
        if rotation != 0:
            angle_rad = math.radians(rotation)
            cos_a = abs(math.cos(angle_rad))
            sin_a = abs(math.sin(angle_rad))
            rotated_size = int(base_size * cos_a + base_size * sin_a)
            total_size = max(base_size, rotated_size)
        else:
            total_size = base_size
        
        # Create temp image at total_size to match GUI widget size
        arc_img = Image.new('RGBA', (total_size, total_size), (0, 0, 0, 0))
        arc_draw = ImageDraw.Draw(arc_img)
        
        # Draw arc centered in temp image
        center = total_size // 2
        bbox = [
            center - radius,
            center - radius,
            center + radius,
            center + radius
        ]
        
        pil_start = -config.start_angle
        pil_end = -(config.start_angle + config.sweep_angle)
        
        # Draw background arc
        arc_draw.arc(bbox, pil_end, pil_start, fill=config.background_color, width=thickness)
        
        # Determine fill color
        if config.use_gradient and config.gradient_colors:
            fill_color = _interpolate_gradient_color(normalized, config.gradient_colors)
        else:
            fill_color = config.fill_color
        
        # Draw filled arc
        if normalized > 0:
            filled_sweep = config.sweep_angle * normalized
            pil_filled_end = -(config.start_angle + filled_sweep)
            arc_draw.arc(bbox, pil_filled_end, pil_start, fill=fill_color, width=thickness)
        
        # Draw border if enabled
        if config.show_border:
            border_width = config.border_width
            outer_bbox = [
                center - radius - thickness // 2 - border_width,
                center - radius - thickness // 2 - border_width,
                center + radius + thickness // 2 + border_width,
                center + radius + thickness // 2 + border_width
            ]
            arc_draw.arc(outer_bbox, pil_end, pil_start, fill=config.border_color, width=border_width)
            inner_bbox = [
                center - radius + thickness // 2 + border_width,
                center - radius + thickness // 2 + border_width,
                center + radius - thickness // 2 - border_width,
                center + radius - thickness // 2 - border_width
            ]
            arc_draw.arc(inner_bbox, pil_end, pil_start, fill=config.border_color, width=border_width)
        
        # Rotate the arc image around its center
        rotated = arc_img.rotate(-rotation, expand=False, resample=Image.BICUBIC)
        
        # Calculate paste position (center at config.position)
        # Use total_size to match GUI's get_position calculation
        cx, cy = config.position
        paste_x = cx - total_size // 2
        paste_y = cy - total_size // 2
        
        # Paste onto main image using alpha channel as mask
        image.paste(rotated, (paste_x, paste_y), rotated)

    def render_shapes(self, draw: ImageDraw.Draw, image: Image.Image, 
                      configs: List[ShapeConfig]):
        """Render decorative shape elements (rectangles, circles, lines, etc.)
        
        These are rendered after bar and circular graphs but BEFORE text/metrics so
        they appear above graph elements and behind text overlays. Good for borders,
        separators, and background decoration that should sit between graphs and text.
        """
        if not configs:
            return

        for config in configs:
            # Backwards-compat: accept dicts from YAML-loaded configs and convert to ShapeConfig-like object
            if isinstance(config, dict):
                # Minimal conversion for needed attributes
                def parse_color(val):
                    if not val:
                        return (0, 0, 0, 255)
                    if isinstance(val, (list, tuple)) and len(val) in (3, 4):
                        if len(val) == 3:
                            return (int(val[0]), int(val[1]), int(val[2]), 255)
                        return (int(val[0]), int(val[1]), int(val[2]), int(val[3]))
                    s = str(val).lstrip('#')
                    if len(s) == 8:
                        r = int(s[0:2], 16); g = int(s[2:4], 16); b = int(s[4:6], 16); a = int(s[6:8], 16)
                        return (r, g, b, a)
                    if len(s) == 6:
                        r = int(s[0:2], 16); g = int(s[2:4], 16); b = int(s[4:6], 16)
                        return (r, g, b, 255)
                    return (0, 0, 0, 255)

                cfg = ShapeConfig(
                    shape_type=ShapeType(config.get('shape_type', 'rectangle')) if config.get('shape_type') else ShapeType.RECTANGLE,
                    position=(int(config.get('position', {}).get('x', 0)) if isinstance(config.get('position'), dict) else int((config.get('position', 0) or 0)),
                              int(config.get('position', {}).get('y', 0)) if isinstance(config.get('position'), dict) else int((config.get('position', 1) or 0))),
                    width=int(config.get('width', 0)),
                    height=int(config.get('height', 0)),
                    rotation=int(config.get('rotation', 0)),
                    filled=bool(config.get('filled', True)),
                    fill_color=parse_color(config.get('fill_color')),
                    border_color=parse_color(config.get('border_color')),
                    border_width=int(config.get('border_width', 0)),
                    corner_radius=int(config.get('corner_radius', 0)),
                    arrow_head_size=int(config.get('arrow_head_size', 0)),
                    enabled=bool(config.get('enabled', True))
                )
                config = cfg
            if not config.enabled:
                continue
            # Log basic shape draw parameters for debugging
            try:
                self.logger.debug(f"Drawing shape: type={config.shape_type}, pos={config.position}, size=({config.width},{config.height}), rotation={config.rotation}, filled={config.filled}")
            except Exception:
                pass

            x, y = config.position
            w, h = config.width, config.height
            rotation = config.rotation

            # If rotation is non-zero, render to a temp image and rotate
            if rotation != 0:
                self._render_rotated_shape(image, config, x, y, w, h, rotation)
            else:
                self._render_shape_direct(draw, image, config, x, y, w, h)

    def _render_shape_direct(self, draw: ImageDraw.Draw, image: Image.Image,
                             config: ShapeConfig, x: int, y: int, w: int, h: int):
        """Render a shape directly (no rotation)"""
        shape_type = config.shape_type
        filled = config.filled
        fill_color = config.fill_color if filled else None
        border_color = config.border_color if config.border_width > 0 else None
        border_width = config.border_width

        if shape_type == ShapeType.RECTANGLE:
            if filled:
                draw.rectangle([x, y, x + w, y + h], fill=fill_color)
            if border_width > 0:
                draw.rectangle([x, y, x + w, y + h], outline=border_color, width=border_width)

        elif shape_type == ShapeType.ROUNDED_RECTANGLE:
            radius = min(config.corner_radius, w // 2, h // 2)
            if filled:
                self._draw_rounded_rect(draw, x, y, w, h, radius, fill_color)
            if border_width > 0:
                self._draw_rounded_rect_outline(draw, x, y, w, h, radius, border_color, border_width)

        elif shape_type == ShapeType.CIRCLE:
            # Circle uses width as diameter, centered at position
            diameter = w
            cx, cy = x + w // 2, y + h // 2
            r = diameter // 2
            bbox = [cx - r, cy - r, cx + r, cy + r]
            if filled:
                draw.ellipse(bbox, fill=fill_color)
            if border_width > 0:
                draw.ellipse(bbox, outline=border_color, width=border_width)

        elif shape_type == ShapeType.ELLIPSE:
            bbox = [x, y, x + w, y + h]
            if filled:
                draw.ellipse(bbox, fill=fill_color)
            if border_width > 0:
                draw.ellipse(bbox, outline=border_color, width=border_width)

        elif shape_type == ShapeType.LINE:
            # Line from left-center to right-center
            # Height represents line thickness
            y_center = y + h // 2
            line_width = max(h, 1)  # Use height as thickness
            draw.line([x, y_center, x + w, y_center], fill=border_color or fill_color, width=line_width)

        elif shape_type == ShapeType.TRIANGLE:
            # Isoceles triangle pointing up
            # Vertices: top-center, bottom-left, bottom-right
            points = [
                (x + w // 2, y),           # Top center
                (x, y + h),                 # Bottom left
                (x + w, y + h)              # Bottom right
            ]
            if filled:
                draw.polygon(points, fill=fill_color)
            if border_width > 0:
                draw.polygon(points, outline=border_color)
                # PIL polygon outline doesn't support width, so draw lines manually
                if border_width > 1:
                    draw.line([points[0], points[1]], fill=border_color, width=border_width)
                    draw.line([points[1], points[2]], fill=border_color, width=border_width)
                    draw.line([points[2], points[0]], fill=border_color, width=border_width)

        elif shape_type == ShapeType.ARROW:
            # Arrow pointing right: line with arrowhead
            head_size = config.arrow_head_size
            line_color = border_color or fill_color
            line_width = max(h, 1)  # Height as line thickness
            y_center = y + h // 2
            
            # Main line (stops before arrowhead)
            arrow_body_end = x + w - head_size
            draw.line([x, y_center, arrow_body_end, y_center], fill=line_color, width=line_width)
            
            # Arrowhead (triangle)
            arrow_points = [
                (x + w, y_center),                    # Tip
                (arrow_body_end, y_center - head_size // 2),  # Top
                (arrow_body_end, y_center + head_size // 2)   # Bottom
            ]
            draw.polygon(arrow_points, fill=line_color)

    def _render_rotated_shape(self, image: Image.Image, config: ShapeConfig,
                              x: int, y: int, w: int, h: int, rotation: int):
        """Render a rotated shape by drawing to temp image and pasting"""
        import math
        
        # Calculate size needed to contain rotated shape, including border padding so it
        # matches the GUI overlay's padding calculations.
        border_padding = 4
        diagonal = int(math.ceil(math.sqrt(w**2 + h**2))) + border_padding * 2
        
        # Create temp image for the shape (with transparency)
        shape_img = Image.new('RGBA', (diagonal, diagonal), (0, 0, 0, 0))
        shape_draw = ImageDraw.Draw(shape_img)
        
        # Calculate offset to center shape in temp image
        offset_x = int(round((diagonal - w) / 2.0))
        offset_y = int(round((diagonal - h) / 2.0))
        
        # Create a modified config with adjusted position for temp image
        temp_config = ShapeConfig(
            shape_type=config.shape_type,
            position=(offset_x, offset_y),
            width=w,
            height=h,
            rotation=0,  # No rotation - we rotate the whole image
            filled=config.filled,
            fill_color=config.fill_color,
            border_color=config.border_color,
            border_width=config.border_width,
            corner_radius=config.corner_radius,
            arrow_head_size=config.arrow_head_size,
            enabled=True
        )
        
        # Render shape at offset position
        self._render_shape_direct(shape_draw, shape_img, temp_config, offset_x, offset_y, w, h)
        
        # Rotate the shape image
        rotated = shape_img.rotate(-rotation, expand=False, resample=Image.BICUBIC)
        
        # Calculate paste position (center the rotated image at the original position)
        paste_x = int(round(x - (diagonal - w) / 2.0))
        paste_y = int(round(y - (diagonal - h) / 2.0))
        
        # Paste onto main image using alpha channel as mask
        image.paste(rotated, (paste_x, paste_y), rotated)
