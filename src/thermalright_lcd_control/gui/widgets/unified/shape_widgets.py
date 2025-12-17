"""
Unified Widget System - Shape Widgets

This module contains geometric shape widgets:
- RectangleWidget: Rectangle with fill and border
- RoundedRectangleWidget: Rectangle with rounded corners
- CircleWidget: Circle/ellipse with fill and border
"""
from .base import UnifiedBaseItem
from PySide6.QtCore import Qt, Signal, Property
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath
from typing import Dict, Any, Optional, Tuple
import logging
import math

logger = logging.getLogger(__name__)


class RectangleWidget(UnifiedBaseItem):
    """
    Widget that displays a rectangle.
    
    Features:
    - Fill color with transparency
    - Border color and width
    - No rounded corners (sharp edges)
    """
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 100, height: float = 60,
                 preview_scale: float = 1.0, **kwargs):
        """
        Initialize rectangle widget.
        
        Additional kwargs:
            enabled: bool = True
            fill_color: Tuple[int, int, int, int] = (255, 255, 255, 128)  # Semi-transparent white
            border_color: Tuple[int, int, int, int] = (0, 0, 0, 255)      # Black
            border_width: int = 1
        """
        super().__init__(widget_name, "rectangle", x, y, width, height, preview_scale)
        
        # Shape properties
        self._fill_color = QColor(*kwargs.get('fill_color', (255, 255, 255, 128)))
        self._border_color = QColor(*kwargs.get('border_color', (0, 0, 0, 255)))
        self._border_width = kwargs.get('border_width', 1)
        
        logger.debug(f"RectangleWidget '{widget_name}' created: {width}x{height}")
    
    def _get_layer(self) -> int:
        """Rectangle widgets are shape layer."""
        return self.SHAPE_LAYER
    
    # ==================== Shape Properties ====================
    
    @Property(QColor)
    def fill_color(self) -> QColor:
        """Get fill color."""
        return self._fill_color
    
    @fill_color.setter
    def fill_color(self, value: QColor):
        """Set fill color."""
        if self._fill_color != value:
            self._fill_color = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(QColor)
    def border_color(self) -> QColor:
        """Get border color."""
        return self._border_color
    
    @border_color.setter
    def border_color(self, value: QColor):
        """Set border color."""
        if self._border_color != value:
            self._border_color = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(int)
    def border_width(self) -> int:
        """Get border width."""
        return self._border_width
    
    @border_width.setter
    def border_width(self, value: int):
        """Set border width."""
        if self._border_width != value:
            self._border_width = max(0, value)  # Ensure non-negative
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    # ==================== Drawing ====================
    
    def _draw_widget(self, painter: QPainter, x: float, y: float,
                    width: float, height: float):
        """Draw the rectangle."""
        painter.save()
        
        # Draw fill
        if self._fill_color.alpha() > 0:  # Only draw if not fully transparent
            painter.setBrush(QBrush(self._fill_color))
        else:
            painter.setBrush(Qt.NoBrush)
        
        # Draw border
        if self._border_width > 0 and self._border_color.alpha() > 0:
            pen = QPen(self._border_color)
            scaled_border_width = max(1, int(round(self._border_width * self._preview_scale)))
            pen.setWidth(scaled_border_width)
            painter.setPen(pen)
        else:
            painter.setPen(Qt.NoPen)
        
        # Draw rectangle
        painter.drawRect(x, y, width, height)
        
        painter.restore()
    
    # ==================== Property System ====================
    
    def get_properties(self) -> Dict[str, Any]:
        """Get all widget properties."""
        props = super().get_properties()
        props.update({
            'fill_color': (self._fill_color.red(),
                          self._fill_color.green(),
                          self._fill_color.blue(),
                          self._fill_color.alpha()),
            'border_color': (self._border_color.red(),
                            self._border_color.green(),
                            self._border_color.blue(),
                            self._border_color.alpha()),
            'border_width': self._border_width,
        })
        return props
    
    def set_properties(self, properties: Dict[str, Any]):
        """Set widget properties."""
        # Handle shape properties
        if 'fill_color' in properties:
            color = properties['fill_color']
            if isinstance(color, (list, tuple)) and len(color) == 4:
                self.fill_color = QColor(*color)
        
        if 'border_color' in properties:
            color = properties['border_color']
            if isinstance(color, (list, tuple)) and len(color) == 4:
                self.border_color = QColor(*color)
        
        if 'border_width' in properties:
            self.border_width = properties['border_width']
        
        # Call parent for basic properties
        super().set_properties(properties)


class RoundedRectangleWidget(RectangleWidget):
    """
    Widget that displays a rectangle with rounded corners.
    
    Inherits from RectangleWidget and adds:
    - Corner radius parameter
    """
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 100, height: float = 60,
                 preview_scale: float = 1.0, **kwargs):
        """
        Initialize rounded rectangle widget.
        
        Additional kwargs (beyond RectangleWidget):
            corner_radius: int = 10
        """
        # Store corner radius before calling parent
        self._corner_radius = kwargs.get('corner_radius', 10)
        
        # Remove corner_radius from kwargs before passing to parent
        if 'corner_radius' in kwargs:
            kwargs_copy = kwargs.copy()
            del kwargs_copy['corner_radius']
            super().__init__(widget_name, x, y, width, height, preview_scale, **kwargs_copy)
        else:
            super().__init__(widget_name, x, y, width, height, preview_scale, **kwargs)
        
        # Update widget type
        self._widget_type = "rounded_rectangle"
        
        logger.debug(f"RoundedRectangleWidget '{widget_name}' created with radius {self._corner_radius}")
    
    # ==================== Rounded Properties ====================
    
    @Property(int)
    def corner_radius(self) -> int:
        """Get corner radius."""
        return self._corner_radius
    
    @corner_radius.setter
    def corner_radius(self, value: int):
        """Set corner radius."""
        if self._corner_radius != value:
            self._corner_radius = max(0, value)  # Ensure non-negative
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    # ==================== Drawing ====================
    
    def _draw_widget(self, painter: QPainter, x: float, y: float,
                    width: float, height: float):
        """Draw the rounded rectangle."""
        painter.save()
        
        # Calculate scaled corner radius
        scaled_radius = int(round(self._corner_radius * self._preview_scale))
        
        # Create rounded rectangle path
        path = QPainterPath()
        path.addRoundedRect(x, y, width, height, scaled_radius, scaled_radius)
        
        # Draw fill
        if self._fill_color.alpha() > 0:
            painter.fillPath(path, QBrush(self._fill_color))
        
        # Draw border
        if self._border_width > 0 and self._border_color.alpha() > 0:
            pen = QPen(self._border_color)
            scaled_border_width = max(1, int(round(self._border_width * self._preview_scale)))
            pen.setWidth(scaled_border_width)
            painter.setPen(pen)
            painter.drawPath(path)
        
        painter.restore()
    
    # ==================== Property System ====================
    
    def get_properties(self) -> Dict[str, Any]:
        """Get all widget properties."""
        props = super().get_properties()
        props.update({
            'corner_radius': self._corner_radius,
            'widget_type': self._widget_type,  # Override parent's type
        })
        return props
    
    def set_properties(self, properties: Dict[str, Any]):
        """Set widget properties."""
        # Handle rounded rectangle properties
        if 'corner_radius' in properties:
            self.corner_radius = properties['corner_radius']
        
        # Call parent for rectangle properties
        super().set_properties(properties)


class CircleWidget(UnifiedBaseItem):
    """
    Widget that displays a circle or ellipse.
    
    Features:
    - Fill color with transparency
    - Border color and width
    - Can be ellipse if width != height
    """
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 80, height: float = 80,  # Default to square for circle
                 preview_scale: float = 1.0, **kwargs):
        """
        Initialize circle widget.
        
        Additional kwargs:
            enabled: bool = True
            fill_color: Tuple[int, int, int, int] = (255, 255, 255, 128)  # Semi-transparent white
            border_color: Tuple[int, int, int, int] = (0, 0, 0, 255)      # Black
            border_width: int = 1
        """
        super().__init__(widget_name, "circle", x, y, width, height, preview_scale)
        
        # Shape properties
        self._fill_color = QColor(*kwargs.get('fill_color', (255, 255, 255, 128)))
        self._border_color = QColor(*kwargs.get('border_color', (0, 0, 0, 255)))
        self._border_width = kwargs.get('border_width', 1)
        
        # Calculate radius (average of width/2 and height/2 for ellipse)
        self._radius_x = width / 2
        self._radius_y = height / 2
        
        logger.debug(f"CircleWidget '{widget_name}' created: {width}x{height}")
    
    def _get_layer(self) -> int:
        """Circle widgets are shape layer."""
        return self.SHAPE_LAYER
    
    # ==================== Shape Properties ====================
    
    @Property(QColor)
    def fill_color(self) -> QColor:
        """Get fill color."""
        return self._fill_color
    
    @fill_color.setter
    def fill_color(self, value: QColor):
        """Set fill color."""
        if self._fill_color != value:
            self._fill_color = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(QColor)
    def border_color(self) -> QColor:
        """Get border color."""
        return self._border_color
    
    @border_color.setter
    def border_color(self, value: QColor):
        """Set border color."""
        if self._border_color != value:
            self._border_color = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(int)
    def border_width(self) -> int:
        """Get border width."""
        return self._border_width
    
    @border_width.setter
    def border_width(self, value: int):
        """Set border width."""
        if self._border_width != value:
            self._border_width = max(0, value)  # Ensure non-negative
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(float)
    def radius_x(self) -> float:
        """Get horizontal radius (half of width)."""
        return self._radius_x
    
    @Property(float)
    def radius_y(self) -> float:
        """Get vertical radius (half of height)."""
        return self._radius_y
    
    # ==================== Drawing ====================
    
    def _draw_widget(self, painter: QPainter, x: float, y: float,
                    width: float, height: float):
        """Draw the circle/ellipse."""
        painter.save()
        
        # Draw fill
        if self._fill_color.alpha() > 0:  # Only draw if not fully transparent
            painter.setBrush(QBrush(self._fill_color))
        else:
            painter.setBrush(Qt.NoBrush)
        
        # Draw border
        if self._border_width > 0 and self._border_color.alpha() > 0:
            pen = QPen(self._border_color)
            scaled_border_width = max(1, int(round(self._border_width * self._preview_scale)))
            pen.setWidth(scaled_border_width)
            painter.setPen(pen)
        else:
            painter.setPen(Qt.NoPen)
        
        # Draw ellipse (circle if width == height)
        painter.drawEllipse(x, y, width, height)
        
        painter.restore()
    
    # ==================== Property System ====================
    
    def get_properties(self) -> Dict[str, Any]:
        """Get all widget properties."""
        props = super().get_properties()
        props.update({
            'fill_color': (self._fill_color.red(),
                          self._fill_color.green(),
                          self._fill_color.blue(),
                          self._fill_color.alpha()),
            'border_color': (self._border_color.red(),
                            self._border_color.green(),
                            self._border_color.blue(),
                            self._border_color.alpha()),
            'border_width': self._border_width,
            'radius_x': self._radius_x,
            'radius_y': self._radius_y,
        })
        return props
    
    def set_properties(self, properties: Dict[str, Any]):
        """Set widget properties."""
        # Handle shape properties
        if 'fill_color' in properties:
            color = properties['fill_color']
            if isinstance(color, (list, tuple)) and len(color) == 4:
                self.fill_color = QColor(*color)
        
        if 'border_color' in properties:
            color = properties['border_color']
            if isinstance(color, (list, tuple)) and len(color) == 4:
                self.border_color = QColor(*color)
        
        if 'border_width' in properties:
            self.border_width = properties['border_width']
        
        # Update radii if size changes
        if 'width' in properties or 'height' in properties:
            width = properties.get('width', self._width)
            height = properties.get('height', self._height)
            self._radius_x = width / 2
            self._radius_y = height / 2
        
        # Call parent for basic properties
        super().set_properties(properties)
