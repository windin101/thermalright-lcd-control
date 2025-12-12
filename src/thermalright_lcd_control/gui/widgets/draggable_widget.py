# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Main window for Media Preview application"""
import math
import threading
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QMouseEvent, QColor, QPixmap, QPainter, QPen, QConicalGradient
from PySide6.QtWidgets import QLabel, QWidget, QPushButton

from thermalright_lcd_control.device_controller.display.utils import _get_default_font_name
from thermalright_lcd_control.device_controller.metrics.cpu_metrics import CpuMetrics
from thermalright_lcd_control.device_controller.metrics.gpu_metrics import GpuMetrics


def _get_pil_text_size(text: str, font_family: str, font_size: int, bold: bool = False) -> tuple[int, int]:
    """Calculate text size using PIL to match the actual rendered size.
    
    Returns (width, height) tuple that matches what PIL renders when drawing at (x, y).
    The height uses ascent+descent (full line height) to match PIL's text positioning.
    """
    if not text:
        return (1, 1)
    
    try:
        # Use the global font manager to get fonts consistently with per-widget font settings
        from thermalright_lcd_control.device_controller.display.font_manager import get_font_manager
        font_manager = get_font_manager()
        font = font_manager.get_font(font_size, font_family if font_family else None, bold)
    except Exception:
        # Fallback to default font
        try:
            font = ImageFont.truetype(font_family, font_size)
        except Exception:
            font = ImageFont.load_default()
    
    # Create a temporary image to measure text
    temp_img = Image.new('RGBA', (1, 1))
    draw = ImageDraw.Draw(temp_img)
    bbox = draw.textbbox((0, 0), text, font=font)
    
    # Width from bbox (right - left)
    width = bbox[2] - bbox[0]
    
    # Height: use ascent + descent for full line height
    # This matches how the widget box should cover the full text area
    try:
        ascent, descent = font.getmetrics()
        height = ascent + descent
    except Exception:
        height = bbox[3] - bbox[1]
    
    return (max(1, width), max(1, height))

# Shared metrics cache for non-blocking widget updates
class _MetricsCache:
    """Thread-safe metrics cache with background updates.
    
    This prevents blocking the GUI thread when fetching metrics
    from subprocess calls (nvidia-smi, etc.) which can take seconds.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._cpu_metrics = None
        self._gpu_metrics = None
        self._cached_values = {}
        self._update_thread = None
        self._running = False
        self._data_lock = threading.Lock()
    
    def start(self):
        """Start background metrics updates"""
        if self._running:
            return
        self._running = True
        # Do immediate first update in background thread
        threading.Thread(target=self._update_metrics, daemon=True).start()
    
    def stop(self):
        """Stop background metrics updates"""
        self._running = False
        if self._update_thread:
            self._update_thread.cancel()
            self._update_thread = None
    
    def _schedule_update(self):
        """Schedule next update"""
        if self._running:
            self._update_thread = threading.Timer(1.0, self._update_metrics)
            self._update_thread.daemon = True
            self._update_thread.start()
    
    def _update_metrics(self):
        """Update metrics in background thread"""
        try:
            # Lazy init metrics instances in background thread
            if self._cpu_metrics is None:
                self._cpu_metrics = CpuMetrics()
            if self._gpu_metrics is None:
                self._gpu_metrics = GpuMetrics()
            
            # Fetch values (these may block on subprocess calls)
            new_values = {
                'cpu_usage': self._cpu_metrics.get_usage_percentage() or 0,
                'cpu_temperature': self._cpu_metrics.get_temperature() or 0,
                'ram_percent': self._cpu_metrics.get_ram_percent() or 0,
                'gpu_usage': self._gpu_metrics.get_usage_percentage() or 0,
                'gpu_temperature': self._gpu_metrics.get_temperature() or 0,
                'gpu_mem_percent': self._gpu_metrics.get_memory_percent() or 0,
            }
            
            # Thread-safe update of cached values
            with self._data_lock:
                self._cached_values = new_values
        except Exception:
            pass
        finally:
            # Schedule next update
            self._schedule_update()
    
    def get_value(self, metric_name: str) -> float:
        """Get cached metric value (non-blocking)"""
        with self._data_lock:
            return self._cached_values.get(metric_name, 0)

# Global metrics cache instance
_metrics_cache = None

def _get_metrics_cache():
    """Get or create the shared metrics cache"""
    global _metrics_cache
    if _metrics_cache is None:
        _metrics_cache = _MetricsCache()
        _metrics_cache.start()
    return _metrics_cache

def cleanup_metrics_cache():
    """Stop and cleanup the metrics cache - call on app close"""
    global _metrics_cache
    if _metrics_cache is not None:
        _metrics_cache.stop()
        _metrics_cache = None

# Legacy functions for backward compatibility
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


def _interpolate_gradient_color(normalized_value: float, gradient_colors: list) -> QColor:
    """
    Interpolate color based on normalized value (0-1) and gradient thresholds.
    
    Args:
        normalized_value: Value between 0 and 1
        gradient_colors: List of (threshold, (r, g, b, a)) tuples, sorted by threshold
                        Thresholds are 0-100 percentages
    
    Returns:
        Interpolated QColor
    """
    if not gradient_colors or len(gradient_colors) < 2:
        return QColor(0, 255, 0, 255)  # Default green
    
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
        return QColor(c[0], c[1], c[2], c[3] if len(c) > 3 else 255)
    
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
    
    return QColor(r, g, b, a)


class ResizeHandle(QWidget):
    """Small draggable handle for resizing widgets.
    
    Positioned at corners or edges of a selected widget to allow resizing.
    """
    
    # Signals
    resizeRequested = Signal(str, int, int)  # handle_type, delta_x, delta_y
    dragStarted = Signal()
    dragEnded = Signal()
    
    HANDLE_SIZE = 10
    
    def __init__(self, parent=None, handle_type="bottom-right"):
        """
        Args:
            parent: Parent widget
            handle_type: One of 'top-left', 'top-right', 'bottom-left', 'bottom-right',
                        'top', 'bottom', 'left', 'right'
        """
        super().__init__(parent)
        self._handle_type = handle_type
        self._dragging = False
        self._armed = False
        self._drag_start = QPoint()
        self._drag_start_global = None
        
        self.setFixedSize(self.HANDLE_SIZE, self.HANDLE_SIZE)
        self.setFocusPolicy(Qt.NoFocus)  # Don't steal focus from the widget
        self._update_cursor()
        self.setStyleSheet("""
            background-color: #2ecc71;
            border: 1px solid #27ae60;
            border-radius: 2px;
        """)
        self.hide()
    
    def _update_cursor(self):
        """Set appropriate cursor based on handle type"""
        cursors = {
            'top-left': Qt.SizeFDiagCursor,
            'bottom-right': Qt.SizeFDiagCursor,
            'top-right': Qt.SizeBDiagCursor,
            'bottom-left': Qt.SizeBDiagCursor,
            'top': Qt.SizeVerCursor,
            'bottom': Qt.SizeVerCursor,
            'left': Qt.SizeHorCursor,
            'right': Qt.SizeHorCursor,
        }
        self.setCursor(cursors.get(self._handle_type, Qt.SizeAllCursor))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Arm the handle, but only start dragging once user moves a bit
            self._armed = True
            self._drag_start = event.globalPos()
            self._drag_start_global = event.globalPos()
            event.accept()
            try:
                self.dragStarted.emit()
            except Exception:
                pass
    
    def mouseMoveEvent(self, event):
        if self._armed and not self._dragging:
            # Check if user moved area exceeds threshold to start actual dragging
            threshold = 6
            moved = event.globalPos() - self._drag_start_global
            if abs(moved.x()) >= threshold or abs(moved.y()) >= threshold:
                self._dragging = True
                # reset _drag_start to current to avoid jumps
                self._drag_start = event.globalPos()
        if self._dragging:
            delta = event.globalPos() - self._drag_start
            self._drag_start = event.globalPos()
            self.resizeRequested.emit(self._handle_type, delta.x(), delta.y())
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._armed = False
            self._drag_start_global = None
            event.accept()
            try:
                self.dragEnded.emit()
            except Exception:
                pass


class RotationHandle(QWidget):
    """Circular handle for rotating widgets.
    
    Positioned above the selected widget, connected by a line.
    Drag to rotate the widget around its center.
    """
    
    # Signal emitted when rotation is requested
    rotationRequested = Signal(float)  # angle in degrees
    dragStarted = Signal()
    dragEnded = Signal()
    
    HANDLE_SIZE = 14
    STEM_LENGTH = 25  # Distance from widget top to handle center
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._armed = False
        self._drag_start = QPoint()
        self._drag_start_global = None
        self._widget_center = QPoint()  # Center of the target widget
        
        self.setFixedSize(self.HANDLE_SIZE, self.HANDLE_SIZE)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.PointingHandCursor)
        # Don't use stylesheet - we'll paint it manually for better visibility
        self.setAutoFillBackground(False)
        self.hide()
    
    def paintEvent(self, event):
        """Paint the rotation handle as a filled circle"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw filled purple circle
        painter.setBrush(QColor(155, 89, 182))  # #9b59b6
        painter.setPen(QPen(QColor(142, 68, 173), 2))  # #8e44ad border
        
        # Draw circle (leave 1px margin for border)
        painter.drawEllipse(1, 1, self.HANDLE_SIZE - 2, self.HANDLE_SIZE - 2)
        painter.end()
    
    def set_widget_center(self, center: QPoint):
        """Set the center point of the target widget for angle calculations"""
        self._widget_center = center
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Arm rotation; start rotation once user has moved beyond threshold
            self._armed = True
            self._drag_start = event.globalPos()
            self._drag_start_global = event.globalPos()
            event.accept()
            try:
                self.dragStarted.emit()
            except Exception:
                pass
    
    def mouseMoveEvent(self, event):
        if self._armed and not self._dragging:
            threshold = 6
            moved = event.globalPos() - self._drag_start_global
            if abs(moved.x()) >= threshold or abs(moved.y()) >= threshold:
                self._dragging = True
                # reset start to avoid sudden jumps
                self._drag_start = event.globalPos()
        if self._dragging:
            # Calculate angle from widget center to current mouse position
            # Convert global pos to parent coordinates
            current_pos = self.parent().mapFromGlobal(event.globalPos())
            
            # Calculate angle from center to mouse position
            dx = current_pos.x() - self._widget_center.x()
            dy = current_pos.y() - self._widget_center.y()
            
            # atan2 gives angle in radians, convert to degrees
            # Adjust so 0 degrees is "up" (negative y-axis)
            angle_rad = math.atan2(dx, -dy)
            angle_deg = math.degrees(angle_rad)
            
            # Normalize to 0-360
            if angle_deg < 0:
                angle_deg += 360
            
            # Snap to cardinal angles (0, 90, 180, 270) if within threshold
            snap_threshold = 8  # degrees - how close to snap
            snap_angles = [0, 90, 180, 270, 360]
            
            for snap_angle in snap_angles:
                diff = abs(angle_deg - snap_angle)
                if diff <= snap_threshold:
                    angle_deg = snap_angle % 360  # 360 becomes 0
                    break
            
            self.rotationRequested.emit(angle_deg)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()
            try:
                self.dragEnded.emit()
            except Exception:
                pass


class ResizeHandleManager(QWidget):
    """Manages resize handles for a selected widget.
    
    Creates and positions handles around a target widget, and translates
    handle drag events into resize operations on the target.
    """
    
    # Emitted when target widget's size/font changes
    sizeChanged = Signal(object, str, object)  # target_widget, property_name, new_value
    rotationChanged = Signal(object, float)  # target_widget, angle in degrees
    resizeDragStarted = Signal()
    resizeDragEnded = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._target = None
        self._handles = {}
        self._rotation_handle = None
        self._preview_scale = 1.0
        self._accumulated_delta = 0.0  # For smooth text resizing
        
        # Create resize handles (initially hidden)
        handle_types = ['top-left', 'top-right', 'bottom-left', 'bottom-right']
        for ht in handle_types:
            handle = ResizeHandle(parent, ht)
            handle.resizeRequested.connect(self._on_resize_requested)
            handle.dragStarted.connect(self._on_handle_drag_started)
            handle.dragEnded.connect(self._on_handle_drag_ended)
            self._handles[ht] = handle
        
        # Create rotation handle (for bar/arc widgets)
        self._rotation_handle = RotationHandle(parent)
        self._rotation_handle.rotationRequested.connect(self._on_rotation_requested)
        self._rotation_handle.dragStarted.connect(self._on_handle_drag_started)
        self._rotation_handle.dragEnded.connect(self._on_handle_drag_ended)
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.hide()
    
    def set_preview_scale(self, scale: float):
        """Update preview scale for calculations"""
        self._preview_scale = scale
        self._update_handle_positions()
    
    def attach_to(self, target_widget):
        """Attach resize handles to a widget"""
        if self._target == target_widget:
            return
        
        self._target = target_widget
        self._accumulated_delta = 0.0  # Reset accumulated delta for new widget
        
        if target_widget is None:
            self._hide_all_handles()
            return
        
        # Determine which handles to show based on widget type
        self._show_appropriate_handles()
        self._update_handle_positions()
    
    def detach(self):
        """Detach handles from current widget"""
        self._target = None
        self._accumulated_delta = 0.0  # Reset accumulated delta
        self._hide_all_handles()
    
    def _hide_all_handles(self):
        """Hide all resize and rotation handles"""
        for handle in self._handles.values():
            handle.hide()
        if self._rotation_handle:
            self._rotation_handle.hide()
    
    def _show_appropriate_handles(self):
        """Show handles appropriate for the target widget type"""
        if self._target is None:
            return
        
        # Get target class name to determine handle types
        class_name = self._target.__class__.__name__
        
        # All widget types get corner handles
        for ht, handle in self._handles.items():
            handle.show()
            handle.raise_()
        
        # Only bar, arc, and shape widgets get rotation handle
        if class_name in ('BarGraphWidget', 'CircularGraphWidget', 'ShapeWidget'):
            self._rotation_handle.show()
            self._rotation_handle.raise_()
        else:
            self._rotation_handle.hide()

    def _on_handle_drag_started(self):
        """Called when a resize/rotation handle starts being dragged"""
        try:
            self.resizeDragStarted.emit()
        except Exception:
            pass

    def _on_handle_drag_ended(self):
        """Called when a resize/rotation handle finishes being dragged"""
        try:
            self.resizeDragEnded.emit()
        except Exception:
            pass
    
    def _update_handle_positions(self):
        """Position handles around the target widget.
        
        For rotatable widgets (bar/arc), use the base dimensions instead of
        the rotated bounding box to keep handles at consistent positions.
        """
        if self._target is None:
            return
        
        class_name = self._target.__class__.__name__
        target_rect = self._target.geometry()
        handle_size = ResizeHandle.HANDLE_SIZE
        half_size = handle_size // 2
        
        # For bar/arc widgets, calculate handle positions based on unrotated size
        if class_name == 'BarGraphWidget':
            # Get base dimensions (unrotated) and apply preview scale
            base_width = int(self._target.get_width() * self._preview_scale)
            base_height = int(self._target.get_height() * self._preview_scale)
            border_padding = 4
            
            # Widget center stays the same
            center_x = target_rect.center().x()
            center_y = target_rect.center().y()
            
            # Calculate corners based on unrotated dimensions from center
            left = center_x - base_width // 2 - border_padding
            right = center_x + base_width // 2 + border_padding
            top = center_y - base_height // 2 - border_padding
            bottom = center_y + base_height // 2 + border_padding
            
            positions = {
                'top-left': (left - half_size, top - half_size),
                'top-right': (right - half_size, top - half_size),
                'bottom-left': (left - half_size, bottom - half_size),
                'bottom-right': (right - half_size, bottom - half_size),
            }
        elif class_name == 'CircularGraphWidget':
            # For arc widgets, use radius-based sizing
            base_radius = int(self._target.get_radius() * self._preview_scale)
            base_thickness = int(self._target.get_thickness() * self._preview_scale)
            border_padding = 4
            
            # Widget center
            center_x = target_rect.center().x()
            center_y = target_rect.center().y()
            
            # Size based on diameter + thickness
            half_size_arc = base_radius + base_thickness // 2 + border_padding
            
            positions = {
                'top-left': (center_x - half_size_arc - half_size, center_y - half_size_arc - half_size),
                'top-right': (center_x + half_size_arc - half_size, center_y - half_size_arc - half_size),
                'bottom-left': (center_x - half_size_arc - half_size, center_y + half_size_arc - half_size),
                'bottom-right': (center_x + half_size_arc - half_size, center_y + half_size_arc - half_size),
            }
        elif class_name == 'ShapeWidget':
            # Get base dimensions (unrotated) and apply preview scale
            base_width = int(self._target.get_width() * self._preview_scale)
            base_height = int(self._target.get_height() * self._preview_scale)
            border_padding = 4
            
            # Widget center stays the same
            center_x = target_rect.center().x()
            center_y = target_rect.center().y()
            
            # Calculate corners based on unrotated dimensions from center
            left = center_x - base_width // 2 - border_padding
            right = center_x + base_width // 2 + border_padding
            top = center_y - base_height // 2 - border_padding
            bottom = center_y + base_height // 2 + border_padding
            
            positions = {
                'top-left': (left - half_size, top - half_size),
                'top-right': (right - half_size, top - half_size),
                'bottom-left': (left - half_size, bottom - half_size),
                'bottom-right': (right - half_size, bottom - half_size),
            }
        else:
            # For other widgets, use the actual geometry
            positions = {
                'top-left': (target_rect.left() - half_size, target_rect.top() - half_size),
                'top-right': (target_rect.right() - half_size, target_rect.top() - half_size),
                'bottom-left': (target_rect.left() - half_size, target_rect.bottom() - half_size),
                'bottom-right': (target_rect.right() - half_size, target_rect.bottom() - half_size),
            }
        
        for ht, (x, y) in positions.items():
            if ht in self._handles:
                self._handles[ht].move(int(x), int(y))
                self._handles[ht].raise_()  # Ensure handles stay on top
        
        # Position rotation handle - always at the top of the widget
        if self._rotation_handle and self._rotation_handle.isVisible():
            rot_handle_size = RotationHandle.HANDLE_SIZE
            stem_length = RotationHandle.STEM_LENGTH
            
            center_x = target_rect.center().x()
            center_y = target_rect.center().y()
            
            # Calculate orbit distance based on widget type
            if class_name == 'BarGraphWidget':
                base_height = int(self._target.get_height() * self._preview_scale)
                orbit_radius = base_height // 2 + stem_length + 4
            elif class_name == 'CircularGraphWidget':
                base_radius = int(self._target.get_radius() * self._preview_scale)
                base_thickness = int(self._target.get_thickness() * self._preview_scale)
                orbit_radius = base_radius + base_thickness // 2 + stem_length + 4
            elif class_name == 'ShapeWidget':
                base_height = int(self._target.get_height() * self._preview_scale)
                orbit_radius = base_height // 2 + stem_length + 4
            else:
                orbit_radius = stem_length
            
            # Always position handle at the top (angle = 0)
            # Handle moves during drag to follow mouse, but snaps back to top when released
            rot_x = center_x - rot_handle_size // 2
            rot_y = center_y - orbit_radius - rot_handle_size // 2
            
            self._rotation_handle.move(int(rot_x), int(rot_y))
            self._rotation_handle.raise_()
            
            # Update widget center for angle calculations
            self._rotation_handle.set_widget_center(QPoint(int(center_x), int(center_y)))
    
    def _on_rotation_requested(self, angle: float):
        """Handle rotation request from the rotation handle"""
        if self._target is None:
            return
        
        class_name = self._target.__class__.__name__
        
        # Bar, arc, and shape widgets support rotation
        if class_name in ('BarGraphWidget', 'CircularGraphWidget', 'ShapeWidget'):
            # Round to nearest degree for cleaner values
            rounded_angle = round(angle)
            self._target.set_rotation(rounded_angle)
            self.rotationChanged.emit(self._target, rounded_angle)
            # Don't update handle positions during rotation - they stay at original corners
            # Only update rotation handle's widget center
            if self._rotation_handle:
                target_rect = self._target.geometry()
                self._rotation_handle.set_widget_center(target_rect.center())
    
    def _on_resize_requested(self, handle_type: str, delta_x: int, delta_y: int):
        """Handle resize request from a drag handle"""
        if self._target is None:
            return
        
        class_name = self._target.__class__.__name__
        
        # For text widgets, use raw pixel deltas (font size is UI interaction)
        # For bar/arc/shape widgets, convert to device coordinates
        if class_name in ('DraggableWidget', 'MetricWidget', 'TimeWidget', 'DateWidget', 'FreeTextWidget'):
            self._resize_text_widget(handle_type, delta_x, delta_y)
        else:
            # Calculate device-coordinate deltas (unscale from preview)
            device_delta_x = int(delta_x / self._preview_scale) if self._preview_scale > 0 else delta_x
            device_delta_y = int(delta_y / self._preview_scale) if self._preview_scale > 0 else delta_y
            
            if class_name == 'BarGraphWidget':
                self._resize_bar_widget(handle_type, device_delta_x, device_delta_y)
            elif class_name == 'CircularGraphWidget':
                self._resize_arc_widget(handle_type, device_delta_x, device_delta_y)
            elif class_name == 'ShapeWidget':
                self._resize_shape_widget(handle_type, device_delta_x, device_delta_y)
        
        # Update handle positions after resize
        self._update_handle_positions()
    
    def _resize_bar_widget(self, handle_type: str, delta_x: int, delta_y: int):
        """Resize a bar graph widget"""
        current_width = self._target.get_width()
        current_height = self._target.get_height()
        
        # Calculate new dimensions based on handle
        new_width = current_width
        new_height = current_height
        
        if 'right' in handle_type:
            new_width = max(10, current_width + delta_x)
        elif 'left' in handle_type:
            new_width = max(10, current_width - delta_x)
        
        if 'bottom' in handle_type:
            new_height = max(5, current_height + delta_y)
        elif 'top' in handle_type:
            new_height = max(5, current_height - delta_y)
        
        # Apply changes
        if new_width != current_width:
            self._target.set_width(new_width)
            self.sizeChanged.emit(self._target, 'width', new_width)
        if new_height != current_height:
            self._target.set_height(new_height)
            self.sizeChanged.emit(self._target, 'height', new_height)
    
    def _resize_arc_widget(self, handle_type: str, delta_x: int, delta_y: int):
        """Resize a circular arc widget"""
        current_radius = self._target.get_radius()
        current_thickness = self._target.get_thickness()
        
        # Use average of x and y delta for radius change (uniform scaling)
        delta = (abs(delta_x) + abs(delta_y)) // 2
        
        # Determine direction based on handle type and deltas
        if handle_type == 'bottom-right':
            if delta_x > 0 or delta_y > 0:
                delta = max(delta_x, delta_y)
            else:
                delta = min(delta_x, delta_y)
        elif handle_type == 'top-left':
            if delta_x < 0 or delta_y < 0:
                delta = -max(abs(delta_x), abs(delta_y))
            else:
                delta = min(abs(delta_x), abs(delta_y))
        elif handle_type == 'top-right':
            delta = delta_x if abs(delta_x) > abs(delta_y) else -delta_y
        elif handle_type == 'bottom-left':
            delta = -delta_x if abs(delta_x) > abs(delta_y) else delta_y
        
        new_radius = max(10, current_radius + delta)
        
        if new_radius != current_radius:
            self._target.set_radius(new_radius)
            self.sizeChanged.emit(self._target, 'radius', new_radius)
    
    def _resize_shape_widget(self, handle_type: str, delta_x: int, delta_y: int):
        """Resize a shape widget"""
        current_width = self._target.get_width()
        current_height = self._target.get_height()
        
        # Calculate new dimensions based on handle
        new_width = current_width
        new_height = current_height
        
        if 'right' in handle_type:
            new_width = max(5, current_width + delta_x)
        elif 'left' in handle_type:
            new_width = max(5, current_width - delta_x)
        
        if 'bottom' in handle_type:
            new_height = max(5, current_height + delta_y)
        elif 'top' in handle_type:
            new_height = max(5, current_height - delta_y)
        
        # Apply changes
        if new_width != current_width:
            self._target.set_width(new_width)
            self.sizeChanged.emit(self._target, 'width', new_width)
        if new_height != current_height:
            self._target.set_height(new_height)
            self.sizeChanged.emit(self._target, 'height', new_height)
    
    def _resize_text_widget(self, handle_type: str, delta_x: int, delta_y: int):
        """Resize a text widget by changing font size.
        
        Uses accumulated deltas for smooth, predictable resizing.
        Dragging outward increases size, inward decreases.
        """
        current_size = self._target.get_font_size()
        
        # Use the dominant axis movement for clearer control
        # Positive = increase font, Negative = decrease font
        if handle_type == 'bottom-right':
            # Dragging right or down = increase
            effective_delta = max(delta_x, delta_y) if (delta_x > 0 or delta_y > 0) else min(delta_x, delta_y)
        elif handle_type == 'top-left':
            # Dragging left or up = increase (negate the deltas)
            effective_delta = max(-delta_x, -delta_y) if (delta_x < 0 or delta_y < 0) else min(-delta_x, -delta_y)
        elif handle_type == 'top-right':
            # Dragging right or up = increase
            effective_delta = max(delta_x, -delta_y) if (delta_x > 0 or delta_y < 0) else min(delta_x, -delta_y)
        elif handle_type == 'bottom-left':
            # Dragging left or down = increase
            effective_delta = max(-delta_x, delta_y) if (delta_x < 0 or delta_y > 0) else min(-delta_x, delta_y)
        else:
            effective_delta = 0
        
        # Accumulate delta for smooth changes
        self._accumulated_delta += effective_delta
        
        # Every 3 pixels of movement = 1pt font change (responsive but not too jumpy)
        pixels_per_point = 3.0
        
        # Calculate how many font points to change
        font_delta = int(self._accumulated_delta / pixels_per_point)
        
        if font_delta != 0:
            # Consume the used delta, keep remainder for smooth sub-point tracking
            self._accumulated_delta -= font_delta * pixels_per_point
            
            new_size = max(8, min(96, current_size + font_delta))
            
            if new_size != current_size:
                self._target.set_font_size(new_size)
                self.sizeChanged.emit(self._target, 'font_size', new_size)


class PropertyPopup(QWidget):
    """Base class for property popup dialogs.
    
    A small floating panel that appears when double-clicking a widget,
    allowing quick editing of common properties.
    """
    
    # Signal emitted when a property changes
    propertyChanged = Signal(object, str, object)  # target_widget, property_name, new_value
    
    # Available metrics for dropdowns
    METRIC_OPTIONS = [
        ("CPU Usage", "cpu_usage"),
        ("CPU Temp", "cpu_temperature"),
        ("GPU Usage", "gpu_usage"),
        ("GPU Temp", "gpu_temperature"),
        ("RAM %", "ram_percent"),
        ("GPU Mem %", "gpu_mem_percent"),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._target = None
        self._color_dialog_open = False  # Track if color dialog is open
        
        # Use Tool window - stays on top but doesn't auto-close like Popup
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # Dark theme styling
        self.setStyleSheet("""
            PropertyPopup, QWidget#popupContainer {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 6px;
            }
            QLabel {
                color: #ffffff;
                font-size: 11px;
            }
            QLabel#titleLabel {
                font-weight: bold;
                font-size: 12px;
                color: #3498db;
            }
            QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px 6px;
                min-width: 60px;
            }
            QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover, QLineEdit:hover {
                border-color: #3498db;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #555555;
                background-color: #3d3d3d;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 8px;
                min-width: 24px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border-color: #3498db;
            }
            QPushButton#closeButton {
                background-color: transparent;
                border: none;
                color: #888888;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#closeButton:hover {
                color: #ffffff;
            }
            QPushButton#colorButton {
                min-width: 32px;
                min-height: 20px;
                border-radius: 3px;
            }
        """)
    
    def show_for_widget(self, target_widget, global_pos):
        """Show popup for a specific widget at the given position"""
        # Reset state
        self._color_dialog_open = False
        self._target = target_widget
        self._populate_fields()
        
        # Position near the click but ensure it stays on screen
        self.adjustSize()
        screen = self.screen().availableGeometry() if self.screen() else None
        
        x = global_pos.x() + 10
        y = global_pos.y() + 10
        
        if screen:
            if x + self.width() > screen.right():
                x = global_pos.x() - self.width() - 10
            if y + self.height() > screen.bottom():
                y = global_pos.y() - self.height() - 10
        
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
    
    def _populate_fields(self):
        """Override in subclasses to populate fields from target widget"""
        pass
    
    def _create_title_bar(self, title: str):
        """Create a title bar with close button"""
        from PySide6.QtWidgets import QHBoxLayout
        
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 5)
        
        title_label = QLabel(title)
        title_label.setObjectName("titleLabel")
        
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.close)
        
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        title_bar.addWidget(close_btn)
        
        return title_bar
    
    def _create_color_button(self, initial_color: QColor, callback):
        """Create a color picker button"""
        btn = QPushButton()
        btn.setObjectName("colorButton")
        btn.setFixedSize(32, 20)
        btn._color = initial_color
        btn.setStyleSheet(f"background-color: {initial_color.name()};")
        popup = self  # Capture reference to popup
        
        def pick_color():
            from PySide6.QtWidgets import QColorDialog
            popup._color_dialog_open = True
            color = QColorDialog.getColor(btn._color, popup, "Select Color")
            popup._color_dialog_open = False
            if color.isValid():
                btn._color = color
                btn.setStyleSheet(f"background-color: {color.name()};")
                callback(color)
            # Re-raise popup after color dialog closes
            popup.raise_()
            popup.activateWindow()
        
        btn.clicked.connect(pick_color)
        return btn
    
    def _create_spin_box(self, min_val, max_val, initial, callback, suffix=""):
        """Create a spin box with callback"""
        from PySide6.QtWidgets import QSpinBox
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(initial)
        if suffix:
            spin.setSuffix(suffix)
        spin.valueChanged.connect(callback)
        return spin
    
    def _create_combo_box(self, items, initial_data, callback):
        """Create a combo box with (display_text, data) items"""
        from PySide6.QtWidgets import QComboBox
        combo = QComboBox()
        current_idx = 0
        for i, (text, data) in enumerate(items):
            combo.addItem(text, data)
            if data == initial_data:
                current_idx = i
        combo.setCurrentIndex(current_idx)
        combo.currentIndexChanged.connect(lambda idx: callback(combo.itemData(idx)))
        return combo
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        super().mousePressEvent(event)


class TextPropertyPopup(PropertyPopup):
    """Property popup for text widgets (MetricWidget, TimeWidget, DateWidget, FreeTextWidget)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox, QCheckBox, QComboBox
        from PySide6.QtGui import QFontDatabase
        
        container = QWidget()
        container.setObjectName("popupContainer")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)
        
        # Title bar
        layout.addLayout(self._create_title_bar("Text Properties"))
        
        # Form layout for properties
        form = QFormLayout()
        form.setSpacing(6)
        form.setLabelAlignment(Qt.AlignRight)
        
        # Font family selector
        self._font_combo = QComboBox()
        self._font_combo.setMaxVisibleItems(15)
        # Get available system fonts
        font_db = QFontDatabase()
        families = sorted(font_db.families())
        for family in families:
            self._font_combo.addItem(family)
        self._font_combo.currentTextChanged.connect(self._on_font_changed)
        form.addRow("Font:", self._font_combo)
        
        # Font size
        self._font_spin = QSpinBox()
        self._font_spin.setRange(8, 96)
        self._font_spin.setSuffix(" pt")
        self._font_spin.valueChanged.connect(self._on_font_size_changed)
        form.addRow("Font Size:", self._font_spin)
        
        # Color
        self._color_btn = self._create_color_button(QColor(255, 255, 255), self._on_color_changed)
        color_row = QHBoxLayout()
        color_row.addWidget(self._color_btn)
        color_row.addStretch()
        form.addRow("Color:", color_row)
        
        # Use theme gradient checkbox
        self._gradient_check = QCheckBox()
        self._gradient_check.setToolTip("When checked, uses the global theme gradient instead of the solid color above")
        self._gradient_check.stateChanged.connect(self._on_gradient_changed)
        form.addRow("Use Gradient:", self._gradient_check)
        
        # Bold checkbox
        self._bold_check = QCheckBox()
        self._bold_check.stateChanged.connect(self._on_bold_changed)
        form.addRow("Bold:", self._bold_check)
        
        layout.addLayout(form)
    
    def _populate_fields(self):
        if not self._target:
            return
        
        # Block signals while populating
        self._font_combo.blockSignals(True)
        self._font_spin.blockSignals(True)
        self._bold_check.blockSignals(True)
        self._gradient_check.blockSignals(True)
        
        # Font family
        if hasattr(self._target, 'get_font_name'):
            font_name = self._target.get_font_name()
            idx = self._font_combo.findText(font_name)
            if idx >= 0:
                self._font_combo.setCurrentIndex(idx)
        
        self._font_spin.setValue(self._target.get_font_size())
        
        # Get color from target using getter method
        if hasattr(self._target, 'get_color'):
            color = self._target.get_color()
        elif hasattr(self._target, 'text_style'):
            color = self._target.text_style.color
        else:
            color = QColor(255, 255, 255)
        self._color_btn._color = color
        self._color_btn.setStyleSheet(f"background-color: {color.name()};")
        
        # Get use_gradient from target
        if hasattr(self._target, 'get_use_gradient'):
            self._gradient_check.setChecked(self._target.get_use_gradient())
        else:
            self._gradient_check.setChecked(True)  # Default to gradient enabled
        
        # Get bold from target using getter method
        if hasattr(self._target, 'get_bold'):
            self._bold_check.setChecked(self._target.get_bold())
        elif hasattr(self._target, 'text_style'):
            self._bold_check.setChecked(self._target.text_style.bold)
        else:
            self._bold_check.setChecked(False)
        
        self._font_combo.blockSignals(False)
        self._font_spin.blockSignals(False)
        self._bold_check.blockSignals(False)
        self._gradient_check.blockSignals(False)
    
    def _on_font_changed(self, font_name):
        if self._target and hasattr(self._target, 'set_font_name'):
            self._target.set_font_name(font_name)
            self.propertyChanged.emit(self._target, 'font_name', font_name)
    
    def _on_font_size_changed(self, value):
        if self._target:
            self._target.set_font_size(value)
            self.propertyChanged.emit(self._target, 'font_size', value)
    
    def _on_color_changed(self, color):
        if self._target:
            if hasattr(self._target, 'set_color'):
                self._target.set_color(color)
            elif hasattr(self._target, 'set_text_color'):
                self._target.set_text_color(color)
            self.propertyChanged.emit(self._target, 'color', color)
    
    def _on_gradient_changed(self, state):
        if self._target:
            use_gradient = bool(state)
            if hasattr(self._target, 'set_use_gradient'):
                self._target.set_use_gradient(use_gradient)
            self.propertyChanged.emit(self._target, 'use_gradient', use_gradient)
    
    def _on_bold_changed(self, state):
        if self._target:
            bold = bool(state)
            if hasattr(self._target, 'set_bold'):
                self._target.set_bold(bold)
            self.propertyChanged.emit(self._target, 'bold', bold)


class MetricPropertyPopup(PropertyPopup):
    """Property popup for MetricWidget with metric selector"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox, QCheckBox, QComboBox
        from PySide6.QtGui import QFontDatabase
        
        container = QWidget()
        container.setObjectName("popupContainer")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)
        
        # Title bar
        layout.addLayout(self._create_title_bar("Metric Properties"))
        
        # Form layout
        form = QFormLayout()
        form.setSpacing(6)
        form.setLabelAlignment(Qt.AlignRight)
        
        # Metric selector
        self._metric_combo = QComboBox()
        for text, data in self.METRIC_OPTIONS:
            self._metric_combo.addItem(text, data)
        self._metric_combo.currentIndexChanged.connect(self._on_metric_changed)
        form.addRow("Metric:", self._metric_combo)
        
        # Font family selector
        self._font_combo = QComboBox()
        self._font_combo.setMaxVisibleItems(15)
        font_db = QFontDatabase()
        families = sorted(font_db.families())
        for family in families:
            self._font_combo.addItem(family)
        self._font_combo.currentTextChanged.connect(self._on_font_changed)
        form.addRow("Font:", self._font_combo)
        
        # Font size
        self._font_spin = QSpinBox()
        self._font_spin.setRange(8, 96)
        self._font_spin.setSuffix(" pt")
        self._font_spin.valueChanged.connect(self._on_font_size_changed)
        form.addRow("Font Size:", self._font_spin)
        
        # Color
        self._color_btn = self._create_color_button(QColor(255, 255, 255), self._on_color_changed)
        color_row = QHBoxLayout()
        color_row.addWidget(self._color_btn)
        color_row.addStretch()
        form.addRow("Color:", color_row)
        
        # Use theme gradient checkbox
        self._gradient_check = QCheckBox()
        self._gradient_check.setToolTip("When checked, uses the global theme gradient instead of the solid color above")
        self._gradient_check.stateChanged.connect(self._on_gradient_changed)
        form.addRow("Use Gradient:", self._gradient_check)
        
        # Bold
        self._bold_check = QCheckBox()
        self._bold_check.stateChanged.connect(self._on_bold_changed)
        form.addRow("Bold:", self._bold_check)
        
        # Character limit (for name metrics only)
        self._char_limit_row = QWidget()
        char_limit_layout = QHBoxLayout(self._char_limit_row)
        char_limit_layout.setContentsMargins(0, 0, 0, 0)
        self._char_limit_spin = QSpinBox()
        self._char_limit_spin.setRange(0, 100)
        self._char_limit_spin.setSpecialValueText("No limit")
        self._char_limit_spin.setToolTip("Limit the number of characters displayed (0 = no limit)")
        self._char_limit_spin.valueChanged.connect(self._on_char_limit_changed)
        char_limit_layout.addWidget(self._char_limit_spin)
        char_limit_layout.addStretch()
        self._char_limit_label = QLabel("Char Limit:")
        form.addRow(self._char_limit_label, self._char_limit_row)
        # Initially hide - will show only for name metrics
        self._char_limit_row.hide()
        self._char_limit_label.hide()
        
        layout.addLayout(form)
    
    def _populate_fields(self):
        if not self._target:
            return
        
        self._font_combo.blockSignals(True)
        self._font_spin.blockSignals(True)
        self._metric_combo.blockSignals(True)
        self._bold_check.blockSignals(True)
        self._char_limit_spin.blockSignals(True)
        
        # Set metric
        metric_name = getattr(self._target, 'metric_name', 'cpu_usage')
        for i in range(self._metric_combo.count()):
            if self._metric_combo.itemData(i) == metric_name:
                self._metric_combo.setCurrentIndex(i)
                break
        
        # Show/hide char limit based on metric type
        is_name_metric = metric_name in ['cpu_name', 'gpu_name']
        self._char_limit_row.setVisible(is_name_metric)
        self._char_limit_label.setVisible(is_name_metric)
        
        # Set char limit value
        if hasattr(self._target, 'get_char_limit'):
            self._char_limit_spin.setValue(self._target.get_char_limit())
        else:
            self._char_limit_spin.setValue(0)
        
        # Font family
        if hasattr(self._target, 'get_font_name'):
            font_name = self._target.get_font_name()
            idx = self._font_combo.findText(font_name)
            if idx >= 0:
                self._font_combo.setCurrentIndex(idx)
        
        self._font_spin.setValue(self._target.get_font_size())
        
        # Color - use getter method
        if hasattr(self._target, 'get_color'):
            color = self._target.get_color()
        elif hasattr(self._target, 'text_style'):
            color = self._target.text_style.color
        else:
            color = QColor(255, 255, 255)
        self._color_btn._color = color
        self._color_btn.setStyleSheet(f"background-color: {color.name()};")
        
        # Get use_gradient from target
        self._gradient_check.blockSignals(True)
        if hasattr(self._target, 'get_use_gradient'):
            self._gradient_check.setChecked(self._target.get_use_gradient())
        else:
            self._gradient_check.setChecked(True)  # Default to gradient enabled
        self._gradient_check.blockSignals(False)
        
        # Bold - use getter method
        if hasattr(self._target, 'get_bold'):
            self._bold_check.setChecked(self._target.get_bold())
        elif hasattr(self._target, 'text_style'):
            self._bold_check.setChecked(self._target.text_style.bold)
        
        self._font_combo.blockSignals(False)
        self._font_spin.blockSignals(False)
        self._metric_combo.blockSignals(False)
        self._bold_check.blockSignals(False)
        self._char_limit_spin.blockSignals(False)
    
    def _on_metric_changed(self, idx):
        if self._target:
            metric = self._metric_combo.itemData(idx)
            # Update the widget's metric_name directly
            if hasattr(self._target, 'set_metric_name'):
                self._target.set_metric_name(metric)
            else:
                self._target.metric_name = metric
            self.propertyChanged.emit(self._target, 'metric_name', metric)
            
            # Show/hide char limit based on metric type
            is_name_metric = metric in ['cpu_name', 'gpu_name']
            self._char_limit_row.setVisible(is_name_metric)
            self._char_limit_label.setVisible(is_name_metric)
    
    def _on_font_changed(self, font_name):
        if self._target and hasattr(self._target, 'set_font_name'):
            self._target.set_font_name(font_name)
            self.propertyChanged.emit(self._target, 'font_name', font_name)
    
    def _on_font_size_changed(self, value):
        if self._target:
            self._target.set_font_size(value)
            self.propertyChanged.emit(self._target, 'font_size', value)
    
    def _on_color_changed(self, color):
        if self._target:
            if hasattr(self._target, 'set_color'):
                self._target.set_color(color)
            self.propertyChanged.emit(self._target, 'color', color)
    
    def _on_gradient_changed(self, state):
        if self._target:
            use_gradient = bool(state)
            if hasattr(self._target, 'set_use_gradient'):
                self._target.set_use_gradient(use_gradient)
            self.propertyChanged.emit(self._target, 'use_gradient', use_gradient)
    
    def _on_bold_changed(self, state):
        if self._target:
            bold = bool(state)
            if hasattr(self._target, 'set_bold'):
                self._target.set_bold(bold)
            self.propertyChanged.emit(self._target, 'bold', bold)
    
    def _on_char_limit_changed(self, value):
        if self._target:
            if hasattr(self._target, 'set_char_limit'):
                self._target.set_char_limit(value)
            self.propertyChanged.emit(self._target, 'char_limit', value)


class BarGraphPropertyPopup(PropertyPopup):
    """Property popup for BarGraphWidget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox, QCheckBox, QComboBox
        
        container = QWidget()
        container.setObjectName("popupContainer")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)
        
        # Title bar
        layout.addLayout(self._create_title_bar("Bar Graph"))
        
        # Form layout
        form = QFormLayout()
        form.setSpacing(6)
        form.setLabelAlignment(Qt.AlignRight)
        
        # Metric selector
        self._metric_combo = QComboBox()
        for text, data in self.METRIC_OPTIONS:
            self._metric_combo.addItem(text, data)
        self._metric_combo.currentIndexChanged.connect(self._on_metric_changed)
        form.addRow("Metric:", self._metric_combo)
        
        # Size row: Width and Height
        size_row = QHBoxLayout()
        self._width_spin = QSpinBox()
        self._width_spin.setRange(10, 500)
        self._width_spin.valueChanged.connect(self._on_width_changed)
        size_row.addWidget(QLabel("W:"))
        size_row.addWidget(self._width_spin)
        
        self._height_spin = QSpinBox()
        self._height_spin.setRange(5, 200)
        self._height_spin.valueChanged.connect(self._on_height_changed)
        size_row.addWidget(QLabel("H:"))
        size_row.addWidget(self._height_spin)
        form.addRow("Size:", size_row)
        
        # Fill color (used when gradient is off)
        self._fill_btn = self._create_color_button(QColor(0, 255, 0), self._on_fill_changed)
        fill_row = QHBoxLayout()
        fill_row.addWidget(self._fill_btn)
        fill_row.addStretch()
        form.addRow("Fill:", fill_row)
        
        # Background color
        self._bg_btn = self._create_color_button(QColor(50, 50, 50), self._on_bg_changed)
        bg_row = QHBoxLayout()
        bg_row.addWidget(self._bg_btn)
        bg_row.addStretch()
        form.addRow("Background:", bg_row)
        
        # Rotation
        self._rotation_spin = QSpinBox()
        self._rotation_spin.setRange(0, 359)
        self._rotation_spin.setSuffix("°")
        self._rotation_spin.valueChanged.connect(self._on_rotation_changed)
        form.addRow("Rotation:", self._rotation_spin)
        
        # Gradient checkbox
        self._gradient_check = QCheckBox()
        self._gradient_check.stateChanged.connect(self._on_gradient_changed)
        form.addRow("Gradient:", self._gradient_check)
        
        # Gradient colors (shown when gradient is enabled)
        self._gradient_container = QWidget()
        gradient_layout = QHBoxLayout(self._gradient_container)
        gradient_layout.setContentsMargins(0, 0, 0, 0)
        gradient_layout.setSpacing(4)
        
        # Low color (0%)
        self._gradient_low_btn = self._create_color_button(QColor(0, 255, 0), self._on_gradient_low_changed)
        gradient_layout.addWidget(QLabel("0%:"))
        gradient_layout.addWidget(self._gradient_low_btn)
        
        # Mid color (50%)
        self._gradient_mid_btn = self._create_color_button(QColor(255, 255, 0), self._on_gradient_mid_changed)
        gradient_layout.addWidget(QLabel("50%:"))
        gradient_layout.addWidget(self._gradient_mid_btn)
        
        # High color (100%)
        self._gradient_high_btn = self._create_color_button(QColor(255, 0, 0), self._on_gradient_high_changed)
        gradient_layout.addWidget(QLabel("100%:"))
        gradient_layout.addWidget(self._gradient_high_btn)
        
        form.addRow("", self._gradient_container)
        self._gradient_container.hide()  # Hidden by default
        
        layout.addLayout(form)
    
    def _populate_fields(self):
        if not self._target:
            return
        
        # Block all signals
        for widget in [self._metric_combo, self._width_spin, self._height_spin, 
                       self._rotation_spin, self._gradient_check]:
            widget.blockSignals(True)
        
        # Metric
        metric = self._target.get_metric_name()
        for i in range(self._metric_combo.count()):
            if self._metric_combo.itemData(i) == metric:
                self._metric_combo.setCurrentIndex(i)
                break
        
        # Size
        self._width_spin.setValue(self._target.get_width())
        self._height_spin.setValue(self._target.get_height())
        
        # Colors
        fill = self._target.get_fill_color()
        self._fill_btn._color = fill
        self._fill_btn.setStyleSheet(f"background-color: {fill.name()};")
        
        bg = self._target.get_background_color()
        self._bg_btn._color = bg
        self._bg_btn.setStyleSheet(f"background-color: {bg.name()};")
        
        # Rotation
        self._rotation_spin.setValue(self._target.get_rotation())
        
        # Gradient
        use_gradient = self._target.get_use_gradient()
        self._gradient_check.setChecked(use_gradient)
        
        # Populate gradient colors from target
        gradient_colors = self._target.get_gradient_colors()
        if gradient_colors and len(gradient_colors) >= 3:
            # Format: [(threshold, (r, g, b, a)), ...]
            low_color = QColor(*gradient_colors[0][1][:3])
            mid_color = QColor(*gradient_colors[1][1][:3])
            high_color = QColor(*gradient_colors[2][1][:3])
        else:
            # Default gradient colors
            low_color = QColor(0, 255, 0)
            mid_color = QColor(255, 255, 0)
            high_color = QColor(255, 0, 0)
        
        self._gradient_low_btn._color = low_color
        self._gradient_low_btn.setStyleSheet(f"background-color: {low_color.name()};")
        self._gradient_mid_btn._color = mid_color
        self._gradient_mid_btn.setStyleSheet(f"background-color: {mid_color.name()};")
        self._gradient_high_btn._color = high_color
        self._gradient_high_btn.setStyleSheet(f"background-color: {high_color.name()};")
        
        # Show/hide gradient colors based on checkbox
        self._gradient_container.setVisible(use_gradient)
        
        # Unblock signals
        for widget in [self._metric_combo, self._width_spin, self._height_spin,
                       self._rotation_spin, self._gradient_check]:
            widget.blockSignals(False)
        
        # Resize popup to fit content
        self.adjustSize()
    
    def _on_metric_changed(self, idx):
        if self._target:
            self._target.set_metric_name(self._metric_combo.itemData(idx))
            self.propertyChanged.emit(self._target, 'metric_name', self._metric_combo.itemData(idx))
    
    def _on_width_changed(self, value):
        if self._target:
            self._target.set_width(value)
            self.propertyChanged.emit(self._target, 'width', value)
    
    def _on_height_changed(self, value):
        if self._target:
            self._target.set_height(value)
            self.propertyChanged.emit(self._target, 'height', value)
    
    def _on_fill_changed(self, color):
        if self._target:
            self._target.set_fill_color(color)
            self.propertyChanged.emit(self._target, 'fill_color', color)
    
    def _on_bg_changed(self, color):
        if self._target:
            self._target.set_background_color(color)
            self.propertyChanged.emit(self._target, 'background_color', color)
    
    def _on_rotation_changed(self, value):
        if self._target:
            self._target.set_rotation(value)
            self.propertyChanged.emit(self._target, 'rotation', value)
    
    def _on_gradient_changed(self, state):
        if self._target:
            use = bool(state)
            self._target.set_use_gradient(use)
            self._gradient_container.setVisible(use)
            self.adjustSize()
            self.propertyChanged.emit(self._target, 'use_gradient', use)
    
    def _update_gradient_colors(self):
        """Update the target's gradient colors from the buttons"""
        if not self._target:
            return
        low = self._gradient_low_btn._color
        mid = self._gradient_mid_btn._color
        high = self._gradient_high_btn._color
        gradient_colors = [
            (0, (low.red(), low.green(), low.blue(), 255)),
            (50, (mid.red(), mid.green(), mid.blue(), 255)),
            (100, (high.red(), high.green(), high.blue(), 255)),
        ]
        self._target.set_gradient_colors(gradient_colors)
        self.propertyChanged.emit(self._target, 'gradient_colors', gradient_colors)
    
    def _on_gradient_low_changed(self, color):
        self._update_gradient_colors()
    
    def _on_gradient_mid_changed(self, color):
        self._update_gradient_colors()
    
    def _on_gradient_high_changed(self, color):
        self._update_gradient_colors()


class ArcGraphPropertyPopup(PropertyPopup):
    """Property popup for CircularGraphWidget (arc graph)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox, QCheckBox, QComboBox
        
        container = QWidget()
        container.setObjectName("popupContainer")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)
        
        # Title bar
        layout.addLayout(self._create_title_bar("Arc Graph"))
        
        # Form layout
        form = QFormLayout()
        form.setSpacing(6)
        form.setLabelAlignment(Qt.AlignRight)
        
        # Metric selector
        self._metric_combo = QComboBox()
        for text, data in self.METRIC_OPTIONS:
            self._metric_combo.addItem(text, data)
        self._metric_combo.currentIndexChanged.connect(self._on_metric_changed)
        form.addRow("Metric:", self._metric_combo)
        
        # Radius
        self._radius_spin = QSpinBox()
        self._radius_spin.setRange(10, 200)
        self._radius_spin.valueChanged.connect(self._on_radius_changed)
        form.addRow("Radius:", self._radius_spin)
        
        # Thickness
        self._thickness_spin = QSpinBox()
        self._thickness_spin.setRange(2, 50)
        self._thickness_spin.valueChanged.connect(self._on_thickness_changed)
        form.addRow("Thickness:", self._thickness_spin)
        
        # Fill color
        self._fill_btn = self._create_color_button(QColor(0, 255, 0), self._on_fill_changed)
        fill_row = QHBoxLayout()
        fill_row.addWidget(self._fill_btn)
        fill_row.addStretch()
        form.addRow("Fill:", fill_row)
        
        # Background color
        self._bg_btn = self._create_color_button(QColor(50, 50, 50), self._on_bg_changed)
        bg_row = QHBoxLayout()
        bg_row.addWidget(self._bg_btn)
        bg_row.addStretch()
        form.addRow("Background:", bg_row)
        
        # Rotation
        self._rotation_spin = QSpinBox()
        self._rotation_spin.setRange(0, 359)
        self._rotation_spin.setSuffix("°")
        self._rotation_spin.valueChanged.connect(self._on_rotation_changed)
        form.addRow("Rotation:", self._rotation_spin)
        
        # Start angle
        self._start_spin = QSpinBox()
        self._start_spin.setRange(0, 359)
        self._start_spin.setSuffix("°")
        self._start_spin.valueChanged.connect(self._on_start_changed)
        form.addRow("Start Angle:", self._start_spin)
        
        # Sweep angle
        self._sweep_spin = QSpinBox()
        self._sweep_spin.setRange(1, 360)
        self._sweep_spin.setSuffix("°")
        self._sweep_spin.valueChanged.connect(self._on_sweep_changed)
        form.addRow("Sweep:", self._sweep_spin)
        
        # Gradient checkbox
        self._gradient_check = QCheckBox()
        self._gradient_check.stateChanged.connect(self._on_gradient_changed)
        form.addRow("Gradient:", self._gradient_check)
        
        layout.addLayout(form)
        
        # Gradient colors (initially hidden)
        self._gradient_widget = QWidget()
        gradient_layout = QFormLayout(self._gradient_widget)
        gradient_layout.setSpacing(6)
        gradient_layout.setContentsMargins(0, 0, 0, 0)
        gradient_layout.setLabelAlignment(Qt.AlignRight)
        
        self._gradient_start_btn = self._create_color_button(QColor(255, 0, 0), self._on_gradient_start_changed)
        start_row = QHBoxLayout()
        start_row.addWidget(self._gradient_start_btn)
        start_row.addStretch()
        gradient_layout.addRow("Start Color:", start_row)
        
        self._gradient_mid_btn = self._create_color_button(QColor(255, 255, 0), self._on_gradient_mid_changed)
        mid_row = QHBoxLayout()
        mid_row.addWidget(self._gradient_mid_btn)
        mid_row.addStretch()
        gradient_layout.addRow("Mid Color:", mid_row)
        
        self._gradient_end_btn = self._create_color_button(QColor(0, 255, 0), self._on_gradient_end_changed)
        end_row = QHBoxLayout()
        end_row.addWidget(self._gradient_end_btn)
        end_row.addStretch()
        gradient_layout.addRow("End Color:", end_row)
        
        self._gradient_widget.hide()
        layout.addWidget(self._gradient_widget)
    
    def _populate_fields(self):
        if not self._target:
            return
        
        # Block all signals
        widgets = [self._metric_combo, self._radius_spin, self._thickness_spin,
                   self._rotation_spin, self._start_spin, self._sweep_spin, self._gradient_check]
        for widget in widgets:
            widget.blockSignals(True)
        
        # Metric
        metric = self._target.get_metric_name()
        for i in range(self._metric_combo.count()):
            if self._metric_combo.itemData(i) == metric:
                self._metric_combo.setCurrentIndex(i)
                break
        
        # Dimensions
        self._radius_spin.setValue(self._target.get_radius())
        self._thickness_spin.setValue(self._target.get_thickness())
        
        # Colors
        fill = self._target.get_fill_color()
        self._fill_btn._color = fill
        self._fill_btn.setStyleSheet(f"background-color: {fill.name()};")
        
        bg = self._target.get_background_color()
        self._bg_btn._color = bg
        self._bg_btn.setStyleSheet(f"background-color: {bg.name()};")
        
        # Angles
        self._rotation_spin.setValue(self._target.get_rotation())
        self._start_spin.setValue(self._target.get_start_angle())
        self._sweep_spin.setValue(self._target.get_sweep_angle())
        
        # Gradient
        use_gradient = self._target.get_use_gradient()
        self._gradient_check.setChecked(use_gradient)
        
        # Gradient colors - convert from [(threshold, (r,g,b,a)), ...] format
        if hasattr(self._target, 'get_gradient_colors'):
            colors = self._target.get_gradient_colors()
            if colors and len(colors) >= 3:
                # Extract RGB tuples and convert to QColor
                _, rgba0 = colors[0]
                _, rgba1 = colors[1]
                _, rgba2 = colors[2]
                
                c0 = QColor(rgba0[0], rgba0[1], rgba0[2], rgba0[3] if len(rgba0) > 3 else 255)
                c1 = QColor(rgba1[0], rgba1[1], rgba1[2], rgba1[3] if len(rgba1) > 3 else 255)
                c2 = QColor(rgba2[0], rgba2[1], rgba2[2], rgba2[3] if len(rgba2) > 3 else 255)
                
                self._gradient_start_btn._color = c0
                self._gradient_start_btn.setStyleSheet(f"background-color: {c0.name()};")
                self._gradient_mid_btn._color = c1
                self._gradient_mid_btn.setStyleSheet(f"background-color: {c1.name()};")
                self._gradient_end_btn._color = c2
                self._gradient_end_btn.setStyleSheet(f"background-color: {c2.name()};")
        
        # Show/hide gradient controls
        self._update_gradient_visibility(use_gradient)
        
        # Unblock signals
        for widget in widgets:
            widget.blockSignals(False)
    
    def _on_metric_changed(self, idx):
        if self._target:
            self._target.set_metric_name(self._metric_combo.itemData(idx))
            self.propertyChanged.emit(self._target, 'metric_name', self._metric_combo.itemData(idx))
    
    def _on_radius_changed(self, value):
        if self._target:
            self._target.set_radius(value)
            self.propertyChanged.emit(self._target, 'radius', value)
    
    def _on_thickness_changed(self, value):
        if self._target:
            self._target.set_thickness(value)
            self.propertyChanged.emit(self._target, 'thickness', value)
    
    def _on_fill_changed(self, color):
        if self._target:
            self._target.set_fill_color(color)
            self.propertyChanged.emit(self._target, 'fill_color', color)
    
    def _on_bg_changed(self, color):
        if self._target:
            self._target.set_background_color(color)
            self.propertyChanged.emit(self._target, 'background_color', color)
    
    def _on_rotation_changed(self, value):
        if self._target:
            self._target.set_rotation(value)
            self.propertyChanged.emit(self._target, 'rotation', value)
    
    def _on_start_changed(self, value):
        if self._target:
            self._target.set_start_angle(value)
            self.propertyChanged.emit(self._target, 'start_angle', value)
    
    def _on_sweep_changed(self, value):
        if self._target:
            self._target.set_sweep_angle(value)
            self.propertyChanged.emit(self._target, 'sweep_angle', value)
    
    def _on_gradient_changed(self, state):
        if self._target:
            use = bool(state)
            self._target.set_use_gradient(use)
            self._update_gradient_visibility(use)
            self.propertyChanged.emit(self._target, 'use_gradient', use)
    
    def _update_gradient_visibility(self, visible):
        """Show or hide gradient color controls"""
        if visible:
            self._gradient_widget.show()
        else:
            self._gradient_widget.hide()
        self.adjustSize()
    
    def _on_gradient_start_changed(self, color):
        if self._target and hasattr(self._target, 'set_gradient_colors'):
            colors = self._target.get_gradient_colors()
            if colors and len(colors) >= 3:
                # Format: [(threshold, (r,g,b,a)), ...]
                new_colors = [
                    (colors[0][0], (color.red(), color.green(), color.blue(), 255)),
                    colors[1],
                    colors[2]
                ]
                self._target.set_gradient_colors(new_colors)
                self.propertyChanged.emit(self._target, 'gradient_colors', new_colors)
    
    def _on_gradient_mid_changed(self, color):
        if self._target and hasattr(self._target, 'set_gradient_colors'):
            colors = self._target.get_gradient_colors()
            if colors and len(colors) >= 3:
                new_colors = [
                    colors[0],
                    (colors[1][0], (color.red(), color.green(), color.blue(), 255)),
                    colors[2]
                ]
                self._target.set_gradient_colors(new_colors)
                self.propertyChanged.emit(self._target, 'gradient_colors', new_colors)
    
    def _on_gradient_end_changed(self, color):
        if self._target and hasattr(self._target, 'set_gradient_colors'):
            colors = self._target.get_gradient_colors()
            if colors and len(colors) >= 3:
                new_colors = [
                    colors[0],
                    colors[1],
                    (colors[2][0], (color.red(), color.green(), color.blue(), 255))
                ]
                self._target.set_gradient_colors(new_colors)
                self.propertyChanged.emit(self._target, 'gradient_colors', new_colors)


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
    # Emit when user starts dragging the widget (left-mouse down)
    dragStarted = Signal()
    # Emit when user finishes dragging the widget (left-mouse release)
    dragEnded = Signal()
    doubleClicked = Signal(object, QPoint)  # widget, global_pos - for property popup
    
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
        # Enable focus to receive keyboard events
        self.setFocusPolicy(Qt.StrongFocus)
        self.dragging = False
        self.drag_start_position = QPoint()
        self.setText(text)
        self.adjustSize()
        self.move(10, 10)
        self.text_style = TextStyleConfig()
        self._individual_font_size = None  # None means use global style (device coordinates)
        self._preview_scale = 1.0  # Scale factor for preview display
        self.enabled = False
        self.display_text = ""
        self._show_position_hint = False
        self._is_hovered = False
        self._is_selected = False  # Track selection state
        self.update_display()

    def update_display(self):
        """Update display - uses empty text box with calculated size"""
        if self.enabled:
            # Don't show text - just use empty box with calculated size
            self.setText("")
            self.setStyleSheet(f"QLabel {{ {self._get_stylesheet()} }}")
            
            # Calculate size using PIL to match actual rendered text
            device_font_size = self._individual_font_size if self._individual_font_size else self.text_style.font_size
            pil_width, pil_height = _get_pil_text_size(
                self.display_text,
                self.text_style.font_family,
                device_font_size,
                self.text_style.bold
            )
            # Scale for preview display
            display_width = int(pil_width * self._preview_scale)
            display_height = int(pil_height * self._preview_scale)
            self.setFixedSize(display_width, display_height)
            self.show()
        else:
            self.setText("")
            self.setStyleSheet(f"QLabel {{ {self._get_stylesheet()} }}")
            self.hide()

    def _get_stylesheet(self) -> str:
        """Get stylesheet for the selection box overlay.
        
        This is just a colored box that shows on hover/drag/select - no text is displayed.
        """
        if self.dragging:
            return "border: 2px solid #e74c3c; background-color: rgba(231, 76, 60, 0.3);"
        elif self._is_selected:
            return "border: 2px solid #2ecc71; background-color: rgba(46, 204, 113, 0.2);"
        elif self._is_hovered:
            return "border: 2px solid #3498db; background-color: rgba(52, 152, 219, 0.25);"
        else:
            return "border: none; background-color: transparent;"

    def set_font_size(self, size: int):
        """Set individual font size for this widget"""
        self._individual_font_size = size
        self.update_display()

    def get_font_size(self) -> int:
        """Get current font size (individual or global) in device coordinates"""
        return self._individual_font_size if self._individual_font_size else self.text_style.font_size

    def set_font_name(self, font_name: str):
        """Set font family for this widget"""
        self.text_style.font_family = font_name
        self.update_display()
    
    def get_font_name(self) -> str:
        """Get current font family"""
        return self.text_style.font_family

    def set_color(self, color: QColor):
        """Set text color for this widget"""
        self.text_style.color = color
        self.update_display()
    
    def get_color(self) -> QColor:
        """Get current text color"""
        return self.text_style.color
    
    def set_bold(self, bold: bool):
        """Set bold state for this widget"""
        self.text_style.bold = bold
        self.update_display()
    
    def get_bold(self) -> bool:
        """Get current bold state"""
        return self.text_style.bold

    def set_use_gradient(self, use_gradient: bool):
        """Set whether to use the global theme gradient for this widget"""
        self._use_gradient = use_gradient
        self.update_display()
    
    def get_use_gradient(self) -> bool:
        """Get whether this widget uses the global theme gradient"""
        return getattr(self, '_use_gradient', True)  # Default True for backward compat

    def set_preview_scale(self, scale: float):
        """Set the preview scale factor and update display"""
        self._preview_scale = scale
        self.update_display()

    def show_position_hint(self, show: bool):
        """Show/hide position hint when dragging"""
        self._show_position_hint = show

    def apply_style(self, style_config: TextStyleConfig):
        self.text_style = style_config
        self.update_display()

    def mousePressEvent(self, event: QMouseEvent):
        """Start dragging and select widget"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_position = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            # Select this widget (grab focus)
            self.setFocus()
            self._is_selected = True
            self.update_display()  # Update style to show drag border
            try:
                self.dragStarted.emit()
            except Exception:
                pass

    def focusInEvent(self, event):
        """Widget gained focus - show selection"""
        self._is_selected = True
        self.update_display()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        """Widget lost focus - hide selection"""
        self._is_selected = False
        self.update_display()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for selected widget"""
        from PySide6.QtCore import Qt as QtCore
        
        key = event.key()
        modifiers = event.modifiers()
        
        # Delete or Backspace - disable widget
        if key in (QtCore.Key_Delete, QtCore.Key_Backspace):
            self.set_enabled(False)
            # Emit signal so main window can update controls
            self.positionChanged.emit(self.pos())
            return
        
        # Arrow keys - nudge position
        # Shift+Arrow = 10px, plain Arrow = 1px
        nudge = 10 if modifiers & QtCore.ShiftModifier else 1
        
        new_pos = self.pos()
        if key == QtCore.Key_Left:
            new_pos.setX(new_pos.x() - nudge)
        elif key == QtCore.Key_Right:
            new_pos.setX(new_pos.x() + nudge)
        elif key == QtCore.Key_Up:
            new_pos.setY(new_pos.y() - nudge)
        elif key == QtCore.Key_Down:
            new_pos.setY(new_pos.y() + nudge)
        else:
            # Pass unhandled keys to parent
            super().keyPressEvent(event)
            return
        
        # Clamp to parent bounds
        if self.parent():
            parent_rect = self.parent().rect()
            widget_rect = self.rect()
            new_pos.setX(max(0, min(new_pos.x(), parent_rect.width() - widget_rect.width())))
            new_pos.setY(max(0, min(new_pos.y(), parent_rect.height() - widget_rect.height())))
        
        self.move(new_pos)
        self.positionChanged.emit(new_pos)
        self.setToolTip(f"Position: ({new_pos.x()}, {new_pos.y()})")

    def contextMenuEvent(self, event):
        """Show right-click context menu"""
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        # Style the menu for visibility
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
        """)
        
        # Enable/Disable action
        if self.enabled:
            disable_action = menu.addAction("Disable")
            disable_action.triggered.connect(lambda: self.set_enabled(False))
        else:
            enable_action = menu.addAction("Enable")
            enable_action.triggered.connect(lambda: self.set_enabled(True))
        
        menu.exec(event.globalPos())

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click to open property popup"""
        if event.button() == Qt.LeftButton and self.enabled:
            self.doubleClicked.emit(self, event.globalPos())
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

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
            try:
                self.dragEnded.emit()
            except Exception:
                pass

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
    dragStarted = Signal()
    dragEnded = Signal()

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

    def set_preview_bounds(self, width: int, height: int):
        """Update the preview bounds (called when rotation changes dimensions)"""
        self._width = width
        self._height = height
        # Constrain foreground widget to new bounds if active
        if self._active:
            scaled_w = int(self._image_size[0] * self._preview_scale)
            scaled_h = int(self._image_size[1] * self._preview_scale)
            max_w = min(scaled_w, width)
            max_h = min(scaled_h, height)
            self.setFixedSize(max_w, max_h)
            # Ensure position is still within bounds
            current_pos = self.pos()
            new_x = min(current_pos.x(), max(0, width - self.width()))
            new_y = min(current_pos.y(), max(0, height - self.height()))
            self.move(new_x, new_y)

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
            try:
                self.dragStarted.emit()
            except Exception:
                pass

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
            try:
                self.dragEnded.emit()
            except Exception:
                pass

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
            # Don't show text - just use empty box with calculated size
            self.setText("")
            self.setStyleSheet(f"QLabel {{ {self._get_stylesheet()} }}")
            
            # Calculate size using PIL to match actual rendered text
            device_font_size = self._individual_font_size if self._individual_font_size else self.text_style.font_size
            pil_width, pil_height = _get_pil_text_size(
                self.display_text,
                self.text_style.font_family,
                device_font_size,
                self.text_style.bold
            )
            # Scale for preview display
            display_width = int(pil_width * self._preview_scale)
            display_height = int(pil_height * self._preview_scale)
            self.setFixedSize(display_width, display_height)
            self.show()
        else:
            self.setText("")
            self.setStyleSheet(f"QLabel {{ {self._get_stylesheet()} }}")
            self.hide()


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
            # Don't show text - just use empty box with calculated size
            self.setText("")
            self.setStyleSheet(f"QLabel {{ {self._get_stylesheet()} }}")
            
            # Calculate size using PIL to match actual rendered text
            device_font_size = self._individual_font_size if self._individual_font_size else self.text_style.font_size
            pil_width, pil_height = _get_pil_text_size(
                self.display_text,
                self.text_style.font_family,
                device_font_size,
                self.text_style.bold
            )
            # Scale for preview display
            display_width = int(pil_width * self._preview_scale)
            display_height = int(pil_height * self._preview_scale)
            self.setFixedSize(display_width, display_height)
            self.show()
        else:
            self.setText("")
            self.hide()


class MetricWidget(DraggableWidget):
    """Generic metric display widget"""
    
    # Label position constants (matching service-side LabelPosition enum)
    # Legacy positions
    LABEL_LEFT = "left"
    LABEL_RIGHT = "right"
    LABEL_ABOVE = "above"
    LABEL_BELOW = "below"
    LABEL_NONE = "none"
    # New grid-based positions
    LABEL_ABOVE_LEFT = "above-left"
    LABEL_ABOVE_CENTER = "above-center"
    LABEL_ABOVE_RIGHT = "above-right"
    LABEL_BELOW_LEFT = "below-left"
    LABEL_BELOW_CENTER = "below-center"
    LABEL_BELOW_RIGHT = "below-right"
    LABEL_LEFT_TOP = "left-top"
    LABEL_LEFT_CENTER = "left-center"
    LABEL_LEFT_BOTTOM = "left-bottom"
    LABEL_RIGHT_TOP = "right-top"
    LABEL_RIGHT_CENTER = "right-center"
    LABEL_RIGHT_BOTTOM = "right-bottom"
    
    # All valid positions
    VALID_POSITIONS = [
        LABEL_NONE,
        LABEL_LEFT, LABEL_RIGHT, LABEL_ABOVE, LABEL_BELOW,  # Legacy
        LABEL_ABOVE_LEFT, LABEL_ABOVE_CENTER, LABEL_ABOVE_RIGHT,
        LABEL_BELOW_LEFT, LABEL_BELOW_CENTER, LABEL_BELOW_RIGHT,
        LABEL_LEFT_TOP, LABEL_LEFT_CENTER, LABEL_LEFT_BOTTOM,
        LABEL_RIGHT_TOP, LABEL_RIGHT_CENTER, LABEL_RIGHT_BOTTOM,
    ]

    def __init__(self, metric: type[CpuMetrics | GpuMetrics], parent=None, metric_name="", display_text=""):
        super().__init__(parent, display_text, metric_name)
        self.metric_instance = metric
        self.metric_name = metric_name
        self.enabled = False
        self.custom_label = ""
        self.custom_unit = ""
        self.label_position = self.LABEL_LEFT  # Default: label on left
        self._label_font_size = None  # None means use same as value font size
        self._label_offset_x = 0  # Horizontal offset for label
        self._label_offset_y = 0  # Vertical offset for label
        self._freq_format = "mhz"  # Default frequency format (mhz or ghz)
        self._char_limit = 0  # 0 means no limit
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
        # Map positions to their display format type
        above_positions = [self.LABEL_ABOVE, self.LABEL_ABOVE_LEFT, self.LABEL_ABOVE_CENTER, self.LABEL_ABOVE_RIGHT]
        below_positions = [self.LABEL_BELOW, self.LABEL_BELOW_LEFT, self.LABEL_BELOW_CENTER, self.LABEL_BELOW_RIGHT]
        left_positions = [self.LABEL_LEFT, self.LABEL_LEFT_TOP, self.LABEL_LEFT_CENTER, self.LABEL_LEFT_BOTTOM]
        right_positions = [self.LABEL_RIGHT, self.LABEL_RIGHT_TOP, self.LABEL_RIGHT_CENTER, self.LABEL_RIGHT_BOTTOM]
        
        if self.label_position == self.LABEL_NONE or not self.custom_label:
            self.format = "{value}{unit}"
        elif self.label_position in left_positions:
            self.format = "{label}: {value}{unit}"
        elif self.label_position in right_positions:
            self.format = "{value}{unit} :{label}"
        elif self.label_position in above_positions:
            self.format = "{label}\n{value}{unit}"
        elif self.label_position in below_positions:
            self.format = "{value}{unit}\n{label}"
        else:
            self.format = "{label}: {value}{unit}"

    def _format_display_text(self) -> str:
        """Format the display text based on current settings"""
        label = self.custom_label if self.custom_label else ""
        value = self.get_value()
        unit = self.get_unit()
        
        # Map positions to their display format type
        above_positions = [self.LABEL_ABOVE, self.LABEL_ABOVE_LEFT, self.LABEL_ABOVE_CENTER, self.LABEL_ABOVE_RIGHT]
        below_positions = [self.LABEL_BELOW, self.LABEL_BELOW_LEFT, self.LABEL_BELOW_CENTER, self.LABEL_BELOW_RIGHT]
        left_positions = [self.LABEL_LEFT, self.LABEL_LEFT_TOP, self.LABEL_LEFT_CENTER, self.LABEL_LEFT_BOTTOM]
        right_positions = [self.LABEL_RIGHT, self.LABEL_RIGHT_TOP, self.LABEL_RIGHT_CENTER, self.LABEL_RIGHT_BOTTOM]
        
        if self.label_position == self.LABEL_NONE or not label:
            return f"{value}{unit}"
        elif self.label_position in left_positions:
            return f"{label}: {value}{unit}"
        elif self.label_position in right_positions:
            return f"{value}{unit} :{label}"
        elif self.label_position in above_positions:
            return f"{label}\n{value}{unit}"
        elif self.label_position in below_positions:
            return f"{value}{unit}\n{label}"
        else:
            return f"{label}: {value}{unit}"

    def _set_initial_position(self):
        """Set initial position based on widget type"""
        positions = {
            "cpu_temperature": (10, 40), "gpu_temperature": (10, 70), "cpu_usage": (10, 100),
            "gpu_usage": (10, 130), "cpu_frequency": (10, 160), "gpu_frequency": (10, 190),
            "cpu_name": (10, 10), "gpu_name": (10, 220), "ram_total": (150, 100),
            "ram_percent": (150, 130), "gpu_mem_total": (150, 160), "gpu_mem_percent": (150, 190)
        }
        if self.metric_name in positions:
            self.move(*positions[self.metric_name])

    def set_label_position(self, position: str):
        """Set the label position relative to value"""
        if position in self.VALID_POSITIONS:
            self.label_position = position
            self._update_format()
            self.update_display()

    def get_label_position(self) -> str:
        """Get current label position"""
        return self.label_position

    def set_label_offset_x(self, offset: int):
        """Set horizontal offset for label positioning"""
        self._label_offset_x = offset
        self.update_display()

    def get_label_offset_x(self) -> int:
        """Get horizontal offset for label"""
        return self._label_offset_x

    def set_label_offset_y(self, offset: int):
        """Set vertical offset for label positioning"""
        self._label_offset_y = offset
        self.update_display()

    def get_label_offset_y(self) -> int:
        """Get vertical offset for label"""
        return self._label_offset_y

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
        """Get stylesheet for the selection box overlay.
        
        This is just a colored box that shows on hover/drag/select - no text is displayed.
        """
        if self.dragging:
            return "border: 2px solid #e74c3c; background-color: rgba(231, 76, 60, 0.3);"
        elif self._is_selected:
            return "border: 2px solid #2ecc71; background-color: rgba(46, 204, 113, 0.2);"
        elif self._is_hovered:
            return "border: 2px solid #3498db; background-color: rgba(52, 152, 219, 0.25);"
        else:
            return "border: none; background-color: transparent;"

    def _format_rich_text(self) -> str:
        """Format display text with separate font sizes for label and value using HTML.
        
        Text color is transparent normally so PIL-rendered text shows through.
        Only visible on hover/drag for positioning feedback.
        """
        label = self.custom_label if self.custom_label else ""
        value = self.get_value()
        unit = self.get_unit()
        
        # Get device font sizes and scale for preview display
        value_font_size = int(self.get_font_size() * self._preview_scale)
        label_font_size = int(self.get_label_font_size() * self._preview_scale)
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
        
        # Group positions by layout type
        above_positions = [self.LABEL_ABOVE, self.LABEL_ABOVE_LEFT, self.LABEL_ABOVE_CENTER, self.LABEL_ABOVE_RIGHT]
        below_positions = [self.LABEL_BELOW, self.LABEL_BELOW_LEFT, self.LABEL_BELOW_CENTER, self.LABEL_BELOW_RIGHT]
        left_positions = [self.LABEL_LEFT, self.LABEL_LEFT_TOP, self.LABEL_LEFT_CENTER, self.LABEL_LEFT_BOTTOM]
        right_positions = [self.LABEL_RIGHT, self.LABEL_RIGHT_TOP, self.LABEL_RIGHT_CENTER, self.LABEL_RIGHT_BOTTOM]
        
        if self.label_position == self.LABEL_NONE or not label:
            return value_span
        elif self.label_position in left_positions:
            return f'{label_span}<span style="{label_style}">: </span>{value_span}'
        elif self.label_position in right_positions:
            return f'{value_span}<span style="{label_style}"> :</span>{label_span}'
        elif self.label_position in above_positions:
            # Determine text-align based on position variant
            if self.label_position == self.LABEL_ABOVE_LEFT:
                align = "left"
            elif self.label_position == self.LABEL_ABOVE_RIGHT:
                align = "right"
            else:
                align = "center"
            return f'<div style="text-align: {align};">{label_span}<br>{value_span}</div>'
        elif self.label_position in below_positions:
            # Determine text-align based on position variant
            if self.label_position == self.LABEL_BELOW_LEFT:
                align = "left"
            elif self.label_position == self.LABEL_BELOW_RIGHT:
                align = "right"
            else:
                align = "center"
            return f'<div style="text-align: {align};">{value_span}<br>{label_span}</div>'
        else:
            return f'{label_span}<span style="{label_style}">: </span>{value_span}'

    def update_display(self):
        """Override to update with calculated box size based on PIL text metrics"""
        if self.enabled:
            # Don't show text - just use empty box with calculated size
            self.setText("")
            self.setStyleSheet(f"QLabel {{ {self._get_rich_text_stylesheet()} }}")
            
            # Get the full display text
            label = self.custom_label if self.custom_label else ""
            value = self.get_value()
            unit = self.get_unit()
            
            # Calculate sizes using PIL to match actual rendered text
            value_font_size = self.get_font_size()
            label_font_size = self.get_label_font_size()
            
            value_text = f"{value}{unit}"
            value_width, value_height = _get_pil_text_size(
                value_text,
                self.text_style.font_family,
                value_font_size,
                self.text_style.bold
            )
            
            if label:
                label_width, label_height = _get_pil_text_size(
                    label,
                    self.text_style.font_family,
                    label_font_size,
                    self.text_style.bold
                )
                
                if self.label_position in [self.LABEL_ABOVE_LEFT, self.LABEL_ABOVE_CENTER, self.LABEL_ABOVE_RIGHT,
                                            self.LABEL_BELOW_LEFT, self.LABEL_BELOW_CENTER, self.LABEL_BELOW_RIGHT]:
                    # Stacked layout - width is max, height is sum
                    total_width = max(value_width, label_width)
                    total_height = value_height + label_height
                else:
                    # Inline layout - width is sum with separator, height is max
                    sep_width, _ = _get_pil_text_size(
                        ": ",
                        self.text_style.font_family,
                        label_font_size,
                        self.text_style.bold
                    )
                    total_width = label_width + sep_width + value_width
                    total_height = max(value_height, label_height)
            else:
                total_width = value_width
                total_height = value_height
            
            # Scale for preview display
            display_width = int(total_width * self._preview_scale)
            display_height = int(total_height * self._preview_scale)
            self.setFixedSize(display_width, display_height)
            self.show()
        else:
            self.setText("")
            self.setStyleSheet(f"QLabel {{ {self._get_rich_text_stylesheet()} }}")
            self.hide()

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
        
        # Apply character limit for name metrics
        if self._char_limit > 0 and self.metric_name in ["cpu_name", "gpu_name"]:
            value = str(value)[:self._char_limit]
            return value
        
        # Convert frequency if this is a frequency metric and format is GHz
        if 'frequency' in self.metric_name and self._freq_format == "ghz":
            try:
                # Value is in MHz, convert to GHz
                mhz_value = float(value)
                ghz_value = mhz_value / 1000.0
                return f"{ghz_value:.2f}"
            except (ValueError, TypeError):
                return value
        
        # Format based on metric type
        try:
            float_value = float(value)
            # Temperature and usage - whole numbers
            if any(x in self.metric_name for x in ['temperature', 'usage', 'percent']):
                return f"{int(round(float_value))}"
            # Frequency in MHz - 2 decimal places
            elif 'frequency' in self.metric_name:
                return f"{float_value:.2f}"
            # RAM/VRAM total/used - 1 decimal place
            elif self.metric_name in ['ram_total', 'ram_used', 'gpu_mem_total', 'gpu_mem_used']:
                return f"{float_value:.1f}"
            else:
                # Default: whole number if no decimals, else as-is
                return str(int(float_value)) if float_value == int(float_value) else str(value)
        except (ValueError, TypeError):
            return str(value)

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

    def set_char_limit(self, limit: int):
        """Set character limit for display value (0 = no limit)"""
        self._char_limit = max(0, limit)
        self.update_display()

    def get_char_limit(self) -> int:
        """Get current character limit"""
        return self._char_limit

    def _get_default_label(self):
        """Get default label based on metric_name"""
        defaults = {
            "cpu_temperature": "CPU",
            "gpu_temperature": "GPU",
            "cpu_usage": "CPU%",
            "gpu_usage": "GPU%",
            "cpu_frequency": "CPU",
            "gpu_frequency": "GPU",
            "cpu_name": "",
            "gpu_name": "",
            "ram_total": "RAM",
            "ram_percent": "RAM%",
            "gpu_mem_total": "VRAM",
            "gpu_mem_percent": "VRAM%"
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
            "gpu_usage": "%",
            "cpu_name": "",
            "gpu_name": "",
            "ram_total": "GB",
            "ram_percent": "%",
            "gpu_mem_total": "GB",
            "gpu_mem_percent": "%"
        }
        return defaults.get(self.metric_name, "")


class BarGraphWidget(QLabel):
    """Draggable bar graph widget for displaying metrics as bars"""
    
    positionChanged = Signal(QPoint)
    doubleClicked = Signal(object, QPoint)  # widget, global_pos - for property popup
    
    def __init__(self, parent=None, widget_name="bar1"):
        super().__init__(parent)
        self.name = widget_name
        self.enabled = False
        self._dragging = False
        self._is_hovered = False
        self._is_selected = False  # Track selection state
        self._preview_scale = 1.0  # Scale factor for preview display
        
        # Enable mouse tracking and transparent background for drag functionality
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)  # Enable keyboard focus
        self.setCursor(Qt.OpenHandCursor)
        self._drag_start = QPoint()
        
        # Bar properties (device coordinates)
        self._metric_name = "cpu_usage"
        self._width = 100
        self._height = 16
        self._orientation = "horizontal"
        self._rotation = 0  # Rotation angle in degrees (0-360)
        
        # Colors
        self._fill_color = QColor(0, 255, 0, 255)
        self._background_color = QColor(50, 50, 50, 255)
        self._border_color = QColor(255, 255, 255, 255)
        
        # Style
        self._show_border = True
        self._border_width = 1
        self._corner_radius = 0
        
        # Gradient support
        self._use_gradient = False
        # Default gradient: green -> yellow -> red
        self._gradient_colors = [
            (0, (0, 255, 0, 255)),      # Green at 0%
            (50, (255, 255, 0, 255)),   # Yellow at 50%
            (100, (255, 0, 0, 255))     # Red at 100%
        ]
        
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

    def set_preview_scale(self, scale: float):
        """Set the preview scale factor and update display"""
        self._preview_scale = scale
        self.update_display()
    
    def _get_rotation_padding(self) -> tuple[int, int]:
        """Calculate the padding offset due to diagonal-based sizing.
        
        Returns (padding_x, padding_y) - how much extra space is on each side
        of the actual bar content within the widget.
        """
        import math
        border_padding = 4
        scaled_width = int(round(self._width * self._preview_scale))
        scaled_height = int(round(self._height * self._preview_scale))
        diagonal = int(math.ceil(math.sqrt(scaled_width**2 + scaled_height**2)))
        total_size = diagonal + border_padding * 2
        # Padding on each side is half the difference between total and scaled size
        padding_x = int(round((total_size - scaled_width) / 2.0))
        padding_y = int(round((total_size - scaled_height) / 2.0))
        return (padding_x, padding_y)

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
        """Update the current value from cached metrics (non-blocking)"""
        if not self.enabled:
            return
        
        # Get value from cached metrics (non-blocking)
        try:
            cache = _get_metrics_cache()
            self._current_value = cache.get_value(self._metric_name)
        except:
            pass
        
        self.update_display()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the widget"""
        self.enabled = enabled
        self.update_display()
    
    def update_display(self):
        """Update the visual display of the bar.
        
        Uses a fixed-size widget based on the bar's diagonal, so rotation
        doesn't change the widget's geometry - content rotates within.
        """
        if not self.enabled:
            self.hide()
            return
        
        import math
        
        # Add padding for the selection border
        border_padding = 4
        
        # Apply preview scale to dimensions for display
        scaled_width = int(self._width * self._preview_scale)
        scaled_height = int(self._height * self._preview_scale)
        
        # Use fixed size based on diagonal so rotation fits within
        # This prevents the widget from growing when rotated
        diagonal = int(math.sqrt(scaled_width**2 + scaled_height**2))
        total_size = diagonal + border_padding * 2
        
        # Create square pixmap that can contain any rotation
        pixmap = QPixmap(total_size, total_size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Calculate fill amount
        normalized = (self._current_value - self._min_value) / max(1, self._max_value - self._min_value)
        normalized = max(0.0, min(1.0, normalized))
        
        # Scale corner radius
        scaled_corner_radius = int(self._corner_radius * self._preview_scale)
        
        # Apply rotation transformation - selection border rotates WITH the bar
        painter.save()
        # Move to center of square widget
        painter.translate(total_size / 2, total_size / 2)
        # Rotate around center
        painter.rotate(self._rotation)
        # Move back so bar is centered (use scaled dimensions)
        painter.translate(-scaled_width / 2, -scaled_height / 2)
        
        # Draw selection border (now rotates with the bar)
        if self._dragging:
            painter.setBrush(QColor(231, 76, 60, 50))
            pen = QPen(QColor(231, 76, 60, 255))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRect(-2, -2, scaled_width + 4, scaled_height + 4)
        elif self._is_selected:
            painter.setBrush(QColor(46, 204, 113, 40))
            pen = QPen(QColor(46, 204, 113, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(-2, -2, scaled_width + 4, scaled_height + 4)
        elif self._is_hovered:
            painter.setBrush(QColor(52, 152, 219, 40))
            pen = QPen(QColor(52, 152, 219, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(-2, -2, scaled_width + 4, scaled_height + 4)
        
        # Now draw as if at origin (0, 0) using scaled dimensions
        bar_x = 0
        bar_y = 0
        
        # Draw background
        painter.setBrush(self._background_color)
        if self._show_border:
            pen = QPen(self._border_color)
            pen.setWidth(self._border_width)
            painter.setPen(pen)
        else:
            painter.setPen(Qt.NoPen)
        
        if scaled_corner_radius > 0:
            painter.drawRoundedRect(bar_x, bar_y, scaled_width, scaled_height, 
                                   scaled_corner_radius, scaled_corner_radius)
        else:
            painter.drawRect(bar_x, bar_y, scaled_width, scaled_height)
        
        # Determine fill color (use gradient if enabled)
        if self._use_gradient and self._gradient_colors:
            fill_color = _interpolate_gradient_color(normalized, self._gradient_colors)
        else:
            fill_color = self._fill_color
        
        # Draw fill
        painter.setBrush(fill_color)
        painter.setPen(Qt.NoPen)
        
        if self._orientation == "horizontal":
            fill_width = int(scaled_width * normalized)
            if fill_width > 0:
                if scaled_corner_radius > 0:
                    painter.drawRoundedRect(bar_x, bar_y, fill_width, scaled_height,
                                           min(scaled_corner_radius, fill_width // 2), 
                                           scaled_corner_radius)
                else:
                    painter.drawRect(bar_x, bar_y, fill_width, scaled_height)
        else:  # vertical
            fill_height = int(scaled_height * normalized)
            if fill_height > 0:
                fill_y = bar_y + scaled_height - fill_height
                if scaled_corner_radius > 0:
                    painter.drawRoundedRect(bar_x, fill_y, scaled_width, fill_height,
                                           scaled_corner_radius,
                                           min(scaled_corner_radius, fill_height // 2))
                else:
                    painter.drawRect(bar_x, fill_y, scaled_width, fill_height)
        
        painter.restore()
        painter.end()
        
        self.setPixmap(pixmap)
        self.setFixedSize(total_size, total_size)
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
            # Select this widget (grab focus)
            self.setFocus()
            self._is_selected = True
            self.update_display()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and self.enabled:
            new_pos = self.pos() + event.pos() - self._drag_start
            # Clamp to parent bounds, accounting for rotation padding
            if self.parent():
                parent_rect = self.parent().rect()
                widget_rect = self.rect()
                # Get padding offset to allow content to reach edges
                pad_x, pad_y = self._get_rotation_padding()
                new_pos.setX(max(-pad_x, min(new_pos.x(), parent_rect.width() - widget_rect.width() + pad_x)))
                new_pos.setY(max(-pad_y, min(new_pos.y(), parent_rect.height() - widget_rect.height() + pad_y)))
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
            # Clear global drag state
            if hasattr(self, '_drag_start_global'):
                del self._drag_start_global
            if hasattr(self, '_orig_pos'):
                del self._orig_pos
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def focusInEvent(self, event):
        """Widget gained focus - show selection"""
        self._is_selected = True
        self.update_display()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        """Widget lost focus - hide selection"""
        self._is_selected = False
        self.update_display()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for selected widget"""
        from PySide6.QtCore import Qt as QtCore
        
        key = event.key()
        modifiers = event.modifiers()
        
        # Delete or Backspace - disable widget
        if key in (QtCore.Key_Delete, QtCore.Key_Backspace):
            self.set_enabled(False)
            self.positionChanged.emit(self.pos())
            return
        
        # Arrow keys - nudge position
        nudge = 10 if modifiers & QtCore.ShiftModifier else 1
        
        new_pos = self.pos()
        if key == QtCore.Key_Left:
            new_pos.setX(new_pos.x() - nudge)
        elif key == QtCore.Key_Right:
            new_pos.setX(new_pos.x() + nudge)
        elif key == QtCore.Key_Up:
            new_pos.setY(new_pos.y() - nudge)
        elif key == QtCore.Key_Down:
            new_pos.setY(new_pos.y() + nudge)
        else:
            super().keyPressEvent(event)
            return
        
        # Clamp to parent bounds, accounting for rotation padding
        if self.parent():
            parent_rect = self.parent().rect()
            widget_rect = self.rect()
            # Get padding offset to allow content to reach edges
            pad_x, pad_y = self._get_rotation_padding()
            new_pos.setX(max(-pad_x, min(new_pos.x(), parent_rect.width() - widget_rect.width() + pad_x)))
            new_pos.setY(max(-pad_y, min(new_pos.y(), parent_rect.height() - widget_rect.height() + pad_y)))
        
        self.move(new_pos)
        self.positionChanged.emit(new_pos)

    def contextMenuEvent(self, event):
        """Show right-click context menu"""
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        # Style the menu for visibility
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
        """)
        
        if self.enabled:
            disable_action = menu.addAction("Disable")
            disable_action.triggered.connect(lambda: self.set_enabled(False))
        else:
            enable_action = menu.addAction("Enable")
            enable_action.triggered.connect(lambda: self.set_enabled(True))
        
        menu.exec(event.globalPos())

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click to open property popup"""
        if event.button() == Qt.LeftButton and self.enabled:
            self.doubleClicked.emit(self, event.globalPos())
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

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
    
    def get_rotation(self) -> int:
        return self._rotation
    
    def set_rotation(self, angle: int):
        self._rotation = angle % 360
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
    
    def get_use_gradient(self) -> bool:
        return self._use_gradient
    
    def set_use_gradient(self, use: bool):
        self._use_gradient = use
        self.update_display()
    
    def get_gradient_colors(self) -> list:
        return self._gradient_colors
    
    def set_gradient_colors(self, colors: list):
        """Set gradient colors as list of (threshold, (r, g, b, a)) tuples"""
        self._gradient_colors = colors
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
    doubleClicked = Signal(object, QPoint)  # widget, global_pos - for property popup
    
    def __init__(self, parent=None, widget_name="arc1"):
        super().__init__(parent)
        self.name = widget_name
        self.enabled = False
        self._dragging = False
        self._is_hovered = False
        self._is_selected = False  # Track selection state
        self._preview_scale = 1.0  # Scale factor for preview display
        
        # Enable mouse tracking and transparent background for drag functionality
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)  # Enable keyboard focus
        self.setCursor(Qt.OpenHandCursor)
        self._drag_start = QPoint()
        
        # Arc properties (device coordinates)
        self._metric_name = "cpu_usage"
        self._radius = 40
        self._thickness = 8
        self._start_angle = 135  # Degrees (0 = 3 o'clock, counter-clockwise)
        self._sweep_angle = 270  # Degrees
        self._rotation = 0  # Rotation angle for the entire arc (0-359)
        
        # Colors
        self._fill_color = QColor(0, 255, 0, 255)
        self._background_color = QColor(50, 50, 50, 255)
        self._border_color = QColor(255, 255, 255, 255)
        
        # Border options
        self._show_border = False
        self._border_width = 1
        
        # Gradient support
        self._use_gradient = False
        # Default gradient: green -> yellow -> red
        self._gradient_colors = [
            (0, (0, 255, 0, 255)),      # Green at 0%
            (50, (255, 255, 0, 255)),   # Yellow at 50%
            (100, (255, 0, 0, 255))     # Red at 100%
        ]
        
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

    def set_preview_scale(self, scale: float):
        """Set the preview scale factor and update display"""
        self._preview_scale = scale
        self.update_display()
    
    def _get_rotation_padding(self) -> tuple[int, int]:
        """Calculate the padding offset due to widget sizing.
        
        Returns (padding_x, padding_y) - how much extra space is on each side
        of the actual arc content within the widget.
        """
        border_padding = 4
        scaled_radius = int(round(self._radius * self._preview_scale))
        scaled_thickness = int(round(self._thickness * self._preview_scale))
        diameter = scaled_radius * 2
        arc_bounds_size = diameter + scaled_thickness
        total_size = arc_bounds_size + border_padding * 2
        # Padding on each side is half the difference between total and bounds size
        padding = int(round((total_size - arc_bounds_size) / 2.0))
        return (padding, padding)

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
        """Update the current value from cached metrics (non-blocking)"""
        if not self.enabled:
            return
        
        try:
            cache = _get_metrics_cache()
            self._current_value = cache.get_value(self._metric_name)
        except:
            pass
        
        self.update_display()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the widget"""
        self.enabled = enabled
        self.update_display()
    
    def update_display(self):
        """Update the visual display of the arc.
        
        Uses a fixed-size widget so rotation doesn't change geometry.
        """
        if not self.enabled:
            self.hide()
            return
        
        import math
        
        # Add padding for the selection border
        border_padding = 4
        
        # Apply preview scale to dimensions for display
        scaled_radius = int(self._radius * self._preview_scale)
        scaled_thickness = int(self._thickness * self._preview_scale)
        
        diameter = scaled_radius * 2
        # Fixed size - arc is already circular so no diagonal needed
        # Just use the full diameter + thickness + padding
        total_size = diameter + scaled_thickness + border_padding * 2
        
        # Create pixmap with padding for border
        pixmap = QPixmap(total_size, total_size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Arc bounds for selection border
        arc_bounds_size = diameter + scaled_thickness
        
        # Apply rotation around center - selection border rotates WITH the arc
        painter.save()
        painter.translate(total_size / 2, total_size / 2)
        painter.rotate(self._rotation)
        painter.translate(-total_size / 2, -total_size / 2)
        
        # Draw selection border (now rotates with the arc)
        arc_bounds_left = (total_size - arc_bounds_size) // 2
        arc_bounds_top = (total_size - arc_bounds_size) // 2
        
        if self._dragging:
            painter.setBrush(QColor(231, 76, 60, 50))
            pen = QPen(QColor(231, 76, 60, 255))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRect(arc_bounds_left - 2, arc_bounds_top - 2, 
                           arc_bounds_size + 4, arc_bounds_size + 4)
        elif self._is_selected:
            painter.setBrush(QColor(46, 204, 113, 40))
            pen = QPen(QColor(46, 204, 113, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(arc_bounds_left - 2, arc_bounds_top - 2,
                           arc_bounds_size + 4, arc_bounds_size + 4)
        elif self._is_hovered:
            painter.setBrush(QColor(52, 152, 219, 40))
            pen = QPen(QColor(52, 152, 219, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(arc_bounds_left - 2, arc_bounds_top - 2,
                           arc_bounds_size + 4, arc_bounds_size + 4)
        
        # Calculate center of arc within pixmap
        center_x = total_size // 2
        center_y = total_size // 2
        
        # Calculate bounding rect for arc (using scaled values)
        arc_rect_size = diameter
        arc_left = center_x - scaled_radius
        arc_top = center_y - scaled_radius
        
        # Calculate fill amount
        normalized = (self._current_value - self._min_value) / max(1, self._max_value - self._min_value)
        normalized = max(0.0, min(1.0, normalized))
        
        # Draw background arc (using scaled thickness)
        pen = QPen(self._background_color)
        pen.setWidth(scaled_thickness)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Qt uses 1/16th of a degree, and angles are counter-clockwise from 3 o'clock
        start_angle_qt = int(self._start_angle * 16)
        sweep_angle_qt = int(self._sweep_angle * 16)
        painter.drawArc(arc_left, arc_top, arc_rect_size, arc_rect_size, start_angle_qt, sweep_angle_qt)
        
        # Draw filled arc
        if normalized > 0:
            # Determine fill color (use gradient if enabled)
            if self._use_gradient and self._gradient_colors:
                fill_color = _interpolate_gradient_color(normalized, self._gradient_colors)
            else:
                fill_color = self._fill_color
            
            pen = QPen(fill_color)
            pen.setWidth(scaled_thickness)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            filled_sweep = int(self._sweep_angle * normalized)
            filled_sweep_qt = int(filled_sweep * 16)
            painter.drawArc(arc_left, arc_top, arc_rect_size, arc_rect_size, start_angle_qt, filled_sweep_qt)
        
        # Scale border width for display
        scaled_border_width = max(1, int(self._border_width * self._preview_scale))
        
        # Draw border if enabled
        if self._show_border and self._border_width > 0:
            pen = QPen(self._border_color)
            pen.setWidth(scaled_border_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            
            # Draw outer border arc (using scaled dimensions)
            outer_rect_size = diameter + scaled_thickness
            outer_left = center_x - scaled_radius - scaled_thickness // 2
            outer_top = center_y - scaled_radius - scaled_thickness // 2
            painter.drawArc(outer_left, outer_top, outer_rect_size, outer_rect_size, start_angle_qt, sweep_angle_qt)
            
            # Draw inner border arc
            inner_rect_size = diameter - scaled_thickness
            inner_left = center_x - scaled_radius + scaled_thickness // 2
            inner_top = center_y - scaled_radius + scaled_thickness // 2
            painter.drawArc(inner_left, inner_top, inner_rect_size, inner_rect_size, start_angle_qt, sweep_angle_qt)
        
        painter.restore()
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
            # Select this widget (grab focus)
            self.setFocus()
            self._is_selected = True
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
                # Get padding offset to allow content to reach edges
                pad_x, pad_y = self._get_rotation_padding()
                new_pos.setX(max(-pad_x, min(new_pos.x(), parent_rect.width() - widget_rect.width() + pad_x)))
                new_pos.setY(max(-pad_y, min(new_pos.y(), parent_rect.height() - widget_rect.height() + pad_y)))
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

    def focusInEvent(self, event):
        """Widget gained focus - show selection"""
        self._is_selected = True
        self.update_display()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        """Widget lost focus - hide selection"""
        self._is_selected = False
        self.update_display()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for selected widget"""
        from PySide6.QtCore import Qt as QtCore
        
        key = event.key()
        modifiers = event.modifiers()
        
        # Delete or Backspace - disable widget
        if key in (QtCore.Key_Delete, QtCore.Key_Backspace):
            self.set_enabled(False)
            self.positionChanged.emit(self.pos())
            return
        
        # Arrow keys - nudge position
        nudge = 10 if modifiers & QtCore.ShiftModifier else 1
        
        new_pos = self.pos()
        if key == QtCore.Key_Left:
            new_pos.setX(new_pos.x() - nudge)
        elif key == QtCore.Key_Right:
            new_pos.setX(new_pos.x() + nudge)
        elif key == QtCore.Key_Up:
            new_pos.setY(new_pos.y() - nudge)
        elif key == QtCore.Key_Down:
            new_pos.setY(new_pos.y() + nudge)
        else:
            super().keyPressEvent(event)
            return
        
        # Clamp to parent bounds, accounting for padding
        if self.parent():
            parent_rect = self.parent().rect()
            widget_rect = self.rect()
            # Get padding offset to allow content to reach edges
            pad_x, pad_y = self._get_rotation_padding()
            new_pos.setX(max(-pad_x, min(new_pos.x(), parent_rect.width() - widget_rect.width() + pad_x)))
            new_pos.setY(max(-pad_y, min(new_pos.y(), parent_rect.height() - widget_rect.height() + pad_y)))
        
        self.move(new_pos)
        self.positionChanged.emit(new_pos)

    def contextMenuEvent(self, event):
        """Show right-click context menu"""
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        # Style the menu for visibility
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
        """)
        
        if self.enabled:
            disable_action = menu.addAction("Disable")
            disable_action.triggered.connect(lambda: self.set_enabled(False))
        else:
            enable_action = menu.addAction("Enable")
            enable_action.triggered.connect(lambda: self.set_enabled(True))
        
        menu.exec(event.globalPos())

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click to open property popup"""
        if event.button() == Qt.LeftButton and self.enabled:
            self.doubleClicked.emit(self, event.globalPos())
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
    
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
        # Allow negative values for clockwise direction, clamp magnitude to 360
        self._sweep_angle = max(-360, min(360, angle))
        if self._sweep_angle == 0:
            self._sweep_angle = 1  # Avoid zero sweep
        self.update_display()
    
    def get_rotation(self) -> int:
        return self._rotation
    
    def set_rotation(self, angle: int):
        self._rotation = angle % 360
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
    
    def get_use_gradient(self) -> bool:
        return self._use_gradient
    
    def set_use_gradient(self, use: bool):
        self._use_gradient = use
        self.update_display()
    
    def get_gradient_colors(self) -> list:
        return self._gradient_colors
    
    def set_gradient_colors(self, colors: list):
        """Set gradient colors as list of (threshold, (r, g, b, a)) tuples"""
        self._gradient_colors = colors
        self.update_display()
    
    def get_position(self) -> tuple:
        """Get center position adjusted for border padding, radius, rotation, and preview scale"""
        import math
        
        border_padding = 4
        # Use scaled dimensions since pos() is in preview coordinates
        scaled_radius = int(self._radius * self._preview_scale)
        scaled_thickness = int(self._thickness * self._preview_scale)
        diameter = scaled_radius * 2
        base_size = diameter + scaled_thickness + border_padding * 2
        
        # Calculate total size accounting for rotation
        if self._rotation != 0:
            angle_rad = math.radians(self._rotation)
            cos_a = abs(math.cos(angle_rad))
            sin_a = abs(math.sin(angle_rad))
            rotated_size = int(base_size * cos_a + base_size * sin_a)
            total_size = max(base_size, rotated_size)
        else:
            total_size = base_size
        
        pos = self.pos()
        # Return the center of the widget (in preview coordinates)
        center_x = pos.x() + total_size // 2
        center_y = pos.y() + total_size // 2
        return (center_x, center_y)


class ShapeWidget(DraggableWidget):
    """Draggable decorative shape widget for borders, separators, backgrounds"""
    
    positionChanged = Signal(QPoint)
    doubleClicked = Signal(object, QPoint)  # widget, global_pos - for property popup
    
    # Shape type constants (matching ShapeType enum values)
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    LINE = "line"
    TRIANGLE = "triangle"
    ARROW = "arrow"
    ROUNDED_RECTANGLE = "rounded_rectangle"
    
    def __init__(self, parent=None, widget_name="shape1"):
        super().__init__(parent)
        self.name = widget_name
        self.enabled = False
        self._dragging = False
        self._is_hovered = False
        self._is_selected = False
        self._preview_scale = 1.0
        
        # Enable mouse tracking and transparent background
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.OpenHandCursor)
        self._drag_start = QPoint()
        
        # Shape properties (device coordinates)
        self._shape_type = self.RECTANGLE
        self._width = 80
        self._height = 50
        self._rotation = 0
        
        # Fill settings
        self._filled = True
        self._fill_color = QColor(100, 100, 100, 128)  # Semi-transparent gray
        
        # Border settings
        self._border_color = QColor(255, 255, 255, 255)  # White
        self._border_width = 2
        
        # Shape-specific settings
        self._corner_radius = 0  # For rounded rectangle
        self._arrow_head_size = 10  # For arrow
        
        self._set_initial_position()
        self.update_display()
    
    def set_preview_scale(self, scale: float):
        """Set the preview scale factor and update display"""
        self._preview_scale = scale
        self.update_display()
    
    def _get_rotation_padding(self) -> tuple[int, int]:
        """Calculate padding offset due to diagonal-based sizing"""
        border_padding = 4
        scaled_width = int(round(self._width * self._preview_scale))
        scaled_height = int(round(self._height * self._preview_scale))
        # Use ceil for diagonal so the GUI matches the generator's allocation
        diagonal = int(math.ceil(math.sqrt(scaled_width**2 + scaled_height**2)))
        total_size = diagonal + border_padding * 2
        # Use rounding to distribute padding symmetrically (avoid 1px drift)
        padding_x = int(round((total_size - scaled_width) / 2.0))
        padding_y = int(round((total_size - scaled_height) / 2.0))
        return (padding_x, padding_y)
    
    def _set_initial_position(self):
        """Set initial position based on widget name"""
        border_padding = 4
        positions = {
            "shape1": (20, 20),
            "shape2": (120, 20),
            "shape3": (20, 100),
            "shape4": (120, 100)
        }
        if self.name in positions:
            x, y = positions[self.name]
            self.move(x - border_padding, y - border_padding)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the widget"""
        self.enabled = enabled
        self.update_display()
    
    def update_display(self):
        """Update the visual display of the shape"""
        if not self.enabled:
            self.hide()
            return
        
        border_padding = 4
        # Use rounded scaled sizes to avoid truncation drift
        scaled_width = int(round(self._width * self._preview_scale))
        scaled_height = int(round(self._height * self._preview_scale))

        # Use diagonal-based size so rotation fits within and match generator (ceil)
        diagonal = int(math.ceil(math.sqrt(scaled_width**2 + scaled_height**2)))
        total_size = diagonal + border_padding * 2
        
        # Create pixmap
        pixmap = QPixmap(total_size, total_size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Apply rotation
        painter.save()
        painter.translate(total_size / 2, total_size / 2)
        painter.rotate(self._rotation)
        painter.translate(-scaled_width / 2, -scaled_height / 2)
        
        # Draw selection border
        if self._dragging:
            painter.setBrush(QColor(231, 76, 60, 50))
            pen = QPen(QColor(231, 76, 60, 255))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRect(-2, -2, scaled_width + 4, scaled_height + 4)
        elif self._is_selected:
            painter.setBrush(QColor(46, 204, 113, 40))
            pen = QPen(QColor(46, 204, 113, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(-2, -2, scaled_width + 4, scaled_height + 4)
        elif self._is_hovered:
            painter.setBrush(QColor(52, 152, 219, 40))
            pen = QPen(QColor(52, 152, 219, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(-2, -2, scaled_width + 4, scaled_height + 4)
        
        # Draw the shape at origin
        self._draw_shape(painter, 0, 0, scaled_width, scaled_height)
        
        painter.restore()
        painter.end()
        
        self.setPixmap(pixmap)
        self.setFixedSize(total_size, total_size)
        self.show()
    
    def _draw_shape(self, painter: QPainter, x: int, y: int, w: int, h: int):
        """Draw the shape based on type"""
        # Set fill
        if self._filled:
            painter.setBrush(self._fill_color)
        else:
            painter.setBrush(Qt.NoBrush)
        
        # Set border
        if self._border_width > 0:
            pen = QPen(self._border_color)
            pen.setWidth(max(1, int(self._border_width * self._preview_scale)))
            painter.setPen(pen)
        else:
            painter.setPen(Qt.NoPen)
        
        scaled_corner_radius = int(self._corner_radius * self._preview_scale)
        scaled_arrow_head = int(self._arrow_head_size * self._preview_scale)
        
        if self._shape_type == self.RECTANGLE:
            painter.drawRect(x, y, w, h)
        
        elif self._shape_type == self.ROUNDED_RECTANGLE:
            radius = min(scaled_corner_radius, w // 2, h // 2)
            painter.drawRoundedRect(x, y, w, h, radius, radius)
        
        elif self._shape_type == self.CIRCLE:
            # Circle uses width as diameter, centered
            diameter = min(w, h)
            cx = x + w // 2
            cy = y + h // 2
            r = diameter // 2
            painter.drawEllipse(cx - r, cy - r, diameter, diameter)
        
        elif self._shape_type == self.ELLIPSE:
            painter.drawEllipse(x, y, w, h)
        
        elif self._shape_type == self.LINE:
            # Treat line as a thin rectangle to match device rendering
            # Draw filled line rectangle or border-only rectangle based on settings
            if self._filled:
                # Use fill color to draw rectangle
                painter.setBrush(self._fill_color)
                pen = QPen(self._border_color if self._border_width > 0 else Qt.NoPen)
                if self._border_width > 0:
                    pen.setWidth(max(1, int(self._border_width * self._preview_scale)))
                painter.setPen(pen)
                painter.drawRect(x, y, w, h)
            else:
                # Border-only: draw rectangle outline using border_color/width
                if self._border_width > 0:
                    pen = QPen(self._border_color)
                    pen.setWidth(max(1, int(self._border_width * self._preview_scale)))
                    painter.setPen(pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawRect(x, y, w, h)
        
        elif self._shape_type == self.TRIANGLE:
            # Isoceles triangle pointing up
            from PySide6.QtGui import QPolygon
            points = QPolygon([
                QPoint(x + w // 2, y),      # Top center
                QPoint(x, y + h),            # Bottom left
                QPoint(x + w, y + h)         # Bottom right
            ])
            painter.drawPolygon(points)
        
        elif self._shape_type == self.ARROW:
            # Arrow pointing right
            line_color = self._border_color if self._border_width > 0 else self._fill_color
            pen = QPen(line_color)
            pen.setWidth(max(1, int(self._border_width * self._preview_scale)) if self._border_width > 0 else 2)
            painter.setPen(pen)
            
            y_center = y + h // 2
            arrow_body_end = x + w - scaled_arrow_head
            
            # Main line
            painter.drawLine(x, y_center, arrow_body_end, y_center)
            
            # Arrowhead
            from PySide6.QtGui import QPolygon
            arrow_points = QPolygon([
                QPoint(x + w, y_center),                         # Tip
                QPoint(arrow_body_end, y_center - scaled_arrow_head // 2),  # Top
                QPoint(arrow_body_end, y_center + scaled_arrow_head // 2)   # Bottom
            ])
            painter.setBrush(line_color)
            painter.drawPolygon(arrow_points)
    
    # Mouse event handlers
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
            # Use global-delta drag to make moving shapes intuitive when rotated.
            # Call base to set dragging state and emit dragStarted
            super().mousePressEvent(event)
            # Also keep local dragging state for visual selection
            self._dragging = True
            self._drag_start = event.pos()
            self._drag_start_global = event.globalPos()
            self._orig_pos = self.pos()
            self._is_selected = True
            self.update_display()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and self.enabled:
            delta = event.globalPos() - getattr(self, '_drag_start_global', event.globalPos())
            orig = getattr(self, '_orig_pos', self.pos())
            new_pos = QPoint(orig.x() + delta.x(), orig.y() + delta.y())
            if self.parent():
                parent_rect = self.parent().rect()
                widget_rect = self.rect()
                pad_x, pad_y = self._get_rotation_padding()
                new_pos.setX(max(-pad_x, min(new_pos.x(), parent_rect.width() - widget_rect.width() + pad_x)))
                new_pos.setY(max(-pad_y, min(new_pos.y(), parent_rect.height() - widget_rect.height() + pad_y)))
            self.move(new_pos)
            self.positionChanged.emit(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # Clear local dragging state and notify base class (which emits dragEnded)
            self._dragging = False
            super().mouseReleaseEvent(event)
            # Ensure cursor and visuals are consistent
            self.setCursor(Qt.OpenHandCursor)
            self.update_display()
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def focusInEvent(self, event):
        self._is_selected = True
        self.update_display()
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        self._is_selected = False
        self.update_display()
        super().focusOutEvent(event)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        from PySide6.QtCore import Qt as QtCore
        
        key = event.key()
        modifiers = event.modifiers()
        
        if key in (QtCore.Key_Delete, QtCore.Key_Backspace):
            self.set_enabled(False)
            self.positionChanged.emit(self.pos())
            return
        
        nudge = 10 if modifiers & QtCore.ShiftModifier else 1
        new_pos = self.pos()
        
        if key == QtCore.Key_Left:
            new_pos.setX(new_pos.x() - nudge)
        elif key == QtCore.Key_Right:
            new_pos.setX(new_pos.x() + nudge)
        elif key == QtCore.Key_Up:
            new_pos.setY(new_pos.y() - nudge)
        elif key == QtCore.Key_Down:
            new_pos.setY(new_pos.y() + nudge)
        else:
            super().keyPressEvent(event)
            return
        
        if self.parent():
            parent_rect = self.parent().rect()
            widget_rect = self.rect()
            pad_x, pad_y = self._get_rotation_padding()
            new_pos.setX(max(-pad_x, min(new_pos.x(), parent_rect.width() - widget_rect.width() + pad_x)))
            new_pos.setY(max(-pad_y, min(new_pos.y(), parent_rect.height() - widget_rect.height() + pad_y)))
        
        self.move(new_pos)
        self.positionChanged.emit(new_pos)
    
    def contextMenuEvent(self, event):
        """Show right-click context menu"""
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #3498db; }
        """)
        
        if self.enabled:
            disable_action = menu.addAction("Disable")
            disable_action.triggered.connect(lambda: self.set_enabled(False))
        else:
            enable_action = menu.addAction("Enable")
            enable_action.triggered.connect(lambda: self.set_enabled(True))
        
        menu.exec(event.globalPos())
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.enabled:
            self.doubleClicked.emit(self, event.globalPos())
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
    
    # Getters and setters
    def get_shape_type(self) -> str:
        return self._shape_type
    
    def set_shape_type(self, shape_type: str):
        self._shape_type = shape_type
        self.update_display()
    
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
    
    def get_rotation(self) -> int:
        return self._rotation
    
    def set_rotation(self, angle: int):
        self._rotation = angle % 360
        self.update_display()
    
    def get_filled(self) -> bool:
        return self._filled
    
    def set_filled(self, filled: bool):
        self._filled = filled
        self.update_display()
    
    def get_fill_color(self) -> QColor:
        return self._fill_color
    
    def set_fill_color(self, color: QColor):
        self._fill_color = color
        self.update_display()
    
    def get_border_color(self) -> QColor:
        return self._border_color
    
    def set_border_color(self, color: QColor):
        self._border_color = color
        self.update_display()
    
    def get_border_width(self) -> int:
        return self._border_width
    
    def set_border_width(self, width: int):
        self._border_width = max(0, width)
        self.update_display()
    
    def get_corner_radius(self) -> int:
        return self._corner_radius
    
    def set_corner_radius(self, radius: int):
        self._corner_radius = max(0, radius)
        self.update_display()
    
    def get_arrow_head_size(self) -> int:
        return self._arrow_head_size
    
    def set_arrow_head_size(self, size: int):
        self._arrow_head_size = max(5, size)
        self.update_display()
    
    def get_position(self) -> tuple:
        """Get position adjusted for border padding"""
        border_padding = 4
        pos = self.pos()
        return (pos.x() + border_padding, pos.y() + border_padding)


class ShapePropertyPopup(PropertyPopup):
    """Property popup for ShapeWidget - allows quick editing of shape properties."""
    
    SHAPE_OPTIONS = [
        ("Rectangle", "rectangle"),
        ("Circle", "circle"),
        ("Ellipse", "ellipse"),
        ("Line", "line"),
        ("Triangle", "triangle"),
        ("Arrow", "arrow"),
        ("Rounded Rect", "rounded_rectangle"),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the popup UI"""
        from PySide6.QtWidgets import (QVBoxLayout, QFormLayout, QHBoxLayout, 
                                        QComboBox, QSpinBox, QCheckBox, QPushButton,
                                        QLabel, QWidget, QColorDialog)
        
        container = QWidget()
        container.setObjectName("popupContainer")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)
        
        # Title bar
        layout.addLayout(self._create_title_bar("Shape Properties"))
        
        # Form layout for properties
        form = QFormLayout()
        form.setSpacing(6)
        form.setLabelAlignment(Qt.AlignRight)
        
        # Shape type selector
        self._shape_combo = QComboBox()
        for display_name, value in self.SHAPE_OPTIONS:
            self._shape_combo.addItem(display_name, value)
        self._shape_combo.currentIndexChanged.connect(self._on_shape_changed)
        form.addRow("Shape:", self._shape_combo)
        
        # Size controls
        size_layout = QHBoxLayout()
        size_layout.setSpacing(4)
        
        self._width_spin = QSpinBox()
        self._width_spin.setRange(5, 500)
        self._width_spin.setSuffix(" px")
        self._width_spin.valueChanged.connect(self._on_width_changed)
        
        self._height_spin = QSpinBox()
        self._height_spin.setRange(5, 500)
        self._height_spin.setSuffix(" px")
        self._height_spin.valueChanged.connect(self._on_height_changed)
        
        size_layout.addWidget(QLabel("W:"))
        size_layout.addWidget(self._width_spin)
        size_layout.addWidget(QLabel("H:"))
        size_layout.addWidget(self._height_spin)
        form.addRow("Size:", size_layout)
        
        # Rotation
        self._rotation_spin = QSpinBox()
        self._rotation_spin.setRange(0, 359)
        self._rotation_spin.setSuffix("°")
        self._rotation_spin.valueChanged.connect(self._on_rotation_changed)
        form.addRow("Rotation:", self._rotation_spin)
        
        # Fill color with filled checkbox
        fill_layout = QHBoxLayout()
        fill_layout.setSpacing(4)
        
        self._fill_color_btn = QPushButton()
        self._fill_color_btn.setObjectName("colorButton")
        self._fill_color_btn.setFixedSize(32, 20)
        self._fill_color_btn.clicked.connect(self._on_fill_color_clicked)
        
        self._filled_check = QCheckBox("Filled")
        self._filled_check.stateChanged.connect(self._on_filled_changed)
        
        fill_layout.addWidget(self._fill_color_btn)
        fill_layout.addWidget(self._filled_check)
        fill_layout.addStretch()
        form.addRow("Fill:", fill_layout)
        
        # Border color and width
        border_layout = QHBoxLayout()
        border_layout.setSpacing(4)
        
        self._border_color_btn = QPushButton()
        self._border_color_btn.setObjectName("colorButton")
        self._border_color_btn.setFixedSize(32, 20)
        self._border_color_btn.clicked.connect(self._on_border_color_clicked)
        
        self._border_width_spin = QSpinBox()
        self._border_width_spin.setRange(0, 20)
        self._border_width_spin.setSuffix(" px")
        self._border_width_spin.valueChanged.connect(self._on_border_width_changed)
        
        border_layout.addWidget(self._border_color_btn)
        border_layout.addWidget(QLabel("Width:"))
        border_layout.addWidget(self._border_width_spin)
        border_layout.addStretch()
        form.addRow("Border:", border_layout)
        
        # Corner radius (for rounded rectangle)
        self._corner_radius_label = QLabel("Radius:")
        self._corner_radius_spin = QSpinBox()
        self._corner_radius_spin.setRange(0, 100)
        self._corner_radius_spin.setSuffix(" px")
        self._corner_radius_spin.valueChanged.connect(self._on_corner_radius_changed)
        form.addRow(self._corner_radius_label, self._corner_radius_spin)
        
        # Arrow head size (for arrow)
        self._arrow_size_label = QLabel("Head Size:")
        self._arrow_size_spin = QSpinBox()
        self._arrow_size_spin.setRange(5, 50)
        self._arrow_size_spin.setSuffix(" px")
        self._arrow_size_spin.valueChanged.connect(self._on_arrow_size_changed)
        form.addRow(self._arrow_size_label, self._arrow_size_spin)
        
        layout.addLayout(form)
        
        self.setFixedWidth(260)
    
    def _populate_fields(self):
        """Populate fields from target ShapeWidget"""
        if not self._target:
            return
        
        # Block signals during population
        self._shape_combo.blockSignals(True)
        self._width_spin.blockSignals(True)
        self._height_spin.blockSignals(True)
        self._rotation_spin.blockSignals(True)
        self._filled_check.blockSignals(True)
        self._border_width_spin.blockSignals(True)
        self._corner_radius_spin.blockSignals(True)
        self._arrow_size_spin.blockSignals(True)
        
        # Set values
        shape_type = self._target.get_shape_type()
        index = self._shape_combo.findData(shape_type)
        if index >= 0:
            self._shape_combo.setCurrentIndex(index)
        
        self._width_spin.setValue(self._target.get_width())
        self._height_spin.setValue(self._target.get_height())
        self._rotation_spin.setValue(self._target.get_rotation())
        self._filled_check.setChecked(self._target.get_filled())
        self._border_width_spin.setValue(self._target.get_border_width())
        self._corner_radius_spin.setValue(self._target.get_corner_radius())
        self._arrow_size_spin.setValue(self._target.get_arrow_head_size())
        
        # Update color buttons
        fill_color = self._target.get_fill_color()
        self._fill_color_btn.setStyleSheet(
            f"background-color: {fill_color.name()}; border: 1px solid #555;"
        )
        
        border_color = self._target.get_border_color()
        self._border_color_btn.setStyleSheet(
            f"background-color: {border_color.name()}; border: 1px solid #555;"
        )
        
        # Unblock signals
        self._shape_combo.blockSignals(False)
        self._width_spin.blockSignals(False)
        self._height_spin.blockSignals(False)
        self._rotation_spin.blockSignals(False)
        self._filled_check.blockSignals(False)
        self._border_width_spin.blockSignals(False)
        self._corner_radius_spin.blockSignals(False)
        self._arrow_size_spin.blockSignals(False)
        
        # Update visibility of conditional controls
        self._update_conditional_controls()
    
    def _update_conditional_controls(self):
        """Show/hide controls based on shape type"""
        shape_type = self._shape_combo.currentData()
        
        # Corner radius only for rounded rectangle
        is_rounded = shape_type == "rounded_rectangle"
        self._corner_radius_label.setVisible(is_rounded)
        self._corner_radius_spin.setVisible(is_rounded)
        
        # Arrow head size only for arrow
        is_arrow = shape_type == "arrow"
        self._arrow_size_label.setVisible(is_arrow)
        self._arrow_size_spin.setVisible(is_arrow)
        
        self.adjustSize()
    
    def _on_shape_changed(self, index):
        if self._target:
            shape_type = self._shape_combo.currentData()
            self._target.set_shape_type(shape_type)
            # If switching to a line, default to a thin height for clarity
            if shape_type == 'line':
                self._target.set_height(6)
            self.propertyChanged.emit(self._target, "shape_type", shape_type)
            self._update_conditional_controls()
    
    def _on_width_changed(self, value):
        if self._target:
            self._target.set_width(value)
            self.propertyChanged.emit(self._target, "width", value)
    
    def _on_height_changed(self, value):
        if self._target:
            self._target.set_height(value)
            self.propertyChanged.emit(self._target, "height", value)
    
    def _on_rotation_changed(self, value):
        if self._target:
            self._target.set_rotation(value)
            self.propertyChanged.emit(self._target, "rotation", value)
    
    def _on_filled_changed(self, state):
        if self._target:
            filled = state == Qt.Checked
            self._target.set_filled(filled)
            self.propertyChanged.emit(self._target, "filled", filled)
    
    def _on_border_width_changed(self, value):
        if self._target:
            self._target.set_border_width(value)
            self.propertyChanged.emit(self._target, "border_width", value)
    
    def _on_corner_radius_changed(self, value):
        if self._target:
            self._target.set_corner_radius(value)
            self.propertyChanged.emit(self._target, "corner_radius", value)
    
    def _on_arrow_size_changed(self, value):
        if self._target:
            self._target.set_arrow_head_size(value)
            self.propertyChanged.emit(self._target, "arrow_head_size", value)
    
    def _on_fill_color_clicked(self):
        if not self._target:
            return
        
        from PySide6.QtWidgets import QColorDialog
        self._color_dialog_open = True
        current_color = self._target.get_fill_color()
        color = QColorDialog.getColor(current_color, self, "Select Fill Color")
        self._color_dialog_open = False
        
        if color.isValid():
            self._target.set_fill_color(color)
            self._fill_color_btn.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #555;"
            )
            self.propertyChanged.emit(self._target, "fill_color", color)
    
    def _on_border_color_clicked(self):
        if not self._target:
            return
        
        from PySide6.QtWidgets import QColorDialog
        self._color_dialog_open = True
        current_color = self._target.get_border_color()
        color = QColorDialog.getColor(current_color, self, "Select Border Color")
        self._color_dialog_open = False
        
        if color.isValid():
            self._target.set_border_color(color)
            self._border_color_btn.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #555;"
            )
            self.propertyChanged.emit(self._target, "border_color", color)
