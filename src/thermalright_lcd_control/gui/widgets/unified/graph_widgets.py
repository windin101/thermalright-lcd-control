"""
Unified Widget System - Graph Widgets

This module contains data visualization widgets:
- GraphWidget: Base class for all graph widgets
- BarGraphWidget: Bar chart (vertical/horizontal)
- CircularGraphWidget: Pie/donut chart
"""
from .base import UnifiedBaseItem
from PySide6.QtCore import Qt, QTimer, Signal, Property, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QLinearGradient
from typing import Dict, Any, Optional, Tuple, List, Union
import logging
import math

logger = logging.getLogger(__name__)


class GraphWidget(UnifiedBaseItem):

    def _get_color_from_variant(self, color):
        """Convert color from QVariant, tuple, or QColor to QColor."""
        from PySide6.QtGui import QColor
        
        if hasattr(color, 'value'):  # It's a QVariant
            color_value = color.value()
            if isinstance(color_value, tuple):
                return QColor(*color_value)
            elif isinstance(color_value, QColor):
                return color_value
            else:
                # Try to create QColor from whatever it is
                try:
                    return QColor(color_value)
                except:
                    return QColor(255, 100, 100, 255)  # Fallback red
        elif isinstance(color, tuple):
            return QColor(*color)
        elif isinstance(color, QColor):
            return color
        else:
            # Try to create QColor from whatever it is
            try:
                return QColor(color)
            except:
                return QColor(255, 100, 100, 255)  # Fallback red

    """
    Base class for all graph visualization widgets.
    
    Features:
    - Data series with values and labels
    - Color schemes
    - Animation for value changes
    - Axis/grid display
    """
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 200, height: float = 150,
                 preview_scale: float = 1.0, **kwargs):
        """
        Initialize graph widget base class.
        
        Additional kwargs:
            enabled: bool = True
            show_grid: bool = True
            grid_color: Tuple[int, int, int, int] = (200, 200, 200, 100)
            animation_duration: int = 500  # ms
            data: List[Dict] = []  # List of {value, label, color}
        """
        super().__init__(widget_name, "graph", x, y, width, height, preview_scale)
        
        # Graph properties
        self._show_grid = kwargs.get('show_grid', True)
        self._grid_color = QColor(*kwargs.get('grid_color', (200, 200, 200, 100)))
        self._animation_duration = kwargs.get('animation_duration', 500)
        
        # Data
        self._data = kwargs.get('data', [])
        if not self._data:
            # Default sample data
            self._data = [
                {'value': 30, 'label': 'A', 'color': (255, 100, 100, 255)},
                {'value': 50, 'label': 'B', 'color': (100, 255, 100, 255)},
                {'value': 70, 'label': 'C', 'color': (100, 100, 255, 255)},
                {'value': 40, 'label': 'D', 'color': (255, 255, 100, 255)},
            ]
        
        # Animation
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._update_animation)
        self._animation_progress = 0.0  # 0.0 to 1.0
        self._animating = False
        
        logger.debug(f"GraphWidget '{widget_name}' created")
    
    def _get_layer(self) -> int:
        """Graph widgets are shape layer."""
        return self.SHAPE_LAYER
    
    # ==================== Graph Properties ====================
    
    @Property(bool)
    def show_grid(self) -> bool:
        """Get whether to show grid."""
        return self._show_grid
    
    @show_grid.setter
    def show_grid(self, value: bool):
        """Set whether to show grid."""
        if self._show_grid != value:
            self._show_grid = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(QColor)
    def grid_color(self) -> QColor:
        """Get grid color."""
        return self._grid_color
    
    @grid_color.setter
    def grid_color(self, value: QColor):
        """Set grid color."""
        if self._grid_color != value:
            self._grid_color = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(int)
    def animation_duration(self) -> int:
        """Get animation duration in milliseconds."""
        return self._animation_duration
    
    @animation_duration.setter
    def animation_duration(self, value: int):
        """Set animation duration in milliseconds."""
        if self._animation_duration != value:
            self._animation_duration = max(0, value)
            self.propertiesChanged.emit(self.get_properties())
    
    # ==================== Data Management ====================
    
    def set_data(self, data: List[Dict]):
        """Set graph data and animate the change."""
        if data != self._data:
            self._data = data
            self._start_animation()
    
    def add_data_point(self, value: float, label: str = "", 
                      color: Tuple[int, int, int, int] = None):
        """Add a data point to the graph."""
        if color is None:
            # Generate a color based on index
            hue = (len(self._data) * 60) % 360
            color = self._hsv_to_rgb(hue, 0.8, 0.9)
        
        self._data.append({
            'value': value,
            'label': label,
            'color': color
        })
        self._start_animation()
    
    def clear_data(self):
        """Clear all data from the graph."""
        self._data = []
        self.update()
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int, int]:
        """Convert HSV to RGB color."""
        # Simplified HSV to RGB conversion
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        
        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        return (
            int((r + m) * 255),
            int((g + m) * 255),
            int((b + m) * 255),
            255
        )
    
    # ==================== Animation ====================
    
    def _start_animation(self):
        """Start animation for data changes."""
        if self._animation_duration > 0:
            self._animation_progress = 0.0
            self._animating = True
            interval = 16  # ~60 FPS
            self._animation_timer.start(interval)
        else:
            self.update()
    
    def _update_animation(self):
        """Update animation progress."""
        if not self._animating:
            self._animation_timer.stop()
            return
        
        self._animation_progress += 16 / self._animation_duration  # 16ms per frame
        if self._animation_progress >= 1.0:
            self._animation_progress = 1.0
            self._animating = False
            self._animation_timer.stop()
        
        self.update()
    
    # ==================== Drawing Helpers ====================
    
    def _draw_grid(self, painter: QPainter, bounds: QRectF):
        """Draw grid lines if enabled."""
        if not self._show_grid:
            return
        
        painter.save()
        
        # Set grid pen
        pen = QPen(self._grid_color)
        pen.setWidth(1)
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        
        # Draw vertical grid lines
        grid_count = 5
        for i in range(1, grid_count):
            x = bounds.left() + (bounds.width() * i / grid_count)
            painter.drawLine(QPointF(x, bounds.top()), 
                           QPointF(x, bounds.bottom()))
        
        # Draw horizontal grid lines
        for i in range(1, grid_count):
            y = bounds.top() + (bounds.height() * i / grid_count)
            painter.drawLine(QPointF(bounds.left(), y),
                           QPointF(bounds.right(), y))
        
        painter.restore()
    
    def _get_data_bounds(self) -> Tuple[float, float]:
        """Get min and max values from data."""
        if not self._data:
            return 0.0, 100.0
        
        values = [item['value'] for item in self._data]
        return min(values), max(values)
    
    # ==================== Property System ====================
    
    def get_properties(self) -> Dict[str, Any]:
        """Get all widget properties."""
        props = super().get_properties()
        props.update({
            'show_grid': self._show_grid,
            'grid_color': (self._grid_color.red(),
                          self._grid_color.green(),
                          self._grid_color.blue(),
                          self._grid_color.alpha()),
            'animation_duration': self._animation_duration,
            'data': self._data.copy(),
        })
        return props
    
    def set_properties(self, properties: Dict[str, Any]):
        """Set widget properties."""
        # Handle graph properties
        if 'show_grid' in properties:
            self.show_grid = properties['show_grid']
        if 'grid_color' in properties:
            color = properties['grid_color']
            if isinstance(color, (list, tuple)) and len(color) == 4:
                self.grid_color = QColor(*color)
        if 'animation_duration' in properties:
            self.animation_duration = properties['animation_duration']
        if 'data' in properties:
            self.set_data(properties['data'])
        
        # Call parent for basic properties
        super().set_properties(properties)
    
    # ==================== Cleanup ====================
    
    def __del__(self):
        """Cleanup timer."""
        try:
            self._animation_timer.stop()
        except:
            pass

# ==================== Bar Graph Widget ====================

class BarGraphWidget(GraphWidget):
    """
    Widget that displays a bar chart.
    
    Features:
    - Vertical or horizontal bars
    - Bar spacing and width control
    - Value labels
    - Color gradients
    """
    
    ORIENTATION_VERTICAL = "vertical"
    ORIENTATION_HORIZONTAL = "horizontal"
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 200, height: float = 150,
                 preview_scale: float = 1.0, **kwargs):
        """
        Initialize bar graph widget.
        
        Additional kwargs (beyond GraphWidget):
            orientation: str = "vertical"  # "vertical" or "horizontal"
            bar_spacing: float = 0.2  # 0.0 to 1.0 (percentage of bar width)
            show_values: bool = True
            show_labels: bool = True
            value_format: str = "{:.1f}"  # Format string for values
            max_value: float = None  # Auto-calculated if None
        """
        kwargs.setdefault('orientation', self.ORIENTATION_VERTICAL)
        kwargs.setdefault('bar_spacing', 0.2)
        kwargs.setdefault('show_values', True)
        kwargs.setdefault('show_labels', True)
        kwargs.setdefault('value_format', "{:.1f}")
        kwargs.setdefault('metric_name', 'cpu_usage')
        
        super().__init__(widget_name, x, y, width, height, preview_scale, **kwargs)
        
        # Bar graph specific properties
        self._orientation = kwargs.get('orientation', self.ORIENTATION_VERTICAL)
        self._bar_spacing = kwargs.get('bar_spacing', 0.2)
        self._show_values = kwargs.get('show_values', True)
        self._show_labels = kwargs.get('show_labels', True)
        self._value_format = kwargs.get('value_format', "{:.1f}")
        self._max_value = kwargs.get('max_value')
        self._metric_name = kwargs.get('metric_name', 'cpu_usage')
        
        # Set sample data based on metric for preview
        self._set_sample_data_for_metric()
        
        # Update widget type
        self._widget_type = "bar_graph"
        
        logger.debug(f"BarGraphWidget '{widget_name}' created ({self._orientation})")
    
    def _set_sample_data_for_metric(self):
        """Set sample data for preview based on metric type."""
        if self._metric_name == 'cpu_usage':
            self._data = [{'value': 45.0, 'label': 'CPU', 'color': (100, 200, 100, 255)}]
        elif self._metric_name == 'gpu_usage':
            self._data = [{'value': 30.0, 'label': 'GPU', 'color': (100, 100, 200, 255)}]
        elif self._metric_name == 'cpu_temperature':
            self._data = [{'value': 65.0, 'label': 'CPU Temp', 'color': (200, 100, 100, 255)}]
        elif self._metric_name == 'gpu_temperature':
            self._data = [{'value': 55.0, 'label': 'GPU Temp', 'color': (200, 100, 100, 255)}]
        elif self._metric_name == 'cpu_frequency':
            self._data = [{'value': 3.2, 'label': 'CPU Freq', 'color': (100, 200, 200, 255)}]
        elif self._metric_name == 'gpu_frequency':
            self._data = [{'value': 1.5, 'label': 'GPU Freq', 'color': (100, 200, 200, 255)}]
        else:
            # Default sample data
            self._data = [{'value': 50.0, 'label': self._metric_name.replace('_', ' ').title(), 'color': (150, 150, 150, 255)}]
    
    # ==================== Bar Graph Properties ====================
    
    @Property(str)
    def orientation(self) -> str:
        """Get bar orientation."""
        return self._orientation
    
    @orientation.setter
    def orientation(self, value: str):
        """Set bar orientation."""
        if self._orientation != value and value in [self.ORIENTATION_VERTICAL, self.ORIENTATION_HORIZONTAL]:
            self._orientation = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(float)
    def bar_spacing(self) -> float:
        """Get bar spacing (0.0 to 1.0)."""
        return self._bar_spacing
    
    @bar_spacing.setter
    def bar_spacing(self, value: float):
        """Set bar spacing (0.0 to 1.0)."""
        if self._bar_spacing != value:
            self._bar_spacing = max(0.0, min(value, 1.0))
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(bool)
    def show_values(self) -> bool:
        """Get whether to show value labels."""
        return self._show_values
    
    @show_values.setter
    def show_values(self, value: bool):
        """Set whether to show value labels."""
        if self._show_values != value:
            self._show_values = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(bool)
    def show_labels(self) -> bool:
        """Get whether to show data labels."""
        return self._show_labels
    
    @show_labels.setter
    def show_labels(self, value: bool):
        """Set whether to show data labels."""
        if self._show_labels != value:
            self._show_labels = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(str)
    def value_format(self) -> str:
        """Get value format string."""
        return self._value_format
    
    @value_format.setter
    def value_format(self, value: str):
        """Set value format string."""
        if self._value_format != value:
            self._value_format = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(str)
    def metric_name(self) -> str:
        """Get metric name."""
        return self._metric_name
    
    @metric_name.setter
    def metric_name(self, value: str):
        """Set metric name."""
        if self._metric_name != value:
            self._metric_name = value
            self._set_sample_data_for_metric()  # Update sample data
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    # ==================== Drawing ====================
    
    def _draw_widget(self, painter: QPainter, x: float, y: float,
                    width: float, height: float):
        """Draw the bar graph."""
        if not self._data:
            # Draw placeholder
            painter.drawText(0, 0, width, height, Qt.AlignCenter, "No data")
            return
        
        # Calculate drawing bounds (with padding)
        padding = 10 * self._preview_scale
        bounds = QRectF(padding, padding, 
                       width - padding * 2, 
                       height - padding * 2)
        
        # Draw grid
        self._draw_grid(painter, bounds)
        
        # Get data range
        min_val, max_val = self._get_data_bounds()
        if self._max_value is not None:
            max_val = max(max_val, self._max_value)
        
        # Ensure non-zero range
        if max_val <= min_val:
            max_val = min_val + 1
        
        data_range = max_val - min_val
        
        # Calculate bar dimensions
        bar_count = len(self._data)
        if bar_count == 0:
            return
        
        if self._orientation == self.ORIENTATION_VERTICAL:
            self._draw_vertical_bars(painter, bounds, bar_count, min_val, data_range)
        else:
            self._draw_horizontal_bars(painter, bounds, bar_count, min_val, data_range)
    
    def _draw_vertical_bars(self, painter: QPainter, bounds: QRectF, 
                           bar_count: int, min_val: float, data_range: float):
        """Draw vertical bars."""
        # Calculate bar dimensions
        total_width = bounds.width()
        bar_width = total_width / bar_count
        spacing_width = bar_width * self._bar_spacing
        actual_bar_width = bar_width - spacing_width
        
        # Draw each bar
        for i, item in enumerate(self._data):
            value = item['value']
            color = item['color']
            label = item.get('label', '')
            
            # Calculate bar position and height
            bar_x = bounds.left() + (i * bar_width) + (spacing_width / 2)
            bar_height = ((value - min_val) / data_range) * bounds.height()
            bar_y = bounds.bottom() - bar_height
            
            # Apply animation
            if self._animating:
                bar_height *= self._animation_progress
                bar_y = bounds.bottom() - bar_height
            
            # Draw bar
            painter.save()
            
            # Create gradient for bar
            gradient = QLinearGradient(bar_x, bar_y, 
                                      bar_x + actual_bar_width, bar_y)
        # Handle color which might be QVariant, tuple, or QColor
        if hasattr(color, 'value'):  # It's a QVariant
            color_value = color.value()
            if isinstance(color_value, tuple):
                base_color = QColor(*color_value)
            elif isinstance(color_value, QColor):
                base_color = color_value
            else:
                # Try to create QColor from whatever it is
                try:
                    base_color = QColor(color_value)
                except:
                    base_color = QColor(255, 100, 100, 255)  # Fallback red
        elif isinstance(color, tuple):
            base_color = QColor(*color)
        elif isinstance(color, QColor):
            base_color = color
        else:
            # Try to create QColor from whatever it is
            try:
                base_color = self._get_color_from_variant(color)
            except:
                base_color = QColor(255, 100, 100, 255)  # Fallback red
            gradient.setColorAt(0, base_color.lighter(120))
            gradient.setColorAt(1, base_color.darker(120))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(base_color.darker(150), 1))
            
            painter.drawRect(bar_x, bar_y, actual_bar_width, bar_height)
            
            # Draw value label
            if self._show_values:
                value_text = self._value_format.format(value)
                text_rect = QRectF(bar_x, bar_y - 20, actual_bar_width, 20)
                painter.setPen(QPen(Qt.black))
                painter.drawText(text_rect, Qt.AlignCenter, value_text)
            
            # Draw data label
            if self._show_labels and label:
                label_rect = QRectF(bar_x, bounds.bottom() + 5, 
                                   actual_bar_width, 15)
                painter.setPen(QPen(Qt.black))
                painter.drawText(label_rect, Qt.AlignCenter, label)
            
            painter.restore()
    
    def _draw_horizontal_bars(self, painter: QPainter, bounds: QRectF,
                             bar_count: int, min_val: float, data_range: float):
        """Draw horizontal bars."""
        # Calculate bar dimensions
        total_height = bounds.height()
        bar_height = total_height / bar_count
        spacing_height = bar_height * self._bar_spacing
        actual_bar_height = bar_height - spacing_height
        
        # Draw each bar
        for i, item in enumerate(self._data):
            value = item['value']
            color = item['color']
            label = item.get('label', '')
            
            # Calculate bar position and width
            bar_y = bounds.top() + (i * bar_height) + (spacing_height / 2)
            bar_width = ((value - min_val) / data_range) * bounds.width()
            
            # Apply animation
            if self._animating:
                bar_width *= self._animation_progress
            
            # Draw bar
            painter.save()
            
            # Create gradient for bar
            gradient = QLinearGradient(bounds.left(), bar_y,
                                      bounds.left(), bar_y + actual_bar_height)
            base_color = self._get_color_from_variant(color)
            gradient.setColorAt(0, base_color.lighter(120))
            gradient.setColorAt(1, base_color.darker(120))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(base_color.darker(150), 1))
            
            painter.drawRect(bounds.left(), bar_y, bar_width, actual_bar_height)
            
            # Draw value label
            if self._show_values:
                value_text = self._value_format.format(value)
                text_rect = QRectF(bounds.left() + bar_width + 5, bar_y,
                                  50, actual_bar_height)
                painter.setPen(QPen(Qt.black))
                painter.drawText(text_rect, Qt.AlignVCenter, value_text)
            
            # Draw data label
            if self._show_labels and label:
                label_rect = QRectF(bounds.left() - 60, bar_y,
                                  55, actual_bar_height)
                painter.setPen(QPen(Qt.black))
                painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, label)
            
            painter.restore()
    
    # ==================== Property System ====================
    
    def get_properties(self) -> Dict[str, Any]:
        """Get all widget properties."""
        props = super().get_properties()
        props.update({
            'orientation': self._orientation,
            'bar_spacing': self._bar_spacing,
            'show_values': self._show_values,
            'show_labels': self._show_labels,
            'value_format': self._value_format,
            'max_value': self._max_value,
            'metric_name': self._metric_name,
            'widget_type': self._widget_type,  # Override parent
        })
        # Remove data since bar graphs use metrics
        if 'data' in props:
            del props['data']
        return props
    
    def set_properties(self, properties: Dict[str, Any]):
        """Set widget properties."""
        # Handle bar graph properties
        if 'orientation' in properties:
            self.orientation = properties['orientation']
        if 'bar_spacing' in properties:
            self.bar_spacing = properties['bar_spacing']
        if 'show_values' in properties:
            self.show_values = properties['show_values']
        if 'show_labels' in properties:
            self.show_labels = properties['show_labels']
        if 'value_format' in properties:
            self.value_format = properties['value_format']
        if 'max_value' in properties:
            # Ensure max_value is a float or None
            max_val = properties['max_value']
            if max_val is not None and not isinstance(max_val, (int, float)):
                try:
                    max_val = float(max_val)
                except (ValueError, TypeError):
                    max_val = None
            self._max_value = max_val
            self.update()
        if 'metric_name' in properties:
            self.metric_name = properties['metric_name']
        
        # Call parent for graph properties
        super().set_properties(properties)

# ==================== Circular Graph Widget ====================

class CircularGraphWidget(GraphWidget):
    """
    Widget that displays a circular chart (pie/donut).
    
    Features:
    - Pie chart or donut chart
    - Exploded segments
    - Percentage labels
    - Smooth animations
    """
    
    CHART_PIE = "pie"
    CHART_DONUT = "donut"
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 200, height: float = 200,  # Square for circle
                 preview_scale: float = 1.0, **kwargs):
        """
        Initialize circular graph widget.
        
        Additional kwargs (beyond GraphWidget):
            chart_type: str = "pie"  # "pie" or "donut"
            hole_size: float = 0.4  # 0.0 to 0.9 (for donut charts)
            show_percentages: bool = True
            exploded: bool = False  # Separate segments slightly
            explode_distance: float = 10.0
        """
        # Set circular graph defaults
        kwargs.setdefault('chart_type', self.CHART_PIE)
        kwargs.setdefault('hole_size', 0.4)
        kwargs.setdefault('show_percentages', True)
        kwargs.setdefault('exploded', False)
        kwargs.setdefault('explode_distance', 10.0)
        kwargs.setdefault('metric_name', 'cpu_usage')
        
        # Ensure square dimensions for circular chart
        if width != height:
            size = min(width, height)
            width = height = size
        
        super().__init__(widget_name, x, y, width, height, preview_scale, **kwargs)
        
        # Circular graph specific properties
        self._chart_type = kwargs.get('chart_type', self.CHART_PIE)
        self._hole_size = kwargs.get('hole_size', 0.4)
        self._show_percentages = kwargs.get('show_percentages', True)
        self._exploded = kwargs.get('exploded', False)
        self._explode_distance = kwargs.get('explode_distance', 10.0)
        self._metric_name = kwargs.get('metric_name', 'cpu_usage')
        
        # Set sample data based on metric for preview
        self._set_sample_data_for_metric()
        
        # Update widget type
        self._widget_type = "circular_graph"
        
        logger.debug(f"CircularGraphWidget '{widget_name}' created ({self._chart_type})")
    
    def _set_sample_data_for_metric(self):
        """Set sample data for preview based on metric type."""
        if self._metric_name == 'cpu_usage':
            self._data = [{'value': 45.0, 'label': 'CPU', 'color': (100, 200, 100, 255)}]
        elif self._metric_name == 'gpu_usage':
            self._data = [{'value': 30.0, 'label': 'GPU', 'color': (100, 100, 200, 255)}]
        elif self._metric_name == 'cpu_temperature':
            self._data = [{'value': 65.0, 'label': 'CPU Temp', 'color': (200, 100, 100, 255)}]
        elif self._metric_name == 'gpu_temperature':
            self._data = [{'value': 55.0, 'label': 'GPU Temp', 'color': (200, 100, 100, 255)}]
        elif self._metric_name == 'cpu_frequency':
            self._data = [{'value': 3.2, 'label': 'CPU Freq', 'color': (100, 200, 200, 255)}]
        elif self._metric_name == 'gpu_frequency':
            self._data = [{'value': 1.5, 'label': 'GPU Freq', 'color': (100, 200, 200, 255)}]
        else:
            # Default sample data
            self._data = [{'value': 50.0, 'label': self._metric_name.replace('_', ' ').title(), 'color': (150, 150, 150, 255)}]
    
    # ==================== Circular Graph Properties ====================
    
    @Property(str)
    def chart_type(self) -> str:
        """Get chart type (pie or donut)."""
        return self._chart_type
    
    @chart_type.setter
    def chart_type(self, value: str):
        """Set chart type (pie or donut)."""
        if self._chart_type != value and value in [self.CHART_PIE, self.CHART_DONUT]:
            self._chart_type = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(float)
    def hole_size(self) -> float:
        """Get hole size for donut charts (0.0 to 0.9)."""
        return self._hole_size
    
    @hole_size.setter
    def hole_size(self, value: float):
        """Set hole size for donut charts (0.0 to 0.9)."""
        if self._hole_size != value:
            self._hole_size = max(0.0, min(value, 0.9))
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(bool)
    def show_percentages(self) -> bool:
        """Get whether to show percentage labels."""
        return self._show_percentages
    
    @show_percentages.setter
    def show_percentages(self, value: bool):
        """Set whether to show percentage labels."""
        if self._show_percentages != value:
            self._show_percentages = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(bool)
    def exploded(self) -> bool:
        """Get whether segments are exploded."""
        return self._exploded
    
    @exploded.setter
    def exploded(self, value: bool):
        """Set whether segments are exploded."""
        if self._exploded != value:
            self._exploded = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(float)
    def explode_distance(self) -> float:
        """Get explode distance."""
        return self._explode_distance
    
    @explode_distance.setter
    def explode_distance(self, value: float):
        """Set explode distance."""
        if self._explode_distance != value:
            self._explode_distance = max(0.0, value)
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(str)
    def metric_name(self) -> str:
        """Get metric name."""
        return self._metric_name
    
    @metric_name.setter
    def metric_name(self, value: str):
        """Set metric name."""
        if self._metric_name != value:
            self._metric_name = value
            self._set_sample_data_for_metric()  # Update sample data
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    # ==================== Drawing ====================
    
    def _draw_widget(self, painter: QPainter, x: float, y: float,
                    width: float, height: float):
        """Draw the circular graph."""
        if not self._data:
            # Draw placeholder
            painter.drawText(0, 0, width, height, Qt.AlignCenter, "No data")
            return
        
        # Calculate total value for percentages
        total_value = sum(item['value'] for item in self._data)
        if total_value == 0:
            # Draw empty circle
            self._draw_empty_chart(painter, width, height)
            return
        
        # Calculate drawing bounds (centered square)
        size = min(width, height)
        chart_size = size * 0.8  # 80% of available space
        center_x = width / 2
        center_y = height / 2
        radius = chart_size / 2
        
        # Draw background circle first
        painter.save()
        painter.setBrush(QBrush(QColor(32, 32, 32, 255)))  # Dark background like bar graphs
        painter.setPen(QPen(QColor(64, 64, 64, 255), 2))
        painter.drawEllipse(center_x - radius, center_y - radius,
                           radius * 2, radius * 2)
        painter.restore()
        
        # Draw grid if enabled
        if self._show_grid:
            self._draw_circular_grid(painter, center_x, center_y, radius)
        
        # Draw chart
        if self._chart_type == self.CHART_PIE:
            self._draw_pie_chart(painter, center_x, center_y, radius, total_value)
        else:
            self._draw_donut_chart(painter, center_x, center_y, radius, total_value)
    
    def _draw_empty_chart(self, painter: QPainter, width: float, height: float):
        """Draw empty chart placeholder."""
        size = min(width, height)
        chart_size = size * 0.8
        center_x = width / 2
        center_y = height / 2
        radius = chart_size / 2
        
        painter.save()
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawEllipse(center_x - radius, center_y - radius,
                           radius * 2, radius * 2)
        painter.restore()
    
    def _draw_circular_grid(self, painter: QPainter, center_x: float, 
                           center_y: float, radius: float):
        """Draw circular grid lines."""
        painter.save()
        
        pen = QPen(self._grid_color)
        pen.setWidth(1)
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        
        # Draw concentric circles
        for i in range(1, 4):
            r = radius * (i / 4)
            painter.drawEllipse(center_x - r, center_y - r, r * 2, r * 2)
        
        # Draw radial lines
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x2 = center_x + radius * math.cos(rad)
            y2 = center_y + radius * math.sin(rad)
            painter.drawLine(center_x, center_y, x2, y2)
        
        painter.restore()
    
    def _draw_pie_chart(self, painter: QPainter, center_x: float, center_y: float,
                       radius: float, total_value: float):
        """Draw pie chart."""
        start_angle = 0
        
        for i, item in enumerate(self._data):
            value = item['value']
            color = item['color']
            label = item.get('label', '')
            
            # Calculate angle for this segment
            angle = (value / total_value) * 360
            
            # Apply animation
            if self._animating:
                angle *= self._animation_progress
            
            # Calculate explode offset
            offset_x = offset_y = 0
            if self._exploded:
                mid_angle = start_angle + angle / 2
                rad = math.radians(mid_angle)
                offset_x = math.cos(rad) * self._explode_distance * self._preview_scale
                offset_y = math.sin(rad) * self._explode_distance * self._preview_scale
            
            # Draw segment
            painter.save()
            
            base_color = self._get_color_from_variant(color)
            painter.setBrush(QBrush(base_color))
            painter.setPen(QPen(base_color.darker(150), 1))
            
            # Draw pie segment
            segment_rect = QRectF(center_x - radius + offset_x,
                                 center_y - radius + offset_y,
                                 radius * 2, radius * 2)
            
            span_angle = int(angle * 16)  # Qt uses 1/16th degree units
            start_angle_16 = int(start_angle * 16)
            
            path = QPainterPath()
            path.moveTo(center_x + offset_x, center_y + offset_y)
            path.arcTo(segment_rect, start_angle, angle)
            path.closeSubpath()
            
            painter.drawPath(path)
            
            # Draw percentage label
            if self._show_percentages and angle > 15:  # Only if segment is large enough
                percentage = (value / total_value) * 100
                label_text = f"{percentage:.1f}%"
                
                # Calculate label position (middle of segment)
                label_angle = start_angle + angle / 2
                label_rad = math.radians(label_angle)
                label_distance = radius * 0.6  # 60% from center
                
                label_x = center_x + offset_x + label_distance * math.cos(label_rad)
                label_y = center_y + offset_y + label_distance * math.sin(label_rad)
                
                painter.setPen(QPen(Qt.white))
                font = painter.font()
                font.setBold(True)
                painter.setFont(font)
                
                # Draw text with background for readability
                # Get text bounding box
                text_rect = painter.boundingRect(0, 0, 0, 0, Qt.AlignCenter, label_text)
                # Convert to QRectF for floating point coordinates
                text_rect_f = QRectF(text_rect)
                text_rect_f.moveCenter(QPointF(label_x, label_y))
                
                painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
                painter.setPen(Qt.NoPen)
                painter.drawRect(text_rect_f.adjusted(-2, -2, 2, 2))
                
                painter.setPen(QPen(Qt.white))
                painter.drawText(text_rect_f, Qt.AlignCenter, label_text)
            
            painter.restore()
            
            # Update start angle for next segment
            start_angle += angle
    
    def _draw_donut_chart(self, painter: QPainter, center_x: float, center_y: float,
                         outer_radius: float, total_value: float):
        """Draw donut chart."""
        inner_radius = outer_radius * self._hole_size
        start_angle = 0
        
        for i, item in enumerate(self._data):
            value = item['value']
            color = item['color']
            label = item.get('label', '')
            
            # Calculate angle for this segment
            angle = (value / total_value) * 360
            
            # Apply animation
            if self._animating:
                angle *= self._animation_progress
            
            # Calculate explode offset
            offset_x = offset_y = 0
            if self._exploded:
                mid_angle = start_angle + angle / 2
                rad = math.radians(mid_angle)
                offset_x = math.cos(rad) * self._explode_distance * self._preview_scale
                offset_y = math.sin(rad) * self._explode_distance * self._preview_scale
            
            # Draw segment
            painter.save()
            
            base_color = self._get_color_from_variant(color)
            
            # Create gradient for donut segment
            gradient = QLinearGradient(center_x - outer_radius, center_y - outer_radius,
                                      center_x + outer_radius, center_y + outer_radius)
            gradient.setColorAt(0, base_color.lighter(120))
            gradient.setColorAt(1, base_color.darker(120))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(base_color.darker(150), 1))
            
            # Draw donut segment using path
            path = QPainterPath()
            
            # Outer arc
            outer_rect = QRectF(center_x - outer_radius + offset_x,
                               center_y - outer_radius + offset_y,
                               outer_radius * 2, outer_radius * 2)
            path.arcMoveTo(outer_rect, start_angle)
            path.arcTo(outer_rect, start_angle, angle)
            
            # Connect to inner arc
            inner_rect = QRectF(center_x - inner_radius + offset_x,
                               center_y - inner_radius + offset_y,
                               inner_radius * 2, inner_radius * 2)
            path.arcTo(inner_rect, start_angle + angle, -angle)
            
            path.closeSubpath()
            painter.drawPath(path)
            
            # Draw percentage label
            if self._show_percentages and angle > 15:
                percentage = (value / total_value) * 100
                label_text = f"{percentage:.1f}%"
                
                # Calculate label position (middle of donut segment)
                label_angle = start_angle + angle / 2
                label_rad = math.radians(label_angle)
                label_distance = (outer_radius + inner_radius) / 2
                
                label_x = center_x + offset_x + label_distance * math.cos(label_rad)
                label_y = center_y + offset_y + label_distance * math.sin(label_rad)
                
                painter.setPen(QPen(Qt.white))
                font = painter.font()
                font.setBold(True)
                painter.setFont(font)
                
                # Draw text with background
                # Get text bounding box
                text_rect = painter.boundingRect(0, 0, 0, 0, Qt.AlignCenter, label_text)
                # Convert to QRectF for floating point coordinates
                text_rect_f = QRectF(text_rect)
                text_rect_f.moveCenter(QPointF(label_x, label_y))
                
                painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
                painter.setPen(Qt.NoPen)
                painter.drawRect(text_rect_f.adjusted(-2, -2, 2, 2))
                
                painter.setPen(QPen(Qt.white))
                painter.drawText(text_rect_f, Qt.AlignCenter, label_text)
            
            painter.restore()
            
            # Update start angle for next segment
            start_angle += angle
    
    # ==================== Property System ====================
    
    def get_properties(self) -> Dict[str, Any]:
        """Get all widget properties."""
        props = super().get_properties()
        props.update({
            'chart_type': self._chart_type,
            'hole_size': self._hole_size,
            'show_percentages': self._show_percentages,
            'exploded': self._exploded,
            'explode_distance': self._explode_distance,
            'metric_name': self._metric_name,
            'widget_type': self._widget_type,  # Override parent
        })
        # Remove data since circular graphs use metrics
        if 'data' in props:
            del props['data']
        return props
    
    def set_properties(self, properties: Dict[str, Any]):
        """Set widget properties."""
        # Handle circular graph properties
        if 'chart_type' in properties:
            self.chart_type = properties['chart_type']
        if 'hole_size' in properties:
            self.hole_size = properties['hole_size']
        if 'show_percentages' in properties:
            self.show_percentages = properties['show_percentages']
        if 'exploded' in properties:
            self.exploded = properties['exploded']
        if 'explode_distance' in properties:
            self.explode_distance = properties['explode_distance']
        if 'metric_name' in properties:
            self.metric_name = properties['metric_name']
        
        # Call parent for graph properties
        super().set_properties(properties)
