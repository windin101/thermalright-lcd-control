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
        elif widget_type == 'text':
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
        
        return DateConfig(
            position=(device_x, device_y),
            font_size=properties.get('font_size', 16),
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
        device_x = int(pos.x() / scale)
        device_y = int(pos.y() / scale)
        
        properties = widget.get_properties()
        
        return MetricConfig(
            name=properties.get('metric_name', ''),
            label=properties.get('label', ''),
            position=(device_x, device_y),
            font_size=properties.get('font_size', 16),
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
            metric_name=properties.get('metric_name', 'cpu_usage'),
            position=(device_x, device_y),
            width=properties.get('width', 100),
            height=properties.get('height', 16),
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
            metric_name=properties.get('metric_name', 'cpu_usage'),
            position=(device_x, device_y),
            radius=properties.get('radius', 40),
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
                elif widget_type == 'text':
                    configs['text_configs'].append(config)
                elif widget_type == 'bar_graph':
                    configs['bar_configs'].append(config)
                elif widget_type == 'circular_graph':
                    configs['circular_configs'].append(config)
                elif widget_type in ['rectangle', 'rounded_rectangle', 'circle']:
                    configs['shape_configs'].append(config)
        
        return configs