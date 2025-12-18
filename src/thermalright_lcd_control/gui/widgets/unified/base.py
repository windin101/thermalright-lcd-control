"""
Unified Widget System - Base Classes

This module contains the foundation classes for the new unified widget system.
All widgets inherit from UnifiedBaseItem and are managed by UnifiedGraphicsView.
"""
from PySide6.QtCore import QObject,  Qt, QRectF, QPointF, Signal, Property
from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem, QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class UnifiedBaseItem(QGraphicsObject):
    """
    Base class for all unified widgets.
    
    Provides common functionality:
    - Position and size management
    - Selection state
    - Mouse event handling
    - Preview scale support
    - Property interface
    """
    
    # Signals
    positionChanged = Signal(QPointF)  # Emitted when widget moves
    selectionChanged = Signal(bool)    # Emitted when selected/deselected
    propertiesChanged = Signal(dict)   # Emitted when properties change
    doubleClicked = Signal()           # Emitted on double-click
    deleteRequested = Signal(str)  # Emitted when widget requests deletion
    propertiesRequested = Signal(object)  # Emitted when widget requests property editor (emits self)
    
    # Layer constants for z-ordering
    BACKGROUND_LAYER = 0
    SHAPE_LAYER = 100
    TEXT_LAYER = 200
    GRAPH_LAYER = 300
    SELECTION_LAYER = 1000  # Selection border on top
    
    def __init__(self, widget_name: str, widget_type: str, 
                 x: float, y: float, width: float, height: float,
                 preview_scale: float = 1.0):
        """
        Initialize base widget.
        
        Args:
            widget_name: Unique identifier for this widget
            widget_type: Type of widget (date, time, rectangle, etc.)
            x, y: Position in scene coordinates
            width, height: Size in scene coordinates
            preview_scale: Scale factor for preview mode
        """
        super().__init__()
        
        # Basic properties
        self._widget_name = widget_name
        self._widget_type = widget_type
        self._preview_scale = preview_scale
        
        # Position and size (in scene coordinates)
        self.setPos(x, y)
        self._width = width
        self._height = height
        
        # State
        self._enabled = True
        self._visible = True
        self._selected = False
        self._dragging = False
        
        # Visual properties
        self._selection_border_color = QColor(255, 0, 0, 255)  # RED for debugging
        self._selection_border_width = 3  # Thicker for debugging
        self._selection_padding = 6  # More padding for debugging
        
        # Resize state
        self._resizing = False
        self._resize_edge = None  # 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw'
        self._resize_start_pos = None
        self._resize_start_size = None
        self._resize_start_mouse_pos = None
        self._resize_handle_size = 8  # Size of resize handles in pixels
        
        # Enable mouse tracking
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)  # We handle dragging manually
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Set z-value based on layer (override in subclasses)
        self.setZValue(self._get_layer())
        
        logger.debug(f"Created {widget_type} widget '{widget_name}' at ({x}, {y})")
    
    def _get_layer(self) -> int:
        """Get z-order layer for this widget type. Override in subclasses."""
        return self.TEXT_LAYER  # Default to text layer
    
    # ==================== Core Properties ====================
    
    @Property(str)
    def widget_name(self) -> str:
        """Get widget name (unique identifier)."""
        return self._widget_name
    
    @Property(str)
    def widget_type(self) -> str:
        """Get widget type (date, time, rectangle, etc.)."""
        return self._widget_type
    
    @Property(bool)
    def enabled(self) -> bool:
        """Get enabled state."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        """Set enabled state."""
        if self._enabled != value:
            self._enabled = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(bool)
    def visible(self) -> bool:
        """Get visible state."""
        return self._visible
    
    @visible.setter
    def visible(self, value: bool):
        """Set visible state."""
        if self._visible != value:
            self._visible = value
            self.setVisible(value)
            self.propertiesChanged.emit(self.get_properties())
    
    @Property(float)
    def preview_scale(self) -> float:
        """Get preview scale factor."""
        return self._preview_scale
    
    @preview_scale.setter
    def preview_scale(self, value: float):
        """Set preview scale factor."""
        if self._preview_scale != value:
            self._preview_scale = value
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    # ==================== Geometry ====================
    
    def boundingRect(self) -> QRectF:
        """
        Return bounding rectangle in local coordinates.
        
        Includes extra padding for selection border.
        """
        padding = self._selection_padding
        return QRectF(-padding, -padding,
                     self._width + padding * 2,
                     self._height + padding * 2)
    
    def get_size(self) -> Tuple[float, float]:
        """Get widget size (width, height)."""
        return (self._width, self._height)
    
    def set_size(self, width: float, height: float):
        """Set widget size."""
        if self._width != width or self._height != height:
            self._width = width
            self._height = height
            self.prepareGeometryChange()
            self.update()
            self.propertiesChanged.emit(self.get_properties())
    
    # ==================== Selection ====================
    
    @Property(bool)
    def selected(self) -> bool:
        """Get selection state."""
        return self._selected
    
    @selected.setter
    def selected(self, value: bool):
        """Set selection state."""
        if self._selected != value:
            self._selected = value
            self.setSelected(value)
            self.update()  # Redraw to show/hide selection border
            self.selectionChanged.emit(value)
            
            # If selecting this widget, ensure it's the only selected widget
            if value and self.scene():
                # Clear selection from all other items in scene
                for item in self.scene().items():
                    if item != self and isinstance(item, UnifiedBaseItem):
                        item.selected = False
    
    def itemChange(self, change, value):
        """Handle item changes (e.g., position changes, selection)."""
        if change == QGraphicsItem.ItemSelectedChange:
            # QGraphicsView is changing our selection state
            # Update our _selected property to match
            self._selected = value
            self.selectionChanged.emit(value)
            return value
        elif change == QGraphicsItem.ItemPositionChange:
            # Store the new position
            new_pos = value
            # You could add constraints here if needed
            return new_pos
        elif change == QGraphicsItem.ItemPositionHasChanged:
            # Position has changed, emit signal
            self.positionChanged.emit(self.pos())
        
        return super().itemChange(change, value)
    
    def _draw_selection_border(self, painter: QPainter):
        """Draw selection border around widget."""
        if not self._selected:
            return
        
        painter.save()
        
        # Set pen for selection border
        pen = QPen(self._selection_border_color)
        pen.setWidth(self._selection_border_width)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw border with padding
        padding = self._selection_padding
        painter.drawRect(-padding, -padding,
                        self._width + padding * 2,
                        self._height + padding * 2)
        
        # Draw resize handles
        if self._selected:
            handle_size = self._resize_handle_size
            half_handle = handle_size / 2
            
            # Fill color for handles
            painter.setBrush(QBrush(self._selection_border_color))
            painter.setPen(Qt.NoPen)
            
            # Define handle positions (relative to widget with padding)
            left = -padding
            right = self._width + padding
            top = -padding
            bottom = self._height + padding
            
            # Corner handles
            handles = [
                (left - half_handle, top - half_handle, handle_size, handle_size),  # NW
                (right - half_handle, top - half_handle, handle_size, handle_size),  # NE
                (right - half_handle, bottom - half_handle, handle_size, handle_size),  # SE
                (left - half_handle, bottom - half_handle, handle_size, handle_size),  # SW
            ]
            
            # Edge handles (centered on edges)
            handles.extend([
                (left - half_handle, (top + bottom) / 2 - half_handle, handle_size, handle_size),  # W
                (right - half_handle, (top + bottom) / 2 - half_handle, handle_size, handle_size),  # E
                ((left + right) / 2 - half_handle, top - half_handle, handle_size, handle_size),  # N
                ((left + right) / 2 - half_handle, bottom - half_handle, handle_size, handle_size),  # S
            ])
            
            # Draw all handles
            for x, y, w, h in handles:
                painter.drawRect(x, y, w, h)
        
        painter.restore()
    
    # ==================== Painting ====================
    
    def paint(self, painter: QPainter, option, widget=None):
        """
        Paint the widget. Called by QGraphicsView.
        
        Subclasses should override _draw_widget() for custom drawing.
        """
        logger.debug(f"Painting widget '{self._widget_name}' at ({self.x()}, {self.y()})")
        
        # Apply any transformations needed
        self._apply_painter_transforms(painter)
        
        # Let subclass draw the actual widget
        self._draw_widget(painter, 0, 0, self._width, self._height)
        
        # Draw selection border (on top)
        self._draw_selection_border(painter)
    
    def _apply_painter_transforms(self, painter: QPainter):
        """Apply any transformations to the painter. Override if needed."""
        pass
    
    def _draw_widget(self, painter: QPainter, x: float, y: float, 
                    width: float, height: float):
        """
        Draw the widget content. MUST be implemented by subclasses.
        
        Args:
            painter: QPainter to use for drawing
            x, y: Local coordinates (usually 0, 0)
            width, height: Widget size in local coordinates
        """
        raise NotImplementedError("Subclasses must implement _draw_widget()")
    
    # ==================== Property System ====================
    
    def get_properties(self) -> Dict[str, Any]:
        """
        Get all widget properties as a dictionary.
        
        Subclasses should extend this to add their own properties.
        """
        return {
            'widget_name': self._widget_name,
            'widget_type': self._widget_type,
            'x': self.x(),
            'y': self.y(),
            'width': self._width,
            'height': self._height,
            'enabled': self._enabled,
            'visible': self._visible,
            'preview_scale': self._preview_scale,
            'selected': self._selected,
        }
    
    def set_properties(self, properties: Dict[str, Any]):
        """
        Set widget properties from dictionary.
        
        Subclasses should extend this to handle their own properties.
        """
        # Update position
        if 'x' in properties or 'y' in properties:
            x = properties.get('x', self.x())
            y = properties.get('y', self.y())
            self.setPos(x, y)
        
        # Update size
        if 'width' in properties or 'height' in properties:
            width = properties.get('width', self._width)
            height = properties.get('height', self._height)
            self.set_size(width, height)
        
        # Update other properties
        if 'enabled' in properties:
            self.enabled = properties['enabled']
        if 'visible' in properties:
            self.visible = properties['visible']
        if 'preview_scale' in properties:
            self.preview_scale = properties['preview_scale']
        if 'selected' in properties:
            self.selected = properties['selected']
        
        # Trigger redraw
        self.update()
    
    # ==================== Serialization ====================
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize widget to dictionary for saving.
        
        Similar to get_properties() but may include additional data.
        """
        return self.get_properties()
    
    def deserialize(self, data: Dict[str, Any]):
        """
        Deserialize widget from dictionary (loading).
        
        Similar to set_properties() but may handle additional data.
        """
        self.set_properties(data)
    
    # ==================== Event Handling ====================
    
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton:
            # Check if clicking on resize edge
            if self._selected:
                edge = self._get_resize_edge(event.pos())
                if edge:
                    # Start resizing
                    self._resizing = True
                    self._resize_edge = edge
                    self._resize_start_size = (self._width, self._height)
                    self._resize_start_pos = (self.x(), self.y())
                    self._resize_start_mouse_pos = event.scenePos()
                    
                    # Disable dragging while resizing
                    self._dragging = False
                    self.setFlag(QGraphicsItem.ItemIsMovable, False)
                    self.grabMouse()
                    event.accept()
                    return
            
            # Otherwise start dragging
            self._dragging = True
            self.setCursor(Qt.ClosedHandCursor)
            
            # Store initial mouse position (in scene coordinates)
            self._last_mouse_pos = event.scenePos()
            
            # Select this widget
            if not self._selected:
                self.selected = True
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move event."""
        if self._resizing and self._resize_edge:
            # Handle resize
            current_pos = event.scenePos()
            
            dx = current_pos.x() - self._resize_start_mouse_pos.x()
            dy = current_pos.y() - self._resize_start_mouse_pos.y()
            
            start_width, start_height = self._resize_start_size
            start_x, start_y = self._resize_start_pos
            
            new_width = start_width
            new_height = start_height
            new_x = start_x
            new_y = start_y
            
            edge = self._resize_edge
            
            # Apply resize based on edge
            if 'e' in edge:  # Right edge
                new_width = max(10, start_width + dx)
            if 'w' in edge:  # Left edge
                new_width = max(10, start_width - dx)
                new_x = start_x + dx
            
            if 's' in edge:  # Bottom edge
                new_height = max(10, start_height + dy)
            if 'n' in edge:  # Top edge
                new_height = max(10, start_height - dy)
                new_y = start_y + dy
            
            # Constrain to scene boundaries
            if self.scene():
                scene_rect = self.scene().sceneRect()
                new_x = max(scene_rect.left(), min(new_x, scene_rect.right() - new_width))
                new_y = max(scene_rect.top(), min(new_y, scene_rect.bottom() - new_height))
            
            # Update widget
            self.set_size(new_width, new_height)
            self.setPos(new_x, new_y)
            self.update()
            
            event.accept()
            
        elif self._dragging:
            # Get current mouse position
            current_pos = event.scenePos()
            
            # Calculate how much mouse moved
            delta = current_pos - self._last_mouse_pos
            
            # Calculate new position
            new_pos = self.pos() + delta
            
            # Constrain to scene boundaries if scene exists
            if self.scene():
                scene_rect = self.scene().sceneRect()
                # Keep widget within scene bounds
                new_x = max(scene_rect.left(), min(new_pos.x(), scene_rect.right() - self._width))
                new_y = max(scene_rect.top(), min(new_pos.y(), scene_rect.bottom() - self._height))
                new_pos = QPointF(new_x, new_y)
            
            # Move widget to constrained position
            self.setPos(new_pos)
            
            # Update last mouse position
            self._last_mouse_pos = current_pos
            
            # Update cursor during drag
            self.setCursor(Qt.ClosedHandCursor)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.LeftButton:
            if self._resizing:
                # Finish resizing
                self._resizing = False
                self._resize_edge = None
                self._resize_start_size = None
                self._resize_start_pos = None
                self._resize_start_mouse_pos = None
                
                # Restore mouse capture
                self.ungrabMouse()
                self.setFlag(QGraphicsItem.ItemIsMovable, True)
                
                # Update cursor
                self.setCursor(Qt.ArrowCursor)
                
                # Emit signals
                self.positionChanged.emit(self.pos())
                self.propertiesChanged.emit(self.get_properties())
                
                event.accept()
            
            elif self._dragging:
                self._dragging = False
                self.setCursor(Qt.ArrowCursor)
                # Emit position changed signal
                self.positionChanged.emit(self.pos())
        
        super().mouseReleaseEvent(event)
    
    def contextMenuEvent(self, event):
        """Handle right-click to show context menu."""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        # Create context menu
        menu = QMenu()
        
        # Add actions
        delete_action = QAction("Delete", menu)
        delete_action.triggered.connect(self._delete_widget)
        menu.addAction(delete_action)
        
        properties_action = QAction("Properties...", menu)
        properties_action.triggered.connect(self._show_properties)
        menu.addAction(properties_action)
        
        menu.addSeparator()
        
        deselect_action = QAction("Deselect All", menu)
        deselect_action.triggered.connect(self._deselect_all)
        menu.addAction(deselect_action)
        
        # Show menu at cursor position
        menu.exec(event.screenPos())
        
        # Accept the event
        event.accept()

    def _delete_widget(self):
        """Delete this widget."""
        print(f"[CONTEXT MENU] Delete {self._widget_name}")
        # Emit signal to notify view to delete this widget
        self.deleteRequested.emit(self._widget_name)

    def _show_properties(self):
        """Show widget properties dialog."""
        logger.debug(f"Requesting property editor for {self._widget_name}")
        # Emit signal to request property editor
        self.propertiesRequested.emit(self)
    def _deselect_all(self):
        """Deselect all widgets in scene."""
        print(f"[CONTEXT MENU] Deselect all")
        if self.scene():
            for item in self.scene().items():
                if isinstance(item, UnifiedBaseItem):
                    item.selected = False

        
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle mouse double-click event."""
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event."""
        self.setCursor(Qt.OpenHandCursor)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        if not self._dragging:
            self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)
    
    def itemChange(self, change, value):
        """Handle item changes (e.g., position changes)."""
        if change == QGraphicsItem.ItemPositionChange:
            # Store the new position
            new_pos = value
            # You could add constraints here if needed
            return new_pos
        elif change == QGraphicsItem.ItemPositionHasChanged:
            # Position has changed, emit signal
            self.positionChanged.emit(self.pos())
        
        return super().itemChange(change, value)
    
    # ==================== Utility Methods ====================
    
    def __repr__(self) -> str:
        return f"<UnifiedBaseItem '{self._widget_name}' ({self._widget_type})>"



    def hoverMoveEvent(self, event):
        """Handle hover move event for cursor changes."""
        if self._selected and not self._resizing:
            # Update cursor based on resize edge
            edge = self._get_resize_edge(event.pos())
            
            if edge == 'n' or edge == 's':
                self.setCursor(Qt.SizeVerCursor)
            elif edge == 'e' or edge == 'w':
                self.setCursor(Qt.SizeHorCursor)
            elif edge == 'nw' or edge == 'se':
                self.setCursor(Qt.SizeFDiagCursor)
            elif edge == 'ne' or edge == 'sw':
                self.setCursor(Qt.SizeBDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        
        super().hoverMoveEvent(event)
    
    def _get_resize_edge(self, pos: QPointF):
        """
        Determine which resize edge the mouse is near.
        Returns: 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw', or None
        """
        if not self._selected:
            return None
        
        padding = self._selection_padding
        handle_size = self._resize_handle_size
        half_handle = handle_size / 2
        
        # Widget bounds with padding
        left = -padding
        right = self._width + padding
        top = -padding
        bottom = self._height + padding
        
        x, y = pos.x(), pos.y()
        
        # Check corners first (they have priority)
        if (x >= left - half_handle and x <= left + half_handle and
            y >= top - half_handle and y <= top + half_handle):
            return 'nw'
        elif (x >= right - half_handle and x <= right + half_handle and
              y >= top - half_handle and y <= top + half_handle):
            return 'ne'
        elif (x >= left - half_handle and x <= left + half_handle and
              y >= bottom - half_handle and y <= bottom + half_handle):
            return 'sw'
        elif (x >= right - half_handle and x <= right + half_handle and
              y >= bottom - half_handle and y <= bottom + half_handle):
            return 'se'
        
        # Check edges
        elif x >= left - half_handle and x <= left + half_handle:
            if y >= top and y <= bottom:
                return 'w'
        elif x >= right - half_handle and x <= right + half_handle:
            if y >= top and y <= bottom:
                return 'e'
        elif y >= top - half_handle and y <= top + half_handle:
            if x >= left and x <= right:
                return 'n'
        elif y >= bottom - half_handle and y <= bottom + half_handle:
            if x >= left and x <= right:
                return 's'
        
        return None
class UnifiedGraphicsView(QObject):
    """
    Manager for unified widgets in a QGraphicsView.
    
    Handles:
    - Widget creation and tracking
    - Scene management
    - Event forwarding
    - Widget lookup and management
    """
    
    
    # Signals
    widgetDeleted = Signal(str)  # Emitted when widget is deleted (widget_name)
    widgetAdded = Signal(object)  # Emitted when widget is added (widget object)
    
    def __init__(self, parent=None):
        
        # Create QGraphicsView and scene
        self._view = QGraphicsView(parent)
        self._scene = QGraphicsScene(self._view)
        self._view.setScene(self._scene)
        
        # Configure view
        self._view.setStyleSheet("background: transparent; border: none;")
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setRenderHint(QPainter.Antialiasing, True)
        self._view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # ENABLE INTERACTION AND SELECTION
        self._view.setInteractive(True)
            # Removed problematic QGraphicsView line
        
        # Override view mouse press for empty area deselection
        original_mouse_press = self._view.mousePressEvent
        def custom_mouse_press(event):
            from PySide6.QtCore import Qt
            
            if event.button() == Qt.LeftButton:
                # Get item at click position
                scene_pos = self._view.mapToScene(event.pos())
                item = self._scene.itemAt(scene_pos, self._view.transform())
                
                # If no item clicked (empty area), deselect all
                if item is None:
                    for widget in self._widgets.values():
                        widget.selected = False
                
            # Call original mouse press
            original_mouse_press(event)
        
        self._view.mousePressEvent = custom_mouse_press

        
        # Widget tracking
        self._widgets = {}  # widget_name -> UnifiedBaseItem
        self._preview_scale = 1.0
        
        
        # Override view keyPressEvent to handle Escape
        original_key_press = self._view.keyPressEvent
        def custom_key_press(event):
            from PySide6.QtCore import Qt
            if event.key() == Qt.Key_Escape:
                # Escape pressed - deselect all
                for widget in self._widgets.values():
                    widget.selected = False
                event.accept()
            else:
                original_key_press(event)
        self._view.keyPressEvent = custom_key_press


        
    def _handle_escape(self):
        """Deselect all widgets (called from view)."""
        for widget in self._widgets.values():
            widget.selected = False

    def _delete_widget_by_name(self, widget_name: str):
        """Delete widget by name (called from widget signal)."""
        print(f"[UNIFIED VIEW] Deleting widget: {widget_name}")
        
        if widget_name in self._widgets:
            widget = self._widgets[widget_name]
            
            # Remove from scene
            self._scene.removeItem(widget)
            
            # Remove from dictionary
            del self._widgets[widget_name]
            
            # Clean up widget
            try:
                widget.deleteLater()
            except:
                pass
            
            print(f"[UNIFIED VIEW] Widget {widget_name} deleted")
            
            # Note: Widget deletion notification is now handled directly by UnifiedController
            # from widget deleteRequested signals, not through this signal
            # self.widgetDeleted.emit(widget_name)
        else:
            print(f"[UNIFIED VIEW] Widget {widget_name} not found")



        # Or use: self._view.setDragMode(QGraphicsView.NoDrag) for single item selection
        
        # Widget tracking
        self._preview_scale = 1.0
        
        logger.debug("UnifiedGraphicsView initialized")
        
        # Configure selection - let QGraphicsView handle it automatically
        self._view.setDragMode(QGraphicsView.RubberBandDrag)
        
    
    # ==================== View Access ====================
    
    @property
    def view(self):
        """Get the QGraphicsView."""
        return self._view
    
    @property
    def scene(self):
        """Get the QGraphicsScene."""
        return self._scene
    
    def set_scene_rect(self, x: float, y: float, width: float, height: float):
        """Set scene rectangle (bounds)."""
        self._scene.setSceneRect(x, y, width, height)
    
    def set_preview_scale(self, scale: float):
        """Set preview scale for all widgets."""
        self._preview_scale = scale
        # Update scale for existing widgets
        for widget in self._widgets.values():
            widget.preview_scale = scale
    
    # ==================== Widget Management ====================
    
    def add_widget(self, widget: UnifiedBaseItem) -> bool:
        """
        Add a widget to the scene.
        
        Args:
            widget: UnifiedBaseItem instance
            
        Returns:
            True if added successfully, False if widget with same name exists
        """
        if widget.widget_name in self._widgets:
            logger.warning(f"Widget '{widget.widget_name}' already exists")
            return False
        
        # Add to scene
        self._scene.addItem(widget)
        
        # Connect widget signals
        widget.deleteRequested.connect(self._delete_widget_by_name)
        widget.propertiesRequested.connect(self._show_property_editor)

        
        # Track widget
        self._widgets[widget.widget_name] = widget
        
        # Connect signals
        widget.positionChanged.connect(self._on_widget_position_changed)
        widget.selectionChanged.connect(self._on_widget_selection_changed)
        widget.doubleClicked.connect(self._on_widget_double_clicked)
        
        # Update view to show the new widget
        self._view.update()
        self._scene.update()
        
        # Update the scene rect around the widget
        widget_rect = widget.sceneBoundingRect()
        self._scene.update(widget_rect)
        
        logger.debug(f"Added widget '{widget.widget_name}' ({widget.widget_type})")
        return True
    
    def remove_widget(self, widget_name: str) -> bool:
        """
        Remove a widget from the scene.
        
        Args:
            widget_name: Name of widget to remove
            
        Returns:
            True if removed, False if widget not found
        """
        if widget_name not in self._widgets:
            logger.warning(f"Widget '{widget_name}' not found")
            return False
        
        widget = self._widgets[widget_name]
        
        # Remove from scene
        self._scene.removeItem(widget)
        
        # Disconnect signals
        try:
            widget.positionChanged.disconnect(self._on_widget_position_changed)
            widget.selectionChanged.disconnect(self._on_widget_selection_changed)
            widget.doubleClicked.disconnect(self._on_widget_double_clicked)
        except:
            pass  # Already disconnected
        
        # Remove from tracking
        del self._widgets[widget_name]
        
        logger.debug(f"Removed widget '{widget_name}'")
        return True
    
    def get_widget(self, widget_name: str) -> Optional[UnifiedBaseItem]:
        """Get widget by name."""
        return self._widgets.get(widget_name)
    
    def get_all_widgets(self) -> Dict[str, UnifiedBaseItem]:
        """Get all widgets."""
        return self._widgets.copy()
    
    def clear_widgets(self):
        """Remove all widgets."""
        for widget_name in list(self._widgets.keys()):
            self.remove_widget(widget_name)
    
    # ==================== Widget Creation Helpers ====================
    
    def create_date_widget(self, widget_name: str, x: float, y: float,
                          width: float = 100, height: float = 20,
                          enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a date widget."""
        try:
            from .text_widgets import DateWidget
            widget = DateWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import DateWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create DateWidget: {e}")
        return None
    
    def create_time_widget(self, widget_name: str, x: float, y: float,
                          width: float = 100, height: float = 20,
                          enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a time widget."""
        try:
            from .text_widgets import TimeWidget
            widget = TimeWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import TimeWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create TimeWidget: {e}")
        return None
    def create_free_text_widget(self, widget_name: str, x: float, y: float,
                               width: float = 100, height: float = 20,
                               enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a free text widget."""
        try:
            from .text_widgets import FreeTextWidget
            widget = FreeTextWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import FreeTextWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create FreeTextWidget: {e}")
        return None
    def create_rectangle_widget(self, widget_name: str, x: float, y: float,
                               width: float = 100, height: float = 60,
                               enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a rectangle widget."""
        try:
            from .shape_widgets import RectangleWidget
            widget = RectangleWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import RectangleWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create RectangleWidget: {e}")
        return None

    def create_rounded_rectangle_widget(self, widget_name: str, x: float, y: float,
                                       width: float = 100, height: float = 60,
                                       enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a rounded rectangle widget."""
        try:
            from .shape_widgets import RoundedRectangleWidget
            widget = RoundedRectangleWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import RoundedRectangleWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create RoundedRectangleWidget: {e}")
        return None

    def create_circle_widget(self, widget_name: str, x: float, y: float,
                            width: float = 80, height: float = 80,
                            enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a circle widget."""
        try:
            from .shape_widgets import CircleWidget
            widget = CircleWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import CircleWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create CircleWidget: {e}")
        return None
    def create_metric_widget(self, widget_name: str, x: float, y: float,
                            width: float = 120, height: float = 25,
                            enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a generic metric widget."""
        try:
            from .metric_widgets import MetricWidget
            widget = MetricWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import MetricWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create MetricWidget: {e}")
        return None

    def create_temperature_widget(self, widget_name: str, x: float, y: float,
                                 width: float = 120, height: float = 25,
                                 enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a temperature widget."""
        try:
            from .metric_widgets import TemperatureWidget
            widget = TemperatureWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import TemperatureWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create TemperatureWidget: {e}")
        return None

    def create_usage_widget(self, widget_name: str, x: float, y: float,
                           width: float = 120, height: float = 25,
                           enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a usage percentage widget."""
        try:
            from .metric_widgets import UsageWidget
            widget = UsageWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import UsageWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create UsageWidget: {e}")
        return None

    def create_frequency_widget(self, widget_name: str, x: float, y: float,
                               width: float = 120, height: float = 25,
                               enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a frequency widget."""
        try:
            from .metric_widgets import FrequencyWidget
            widget = FrequencyWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import FrequencyWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create FrequencyWidget: {e}")
        return None

    def create_name_widget(self, widget_name: str, x: float, y: float,
                          width: float = 200, height: float = 25,
                          enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a name widget (CPU/GPU name)."""
        try:
            from .metric_widgets import NameWidget
            widget = NameWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import NameWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create NameWidget: {e}")
        return None

    def create_ram_widget(self, widget_name: str, x: float, y: float,
                         width: float = 150, height: float = 25,
                         enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a RAM widget."""
        try:
            from .metric_widgets import RAMWidget
            widget = RAMWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import RAMWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create RAMWidget: {e}")
        return None

    def create_gpu_memory_widget(self, widget_name: str, x: float, y: float,
                                width: float = 150, height: float = 25,
                                enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a GPU memory widget."""
        try:
            from .metric_widgets import GPUMemoryWidget
            widget = GPUMemoryWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import GPUMemoryWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create GPUMemoryWidget: {e}")
        return None
    def _on_widget_position_changed(self, position: QPointF):
        """Handle widget position change."""
        # Find which widget emitted the signal
        for widget_name, widget in self._widgets.items():
            if widget.pos() == position:
                logger.debug(f"Widget '{widget_name}' moved to {position}")
                # Emit our own signal if needed
                break
    def create_graph_widget(self, widget_name: str, x: float, y: float,
                           width: float = 200, height: float = 150,
                           enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a generic graph widget."""
        try:
            from .graph_widgets import GraphWidget
            widget = GraphWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import GraphWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create GraphWidget: {e}")
        return None

    def create_bar_graph_widget(self, widget_name: str, x: float, y: float,
                               width: float = 200, height: float = 150,
                               enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a bar graph widget."""
        try:
            from .graph_widgets import BarGraphWidget
            widget = BarGraphWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import BarGraphWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create BarGraphWidget: {e}")
        return None

    def create_circular_graph_widget(self, widget_name: str, x: float, y: float,
                                    width: float = 200, height: float = 200,
                                    enabled: bool = True, **kwargs) -> Optional[UnifiedBaseItem]:
        """Create a circular graph widget (pie/donut)."""
        try:
            from .graph_widgets import CircularGraphWidget
            widget = CircularGraphWidget(
                widget_name=widget_name,
                x=x,
                y=y,
                width=width,
                height=height,
                preview_scale=self._preview_scale,
                enabled=enabled,
                **kwargs
            )
            if self.add_widget(widget):
                return widget
        except ImportError as e:
            logger.error(f"Failed to import CircularGraphWidget: {e}")
        except Exception as e:
            logger.error(f"Failed to create CircularGraphWidget: {e}")
        return None

    
    def _on_widget_selection_changed(self, selected: bool):
        """Handle widget selection change."""
        # Find which widget emitted the signal
        for widget_name, widget in self._widgets.items():
            if widget.selected == selected:
                action = "selected" if selected else "deselected"
                logger.debug(f"Widget '{widget_name}' {action}")
                break
    
    def _on_widget_double_clicked(self):
        """Handle widget double-click."""
        # Find which widget emitted the signal
        for widget_name, widget in self._widgets.items():
            # Check if this widget is the sender
            # Note: We need to connect properly to get sender
            logger.debug(f"Widget '{widget_name}' double-clicked")
            # Show property dialog here
            break
    
    # ==================== Utility Methods ====================
    
    def __repr__(self) -> str:
        return f"<UnifiedGraphicsView with {len(self._widgets)} widgets>"

    def _show_property_editor(self, widget):
        """Show property editor for widget."""
        print(f"[UNIFIED VIEW] Showing property editor for {widget.widget_name}")
        
        # Import here to avoid circular imports
        from .property_editor_dialog import PropertyEditorDialog
        
        # Create and show dialog
        dialog = PropertyEditorDialog(self._view)
        dialog.set_widget(widget)
        
        # Connect dialog signals
        dialog.propertiesApplied.connect(self._on_properties_applied)
        
        # Show dialog (modal)
        dialog.exec()
    
    def _on_properties_applied(self, properties: dict):
        """Handle properties applied from editor."""
        print(f"[UNIFIED VIEW] Properties applied: {properties}")