# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

import os
import time
from typing import Dict, Any, Tuple

from PIL import Image, ImageDraw

from .config import DisplayConfig
from .frame_manager import FrameManager
from .text_renderer import TextRenderer
from .utils import async_background
from .config_unified import ShapeType
from ...common.logging_config import LoggerConfig


class DisplayGenerator:
    """Display image generator with dynamic background and real-time metrics"""

    def __init__(self, config: DisplayConfig):
        self.config = config
        self.logger = self.logger = LoggerConfig.setup_service_logger()
        self.refresh_interval = 0.01
        # Initialize components
        self.frame_manager = FrameManager(config)
        self.text_renderer = TextRenderer(config)  # Pass config for global font

        self.logger.info(f"DisplayGenerator initialized with background type: {self.config.background_type}")
        self.logger.info(f"Global font: {self.config.global_font_path or 'Default system font'}")

    def _add_foreground_image(self, background: Image.Image) -> Image.Image:
        """Add foreground image to background"""
        if not self.config.foreground_image_path or not os.path.exists(self.config.foreground_image_path):
            return background

        try:
            foreground = Image.open(self.config.foreground_image_path)
            if foreground.mode != 'RGBA':
                foreground = foreground.convert('RGBA')

            # Apply transparency
            if self.config.foreground_alpha < 1.0:
                alpha = foreground.split()[-1]  # Alpha channel
                alpha = alpha.point(lambda p: int(p * self.config.foreground_alpha))
                foreground.putalpha(alpha)

            # Compose foreground image
            result = background.copy()
            result.paste(foreground, self.config.foreground_position, foreground)
            return result

        except Exception as e:
            self.logger.warning(f"Cannot load foreground image: {e}")
            return background

    def generate_frame_with_metrics(self, metrics: dict) -> Image.Image:
        """
        Generate a complete frame with all elements and real-time metrics
        """
        # Get current background
        background = self.frame_manager.get_current_frame()

        # Add foreground image if configured
        result = self._add_foreground_image(background)

        # Create drawing object
        draw = ImageDraw.Draw(result)

        # Draw metrics
        self.text_renderer.render_metrics(draw, metrics, self.config.metrics_configs)

        # Draw date (dd/mm format)
        self.text_renderer.render_date(draw, self.config.date_config)

        # Draw time (HH:MM format)
        self.text_renderer.render_time(draw, self.config.time_config)

        # Draw custom text widgets
        if hasattr(self.config, 'text_configs') and self.config.text_configs:
            for text_config in self.config.text_configs:
                if text_config.enabled:
                    self.text_renderer.render_custom_text(draw, text_config)

        # Draw shapes
        if hasattr(self.config, 'shape_configs') and self.config.shape_configs:
            self._render_shapes(draw, self.config.shape_configs)

        # Draw bar graphs
        if hasattr(self.config, 'bar_configs') and self.config.bar_configs:
            self.logger.debug(f"Found {len(self.config.bar_configs)} bar graph configs")
            self._render_bar_graphs(draw, metrics, self.config.bar_configs)
        else:
            self.logger.debug("No bar_configs found or bar_configs is empty")

        # Draw circular graphs
        if hasattr(self.config, 'circular_configs') and self.config.circular_configs:
            self._render_circular_graphs(draw, metrics, self.config.circular_configs)

        convert = result.convert('RGB')

        # Apply rotation if specified
        if hasattr(self.config, 'rotation') and self.config.rotation:
            convert = convert.rotate(-self.config.rotation)  # PIL rotate uses counterclockwise

        return convert

    def generate_frame(self) -> Image.Image:
        # Get current real-time metrics
        metrics = self.frame_manager.get_current_metrics()
        return self.generate_frame_with_metrics(metrics)

    def get_frame_with_duration(self) -> Tuple[Image.Image, float]:
        """
        Generate a complete frame and return it with its display duration

        Returns:
            Tuple[Image.Image, float]: (generated_image, display_duration_seconds)
        """
        # Generate the complete frame
        frame = self.generate_frame()
        return frame, self.refresh_interval

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.frame_manager.get_current_metrics()

    def _render_shapes(self, draw: ImageDraw.Draw, shape_configs):
        """Render shape widgets"""
        for config in shape_configs:
            if not config.enabled:
                continue

            try:
                if config.shape_type.value == 'rectangle':
                    if config.filled:
                        draw.rectangle(
                            [config.position[0], config.position[1],
                             config.position[0] + config.width, config.position[1] + config.height],
                            fill=config.color[:3],  # RGB only
                            outline=config.border_color[:3] if config.border_color else None,
                            width=config.border_width
                        )
                    else:
                        draw.rectangle(
                            [config.position[0], config.position[1],
                             config.position[0] + config.width, config.position[1] + config.height],
                            outline=config.border_color[:3] if config.border_color else config.color[:3],
                            width=config.border_width
                        )

                elif config.shape_type.value == 'circle':
                    # Draw circle (ellipse with equal width/height)
                    bbox = [config.position[0], config.position[1],
                           config.position[0] + config.width, config.position[1] + config.height]
                    if config.filled:
                        draw.ellipse(bbox, fill=config.color[:3], outline=config.border_color[:3] if config.border_color else None, width=config.border_width)
                    else:
                        draw.ellipse(bbox, outline=config.border_color[:3] if config.border_color else config.color[:3], width=config.border_width)

                elif config.shape_type.value == 'rounded_rectangle':
                    # For rounded rectangle, we'll approximate with a regular rectangle for now
                    # PIL doesn't have native rounded rectangle support
                    if config.filled:
                        draw.rectangle(
                            [config.position[0], config.position[1],
                             config.position[0] + config.width, config.position[1] + config.height],
                            fill=config.color[:3],
                            outline=config.border_color[:3] if config.border_color else None,
                            width=config.border_width
                        )
                    else:
                        draw.rectangle(
                            [config.position[0], config.position[1],
                             config.position[0] + config.width, config.position[1] + config.height],
                            outline=config.border_color[:3] if config.border_color else config.color[:3],
                            width=config.border_width
                        )

            except Exception as e:
                self.logger.warning(f"Error rendering shape: {e}")

    def _render_bar_graphs(self, draw: ImageDraw.Draw, metrics: dict, bar_configs):
        """Render bar graph widgets"""
        for config in bar_configs:
            if not config.enabled:
                continue

            try:
                self.logger.debug(f"Rendering bar graph: position={config.position}, width={config.width}, height={config.height}, color={getattr(config, 'color', 'None')}, fill_color={getattr(config, 'fill_color', 'None')}, background_color={getattr(config, 'background_color', 'None')}")
                
                # Get metric value
                value = metrics.get(config.metric_name, 0.0)
                if value is None:
                    value = 0.0

                self.logger.debug(f"Bar graph metric {config.metric_name}: raw_value={value}, min_value={config.min_value}, max_value={config.max_value}")

                # Normalize value to 0-1 range
                normalized_value = max(0.0, min(1.0, (value - config.min_value) / (config.max_value - config.min_value)))

                self.logger.debug(f"Bar graph normalized_value: {normalized_value}")

                # Calculate bar dimensions
                bar_width = int(config.width * normalized_value)
                bar_height = config.height

                self.logger.debug(f"Bar graph dimensions: bar_width={bar_width}, bar_height={bar_height}")

                # Draw background bar
                draw.rectangle(
                    [config.position[0], config.position[1],
                     config.position[0] + config.width, config.position[1] + config.height],
                    fill=config.background_color[:3] if hasattr(config, 'background_color') and config.background_color else (64, 64, 64),
                    outline=config.border_color[:3] if hasattr(config, 'border_color') and config.border_color else None,
                    width=config.border_width if hasattr(config, 'border_width') else 1
                )

                # Draw filled bar
                if bar_width > 0:
                    fill_color = config.fill_color[:3] if hasattr(config, 'fill_color') and config.fill_color else config.color[:3]
                    self.logger.debug(f"Drawing filled bar with color: {fill_color}")
                    draw.rectangle(
                        [config.position[0], config.position[1],
                         config.position[0] + bar_width, config.position[1] + config.height],
                        fill=fill_color
                    )

                # Draw value text if enabled
                if hasattr(config, 'show_value') and config.show_value:
                    value_text = f"{value:.1f}"
                    font = self.text_renderer._get_font(min(12, config.height - 4))
                    bbox = draw.textbbox(config.position, value_text, font=font)
                    text_x = config.position[0] + config.width // 2
                    text_y = config.position[1] + config.height // 2
                    draw.text((text_x, text_y), value_text, fill=(255, 255, 255), font=font, anchor='mm')

            except Exception as e:
                self.logger.warning(f"Error rendering bar graph: {e}")

    def _render_circular_graphs(self, draw: ImageDraw.Draw, metrics: dict, circular_configs):
        """Render circular graph widgets"""
        for config in circular_configs:
            if not config.enabled:
                continue

            try:
                self.logger.debug(f"Rendering circular graph: position={config.position}, radius={config.radius}, color={getattr(config, 'color', 'None')}, fill_color={getattr(config, 'fill_color', 'None')}, background_color={getattr(config, 'background_color', 'None')}")
                
                # Get metric value
                value = metrics.get(config.metric_name, 0.0)
                if value is None:
                    value = 0.0

                self.logger.debug(f"Circular graph metric {config.metric_name}: raw_value={value}, min_value={config.min_value}, max_value={config.max_value}")

                # Normalize value to 0-1 range
                normalized_value = max(0.0, min(1.0, (value - config.min_value) / (config.max_value - config.min_value)))

                self.logger.debug(f"Circular graph normalized_value: {normalized_value}, sweep_angle will be: {int(config.sweep_angle * normalized_value)}")

                # Calculate angles
                start_angle = config.start_angle
                sweep_angle = int(config.sweep_angle * normalized_value)

                # Draw background circle
                bbox = [config.position[0] - config.radius, config.position[1] - config.radius,
                       config.position[0] + config.radius, config.position[1] + config.radius]

                if hasattr(config, 'background_color') and config.background_color:
                    self.logger.debug(f"Drawing background circle with color: {config.background_color}")
                    draw.ellipse(bbox, fill=config.background_color[:3])

                # Draw filled arc
                if sweep_angle > 0:
                    fill_color = config.fill_color[:3] if hasattr(config, 'fill_color') and config.fill_color else config.color[:3]
                    self.logger.debug(f"Drawing filled arc with color: {fill_color}")
                    draw.pieslice(
                        bbox,
                        start=start_angle,
                        end=start_angle + sweep_angle,
                        fill=fill_color
                    )

                # Draw border if enabled
                if hasattr(config, 'show_border') and config.show_border:
                    draw.ellipse(
                        bbox,
                        outline=config.border_color[:3] if hasattr(config, 'border_color') and config.border_color else None,
                        width=config.border_width if hasattr(config, 'border_width') else 1
                    )

                # Draw value text if enabled
                if hasattr(config, 'show_percentage') and config.show_percentage:
                    percentage = int(normalized_value * 100)
                    value_text = f"{percentage}%"
                    font = self.text_renderer._get_font(min(12, config.radius // 2))
                    text_x = config.position[0]
                    text_y = config.position[1]
                    draw.text((text_x, text_y), value_text, fill=(255, 255, 255), font=font, anchor='mm')

            except Exception as e:
                self.logger.warning(f"Error rendering circular graph: {e}")

    @async_background
    def cleanup(self):
        """Clean up resources"""
        self.frame_manager.cleanup()
        self.logger.debug("DisplayGenerator cleaned up")

    def __del__(self):
        """Destructor to automatically clean up"""
        self.cleanup()
