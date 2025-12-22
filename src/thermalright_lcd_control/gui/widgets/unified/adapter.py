"""
Adapter to convert unified widgets to display configs for backend rendering.
MINIMAL VERSION for immediate POC integration.
"""
from typing import Optional, Tuple, Any

from thermalright_lcd_control.device_controller.display.config_unified import (
    DateConfig, TimeConfig, MetricConfig, TextConfig, 
    BarGraphConfig, CircularGraphConfig, ShapeConfig, ShapeType, LabelPosition
)


class UnifiedToDisplayAdapter:
    """Convert unified widgets to display configs - MINIMAL VERSION"""
    
    @staticmethod
    def widget_to_display_config(widget, scale: float = 1.0) -> Optional[Any]:
        """Convert any unified widget to appropriate display config"""
        if not widget:
            return None
            
        widget_type = getattr(widget, 'widget_type', '')
        
        if widget_type == 'date':
            return UnifiedToDisplayAdapter._date_to_config(widget, scale)
        elif widget_type == 'time':
            return UnifiedToDisplayAdapter._time_to_config(widget, scale)
        elif widget_type in ['text', 'free_text']:
            return UnifiedToDisplayAdapter._text_to_config(widget, scale)
        elif widget_type == 'metric':
            return UnifiedToDisplayAdapter._metric_to_config(widget, scale)
        elif widget_type in ['rectangle', 'rounded_rectangle', 'circle']:
            return UnifiedToDisplayAdapter._shape_to_config(widget, scale)
        elif widget_type == 'bar_graph':
            return UnifiedToDisplayAdapter._bar_to_config(widget, scale)
        elif widget_type == 'circular_graph':
            return UnifiedToDisplayAdapter._circular_to_config(widget, scale)
        
        return None
    
    @staticmethod
    def get_all_configs_from_view(unified_view, scale: float = 1.0) -> dict:
        """Get all display configs from a unified view"""
        if not unified_view:
            return {}
        
        configs = {
            'date_config': None,
            'time_config': None,
            'metrics_configs': [],
            'text_configs': [],
            'bar_configs': [],
            'circular_configs': [],
            'shape_configs': []
        }
        
        # Get all widgets from the view
        if hasattr(unified_view, 'get_all_widgets'):
            widgets = unified_view.get_all_widgets()
            for widget in widgets.values():
                config = UnifiedToDisplayAdapter.widget_to_display_config(widget, scale)
                if config:
                    widget_type = getattr(widget, 'widget_type', '')
                    
                    if widget_type == 'date':
                        configs['date_config'] = config
                    elif widget_type == 'time':
                        configs['time_config'] = config
                    elif widget_type == 'metric':
                        configs['metrics_configs'].append(config)
                    elif widget_type in ['text', 'free_text']:
                        configs['text_configs'].append(config)
                    elif widget_type == 'bar_graph':
                        configs['bar_configs'].append(config)
                    elif widget_type == 'circular_graph':
                        configs['circular_configs'].append(config)
                    elif widget_type in ['rectangle', 'rounded_rectangle', 'circle']:
                        configs['shape_configs'].append(config)
        
        return configs
    
    @staticmethod
    def _date_to_config(widget, scale: float) -> DateConfig:
        """Convert DateWidget to DateConfig"""
        # Get position in device coordinates
        pos = widget.pos()
        width = getattr(widget, '_width', 150)  # Default width if not available
        height = getattr(widget, '_height', 30)  # Default height if not available
        
        # Calculate centered position (text is drawn from top-left, so center it in the widget bounds)
        centered_x = pos.x() + width / 2
        centered_y = pos.y() + height / 2
        
        device_x = int(centered_x / scale)
        device_y = int(centered_y / scale)
        
        # Get properties from widget
        properties = widget.get_properties()
        
        # Calculate scaled font size based on widget height
        # Same scaling formula as in widget rendering
        base_height = 30  # Default widget height in preview
        base_font_size = properties.get('font_size', 16)
        
        # Scale factor: how much taller/shorter widget is compared to default
        height_scale = height / base_height
        
        # Calculate scaled font size (for device)
        scaled_font_size = int(round(base_font_size * height_scale))
        
        # Apply min/max limits for device display
        scaled_font_size = max(8, min(72, scaled_font_size))
        
        return DateConfig(
            position=(device_x, device_y),
            font_size=scaled_font_size,
            color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('text_color')),
            show_weekday=properties.get('show_weekday', True),
            show_year=properties.get('show_year', False),
            date_format=properties.get('date_format', 'default'),
            enabled=getattr(widget, 'enabled', True)
        )
    
    @staticmethod
    def _time_to_config(widget, scale: float) -> TimeConfig:
        """Convert TimeWidget to TimeConfig"""
        pos = widget.pos()
        width = getattr(widget, '_width', 150)  # Default width if not available
        height = getattr(widget, '_height', 30)  # Default height if not available
        
        # Calculate centered position (text is drawn from top-left, so center it in the widget bounds)
        centered_x = pos.x() + width / 2
        centered_y = pos.y() + height / 2
        
        device_x = int(centered_x / scale)
        device_y = int(centered_y / scale)
        
        properties = widget.get_properties()
        
        return TimeConfig(
            position=(device_x, device_y),
            font_size=properties.get('font_size', 16),
            color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('text_color')),
            use_24_hour=properties.get('use_24_hour', True),
            show_seconds=properties.get('show_seconds', False),
            show_am_pm=properties.get('show_am_pm', False),
            enabled=getattr(widget, 'enabled', True)
        )
    
    @staticmethod
    def _text_to_config(widget, scale: float) -> TextConfig:
        """Convert FreeTextWidget to TextConfig"""
        pos = widget.pos()
        device_x = int(pos.x() / scale)
        device_y = int(pos.y() / scale)
        
        properties = widget.get_properties()
        
        return TextConfig(
            position=(device_x, device_y),
            text=properties.get('text', ''),
            font_size=properties.get('font_size', 16),
            color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('text_color')),
            enabled=getattr(widget, 'enabled', True)
        )
    
    @staticmethod
    def _metric_to_config(widget, scale: float) -> MetricConfig:
        """Convert MetricWidget to MetricConfig"""
        pos = widget.pos()
        width = getattr(widget, '_width', 120)  # Default width if not available
        height = getattr(widget, '_height', 25)  # Default height if not available
        
        # Calculate centered position (text is drawn from middle with anchor='mm')
        centered_x = pos.x() + width / 2
        centered_y = pos.y() + height / 2
        
        device_x = int(centered_x / scale)
        device_y = int(centered_y / scale)
        
        properties = widget.get_properties()
        
        # Use label or prefix (some widgets use prefix instead of label)
        raw_label = properties.get('label', '') or properties.get('prefix', '')
        
        # Clean prefix: remove trailing ": " if present
        if raw_label.endswith(': '):
            cleaned_label = raw_label[:-2]
        elif raw_label.endswith(':'):
            cleaned_label = raw_label[:-1]
        else:
            cleaned_label = raw_label
        
        # Calculate scaled font size based on widget height
        # Same scaling formula as in widget rendering
        base_height = 30  # Default widget height in preview
        base_font_size = properties.get('font_size', 16)
        
        # Get widget height from properties (in preview coordinates)
        widget_height = properties.get('height', base_height)
        
        # Scale factor: how much taller/shorter widget is compared to default
        height_scale = widget_height / base_height
        
        # Calculate scaled font size (for device)
        scaled_font_size = int(round(base_font_size * height_scale))
        
        # Apply min/max limits for device display
        scaled_font_size = max(8, min(72, scaled_font_size))
        
        return MetricConfig(
            name=properties.get('metric_type', ''),
            label=cleaned_label,
            position=(device_x, device_y),
            font_size=scaled_font_size,
            color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('text_color')),
            enabled=getattr(widget, 'enabled', True),
            label_position=LabelPosition.LEFT,
            unit=properties.get('unit', '')
        )
    
    @staticmethod
    def _shape_to_config(widget, scale: float) -> ShapeConfig:
        """Convert ShapeWidget to ShapeConfig"""
        pos = widget.pos()
        device_x = int(pos.x() / scale)
        device_y = int(pos.y() / scale)
        
        properties = widget.get_properties()
        widget_type = getattr(widget, 'widget_type', 'rectangle')
        
        # Map widget type to ShapeType
        shape_type_map = {
            'rectangle': ShapeType.RECTANGLE,
            'rounded_rectangle': ShapeType.ROUNDED_RECTANGLE,
            'circle': ShapeType.CIRCLE
        }
        
        return ShapeConfig(
            shape_type=shape_type_map.get(widget_type, ShapeType.RECTANGLE),
            position=(device_x, device_y),
            width=properties.get('width', 100),
            height=properties.get('height', 50),
            rotation=properties.get('rotation', 0),
            filled=properties.get('filled', True),
            fill_color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('fill_color')),
            border_color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('border_color')),
            border_width=properties.get('border_width', 2),
            corner_radius=properties.get('corner_radius', 0),
            enabled=getattr(widget, 'enabled', True)
        )
    
    @staticmethod
    def _bar_to_config(widget, scale: float) -> BarGraphConfig:
        """Convert BarGraphWidget to BarGraphConfig"""
        pos = widget.pos()
        device_x = int(pos.x() / scale)
        device_y = int(pos.y() / scale)
        
        properties = widget.get_properties()
        
        return BarGraphConfig(
            position=(device_x, device_y),
            width=properties.get('width', 100),
            height=properties.get('height', 16),
            color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('fill_color', '#4ECDC4')),
            orientation=properties.get('orientation', 'horizontal'),
            rotation=properties.get('rotation', 0),
            fill_color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('fill_color')),
            background_color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('background_color')),
            border_color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('border_color')),
            show_border=properties.get('show_border', True),
            border_width=properties.get('border_width', 1),
            corner_radius=properties.get('corner_radius', 0),
            min_value=properties.get('min_value', 0.0),
            max_value=properties.get('max_value', 100.0),
            enabled=getattr(widget, 'enabled', True)
        )
    
    @staticmethod
    def _circular_to_config(widget, scale: float) -> CircularGraphConfig:
        """Convert CircularGraphWidget to CircularGraphConfig"""
        pos = widget.pos()
        device_x = int(pos.x() / scale)
        device_y = int(pos.y() / scale)
        
        properties = widget.get_properties()
        
        return CircularGraphConfig(
            position=(device_x, device_y),
            radius=properties.get('radius', 40),
            color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('fill_color', '#4ECDC4')),
            thickness=properties.get('thickness', 8),
            start_angle=properties.get('start_angle', 135),
            sweep_angle=properties.get('sweep_angle', 270),
            rotation=properties.get('rotation', 0),
            fill_color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('fill_color')),
            background_color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('background_color')),
            border_color=UnifiedToDisplayAdapter._color_to_rgba(properties.get('border_color')),
            show_border=properties.get('show_border', False),
            border_width=properties.get('border_width', 1),
            min_value=properties.get('min_value', 0.0),
            max_value=properties.get('max_value', 100.0),
            enabled=getattr(widget, 'enabled', True)
        )
    
    @staticmethod
    def _color_to_rgba(color) -> Tuple[int, int, int, int]:
        """Convert color to RGBA tuple"""
        if isinstance(color, (list, tuple)):
            if len(color) == 3:
                return (color[0], color[1], color[2], 255)
            elif len(color) == 4:
                return tuple(color)
        elif isinstance(color, str):
            # Handle hex color strings like '#RRGGBB' or '#RRGGBBAA'
            color = color.strip()
            if color.startswith('#'):
                color = color[1:]
                if len(color) == 6:
                    # RGB hex
                    r = int(color[0:2], 16)
                    g = int(color[2:4], 16)
                    b = int(color[4:6], 16)
                    return (r, g, b, 255)
                elif len(color) == 8:
                    # RGBA hex
                    r = int(color[0:2], 16)
                    g = int(color[2:4], 16)
                    b = int(color[4:6], 16)
                    a = int(color[6:8], 16)
                    return (r, g, b, a)
        # Default white
        return (255, 255, 255, 255)
    
    @staticmethod
    def get_all_configs_from_view(unified_view, scale: float = 1.0) -> dict:
        """Get all display configs from unified view"""
        if not unified_view:
            return {}
        
        configs = {
            'date_config': None,
            'time_config': None,
            'metrics_configs': [],
            'text_configs': [],
            'bar_configs': [],
            'circular_configs': [],
            'shape_configs': []
        }
        
        widgets = unified_view.get_all_widgets()
        print(f"[DEBUG] Adapter: Found {len(widgets)} widgets in view")
        for widget_name, widget in widgets.items():
            print(f"[DEBUG] Adapter: Widget {widget_name} type: {getattr(widget, 'widget_type', 'unknown')}")
            config = UnifiedToDisplayAdapter.widget_to_display_config(widget, scale)
            if config:
                widget_type = getattr(widget, 'widget_type', '')
                print(f"[DEBUG] Adapter: Created config for {widget_name} type: {widget_type}")
                
                if widget_type == 'date':
                    configs['date_config'] = config
                elif widget_type == 'time':
                    configs['time_config'] = config
                elif widget_type == 'metric':
                    configs['metrics_configs'].append(config)
                elif widget_type == 'text':
                    configs['text_configs'].append(config)
                elif widget_type == 'bar_graph':
                    configs['bar_configs'].append(config)
                    print(f"[DEBUG] Adapter: Added bar_graph config")
                elif widget_type == 'circular_graph':
                    configs['circular_configs'].append(config)
                    print(f"[DEBUG] Adapter: Added circular_graph config")
                elif widget_type in ['rectangle', 'rounded_rectangle', 'circle']:
                    configs['shape_configs'].append(config)
        
        print(f"[DEBUG] Adapter: Final configs - bar: {len(configs['bar_configs'])}, circular: {len(configs['circular_configs'])}")
        return configs