"""
Property Editor Dialog - Modal dialog wrapper for PropertyEditor
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox, QWidget
from PySide6.QtCore import Qt, Signal

from .property_editor import PropertyEditor
import logging


class PropertyEditorDialog(QDialog):
    """Modal dialog for editing widget properties"""
    
    propertiesApplied = Signal(dict)  # Emitted when Apply is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._widget = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Widget Properties")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # Property editor
        self.property_editor = PropertyEditor(self)
        layout.addWidget(self.property_editor)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Apply | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Connect Apply button
        apply_button = button_box.button(QDialogButtonBox.Apply)
        apply_button.clicked.connect(self._on_apply)
        
        layout.addWidget(button_box)
        
        # Connect property editor signals
        self.property_editor.propertyChanged.connect(self._on_property_changed)
    
    def set_widget(self, widget):
        """Set widget to edit"""
        self._widget = widget
        self.property_editor.set_widget(widget)
        
        # Update window title with widget info
        if widget:
            widget_type = getattr(widget, 'widget_type', 'unknown')
            widget_name = getattr(widget, 'widget_name', 'unnamed')
            self.setWindowTitle(f"Properties: {widget_type} - {widget_name}")
    
    def _on_apply(self):
        """Handle Apply button click"""
        try:
            # Get properties from editor
            if hasattr(self.property_editor, '_get_current_properties'):
                properties = self.property_editor._get_current_properties()
            else:
                # Fallback: trigger apply changes in editor
                self.property_editor._apply_changes()
                properties = {}
            
            # Update widget properties if we have a widget
            if self._widget and properties:
                if hasattr(self._widget, 'set_properties'):
                    self._widget.set_properties(properties)
                    self.logger.info(f"Updated widget properties: {properties}")
                else:
                    self.logger.warning(f"Widget has no set_properties method")
            
            # Emit signal
            self.propertiesApplied.emit(properties)
            self.logger.info(f"Applied properties for widget: {getattr(self._widget, 'widget_name', 'unknown')}")
            
        except Exception as e:
            self.logger.error(f"Error applying properties: {e}")
    
    def _on_property_changed(self, properties: dict):
        """Handle property changes from editor"""
        self.logger.debug(f"Properties changed: {properties}")
    
    def accept(self):
        """Handle OK button - apply changes and close"""
        self._on_apply()  # Apply changes
        super().accept()
    
    def reject(self):
        """Handle Cancel button - discard changes and close"""
        self.logger.debug("Property editor cancelled")
        super().reject()