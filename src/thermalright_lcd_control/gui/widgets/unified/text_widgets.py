"""
Unified Widget System - Text Widgets

This module contains text-based widgets:
- DateWidget: Displays current date
- TimeWidget: Displays current time  
- FreeTextWidget: Displays custom text
- MetricWidget: Displays system metrics (CPU/GPU/RAM)
"""
from .base import UnifiedBaseItem
from PySide6.QtCore import Qt, QTimer, Signal, Property
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DateWidget(UnifiedBaseItem):
    """
    Widget that displays the current date.
    
    Features:
    - Multiple date formats (dd/MM, MM/dd, etc.)
    - Automatic daily updates
    - Customizable font and color
    """
    
    # Format conversion map: UI format -> strftime format
    FORMAT_MAP = {
        "dd/MM": "%d/%m",          # 15/12
        "MM/dd": "%m/%d",          # 12/15
        "dd-MM": "%d-%m",          # 15-12
        "MM-dd": "%m-%d",          # 12-15
        "dd.MM": "%d.%m",          # 15.12
        "MM.dd": "%m.%d",          # 12.15
        "yyyy-MM-dd": "%Y-%m-%d",  # 2025-12-15
        "dd/MM/yyyy": "%d/%m/%Y",  # 15/12/2025
        "MM/dd/yyyy": "%m/%d/%Y",  # 12/15/2025
    }
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 100, height: float = 20,
                 preview_scale: float = 1.0, **kwargs):
        """
        Initialize date widget.
        
        Additional kwargs:
            enabled: bool = True
            font_family: str = "Arial"
            font_size: int = 12
            bold: bool = False
            text_color: Tuple[int, int, int, int] = (0, 0, 0, 255)
            date_format: str = "dd/MM"
        """
        super().__init__(widget_name, "date", x, y, width, height, preview_scale)
        
        # Text properties
        self._font_family = kwargs.get('font_family', 'Arial')
        self._font_size = kwargs.get('font_size', 12)  # Device coordinates
        self._bold = kwargs.get('bold', False)
        self._text_color = QColor(*kwargs.get('text_color', (0, 0, 0, 255)))
        
        # Date properties
        self._date_format = kwargs.get('date_format', 'dd/MM')
        self._current_date = ""
        
        # Timer for daily updates (update at midnight)
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_date)
        self._update_timer.start(60000)  # Check every minute
        
        # Initial update
        self._update_date()
        
        logger.debug(f"DateWidget '{widget_name}' created with format '{self._date_format}'")
    
    def _get_layer(self) -> int:
        """Date widgets are text layer."""
        return self.TEXT_LAYER
    
    # ==================== Date Properties ====================
    
    @Property(str)
    def date_format(self) -> str:
        """Get date format (e.g., 'dd/MM')."""
        return self._date_format
    
    @date_format.setter
    def date_format(self, value: str):
        """Set date format."""
        if self._date_format != value and value in self.FORMAT_MAP:
            self._date_format = value
            self._update_date()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(str)
    def current_date(self) -> str:
        """Get current displayed date."""
        return self._current_date
    
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
    
    # ==================== Date Updates ====================
    
    def _update_date(self):
        """Update displayed date."""
        if not self._enabled:
            return
        
        # Convert UI format to strftime format
        python_format = self.FORMAT_MAP.get(self._date_format, "%d/%m")
        
        # Get current date
        new_date = datetime.now().strftime(python_format)
        
        # Update if date changed
        if new_date != self._current_date:
            self._current_date = new_date
            self.update()
            logger.debug(f"DateWidget '{self._widget_name}' updated to '{new_date}'")
    
    # ==================== Drawing ====================
    
    def _draw_widget(self, painter: QPainter, x: float, y: float,
                    width: float, height: float):
        """Draw the date text."""
        if not self._current_date:
            return
        
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
        text_rect = painter.boundingRect(0, 0, width, height,
                                        Qt.AlignCenter, self._current_date)
        
        # Adjust position to center
        draw_x = (width - text_rect.width()) / 2
        draw_y = (height - text_rect.height()) / 2
        
        painter.drawText(draw_x, draw_y + text_rect.height(),
                        self._current_date)
    
    # ==================== Property System ====================
    
    def get_properties(self) -> Dict[str, Any]:
        """Get all widget properties."""
        props = super().get_properties()
        props.update({
            'date_format': self._date_format,
            'current_date': self._current_date,
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
        # Handle text properties
        if 'font_family' in properties:
            self.font_family = properties['font_family']
        if 'font_size' in properties:
            self.font_size = properties['font_size']
        if 'bold' in properties:
            self.bold = properties['bold']
        if 'text_color' in properties:
            color = properties['text_color']
            if isinstance(color, (list, tuple)) and len(color) == 4:
                self.text_color = QColor(*color)
        
        # Handle date properties
        if 'date_format' in properties:
            self.date_format = properties['date_format']
        
        # Call parent for basic properties
        super().set_properties(properties)
    
    # ==================== Cleanup ====================
    
    def __del__(self):
        """Cleanup timer."""
        try:
            self._update_timer.stop()
        except:
            pass


class TimeWidget(UnifiedBaseItem):
    """
    Widget that displays the current time.
    
    Features:
    - 12/24 hour format
    - Multiple time formats (HH:mm, hh:mm AP, etc.)
    - Second-by-second updates
    - Customizable font and color
    """
    
    # Format conversion map: UI format -> strftime format
    FORMAT_MAP = {
        "HH:mm": "%H:%M",              # 14:30 (24-hour)
        "hh:mm": "%I:%M",              # 02:30 (12-hour)
        "HH:mm:ss": "%H:%M:%S",        # 14:30:45 (24-hour with seconds)
        "hh:mm:ss": "%I:%M:%S",        # 02:30:45 (12-hour with seconds)
        "HH:mm AP": "%H:%M %p",        # 14:30 PM (24-hour with AM/PM)
        "hh:mm AP": "%I:%M %p",        # 02:30 PM (12-hour with AM/PM)
        "HH:mm:ss AP": "%H:%M:%S %p",  # 14:30:45 PM
        "hh:mm:ss AP": "%I:%M:%S %p",  # 02:30:45 PM
    }
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 100, height: float = 20,
                 preview_scale: float = 1.0, **kwargs):
        """
        Initialize time widget.
        
        Additional kwargs:
            enabled: bool = True
            font_family: str = "Arial"
            font_size: int = 12
            bold: bool = False
            text_color: Tuple[int, int, int, int] = (0, 0, 0, 255)
            time_format: str = "HH:mm"
            use_24_hour: bool = True  # Overridden by time_format if specified
        """
        # Determine time format
        time_format = kwargs.get('time_format', 'HH:mm')
        use_24_hour = kwargs.get('use_24_hour', True)
        
        # If use_24_hour is specified but time_format not, set appropriate format
        if 'time_format' not in kwargs:
            time_format = "HH:mm" if use_24_hour else "hh:mm AP"
        
        # Store format in kwargs for super().__init__
        kwargs['time_format'] = time_format
        
        super().__init__(widget_name, "time", x, y, width, height, preview_scale)
        
        # Text properties
        self._font_family = kwargs.get('font_family', 'Arial')
        self._font_size = kwargs.get('font_size', 12)
        self._bold = kwargs.get('bold', False)
        self._text_color = QColor(*kwargs.get('text_color', (0, 0, 0, 255)))
        
        # Time properties
        self._time_format = time_format
        self._use_24_hour = use_24_hour
        self._current_time = ""
        
        # Timer for second-by-second updates
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_time)
        self._update_timer.start(1000)  # Update every second
        
        # Initial update
        self._update_time()
        
        logger.debug(f"TimeWidget '{widget_name}' created with format '{self._time_format}'")
    
    def _get_layer(self) -> int:
        """Time widgets are text layer."""
        return self.TEXT_LAYER
    
    # ==================== Time Properties ====================
    
    @Property(str)
    def time_format(self) -> str:
        """Get time format (e.g., 'HH:mm')."""
        return self._time_format
    
    @time_format.setter
    def time_format(self, value: str):
        """Set time format."""
        if self._time_format != value and value in self.FORMAT_MAP:
            self._time_format = value
            # Update 24-hour setting based on format
            self._use_24_hour = value.startswith('HH')
            self._update_time()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(bool)
    def use_24_hour(self) -> bool:
        """Get 24-hour format setting."""
        return self._use_24_hour
    
    @use_24_hour.setter
    def use_24_hour(self, value: bool):
        """Set 24-hour format."""
        if self._use_24_hour != value:
            self._use_24_hour = value
            # Update format based on 24-hour setting
            if value:
                self.time_format = "HH:mm"
            else:
                self.time_format = "hh:mm AP"
    
    @Property(str)
    def current_time(self) -> str:
        """Get current displayed time."""
        return self._current_time
    
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
    
    # ==================== Time Updates ====================
    
    def _update_time(self):
        """Update displayed time."""
        if not self._enabled:
            return
        
        # Convert UI format to strftime format
        python_format = self.FORMAT_MAP.get(self._time_format, "%H:%M")
        
        # Get current time
        new_time = datetime.now().strftime(python_format)
        
        # Update if time changed
        if new_time != self._current_time:
            self._current_time = new_time
            self.update()
            # Debug logging less frequently to avoid spam
            # logger.debug(f"TimeWidget '{self._widget_name}' updated to '{new_time}'")
    
    # ==================== Drawing ====================
    
    def _draw_widget(self, painter: QPainter, x: float, y: float,
                    width: float, height: float):
        """Draw the time text."""
        if not self._current_time:
            return
        
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
        # Get text metrics without alignment flags
        text_rect = painter.boundingRect(0, 0, 0, 0, 0, self._current_time)
        
        # Calculate centered position
        draw_x = (width - text_rect.width()) / 2
        draw_y = (height + text_rect.height()) / 2
        
        painter.drawText(int(draw_x), int(draw_y), self._current_time)
    
    # ==================== Property System ====================
    
    def get_properties(self) -> Dict[str, Any]:
        """Get all widget properties."""
        props = super().get_properties()
        props.update({
            'time_format': self._time_format,
            'use_24_hour': self._use_24_hour,
            'current_time': self._current_time,
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
        # Handle text properties
        if 'font_family' in properties:
            self.font_family = properties['font_family']
        if 'font_size' in properties:
            self.font_size = properties['font_size']
        if 'bold' in properties:
            self.bold = properties['bold']
        if 'text_color' in properties:
            color = properties['text_color']
            if isinstance(color, (list, tuple)) and len(color) == 4:
                self.text_color = QColor(*color)
        
        # Handle time properties
        if 'time_format' in properties:
            self.time_format = properties['time_format']
        if 'use_24_hour' in properties:
            self.use_24_hour = properties['use_24_hour']
        
        # Call parent for basic properties
        super().set_properties(properties)
    
    # ==================== Cleanup ====================
    
    def __del__(self):
        """Cleanup timer."""
        try:
            self._update_timer.stop()
        except:
            pass

class FreeTextWidget(UnifiedBaseItem):
    """
    Widget that displays custom text.
    
    Features:
    - User-defined text content
    - Customizable font, size, color
    - Text alignment options
    - No automatic updates (static text)
    """
    
    def __init__(self, widget_name: str, x: float, y: float,
                 width: float = 100, height: float = 20,
                 preview_scale: float = 1.0, **kwargs):
        """
        Initialize free text widget.
        
        Additional kwargs:
            enabled: bool = True
            font_family: str = "Arial"
            font_size: int = 12
            bold: bool = False
            text_color: Tuple[int, int, int, int] = (0, 0, 0, 255)
            text: str = "Text"
            alignment: str = "center"  # "left", "center", "right"
        """
        super().__init__(widget_name, "free_text", x, y, width, height, preview_scale)
        
        # Text properties
        self._font_family = kwargs.get('font_family', 'Arial')
        self._font_size = kwargs.get('font_size', 12)
        self._bold = kwargs.get('bold', False)
        self._text_color = QColor(*kwargs.get('text_color', (0, 0, 0, 255)))
        
        # Text content
        self._text = kwargs.get('text', 'Text')
        self._alignment = kwargs.get('alignment', 'center')
        
        logger.debug(f"FreeTextWidget '{widget_name}' created with text: '{self._text}'")
    
    def _get_layer(self) -> int:
        """Free text widgets are text layer."""
        return self.TEXT_LAYER
    
    # ==================== Text Properties ====================
    
    @Property(str)
    def text(self) -> str:
        """Get displayed text."""
        return self._text
    
    @text.setter
    def text(self, value: str):
        """Set displayed text."""
        if self._text != value:
            self._text = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(str)
    def alignment(self) -> str:
        """Get text alignment."""
        return self._alignment
    
    @alignment.setter
    def alignment(self, value: str):
        """Set text alignment."""
        if self._alignment != value and value in ('left', 'center', 'right'):
            self._alignment = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
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
    
    # ==================== Drawing ====================
    
    def _draw_widget(self, painter: QPainter, x: float, y: float,
                    width: float, height: float):
        """Draw the text."""
        if not self._text:
            return
        
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
        
        # Determine alignment
        if self._alignment == 'left':
            alignment = Qt.AlignLeft | Qt.AlignVCenter
        elif self._alignment == 'right':
            alignment = Qt.AlignRight | Qt.AlignVCenter
        else:  # center
            alignment = Qt.AlignCenter
        
        # Draw text
        painter.drawText(0, 0, width, height, alignment, self._text)
    
    # ==================== Property System ====================
    
    def get_properties(self) -> Dict[str, Any]:
        """Get all widget properties."""
        props = super().get_properties()
        props.update({
            'text': self._text,
            'alignment': self._alignment,
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
        # Handle text properties
        if 'text' in properties:
            self.text = properties['text']
        if 'alignment' in properties:
            self.alignment = properties['alignment']
        if 'font_family' in properties:
            self.font_family = properties['font_family']
        if 'font_size' in properties:
            self.font_size = properties['font_size']
        if 'bold' in properties:
            self.bold = properties['bold']
        if 'text_color' in properties:
            color = properties['text_color']
            if isinstance(color, (list, tuple)) and len(color) == 4:
                self.text_color = QColor(*color)
        
        # Call parent for basic properties
        super().set_properties(properties)

class MetricWidget(UnifiedBaseItem):
    """Widget that displays system metrics. To be implemented."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise NotImplementedError("MetricWidget not yet implemented")
