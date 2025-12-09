# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

from datetime import datetime
from typing import Optional, List, Dict, Any

from PIL import ImageDraw, ImageFont, ImageFilter, Image

from thermalright_lcd_control.device_controller.display.config import TextConfig, MetricConfig, DisplayConfig, LabelPosition, DateConfig, TimeConfig
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

    def _get_font(self, font_size: int) -> ImageFont.ImageFont:
        return self.font_manager.get_font(font_size)

    def _draw_text_with_effects(self, draw: ImageDraw.Draw, image: Image.Image, 
                                 position: tuple, text: str, font: ImageFont.ImageFont, 
                                 fill: tuple):
        """Draw text with shadow, outline, and gradient effects if enabled"""
        x, y = position
        
        # Draw shadow first (behind everything)
        if self.display_config.shadow_enabled:
            shadow_x = x + self.display_config.shadow_offset_x
            shadow_y = y + self.display_config.shadow_offset_y
            shadow_color = self.display_config.shadow_color
            
            if self.display_config.shadow_blur > 0:
                # Create shadow on temporary image for blur effect
                bbox = draw.textbbox(position, text, font=font)
                padding = self.display_config.shadow_blur * 2 + abs(self.display_config.shadow_offset_x) + abs(self.display_config.shadow_offset_y)
                shadow_img = Image.new('RGBA', (bbox[2] - bbox[0] + padding * 2, bbox[3] - bbox[1] + padding * 2), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_img)
                shadow_draw.text((padding, padding), text, fill=shadow_color, font=font)
                shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=self.display_config.shadow_blur))
                # Paste shadow onto main image
                paste_x = shadow_x - padding + (bbox[0] - x)
                paste_y = shadow_y - padding + (bbox[1] - y)
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
        
        # Draw main text (with gradient if enabled)
        if self.display_config.gradient_enabled:
            # Create gradient text
            bbox = draw.textbbox(position, text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            if text_width > 0 and text_height > 0:
                # Create text mask
                text_img = Image.new('RGBA', (text_width + 4, text_height + 4), (0, 0, 0, 0))
                text_draw = ImageDraw.Draw(text_img)
                text_draw.text((2, 2), text, fill=(255, 255, 255, 255), font=font)
                
                # Create gradient
                gradient_img = Image.new('RGBA', (text_width + 4, text_height + 4), (0, 0, 0, 0))
                c1 = self.display_config.gradient_color1
                c2 = self.display_config.gradient_color2
                
                for i in range(text_height + 4):
                    if self.display_config.gradient_direction == "vertical":
                        ratio = i / (text_height + 3)
                    elif self.display_config.gradient_direction == "horizontal":
                        ratio = 0.5  # Will be overridden per pixel
                    else:  # diagonal
                        ratio = i / (text_height + 3)
                    
                    r = int(c1[0] + (c2[0] - c1[0]) * ratio)
                    g = int(c1[1] + (c2[1] - c1[1]) * ratio)
                    b = int(c1[2] + (c2[2] - c1[2]) * ratio)
                    a = int(c1[3] + (c2[3] - c1[3]) * ratio)
                    
                    for j in range(text_width + 4):
                        if self.display_config.gradient_direction == "horizontal":
                            ratio = j / (text_width + 3)
                            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
                            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
                            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
                            a = int(c1[3] + (c2[3] - c1[3]) * ratio)
                        elif self.display_config.gradient_direction == "diagonal":
                            ratio = (i + j) / (text_height + text_width + 6)
                            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
                            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
                            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
                            a = int(c1[3] + (c2[3] - c1[3]) * ratio)
                        gradient_img.putpixel((j, i), (r, g, b, a))
                
                # Apply text as mask to gradient
                gradient_img.putalpha(text_img.split()[3])
                
                # Paste gradient text onto image
                paste_x = x + (bbox[0] - x) - 2
                paste_y = y + (bbox[1] - y) - 2
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
                    # If conversion fails, return the string as-is
                    return value

            # If it's already a number, format it
            if isinstance(value, (int, float)):
                # Check if the format string contains decimal formatting
                if '.0f' in format_string or '.1f' in format_string or '.2f' in format_string:
                    return format_string.format(value=value)
                else:
                    # For other format strings, convert to string first
                    return format_string.format(value=str(value))

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

            # Get metric value
            value = metrics.get(config.name)
            if value is None:
                continue

            # Get fonts - separate for value and label
            value_font = self._get_font(config.font_size)
            label_font = self._get_font(config.get_label_font_size())
            
            # Format the value part
            formatted_value = self._safe_format_value(value, "{value}", config.name)
            value_text = f"{formatted_value}{config.unit}"
            label_text = config.label if config.label else ""
            
            # Get label position (default to LEFT for backward compatibility)
            label_pos = getattr(config, 'label_position', LabelPosition.LEFT)
            
            # Render based on label position
            if label_pos == LabelPosition.NONE or not label_text:
                # Just render value with unit
                self._draw_text_with_effects(draw, image, config.position, value_text, value_font, config.color)
            elif label_pos == LabelPosition.LEFT:
                # Label: Value (draw separately for different font sizes)
                label_with_colon = f"{label_text}: "
                self._draw_text_with_effects(draw, image, config.position, label_with_colon, label_font, config.color)
                # Calculate label width to position value after it
                label_bbox = draw.textbbox(config.position, label_with_colon, font=label_font)
                value_x = label_bbox[2]  # Right edge of label
                self._draw_text_with_effects(draw, image, (value_x, config.position[1]), value_text, value_font, config.color)
            elif label_pos == LabelPosition.RIGHT:
                # Value :Label (draw separately for different font sizes)
                self._draw_text_with_effects(draw, image, config.position, value_text, value_font, config.color)
                value_bbox = draw.textbbox(config.position, value_text, font=value_font)
                label_x = value_bbox[2]  # Right edge of value
                self._draw_text_with_effects(draw, image, (label_x, config.position[1]), f" :{label_text}", label_font, config.color)
            elif label_pos == LabelPosition.ABOVE:
                # Label on top, value below - center label horizontally over value
                label_bbox = draw.textbbox((0, 0), label_text, font=label_font)
                value_bbox = draw.textbbox((0, 0), value_text, font=value_font)
                label_width = label_bbox[2] - label_bbox[0]
                value_width = value_bbox[2] - value_bbox[0]
                label_height = label_bbox[3] - label_bbox[1]
                # Center label over value
                if value_width > label_width:
                    label_x = config.position[0] + (value_width - label_width) // 2
                    value_x = config.position[0]
                else:
                    label_x = config.position[0]
                    value_x = config.position[0] + (label_width - value_width) // 2
                # Draw label at position (centered)
                self._draw_text_with_effects(draw, image, (label_x, config.position[1]), label_text, label_font, config.color)
                # Draw value below label (centered)
                value_pos = (value_x, config.position[1] + label_height + 2)
                self._draw_text_with_effects(draw, image, value_pos, value_text, value_font, config.color)
            elif label_pos == LabelPosition.BELOW:
                # Value on top, label below - center label horizontally under value
                value_bbox = draw.textbbox((0, 0), value_text, font=value_font)
                label_bbox = draw.textbbox((0, 0), label_text, font=label_font)
                value_width = value_bbox[2] - value_bbox[0]
                label_width = label_bbox[2] - label_bbox[0]
                value_height = value_bbox[3] - value_bbox[1]
                # Center the narrower text under/over the wider one
                if value_width > label_width:
                    value_x = config.position[0]
                    label_x = config.position[0] + (value_width - label_width) // 2
                else:
                    value_x = config.position[0] + (label_width - value_width) // 2
                    label_x = config.position[0]
                # Draw value at position (centered)
                self._draw_text_with_effects(draw, image, (value_x, config.position[1]), value_text, value_font, config.color)
                # Draw label below value (centered)
                label_pos_y = (label_x, config.position[1] + value_height + 2)
                self._draw_text_with_effects(draw, image, label_pos_y, label_text, label_font, config.color)
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
                self._draw_text_with_effects(draw, image, config.position, text, value_font, config.color)

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

        # Get font using global font configuration
        font = self._get_font(config.font_size)

        # Draw text with effects
        self._draw_text_with_effects(draw, image, config.position, current_date, font, config.color)

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

        # Get font using global font configuration
        font = self._get_font(config.font_size)

        # Draw text with effects
        self._draw_text_with_effects(draw, image, config.position, current_time, font, config.color)

    def render_custom_text(self, draw: ImageDraw.Draw, image: Image.Image, config: TextConfig):
        """Display custom text"""
        if not config.enabled or not config.text:
            return

        # Get font using global font configuration
        font = self._get_font(config.font_size)

        # Draw text with effects
        self._draw_text_with_effects(draw, image, config.position, config.text, font, config.color)
