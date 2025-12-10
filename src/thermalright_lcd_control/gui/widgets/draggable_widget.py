# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Main window for Media Preview application"""
import math
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QMouseEvent, QColor, QPixmap, QPainter, QPen, QConicalGradient
from PySide6.QtWidgets import QLabel, QWidget

from thermalright_lcd_control.device_controller.display.utils import _get_default_font_name
from thermalright_lcd_control.device_controller.metrics.cpu_metrics import CpuMetrics
from thermalright_lcd_control.device_controller.metrics.gpu_metrics import GpuMetrics

# Shared metrics instances for widget value updates
_cpu_metrics_instance = None
_gpu_metrics_instance = None

def _get_cpu_metrics():
    """Get or create shared CpuMetrics instance"""
    global _cpu_metrics_instance
    if _cpu_metrics_instance is None:
        _cpu_metrics_instance = CpuMetrics()
    return _cpu_metrics_instance

def _get_gpu_metrics():
    """Get or create shared GpuMetrics instance"""
    global _gpu_metrics_instance
    if _gpu_metrics_instance is None:
        _gpu_metrics_instance = GpuMetrics()
    return _gpu_metrics_instance


class GridOverlayWidget(QWidget):
    """Transparent overlay that draws a grid pattern"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._grid_size = 10
        self._visible = False
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # Click-through
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        self.hide()
    
    def set_grid_size(self, size: int):
        """Set the grid size in pixels"""
        self._grid_size = max(1, size)
        if self._visible:
            self.update()
    
    def set_visible(self, visible: bool):
        """Show or hide the grid"""
        self._visible = visible
        if visible:
            self.show()
            self.raise_()
            self.update()
        else:
            self.hide()
    
    def paintEvent(self, event):
        """Draw the grid with intersection markers"""
        if not self._visible:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        # Semi-transparent grid lines
        line_pen = QPen(QColor(100, 100, 100, 60))
        line_pen.setWidth(1)
        
        # Draw vertical lines
        x = 0
        while x <= self.width():
            painter.setPen(line_pen)
            painter.drawLine(x, 0, x, self.height())
            x += self._grid_size
        
        # Draw horizontal lines
        y = 0
        while y <= self.height():
            painter.setPen(line_pen)
            painter.drawLine(0, y, self.width(), y)
            y += self._grid_size
        
        # Draw small dots at intersections for better visibility
        dot_pen = QPen(QColor(52, 152, 219, 120))  # Blue dots
        dot_pen.setWidth(3)
        painter.setPen(dot_pen)
        
        y = 0
        while y <= self.height():
            x = 0
            while x <= self.width():
                painter.drawPoint(x, y)
                x += self._grid_size
            y += self._grid_size
        
        painter.end()


class TextStyleConfig:
    """Global text style configuration"""

    def __init__(self):
        self.font_family = _get_default_font_name()
        self.font_size = 18
        self.color = QColor(0, 0, 0)
        self.bold = True
        # Shadow settings
        self.shadow_enabled = False
        self.shadow_color = QColor(0, 0, 0, 128)
        self.shadow_offset_x = 2
        self.shadow_offset_y = 2
        self.shadow_blur = 3
        # Outline settings
        self.outline_enabled = False
        self.outline_color = QColor(0, 0, 0)
        self.outline_width = 1
        # Gradient settings
        self.gradient_enabled = False
        self.gradient_color1 = QColor(255, 255, 255)
        self.gradient_color2 = QColor(100, 100, 255)
        self.gradient_direction = "vertical"  # vertical, horizontal, diagonal

    def selected_stylesheet(self):
        """Convert to CSS stylesheet for selected widget"""
        return f"""
            background-color: transparent; color: {self.color.name()};
            border: 0px transparent; padding: 0px;
            font-family: {self.font_family}; font-size: {self.font_size}px;
            font-weight: {'bold' if self.bold else 'normal'};
        """

    def hidden_stylesheet(self):
        return f"""
                background-color: transparent; color: {self.color.name()};
                border: 0px transparent; padding: 0px;
                font-family: {self.font_family}; font-size: {self.font_size}px;
                font-weight: {'bold' if self.bold else 'normal'};
            """


class DraggableWidget(QLabel):
    """Base class for draggable overlay widgets"""
    positionChanged = Signal(QPoint)
    
    # Class-level snap-to-grid settings (shared by all widgets)
    _snap_to_grid_enabled = False
    _grid_size = 10  # pixels

    @classmethod
    def set_snap_to_grid(cls, enabled: bool):
        """Enable or disable snap-to-grid for all widgets"""
        cls._snap_to_grid_enabled = enabled

    @classmethod
    def set_grid_size(cls, size: int):
        """Set the grid size in pixels"""
        cls._grid_size = max(1, size)

    @classmethod
    def get_snap_to_grid(cls) -> bool:
        """Check if snap-to-grid is enabled"""
        return cls._snap_to_grid_enabled

    @classmethod
    def get_grid_size(cls) -> int:
        """Get the current grid size"""
        return cls._grid_size

    def _snap_position(self, pos: QPoint) -> QPoint:
        """Snap a position to the grid if enabled"""
        if not self._snap_to_grid_enabled:
            return pos
        grid = self._grid_size
        snapped_x = round(pos.x() / grid) * grid
        snapped_y = round(pos.y() / grid) * grid
        return QPoint(snapped_x, snapped_y)

    def __init__(self, parent=None, text="", widget_name="widget"):
        super().__init__(parent)
        self.widget_name = widget_name
        # Use top-left alignment to match PIL text rendering (which draws from top-left)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # Remove all internal margins/indents to match PIL positioning exactly
        self.setContentsMargins(0, 0, 0, 0)
        self.setMargin(0)
        self.setIndent(0)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.dragging = False
        self.drag_start_position = QPoint()
        self.setText(text)
        self.adjustSize()
        self.move(10, 10)
        self.text_style = TextStyleConfig()
        self._individual_font_size = None  # None means use global style
        self.enabled = False
        self.display_text = ""
        self._show_position_hint = False
        self._is_hovered = False
        self.update_display()

    def update_display(self):
        """Update display"""
        if self.enabled:
            self.setText(self.display_text)
            self.setStyleSheet(f"QLabel {{ {self._get_stylesheet()} }}")
            self.show()
        else:
            self.setText("")
            self.setStyleSheet(f"QLabel {{ {self._get_stylesheet()} }}")
            self.hide()
        self.adjustSize()

    def _get_stylesheet(self) -> str:
        """Get stylesheet with individual or global font size and drag state styling.
        
        Text is rendered transparently (invisible) by default so that the PIL-rendered
        text with proper effects shows through. Only on hover/drag do we show a subtle
        text color for positioning feedback.
        """
        font_size = self._individual_font_size if self._individual_font_size else self.text_style.font_size
        
        # Use outline instead of border - outline doesn't affect layout/positioning
        # Text is transparent normally, slightly visible on hover/drag for feedback
        if self.dragging:
            outline_style = "outline: 3px solid #e74c3c; background-color: rgba(231, 76, 60, 0.2);"
            text_color = "rgba(231, 76, 60, 0.7)"  # Semi-transparent red for positioning
        elif self._is_hovered:
            outline_style = "outline: 2px solid #3498db; background-color: rgba(52, 152, 219, 0.15);"
            text_color = "rgba(52, 152, 219, 0.5)"  # Semi-transparent blue for hover
        else:
            outline_style = "outline: none; background-color: transparent;"
            text_color = "transparent"  # Text is invisible - PIL renders the actual text
        
        return f"""
            {outline_style}
            color: {text_color};
            padding: 0px;
            margin: 0px;
            font-family: {self.text_style.font_family};
            font-size: {font_size}px;
            font-weight: {'bold' if self.text_style.bold else 'normal'};
        """

    def set_font_size(self, size: int):
        """Set individual font size for this widget"""
        self._individual_font_size = size
        self.update_display()

    def get_font_size(self) -> int:
        """Get current font size (individual or global)"""
        return self._individual_font_size if self._individual_font_size else self.text_style.font_size

    def show_position_hint(self, show: bool):
        """Show/hide position hint when dragging"""
        self._show_position_hint = show

    def apply_style(self, style_config: TextStyleConfig):
        self.text_style = style_config
        self.update_display()

    def mousePressEvent(self, event: QMouseEvent):
        """Start dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_position = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            self.update_display()  # Update style to show drag border

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle dragging movement"""
        if self.dragging and event.buttons() == Qt.LeftButton:
            new_pos = self.pos() + event.pos() - self.drag_start_position
            if self.parent():
                parent_rect = self.parent().rect()
                widget_rect = self.rect()
                new_pos.setX(max(0, min(new_pos.x(), parent_rect.width() - widget_rect.width())))
                new_pos.setY(max(0, min(new_pos.y(), parent_rect.height() - widget_rect.height())))
            self.move(new_pos)
            self.positionChanged.emit(new_pos)
            # Update tooltip with current position
            self.setToolTip(f"Position: ({new_pos.x()}, {new_pos.y()})")

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Finish dragging and snap to grid if enabled"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)
            
            # Snap to grid if enabled
            if self._snap_to_grid_enabled:
                snapped_pos = self._snap_position(self.pos())
                # Clamp to parent bounds after snapping
                if self.parent():
                    parent_rect = self.parent().rect()
                    widget_rect = self.rect()
                    snapped_pos.setX(max(0, min(snapped_pos.x(), parent_rect.width() - widget_rect.width())))
                    snapped_pos.setY(max(0, min(snapped_pos.y(), parent_rect.height() - widget_rect.height())))
                self.move(snapped_pos)
                self.positionChanged.emit(snapped_pos)
                self.setToolTip(f"Position: ({snapped_pos.x()}, {snapped_pos.y()})")
            
            self.update_display()  # Update style to remove drag border

    def enterEvent(self, event):
        """Change cursor and show hover border"""
        self._is_hovered = True
        self.setCursor(Qt.OpenHandCursor)
        self.update_display()

    def leaveEvent(self, event):
        """Reset cursor and hide hover border"""
        self._is_hovered = False
        if not self.dragging:
            self.setCursor(Qt.ArrowCursor)
        self.update_display()

    def set_enabled(self, enabled):
        """Enable/disable display"""
        self.enabled = enabled
        self.update_display()

    def set_position(self, x: int, y: int):
        """Set widget position programmatically"""
        if self.parent():
            parent_rect = self.parent().rect()
            widget_rect = self.rect()
            x = max(0, min(x, parent_rect.width() - widget_rect.width()))
            y = max(0, min(y, parent_rect.height() - widget_rect.height()))
        self.move(x, y)
        self.positionChanged.emit(QPoint(x, y))

    def get_position(self) -> tuple:
        """Get current widget position"""
        return (self.pos().x(), self.pos().y())


class DraggableForegroundWidget(QLabel):
    """Draggable transparent overlay for positioning the foreground image.
    
    This widget acts as an invisible drag handle over the foreground image area.
    It shows a subtle border on hover to indicate it can be dragged.
    The actual image rendering is handled by the preview manager.
    """
    positionChanged = Signal(int, int)

    def __init__(self, parent=None, width=320, height=240):
        super().__init__(parent)
        self._width = width
        self._height = height
        self._preview_scale = 1.0  # Scale factor for preview vs device coordinates
        self.setFixedSize(width, height)
        self._normal_style = "background-color: transparent; border: none;"
        self._hover_style = "background-color: rgba(52, 152, 219, 0.15); border: 2px solid #3498db;"
        self._dragging_style = "background-color: rgba(231, 76, 60, 0.2); border: 3px solid #e74c3c;"
        self.setStyleSheet(self._normal_style)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.dragging = False
        self.drag_start_position = QPoint()
        self._image_path = None
        self._last_emit_time = 0  # For throttling position updates
        self._image_size = (width, height)  # Actual foreground image size (device coordinates)
        self._active = False  # Whether a foreground is set
        self.move(0, 0)
        self.hide()  # Hidden by default until foreground is set

    def set_preview_scale(self, scale: float):
        """Set the preview scale factor"""
        self._preview_scale = scale
        # Update size if we have an image
        if self._image_path and self._active:
            scaled_w = int(self._image_size[0] * scale)
            scaled_h = int(self._image_size[1] * scale)
            if self.parent():
                max_w = min(scaled_w, self.parent().width())
                max_h = min(scaled_h, self.parent().height())
                self.setFixedSize(max_w, max_h)
            else:
                self.setFixedSize(scaled_w, scaled_h)

    def set_foreground_active(self, active: bool, image_path: str = None, image_size: tuple = None):
        """Activate/deactivate the foreground drag handle"""
        self._active = active
        self._image_path = image_path
        
        if active:
            # Update size to match foreground image if provided (scaled for preview)
            if image_size:
                self._image_size = image_size
                scaled_w = int(image_size[0] * self._preview_scale)
                scaled_h = int(image_size[1] * self._preview_scale)
                if self.parent():
                    max_w = min(scaled_w, self.parent().width())
                    max_h = min(scaled_h, self.parent().height())
                    self.setFixedSize(max_w, max_h)
                else:
                    self.setFixedSize(scaled_w, scaled_h)
            self.show()
            # Note: z-order is managed by main_window._raise_overlay_widgets()
        else:
            self.hide()

    def set_foreground_image(self, image_path: str, opacity: float = 1.0):
        """Set the foreground - just activates the drag handle"""
        if image_path:
            # Get actual image size (device coordinates)
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self._image_size = (pixmap.width(), pixmap.height())
                # Scale the drag handle to match the preview scale
                scaled_w = int(pixmap.width() * self._preview_scale)
                scaled_h = int(pixmap.height() * self._preview_scale)
                if self.parent():
                    max_w = min(scaled_w, self.parent().width())
                    max_h = min(scaled_h, self.parent().height())
                    self.setFixedSize(max_w, max_h)
                else:
                    self.setFixedSize(scaled_w, scaled_h)
            self.set_foreground_active(True, image_path, self._image_size)
        else:
            self.set_foreground_active(False)

    def set_opacity(self, opacity: float):
        """Set foreground opacity - no-op for drag handle"""
        pass  # Opacity is handled by preview manager

    def clear_foreground(self):
        """Clear/hide the foreground drag handle"""
        self._image_path = None
        self._active = False
        self.hide()

    def mousePressEvent(self, event: QMouseEvent):
        """Start dragging"""
        if event.button() == Qt.LeftButton and self._active:
            self.dragging = True
            self.drag_start_position = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            self.setStyleSheet(self._dragging_style)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle dragging movement"""
        if self.dragging and event.buttons() == Qt.LeftButton:
            new_pos = self.pos() + event.pos() - self.drag_start_position
            # Allow negative positions for foreground (can be partially off-screen)
            if self.parent():
                parent_rect = self.parent().rect()
                # Limit to keep at least some of the image visible
                min_x = -self.width() + 20
                max_x = parent_rect.width() - 20
                min_y = -self.height() + 20
                max_y = parent_rect.height() - 20
                new_pos.setX(max(min_x, min(new_pos.x(), max_x)))
                new_pos.setY(max(min_y, min(new_pos.y(), max_y)))
            self.move(new_pos)
            self.setToolTip(f"Foreground: ({new_pos.x()}, {new_pos.y()})")
            
            # Throttle position updates to max ~20fps to prevent GUI blocking
            import time
            current_time = time.time()
            if current_time - self._last_emit_time >= 0.05:  # 50ms throttle
                self.positionChanged.emit(new_pos.x(), new_pos.y())
                self._last_emit_time = current_time

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Finish dragging and snap to grid if enabled"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)
            self.setStyleSheet(self._hover_style if self.underMouse() else self._normal_style)
            
            # Snap to grid if enabled (use DraggableWidget's class settings)
            if DraggableWidget.get_snap_to_grid():
                grid = DraggableWidget.get_grid_size()
                snapped_x = round(self.pos().x() / grid) * grid
                snapped_y = round(self.pos().y() / grid) * grid
                # Clamp to bounds after snapping
                if self.parent():
                    parent_rect = self.parent().rect()
                    min_x = -self.width() + 20
                    max_x = parent_rect.width() - 20
                    min_y = -self.height() + 20
                    max_y = parent_rect.height() - 20
                    snapped_x = max(min_x, min(snapped_x, max_x))
                    snapped_y = max(min_y, min(snapped_y, max_y))
                self.move(snapped_x, snapped_y)
                self.setToolTip(f"Foreground: ({snapped_x}, {snapped_y})")
                self.positionChanged.emit(snapped_x, snapped_y)
            else:
                # Emit final position on release
                self.positionChanged.emit(self.pos().x(), self.pos().y())

    def enterEvent(self, event):
        """Change cursor and show border on hover"""
        if self._active:
            self.setCursor(Qt.OpenHandCursor)
            self.setStyleSheet(self._hover_style)

    def leaveEvent(self, event):
        """Reset cursor and hide border"""
        if not self.dragging:
            self.setCursor(Qt.ArrowCursor)
            self.setStyleSheet(self._normal_style)

    def set_position(self, x: int, y: int):
        """Set position programmatically"""
        self.move(x, y)

    def get_position(self) -> tuple:
        """Get current position"""
        return (self.pos().x(), self.pos().y())


class TimerWidget(DraggableWidget):
    """Base class for time-based widgets"""

    def __init__(self, parent=None, widget_name="", time_format=""):
        super().__init__(parent, "", widget_name)
        self.time_format = time_format
        self.display_text = datetime.now().strftime(self.time_format)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)

    def update_display(self):
        """Update display with current time using the format string"""
        if self.enabled:
            self.display_text = datetime.now().strftime(self.time_format)
            self.setText(self.display_text)
            self.setStyleSheet(f"QLabel {{ {self._get_stylesheet()} }}")
            self.show()
        else:
            self.setText("")
            self.setStyleSheet(f"QLabel {{ {self._get_stylesheet()} }}")
            self.hide()
        self.adjustSize()


class DateWidget(TimerWidget):
    """Date display widget with format options"""

    def __init__(self, parent=None):
        super().__init__(parent, "date", "%A %-d %B")
        self.show_weekday = True
        self.show_year = False
        self.date_format = "default"  # default, short, numeric
        self._update_format()

    def _update_format(self):
        """Update the time format string based on options"""
        if self.date_format == "numeric":
            # e.g., 09/12/2025 or 09/12
            if self.show_year:
                self.time_format = "%d/%m/%Y"
            else:
                self.time_format = "%d/%m"
        elif self.date_format == "short":
            # e.g., Dec 9, 2025 or Tue Dec 9
            parts = []
            if self.show_weekday:
                parts.append("%a")
            parts.append("%b %-d")
            if self.show_year:
                parts.append("%Y")
            self.time_format = " ".join(parts)
        else:  # default
            # e.g., Tuesday 9 December 2025
            parts = []
            if self.show_weekday:
                parts.append("%A")
            parts.append("%-d %B")
            if self.show_year:
                parts.append("%Y")
            self.time_format = " ".join(parts)
        self.update_display()

    def set_show_weekday(self, show: bool):
        """Set whether to show weekday"""
        self.show_weekday = show
        self._update_format()

    def set_show_year(self, show: bool):
        """Set whether to show year"""
        self.show_year = show
        self._update_format()

    def set_date_format(self, format_type: str):
        """Set date format type (default, short, numeric)"""
        self.date_format = format_type
        self._update_format()

    def get_show_weekday(self) -> bool:
        return self.show_weekday

    def get_show_year(self) -> bool:
        return self.show_year

    def get_date_format(self) -> str:
        return self.date_format


class TimeWidget(TimerWidget):
    """Time display widget with format options"""

    def __init__(self, parent=None):
        super().__init__(parent, "time", "%H:%M")
        self.use_24_hour = True
        self.show_seconds = False
        self.show_am_pm = False
        self._update_format()

    def _update_format(self):
        """Update the time format string based on options"""
        if self.use_24_hour:
            if self.show_seconds:
                self.time_format = "%H:%M:%S"
            else:
                self.time_format = "%H:%M"
        else:
            if self.show_seconds:
                fmt = "%I:%M:%S"
            else:
                fmt = "%I:%M"
            if self.show_am_pm:
                fmt += " %p"
            self.time_format = fmt
        self.update_display()

    def set_use_24_hour(self, use: bool):
        """Set whether to use 24-hour format"""
        self.use_24_hour = use
        self._update_format()

    def set_show_seconds(self, show: bool):
        """Set whether to show seconds"""
        self.show_seconds = show
        self._update_format()

    def set_show_am_pm(self, show: bool):
        """Set whether to show AM/PM indicator"""
        self.show_am_pm = show
        self._update_format()

    def get_use_24_hour(self) -> bool:
        return self.use_24_hour

    def get_show_seconds(self) -> bool:
        return self.show_seconds

    def get_show_am_pm(self) -> bool:
        return self.show_am_pm


class FreeTextWidget(DraggableWidget):
    """Free text display widget - allows custom text entry"""

    def __init__(self, parent=None, widget_name="text1"):
        super().__init__(parent, "", widget_name)
        self.name = widget_name
        self.custom_text = ""
        self._set_initial_position()
        self.update_display()

    def _set_initial_position(self):
        """Set initial position based on widget name"""
        positions = {
            "text1": (10, 200),
            "text2": (10, 220),
            "text3": (10, 240),
            "text4": (10, 260)
        }
        if self.name in positions:
            self.move(*positions[self.name])

    def set_text(self, text: str):
        """Set the custom text to display"""
        self.custom_text = text
        self.display_text = text
        self.update_display()

    def get_text(self) -> str:
        """Get the current custom text"""
        return self.custom_text

    def update_display(self):
        """Update display with custom text"""
        if self.enabled and self.custom_text:
            self.display_text = self.custom_text
            self.setText(self.display_text)
            self.setStyleSheet(f"QLabel {{ {self._get_stylesheet()} }}")
            self.show()
        else:
            self.setText("")
            self.hide()
        self.adjustSize()


class MetricWidget(DraggableWidget):
    """Generic metric display widget"""
    
    # Label position constants (matching service-side LabelPosition enum)
    LABEL_LEFT = "left"
    LABEL_RIGHT = "right"
    LABEL_ABOVE = "above"
    LABEL_BELOW = "below"
    LABEL_NONE = "none"

    def __init__(self, metric: type[CpuMetrics | GpuMetrics], parent=None, metric_name="", display_text=""):
        super().__init__(parent, display_text, metric_name)
        self.metric_instance = metric
        self.metric_name = metric_name
        self.enabled = False
        self.custom_label = ""
        self.custom_unit = ""
        self.label_position = self.LABEL_LEFT  # Default: label on left
        self._label_font_size = None  # None means use same as value font size
        self._freq_format = "mhz"  # Default frequency format (mhz or ghz)
        self._update_format()
        self.display_text = self._format_display_text()
        self.setText(self.display_text)
        self._set_initial_position()
        self.update_display()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)

    def _update_format(self):
        """Update format string based on label position"""
        if self.label_position == self.LABEL_NONE or not self.custom_label:
            self.format = "{value}{unit}"
        elif self.label_position == self.LABEL_LEFT:
            self.format = "{label}: {value}{unit}"
        elif self.label_position == self.LABEL_RIGHT:
            self.format = "{value}{unit} :{label}"
        elif self.label_position == self.LABEL_ABOVE:
            self.format = "{label}\n{value}{unit}"
        elif self.label_position == self.LABEL_BELOW:
            self.format = "{value}{unit}\n{label}"
        else:
            self.format = "{label}: {value}{unit}"

    def _format_display_text(self) -> str:
        """Format the display text based on current settings"""
        label = self.custom_label if self.custom_label else ""
        value = self.get_value()
        unit = self.get_unit()
        
        if self.label_position == self.LABEL_NONE or not label:
            return f"{value}{unit}"
        elif self.label_position == self.LABEL_LEFT:
            return f"{label}: {value}{unit}"
        elif self.label_position == self.LABEL_RIGHT:
            return f"{value}{unit} :{label}"
        elif self.label_position == self.LABEL_ABOVE:
            return f"{label}\n{value}{unit}"
        elif self.label_position == self.LABEL_BELOW:
            return f"{value}{unit}\n{label}"
        else:
            return f"{label}: {value}{unit}"

    def _set_initial_position(self):
        """Set initial position based on widget type"""
        positions = {
            "cpu_temperature": (10, 40), "gpu_temperature": (10, 70), "cpu_usage": (10, 100),
            "gpu_usage": (10, 130), "cpu_frequency": (10, 160), "gpu_frequency": (10, 190)
        }
        if self.metric_name in positions:
            self.move(*positions[self.metric_name])

    def set_label_position(self, position: str):
        """Set the label position relative to value"""
        if position in [self.LABEL_LEFT, self.LABEL_RIGHT, self.LABEL_ABOVE, self.LABEL_BELOW, self.LABEL_NONE]:
            self.label_position = position
            self._update_format()
            self.update_display()

    def get_label_position(self) -> str:
        """Get current label position"""
        return self.label_position

    def set_label_font_size(self, size: int):
        """Set individual font size for labels"""
        self._label_font_size = size
        self.update_display()

    def get_label_font_size(self) -> int:
        """Get current label font size (individual or same as value)"""
        return self._label_font_size if self._label_font_size else self.get_font_size()

    def set_custom_label(self, label):
        """Set custom label"""
        self.custom_label = label
        self._update_format()
        self.update_display()

    def set_custom_unit(self, unit):
        """Set custom unit"""
        self.custom_unit = unit
        self.update_display()

    def _get_rich_text_stylesheet(self) -> str:
        """Get base stylesheet for rich text (font size handled in HTML).
        
        Text is transparent by default so PIL-rendered text with effects shows through.
        """
        # Use outline instead of border - outline doesn't affect layout/positioning
        if self.dragging:
            outline_style = "outline: 3px solid #e74c3c; background-color: rgba(231, 76, 60, 0.2);"
        elif self._is_hovered:
            outline_style = "outline: 2px solid #3498db; background-color: rgba(52, 152, 219, 0.15);"
        else:
            outline_style = "outline: none; background-color: transparent;"
        
        return f"""
            {outline_style}
            padding: 0px;
            margin: 0px;
        """

    def _format_rich_text(self) -> str:
        """Format display text with separate font sizes for label and value using HTML.
        
        Text color is transparent normally so PIL-rendered text shows through.
        Only visible on hover/drag for positioning feedback.
        """
        label = self.custom_label if self.custom_label else ""
        value = self.get_value()
        unit = self.get_unit()
        
        value_font_size = self.get_font_size()
        label_font_size = self.get_label_font_size()
        font_family = self.text_style.font_family
        font_weight = 'bold' if self.text_style.bold else 'normal'
        
        # Determine text color based on hover/drag state
        if self.dragging:
            color = "rgba(231, 76, 60, 0.7)"  # Semi-transparent red for positioning
        elif self._is_hovered:
            color = "rgba(52, 152, 219, 0.5)"  # Semi-transparent blue for hover
        else:
            color = "transparent"  # Invisible - PIL renders the actual text
        
        # Build styled spans
        label_style = f"font-family: {font_family}; font-size: {label_font_size}px; font-weight: {font_weight}; color: {color};"
        value_style = f"font-family: {font_family}; font-size: {value_font_size}px; font-weight: {font_weight}; color: {color};"
        
        label_span = f'<span style="{label_style}">{label}</span>'
        value_span = f'<span style="{value_style}">{value}{unit}</span>'
        
        if self.label_position == self.LABEL_NONE or not label:
            return value_span
        elif self.label_position == self.LABEL_LEFT:
            return f'{label_span}<span style="{label_style}">: </span>{value_span}'
        elif self.label_position == self.LABEL_RIGHT:
            return f'{value_span}<span style="{label_style}"> :</span>{label_span}'
        elif self.label_position == self.LABEL_ABOVE:
            # Center-align both lines using div with text-align center
            return f'<div style="text-align: center;">{label_span}<br>{value_span}</div>'
        elif self.label_position == self.LABEL_BELOW:
            # Center-align both lines using div with text-align center
            return f'<div style="text-align: center;">{value_span}<br>{label_span}</div>'
        else:
            return f'{label_span}<span style="{label_style}">: </span>{value_span}'

    def update_display(self):
        """Override to update with rich text formatting"""
        if self.enabled:
            rich_text = self._format_rich_text()
            self.setText(rich_text)
            self.setStyleSheet(f"QLabel {{ {self._get_rich_text_stylesheet()} }}")
            self.show()
        else:
            self.setText("")
            self.setStyleSheet(f"QLabel {{ {self._get_rich_text_stylesheet()} }}")
            self.hide()
        self.adjustSize()

    def format_label(self):
        return f"{self.custom_label}: " if self.custom_label else ""

    def get_label(self):
        """Get label (custom or default)"""
        return self.custom_label if self.custom_label else ""

    def get_unit(self):
        """Get unit (custom or default)"""
        return self.custom_unit if self.custom_unit else self._get_default_unit()

    def get_value(self):
        value = self.metric_instance.get_metric_value(self.metric_name)
        if value is None:
            return "N/A"
        
        # Convert frequency if this is a frequency metric and format is GHz
        if 'frequency' in self.metric_name and self._freq_format == "ghz":
            try:
                # Value is in MHz, convert to GHz
                mhz_value = float(value)
                ghz_value = mhz_value / 1000.0
                return f"{ghz_value:.2f}"
            except (ValueError, TypeError):
                return value
        
        return value

    def set_freq_format(self, format_type: str):
        """Set frequency format (mhz or ghz)"""
        if format_type in ["mhz", "ghz"]:
            self._freq_format = format_type
            # Clear custom unit so it uses the default based on format
            self.custom_unit = ""
            self.update_display()

    def get_freq_format(self) -> str:
        """Get current frequency format"""
        return self._freq_format

    def _get_default_label(self):
        """Get default label based on metric_name"""
        defaults = {
            "cpu_temperature": "CPU",
            "gpu_temperature": "GPU",
            "cpu_usage": "CPU%",
            "gpu_usage": "GPU%",
            "cpu_frequency": "CPU",
            "gpu_frequency": "GPU"
        }
        return defaults.get(self.metric_name, "")

    def _get_default_unit(self):
        """Get default unit based on metric_name and frequency format"""
        # For frequency metrics, return based on current format
        if 'frequency' in self.metric_name:
            return "GHz" if self._freq_format == "ghz" else "MHz"
        
        defaults = {
            "cpu_temperature": "°",
            "gpu_temperature": "°",
            "cpu_usage": "%",
            "gpu_usage": "%"
        }
        return defaults.get(self.metric_name, "")


class BarGraphWidget(QLabel):
    """Draggable bar graph widget for displaying metrics as bars"""
    
    positionChanged = Signal(QPoint)
    
    def __init__(self, parent=None, widget_name="bar1"):
        super().__init__(parent)
        self.name = widget_name
        self.enabled = False
        self._dragging = False
        self._is_hovered = False
        
        # Enable mouse tracking and transparent background for drag functionality
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.OpenHandCursor)
        self._drag_start = QPoint()
        
        # Bar properties
        self._metric_name = "cpu_usage"
        self._width = 100
        self._height = 16
        self._orientation = "horizontal"
        
        # Colors
        self._fill_color = QColor(0, 255, 0, 255)
        self._background_color = QColor(50, 50, 50, 255)
        self._border_color = QColor(255, 255, 255, 255)
        
        # Style
        self._show_border = True
        self._border_width = 1
        self._corner_radius = 0
        
        # Value range
        self._min_value = 0.0
        self._max_value = 100.0
        
        # Current value for display
        self._current_value = 50.0
        
        # Timer for updating value
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_value)
        self.update_timer.start(1000)
        
        self._set_initial_position()
        self.update_display()
    
    def _set_initial_position(self):
        """Set initial position based on widget name.
        
        Widget has 4px padding for selection border, so subtract padding
        from desired bar position to get widget position.
        """
        border_padding = 4
        # These are the desired bar positions
        bar_positions = {
            "bar1": (10, 50),
            "bar2": (10, 75),
            "bar3": (10, 100),
            "bar4": (10, 125)
        }
        if self.name in bar_positions:
            x, y = bar_positions[self.name]
            # Widget position = bar position - padding
            self.move(x - border_padding, y - border_padding)
    
    def _update_value(self):
        """Update the current value from metrics"""
        if not self.enabled:
            return
        
        # Get value from metrics
        try:
            if self._metric_name.startswith("cpu"):
                cpu = _get_cpu_metrics()
                if self._metric_name == "cpu_usage":
                    self._current_value = cpu.get_usage_percentage() or 0
                elif self._metric_name == "cpu_temperature":
                    self._current_value = cpu.get_temperature() or 0
            elif self._metric_name.startswith("gpu"):
                gpu = _get_gpu_metrics()
                if self._metric_name == "gpu_usage":
                    self._current_value = gpu.get_usage_percentage() or 0
                elif self._metric_name == "gpu_temperature":
                    self._current_value = gpu.get_temperature() or 0
        except:
            pass
        
        self.update_display()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the widget"""
        self.enabled = enabled
        self.update_display()
    
    def update_display(self):
        """Update the visual display of the bar"""
        if not self.enabled:
            self.hide()
            return
        
        # Add padding for the selection border
        border_padding = 4
        total_width = self._width + border_padding * 2
        total_height = self._height + border_padding * 2
        
        # Create pixmap with padding for border
        pixmap = QPixmap(total_width, total_height)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw selection border if dragging or hovered
        if self._dragging:
            # Red border when dragging
            painter.setBrush(QColor(231, 76, 60, 50))  # Semi-transparent red background
            pen = QPen(QColor(231, 76, 60, 255))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRect(1, 1, total_width - 2, total_height - 2)
        elif self._is_hovered:
            # Blue border on hover
            painter.setBrush(QColor(52, 152, 219, 40))  # Semi-transparent blue background
            pen = QPen(QColor(52, 152, 219, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(1, 1, total_width - 2, total_height - 2)
        
        # Calculate fill amount
        normalized = (self._current_value - self._min_value) / max(1, self._max_value - self._min_value)
        normalized = max(0.0, min(1.0, normalized))
        
        # Offset for drawing the actual bar (inside the padding)
        bar_x = border_padding
        bar_y = border_padding
        
        # Draw background
        painter.setBrush(self._background_color)
        if self._show_border:
            pen = QPen(self._border_color)
            pen.setWidth(self._border_width)
            painter.setPen(pen)
        else:
            painter.setPen(Qt.NoPen)
        
        if self._corner_radius > 0:
            painter.drawRoundedRect(bar_x, bar_y, self._width, self._height, 
                                   self._corner_radius, self._corner_radius)
        else:
            painter.drawRect(bar_x, bar_y, self._width, self._height)
        
        # Draw fill
        painter.setBrush(self._fill_color)
        painter.setPen(Qt.NoPen)
        
        if self._orientation == "horizontal":
            fill_width = int(self._width * normalized)
            if fill_width > 0:
                if self._corner_radius > 0:
                    painter.drawRoundedRect(bar_x, bar_y, fill_width, self._height,
                                           min(self._corner_radius, fill_width // 2), 
                                           self._corner_radius)
                else:
                    painter.drawRect(bar_x, bar_y, fill_width, self._height)
        else:  # vertical
            fill_height = int(self._height * normalized)
            if fill_height > 0:
                fill_y = bar_y + self._height - fill_height
                if self._corner_radius > 0:
                    painter.drawRoundedRect(bar_x, fill_y, self._width, fill_height,
                                           self._corner_radius,
                                           min(self._corner_radius, fill_height // 2))
                else:
                    painter.drawRect(bar_x, fill_y, self._width, fill_height)
        
        painter.end()
        
        self.setPixmap(pixmap)
        self.setFixedSize(total_width, total_height)
        self.show()
    
    def enterEvent(self, event):
        """Handle mouse enter for hover feedback"""
        self._is_hovered = True
        self.update_display()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave"""
        self._is_hovered = False
        self.update_display()
        super().leaveEvent(event)
    
    # Mouse events for dragging
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.enabled:
            self._dragging = True
            self._drag_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            self.update_display()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and self.enabled:
            new_pos = self.pos() + event.pos() - self._drag_start
            # Clamp to parent bounds
            if self.parent():
                parent_rect = self.parent().rect()
                widget_rect = self.rect()
                new_pos.setX(max(0, min(new_pos.x(), parent_rect.width() - widget_rect.width())))
                new_pos.setY(max(0, min(new_pos.y(), parent_rect.height() - widget_rect.height())))
            self.move(new_pos)
            self.positionChanged.emit(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self.setCursor(Qt.OpenHandCursor)
            self.update_display()
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    # Getters and setters for all properties
    def get_metric_name(self) -> str:
        return self._metric_name
    
    def set_metric_name(self, name: str):
        self._metric_name = name
        self._update_value()
    
    def get_width(self) -> int:
        return self._width
    
    def set_width(self, width: int):
        self._width = max(10, width)
        self.update_display()
    
    def get_height(self) -> int:
        return self._height
    
    def set_height(self, height: int):
        self._height = max(5, height)
        self.update_display()
    
    def get_orientation(self) -> str:
        return self._orientation
    
    def set_orientation(self, orientation: str):
        self._orientation = orientation
        self.update_display()
    
    def get_fill_color(self) -> QColor:
        return self._fill_color
    
    def set_fill_color(self, color: QColor):
        self._fill_color = color
        self.update_display()
    
    def get_background_color(self) -> QColor:
        return self._background_color
    
    def set_background_color(self, color: QColor):
        self._background_color = color
        self.update_display()
    
    def get_border_color(self) -> QColor:
        return self._border_color
    
    def set_border_color(self, color: QColor):
        self._border_color = color
        self.update_display()
    
    def get_show_border(self) -> bool:
        return self._show_border
    
    def set_show_border(self, show: bool):
        self._show_border = show
        self.update_display()
    
    def get_border_width(self) -> int:
        return self._border_width
    
    def set_border_width(self, width: int):
        self._border_width = max(1, width)
        self.update_display()
    
    def get_corner_radius(self) -> int:
        return self._corner_radius
    
    def set_corner_radius(self, radius: int):
        self._corner_radius = max(0, radius)
        self.update_display()
    
    def get_min_value(self) -> float:
        return self._min_value
    
    def set_min_value(self, value: float):
        self._min_value = value
        self.update_display()
    
    def get_max_value(self) -> float:
        return self._max_value
    
    def set_max_value(self, value: float):
        self._max_value = value
        self.update_display()
    
    def get_position(self) -> tuple:
        """Get position adjusted for border padding"""
        # The widget has 4px padding for selection border, 
        # so we add the padding to get the actual bar position
        border_padding = 4
        pos = self.pos()
        return (pos.x() + border_padding, pos.y() + border_padding)


class CircularGraphWidget(QLabel):
    """Draggable circular/arc graph widget for displaying metrics"""
    
    positionChanged = Signal(QPoint)
    
    def __init__(self, parent=None, widget_name="arc1"):
        super().__init__(parent)
        self.name = widget_name
        self.enabled = False
        self._dragging = False
        self._is_hovered = False
        
        # Enable mouse tracking and transparent background for drag functionality
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.OpenHandCursor)
        self._drag_start = QPoint()
        
        # Arc properties
        self._metric_name = "cpu_usage"
        self._radius = 40
        self._thickness = 8
        self._start_angle = 135  # Degrees (0 = 3 o'clock, counter-clockwise)
        self._sweep_angle = 270  # Degrees
        
        # Colors
        self._fill_color = QColor(0, 255, 0, 255)
        self._background_color = QColor(50, 50, 50, 255)
        self._border_color = QColor(255, 255, 255, 255)
        
        # Border options
        self._show_border = False
        self._border_width = 1
        
        # Value range
        self._min_value = 0.0
        self._max_value = 100.0
        
        # Current value for display
        self._current_value = 50.0
        
        # Timer for updating value
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_value)
        self.update_timer.start(1000)
        
        self._set_initial_position()
        self.update_display()
    
    def _set_initial_position(self):
        """Set initial position based on widget name."""
        border_padding = 4
        arc_positions = {
            "arc1": (60, 60),
            "arc2": (160, 60),
            "arc3": (60, 160),
            "arc4": (160, 160)
        }
        if self.name in arc_positions:
            x, y = arc_positions[self.name]
            # Position is center of arc, so offset by radius + padding
            self.move(x - self._radius - border_padding, y - self._radius - border_padding)
    
    def _update_value(self):
        """Update the current value from metrics"""
        if not self.enabled:
            return
        
        try:
            if self._metric_name.startswith("cpu"):
                cpu = _get_cpu_metrics()
                if self._metric_name == "cpu_usage":
                    self._current_value = cpu.get_usage_percentage() or 0
                elif self._metric_name == "cpu_temperature":
                    self._current_value = cpu.get_temperature() or 0
            elif self._metric_name.startswith("gpu"):
                gpu = _get_gpu_metrics()
                if self._metric_name == "gpu_usage":
                    self._current_value = gpu.get_usage_percentage() or 0
                elif self._metric_name == "gpu_temperature":
                    self._current_value = gpu.get_temperature() or 0
        except:
            pass
        
        self.update_display()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the widget"""
        self.enabled = enabled
        self.update_display()
    
    def update_display(self):
        """Update the visual display of the arc"""
        if not self.enabled:
            self.hide()
            return
        
        # Add padding for the selection border
        border_padding = 4
        diameter = self._radius * 2
        total_size = diameter + self._thickness + border_padding * 2
        
        # Create pixmap with padding for border
        pixmap = QPixmap(total_size, total_size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw selection border if dragging or hovered
        if self._dragging:
            painter.setBrush(QColor(231, 76, 60, 50))
            pen = QPen(QColor(231, 76, 60, 255))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRect(1, 1, total_size - 2, total_size - 2)
        elif self._is_hovered:
            painter.setBrush(QColor(52, 152, 219, 40))
            pen = QPen(QColor(52, 152, 219, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(1, 1, total_size - 2, total_size - 2)
        
        # Calculate center of arc within pixmap
        center_x = total_size // 2
        center_y = total_size // 2
        
        # Calculate bounding rect for arc
        arc_rect_size = diameter
        arc_left = center_x - self._radius
        arc_top = center_y - self._radius
        
        # Calculate fill amount
        normalized = (self._current_value - self._min_value) / max(1, self._max_value - self._min_value)
        normalized = max(0.0, min(1.0, normalized))
        
        # Draw background arc
        pen = QPen(self._background_color)
        pen.setWidth(self._thickness)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Qt uses 1/16th of a degree, and angles are counter-clockwise from 3 o'clock
        start_angle_qt = int(self._start_angle * 16)
        sweep_angle_qt = int(self._sweep_angle * 16)
        painter.drawArc(arc_left, arc_top, arc_rect_size, arc_rect_size, start_angle_qt, sweep_angle_qt)
        
        # Draw filled arc
        if normalized > 0:
            pen = QPen(self._fill_color)
            pen.setWidth(self._thickness)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            filled_sweep = int(self._sweep_angle * normalized)
            filled_sweep_qt = int(filled_sweep * 16)
            painter.drawArc(arc_left, arc_top, arc_rect_size, arc_rect_size, start_angle_qt, filled_sweep_qt)
        
        # Draw border if enabled
        if self._show_border and self._border_width > 0:
            pen = QPen(self._border_color)
            pen.setWidth(self._border_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            
            # Draw outer border arc
            outer_offset = self._thickness // 2 + self._border_width // 2
            outer_rect_size = diameter + self._thickness
            outer_left = center_x - self._radius - self._thickness // 2
            outer_top = center_y - self._radius - self._thickness // 2
            painter.drawArc(outer_left, outer_top, outer_rect_size, outer_rect_size, start_angle_qt, sweep_angle_qt)
            
            # Draw inner border arc
            inner_rect_size = diameter - self._thickness
            inner_left = center_x - self._radius + self._thickness // 2
            inner_top = center_y - self._radius + self._thickness // 2
            painter.drawArc(inner_left, inner_top, inner_rect_size, inner_rect_size, start_angle_qt, sweep_angle_qt)
        
        painter.end()
        
        self.setPixmap(pixmap)
        self.setFixedSize(total_size, total_size)
        self.show()
    
    def enterEvent(self, event):
        self._is_hovered = True
        self.update_display()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._is_hovered = False
        self.update_display()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.enabled:
            self._dragging = True
            self._drag_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            self.update_display()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and self.enabled:
            new_pos = self.pos() + event.pos() - self._drag_start
            if self.parent():
                parent_rect = self.parent().rect()
                widget_rect = self.rect()
                new_pos.setX(max(0, min(new_pos.x(), parent_rect.width() - widget_rect.width())))
                new_pos.setY(max(0, min(new_pos.y(), parent_rect.height() - widget_rect.height())))
            self.move(new_pos)
            self.positionChanged.emit(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self.setCursor(Qt.OpenHandCursor)
            self.update_display()
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    # Getters and setters
    def get_metric_name(self) -> str:
        return self._metric_name
    
    def set_metric_name(self, name: str):
        self._metric_name = name
        self._update_value()
    
    def get_radius(self) -> int:
        return self._radius
    
    def set_radius(self, radius: int):
        self._radius = max(10, radius)
        self.update_display()
    
    def get_thickness(self) -> int:
        return self._thickness
    
    def set_thickness(self, thickness: int):
        self._thickness = max(2, thickness)
        self.update_display()
    
    def get_start_angle(self) -> int:
        return self._start_angle
    
    def set_start_angle(self, angle: int):
        self._start_angle = angle % 360
        self.update_display()
    
    def get_sweep_angle(self) -> int:
        return self._sweep_angle
    
    def set_sweep_angle(self, angle: int):
        self._sweep_angle = max(1, min(360, angle))
        self.update_display()
    
    def get_fill_color(self) -> QColor:
        return self._fill_color
    
    def set_fill_color(self, color: QColor):
        self._fill_color = color
        self.update_display()
    
    def get_background_color(self) -> QColor:
        return self._background_color
    
    def set_background_color(self, color: QColor):
        self._background_color = color
        self.update_display()
    
    def get_border_color(self) -> QColor:
        return self._border_color
    
    def set_border_color(self, color: QColor):
        self._border_color = color
        self.update_display()
    
    def get_show_border(self) -> bool:
        return self._show_border
    
    def set_show_border(self, show: bool):
        self._show_border = show
        self.update_display()
    
    def get_border_width(self) -> int:
        return self._border_width
    
    def set_border_width(self, width: int):
        self._border_width = max(1, width)
        self.update_display()
    
    def get_min_value(self) -> float:
        return self._min_value
    
    def set_min_value(self, value: float):
        self._min_value = value
        self.update_display()
    
    def get_max_value(self) -> float:
        return self._max_value
    
    def set_max_value(self, value: float):
        self._max_value = value
        self.update_display()
    
    def get_position(self) -> tuple:
        """Get center position adjusted for border padding and radius"""
        border_padding = 4
        pos = self.pos()
        # Return the center of the arc
        center_x = pos.x() + border_padding + self._radius + self._thickness // 2
        center_y = pos.y() + border_padding + self._radius + self._thickness // 2
        return (center_x, center_y)
