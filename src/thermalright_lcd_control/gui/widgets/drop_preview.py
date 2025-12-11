# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Drop-enabled preview widget for accepting palette widget drops"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal


class DropPreviewWidget(QWidget):
    """A QWidget that accepts drops from the widget palette"""
    
    # Signal emitted when a widget is dropped: (widget_type, x, y)
    widget_dropped = Signal(str, int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._drop_indicator_visible = False
    
    def dragEnterEvent(self, event):
        """Handle drag enter - accept if it's a widget type"""
        if event.mimeData().hasFormat("application/x-widget-type"):
            event.acceptProposedAction()
            self._drop_indicator_visible = True
            self.update()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move - update drop position indicator"""
        if event.mimeData().hasFormat("application/x-widget-type"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave - hide drop indicator"""
        self._drop_indicator_visible = False
        self.update()
        super().dragLeaveEvent(event)
    
    def dropEvent(self, event):
        """Handle drop - emit signal with widget type and position"""
        if event.mimeData().hasFormat("application/x-widget-type"):
            widget_type = event.mimeData().data("application/x-widget-type").data().decode()
            pos = event.position().toPoint()
            
            # Emit signal with widget type and drop position
            self.widget_dropped.emit(widget_type, pos.x(), pos.y())
            
            event.acceptProposedAction()
            self._drop_indicator_visible = False
            self.update()
        else:
            event.ignore()
