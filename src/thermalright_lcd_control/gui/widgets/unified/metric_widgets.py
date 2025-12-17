"""
Unified Widget System - Metric Widgets

This module contains system metric display widgets:
- MetricWidget: Base class for all metric widgets
- TemperatureWidget: CPU/GPU temperature display
- UsageWidget: CPU/GPU usage percentage display
- FrequencyWidget: CPU/GPU frequency display
- NameWidget: CPU/GPU name display
- RAMWidget: RAM usage display
"""
from .base import UnifiedBaseItem
from PySide6.QtCore import Qt, QTimer, Signal, Property
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from typing import Dict, Any, Optional, Tuple, Callable
import logging

logger = logging.getLogger(__name__)


class MetricWidget(UnifiedBaseItem):
    """
    Base class for all metric display widgets.
    
    Features:
    - Connects to system metrics
    - Automatic updates (configurable interval)
    - Value formatting (units, decimal places)
    - Fallback display when metrics unavailable
    """
    
    # Metric type constants
    METRIC_TYPES = {
        'cpu_temperature': 'CPU Temperature',
        'gpu_temperature': 'GPU Temperature',
        'cpu_usage': 'CPU Usage',
        'gpu_usage': 'GPU Usage',
        'cpu_frequency': 'CPU Frequency',
        'gpu_frequency': 'GPU Frequency',
        'cpu_name': 'CPU Name',
        'gpu_name': 'GPU Name',
        'ram_total': 'RAM Total',
        'ram_percent': 'RAM Usage',
        'gpu_mem_total': 'GPU Memory Total',
        'gpu_mem_percent': 'GPU Memory Usage',
    }
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 120, height: float = 25,
                 preview_scale: float = 1.0, **kwargs):
        """
        Initialize metric widget base class.
        
        Additional kwargs:
            enabled: bool = True
            font_family: str = "Arial"
            font_size: int = 12
            bold: bool = False
            text_color: Tuple[int, int, int, int] = (0, 0, 0, 255)
            metric_type: str = "cpu_temperature"
            update_interval: int = 2000  # ms
            unit: str = "°C"  # Display unit
            decimal_places: int = 1
            prefix: str = ""  # Text before value
            suffix: str = ""  # Text after value
        """
        super().__init__(widget_name, "metric", x, y, width, height, preview_scale)
        
        # Text properties
        self._font_family = kwargs.get('font_family', 'Arial')
        self._font_size = kwargs.get('font_size', 12)
        self._bold = kwargs.get('bold', False)
        self._text_color = QColor(*kwargs.get('text_color', (0, 0, 0, 255)))
        
        # Metric properties
        self._metric_type = kwargs.get('metric_type', 'cpu_temperature')
        self._update_interval = kwargs.get('update_interval', 2000)  # 2 seconds
        self._unit = kwargs.get('unit', '°C')
        self._decimal_places = kwargs.get('decimal_places', 1)
        self._prefix = kwargs.get('prefix', '')
        self._suffix = kwargs.get('suffix', '')
        
        # Current value
        self._current_value = None
        self._current_text = "Loading..."
        
        # Metrics system connection (will be set when available)
        self._metrics_provider = None
        
        # Timer for updates
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_metric)
        if self._enabled:
            self._update_timer.start(self._update_interval)
        
        logger.debug(f"MetricWidget '{widget_name}' created for {self._metric_type}")
    
    def _get_layer(self) -> int:
        """Metric widgets are text layer."""
        return self.TEXT_LAYER
    
    # ==================== Metric Properties ====================
    
    @Property(str)
    def metric_type(self) -> str:
        """Get metric type."""
        return self._metric_type
    
    @metric_type.setter
    def metric_type(self, value: str):
        """Set metric type."""
        if self._metric_type != value and value in self.METRIC_TYPES:
            self._metric_type = value
            self._update_metric()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(int)
    def update_interval(self) -> int:
        """Get update interval in milliseconds."""
        return self._update_interval
    
    @update_interval.setter
    def update_interval(self, value: int):
        """Set update interval in milliseconds."""
        if self._update_interval != value:
            self._update_interval = max(500, value)  # Minimum 500ms
            if self._update_timer.isActive():
                self._update_timer.stop()
                self._update_timer.start(self._update_interval)
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(str)
    def unit(self) -> str:
        """Get display unit."""
        return self._unit
    
    @unit.setter
    def unit(self, value: str):
        """Set display unit."""
        if self._unit != value:
            self._unit = value
            self._update_display_text()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(int)
    def decimal_places(self) -> int:
        """Get decimal places for value display."""
        return self._decimal_places
    
    @decimal_places.setter
    def decimal_places(self, value: int):
        """Set decimal places for value display."""
        if self._decimal_places != value:
            self._decimal_places = max(0, min(value, 4))  # 0-4 decimal places
            self._update_display_text()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(str)
    def prefix(self) -> str:
        """Get text prefix."""
        return self._prefix
    
    @prefix.setter
    def prefix(self, value: str):
        """Set text prefix."""
        if self._prefix != value:
            self._prefix = value
            self._update_display_text()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(str)
    def suffix(self) -> str:
        """Get text suffix."""
        return self._suffix
    
    @suffix.setter
    def suffix(self, value: str):
        """Set text suffix."""
        if self._suffix != value:
            self._suffix = value
            self._update_display_text()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(str)
    def current_text(self) -> str:
        """Get current displayed text."""
        return self._current_text
    
    # ==================== Text Properties ====================
    
    @Property(str)
    def font_family(self) -> str:
        """Get font family."""
        return self._font_family
    
    @font_family.setter
    def font_family(self, value: str):
        """Set font family."""
        if self._font_family != value:
            self._font_family = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(int)
    def font_size(self) -> int:
        """Get font size (device coordinates)."""
        return self._font_size
    
    @font_size.setter
    def font_size(self, value: int):
        """Set font size."""
        if self._font_size != value:
            self._font_size = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(bool)
    def bold(self) -> bool:
        """Get bold setting."""
        return self._bold
    
    @bold.setter
    def bold(self, value: bool):
        """Set bold setting."""
        if self._bold != value:
            self._bold = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(QColor)
    def text_color(self) -> QColor:
        """Get text color."""
        return self._text_color
    
    @text_color.setter
    def text_color(self, value: QColor):
        """Set text color."""
        if self._text_color != value:
            self._text_color = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())

    # ==================== Metrics Connection ====================
    
    def set_metrics_provider(self, provider):
        """
        Set the metrics provider.
        
        Args:
            provider: Object with get_metric_value(metric_name) method
        """
        self._metrics_provider = provider
        logger.debug(f"MetricWidget '{self._widget_name}' connected to metrics provider")
        self._update_metric()  # Immediate update
    
    def _get_metric_value(self) -> Any:
        """Get current metric value from provider."""
        if not self._metrics_provider:
            return None
        
        try:
            return self._metrics_provider.get_metric_value(self._metric_type)
        except Exception as e:
            logger.error(f"Failed to get metric '{self._metric_type}': {e}")
            return None
    
    # ==================== Metric Updates ====================
    
    def _update_metric(self):
        """Update metric value from system."""
        if not self._enabled:
            return
        
        # Get new value
        new_value = self._get_metric_value()
        
        # Update if value changed
        if new_value != self._current_value:
            self._current_value = new_value
            self._update_display_text()
            self.update()
    
    def _update_display_text(self):
        """Update displayed text based on current value."""
        if self._current_value is None:
            self._current_text = "N/A"
            return
        
        try:
            # Format based on value type
            if isinstance(self._current_value, (int, float)):
                # Numeric value with formatting
                if self._decimal_places == 0:
                    formatted = f"{int(self._current_value)}"
                else:
                    format_str = f"{{:.{self._decimal_places}f}}"
                    formatted = format_str.format(self._current_value)
                
                # Add unit
                if self._unit:
                    formatted = f"{formatted}{self._unit}"
            else:
                # String value (e.g., CPU name)
                formatted = str(self._current_value)
            
            # Add prefix and suffix
            self._current_text = f"{self._prefix}{formatted}{self._suffix}"
            
        except Exception as e:
            logger.error(f"Failed to format value {self._current_value}: {e}")
            self._current_text = "Error"
    
    # ==================== Drawing ====================
    
    def _draw_widget(self, painter: QPainter, x: float, y: float,
                    width: float, height: float):
        """Draw the metric text."""
        # DO NOT use painter.save()/restore() here!
        # The parent paint() method already handles painter state.
        
        # Set font
        font = QFont(self._font_family)
        scaled_font_size = int(round(self._font_size * self._preview_scale))
        font.setPixelSize(scaled_font_size)
        font.setBold(self._bold)
        painter.setFont(font)
        
        # Set text color
        painter.setPen(QPen(self._text_color))
        
        # Draw text centered in widget bounds
        painter.drawText(0, 0, width, height,
                        Qt.AlignCenter, self._current_text)
    
    # ==================== Enabled State ====================
    
    @UnifiedBaseItem.enabled.setter
    def enabled(self, value: bool):
        """Override enabled setter to control timer."""
        if self._enabled != value:
            self._enabled = value
            if value:
                self._update_timer.start(self._update_interval)
                self._update_metric()  # Immediate update
            else:
                self._update_timer.stop()
                self._current_text = "Disabled"
                self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    # ==================== Property System ====================
    
    def get_properties(self) -> Dict[str, Any]:
        """Get all widget properties."""
        props = super().get_properties()
        props.update({
            'metric_type': self._metric_type,
            'label': getattr(self, '_label', ''),
            'update_interval': self._update_interval,
            'unit': self._unit,
            'decimal_places': self._decimal_places,
            'prefix': self._prefix,
            'suffix': self._suffix,
            'current_text': self._current_text,
            'current_value': self._current_value,
            'font_family': self._font_family,
            'font_size': self._font_size,
            'bold': self._bold,
            'text_color': (self._text_color.red(),
                          self._text_color.green(),
                          self._text_color.blue(),
                          self._text_color.alpha()),
        })
        return props
    
    def set_properties(self, properties: Dict[str, Any]):
        """Set widget properties."""
        # Convert string values to appropriate types
        converted_properties = {}
        for key, value in properties.items():
            if key in ['font_size', 'update_interval', 'decimal_places']:
                # Convert to int
                try:
                    converted_properties[key] = int(value)
                except (ValueError, TypeError):
                    converted_properties[key] = value
            elif key == 'bold':
                # Convert to bool
                if isinstance(value, str):
                    converted_properties[key] = value.lower() in ['true', 'yes', '1', 'on']
                else:
                    converted_properties[key] = bool(value)
            else:
                converted_properties[key] = value
        
        # Handle metric properties
        if 'metric_type' in converted_properties:
            self.metric_type = converted_properties['metric_type']
        if 'update_interval' in converted_properties:
            self.update_interval = converted_properties['update_interval']
        if 'unit' in converted_properties:
            self.unit = converted_properties['unit']
        if 'decimal_places' in converted_properties:
            self.decimal_places = converted_properties['decimal_places']
        if 'prefix' in converted_properties:
            self.prefix = converted_properties['prefix']
        if 'suffix' in converted_properties:
            self.suffix = converted_properties['suffix']
        
        # Handle text properties
        if 'font_family' in converted_properties:
            self.font_family = converted_properties['font_family']
        if 'font_size' in converted_properties:
            self.font_size = converted_properties['font_size']
        if 'bold' in converted_properties:
            self.bold = converted_properties['bold']
        if 'text_color' in converted_properties:
            color = converted_properties['text_color']
            if isinstance(color, (list, tuple)) and len(color) == 4:
                self.text_color = QColor(*color)
        
        # Call parent for basic properties
        super().set_properties(converted_properties)
        
        # Trigger redraw
        self.update()
    
    # ==================== Cleanup ====================
    
    def __del__(self):
        """Cleanup timer."""
        try:
            self._update_timer.stop()
        except:
            pass

# ==================== Specialized Metric Widgets ====================

class TemperatureWidget(MetricWidget):
    """
    Widget for displaying CPU/GPU temperature.
    
    Default settings for temperature display:
    - Unit: °C
    - Decimal places: 1
    - Update interval: 2000ms (2 seconds)
    """
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 120, height: float = 25,
                 preview_scale: float = 1.0, **kwargs):
        # Set temperature defaults
        kwargs.setdefault('unit', '°C')
        kwargs.setdefault('decimal_places', 1)
        kwargs.setdefault('update_interval', 2000)
        
        # Determine if CPU or GPU based on metric_type
        metric_type = kwargs.get('metric_type', 'cpu_temperature')
        if metric_type.startswith('cpu'):
            kwargs.setdefault('prefix', 'CPU: ')
        elif metric_type.startswith('gpu'):
            kwargs.setdefault('prefix', 'GPU: ')
        
        super().__init__(widget_name, x, y, width, height, preview_scale, **kwargs)


class UsageWidget(MetricWidget):
    """
    Widget for displaying CPU/GPU usage percentage.
    
    Default settings for usage display:
    - Unit: %
    - Decimal places: 1
    - Update interval: 1000ms (1 second)
    """
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 120, height: float = 25,
                 preview_scale: float = 1.0, **kwargs):
        # Set usage defaults
        kwargs.setdefault('unit', '%')
        kwargs.setdefault('decimal_places', 1)
        kwargs.setdefault('update_interval', 1000)
        
        # Determine if CPU or GPU based on metric_type
        metric_type = kwargs.get('metric_type', 'cpu_usage')
        if metric_type.startswith('cpu'):
            kwargs.setdefault('prefix', 'CPU: ')
        elif metric_type.startswith('gpu'):
            kwargs.setdefault('prefix', 'GPU: ')
        
        super().__init__(widget_name, x, y, width, height, preview_scale, **kwargs)


class FrequencyWidget(MetricWidget):
    """
    Widget for displaying CPU/GPU frequency.
    
    Default settings for frequency display:
    - Unit: MHz
    - Decimal places: 0
    - Update interval: 3000ms (3 seconds)
    """
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 120, height: float = 25,
                 preview_scale: float = 1.0, **kwargs):
        # Set frequency defaults
        kwargs.setdefault('unit', ' MHz')
        kwargs.setdefault('decimal_places', 0)
        kwargs.setdefault('update_interval', 3000)
        
        # Determine if CPU or GPU based on metric_type
        metric_type = kwargs.get('metric_type', 'cpu_frequency')
        if metric_type.startswith('cpu'):
            kwargs.setdefault('prefix', 'CPU: ')
        elif metric_type.startswith('gpu'):
            kwargs.setdefault('prefix', 'GPU: ')
        
        super().__init__(widget_name, x, y, width, height, preview_scale, **kwargs)


class NameWidget(MetricWidget):
    """
    Widget for displaying CPU/GPU name.
    
    Default settings for name display:
    - No unit
    - Update interval: 10000ms (10 seconds) - names don't change often
    """
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 200, height: float = 25,  # Wider for names
                 preview_scale: float = 1.0, **kwargs):
        # Set name defaults
        kwargs.setdefault('unit', '')
        kwargs.setdefault('decimal_places', 0)
        kwargs.setdefault('update_interval', 10000)  # 10 seconds
        
        # Determine if CPU or GPU based on metric_type
        metric_type = kwargs.get('metric_type', 'cpu_name')
        if metric_type.startswith('cpu'):
            kwargs.setdefault('prefix', 'CPU: ')
        elif metric_type.startswith('gpu'):
            kwargs.setdefault('prefix', 'GPU: ')
        
        super().__init__(widget_name, x, y, width, height, preview_scale, **kwargs)


class RAMWidget(MetricWidget):
    """
    Widget for displaying RAM usage.
    
    Default settings for RAM display:
    - Unit: % for percentage, GB for total
    - Update interval: 2000ms (2 seconds)
    """
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 150, height: float = 25,
                 preview_scale: float = 1.0, **kwargs):
        # Set RAM defaults based on metric type
        metric_type = kwargs.get('metric_type', 'ram_percent')
        
        if metric_type == 'ram_percent':
            kwargs.setdefault('unit', '%')
            kwargs.setdefault('decimal_places', 1)
            kwargs.setdefault('prefix', 'RAM: ')
        elif metric_type == 'ram_total':
            kwargs.setdefault('unit', ' GB')
            kwargs.setdefault('decimal_places', 1)
            kwargs.setdefault('prefix', 'RAM Total: ')
        
        kwargs.setdefault('update_interval', 2000)
        
        super().__init__(widget_name, x, y, width, height, preview_scale, **kwargs)


class GPUMemoryWidget(MetricWidget):
    """
    Widget for displaying GPU memory usage.
    
    Default settings for GPU memory display:
    - Unit: % for percentage, GB for total
    - Update interval: 2000ms (2 seconds)
    """
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 150, height: float = 25,
                 preview_scale: float = 1.0, **kwargs):
        # Set GPU memory defaults based on metric type
        metric_type = kwargs.get('metric_type', 'gpu_mem_percent')
        
        if metric_type == 'gpu_mem_percent':
            kwargs.setdefault('unit', '%')
            kwargs.setdefault('decimal_places', 1)
            kwargs.setdefault('prefix', 'GPU Mem: ')
        elif metric_type == 'gpu_mem_total':
            kwargs.setdefault('unit', ' GB')
            kwargs.setdefault('decimal_places', 1)
            kwargs.setdefault('prefix', 'GPU Mem Total: ')
        
        kwargs.setdefault('update_interval', 2000)
        
        super().__init__(widget_name, x, y, width, height, preview_scale, **kwargs)
