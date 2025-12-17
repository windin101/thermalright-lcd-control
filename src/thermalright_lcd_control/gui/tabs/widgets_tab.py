"""
Widgets Tab - For adding and configuring display widgets
"""
from typing import Optional, Dict, Any, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QLineEdit,
    QSpinBox, QScrollArea, QFormLayout, QListWidget,
    QListWidgetItem, QMessageBox
)

from ...common.logging_config import get_gui_logger


class WidgetsTab(QWidget):
    """Tab for managing display widgets"""
    
    widget_added = Signal(str, dict)  # widget_type, properties
    widget_removed = Signal(str)  # widget_id
    widget_updated = Signal(str, dict)  # widget_id, properties
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_gui_logger()
        self.widgets = {}  # widget_id -> properties
        self.current_widget_id = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup widgets tab UI"""
        main_layout = QVBoxLayout(self)
        
        # Widget list section
        list_group = QGroupBox("Widgets")
        list_layout = QVBoxLayout(list_group)
        
        # Widget list
        self.widget_list = QListWidget()
        self.widget_list.itemSelectionChanged.connect(self._on_widget_selected)
        list_layout.addWidget(self.widget_list)
        
        # Add widget button
        add_widget_btn = QPushButton("+ Add Widget")
        add_widget_btn.clicked.connect(self._show_add_widget_dialog)
        list_layout.addWidget(add_widget_btn)
        
        # Remove widget button
        remove_widget_btn = QPushButton("- Remove Widget")
        remove_widget_btn.clicked.connect(self._remove_selected_widget)
        list_layout.addWidget(remove_widget_btn)
        
        main_layout.addWidget(list_group)
        
        # Widget properties section (initially hidden)
        self.properties_group = QGroupBox("Widget Properties")
        self.properties_group.setVisible(False)
        self.properties_layout = QFormLayout(self.properties_group)
        main_layout.addWidget(self.properties_group)
        
        main_layout.addStretch()
    
    def _show_add_widget_dialog(self):
        """Show dialog to add new widget"""
        from PySide6.QtWidgets import QDialog, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Widget")
        dialog_layout = QVBoxLayout(dialog)
        
        # Widget type selection
        type_label = QLabel("Widget Type:")
        dialog_layout.addWidget(type_label)
        
        type_combo = QComboBox()
        type_combo.addItems(["Metric", "Text", "Bar Graph", "Circular Graph", "Shape"])
        dialog_layout.addWidget(type_combo)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addWidget(buttons)
        
        if dialog.exec():
            widget_type = type_combo.currentText().lower().replace(" ", "_")
            self._add_widget(widget_type)
    
    def _add_widget(self, widget_type: str):
        """Add a new widget"""
        import uuid
        widget_id = f"{widget_type}_{uuid.uuid4().hex[:8]}"
        
        # Default properties based on widget type
        if widget_type == "metric":
            properties = {
                "type": "metric",
                "label": "CPU",
                "metric_type": "cpu_usage",
                "unit": "%",
                "position": (50, 50),
                "size": (100, 30)
            }
        elif widget_type == "text":
            properties = {
                "type": "text",
                "text": "Sample Text",
                "font_size": 16,
                "position": (50, 100),
                "size": (100, 30)
            }
        else:
            properties = {
                "type": widget_type,
                "position": (50, 150),
                "size": (100, 100)
            }
        
        self.widgets[widget_id] = properties
        self._update_widget_list()
        
        # Emit signal for main window to create actual widget
        self.widget_added.emit(widget_type, properties)
        
        self.logger.info(f"Added widget: {widget_id} ({widget_type})")
    
    def _remove_selected_widget(self):
        """Remove selected widget"""
        selected = self.widget_list.currentItem()
        if not selected:
            return
        
        widget_id = selected.data(Qt.UserRole)
        if widget_id in self.widgets:
            del self.widgets[widget_id]
            self._update_widget_list()
            self.widget_removed.emit(widget_id)
            self.properties_group.setVisible(False)
            self.logger.info(f"Removed widget: {widget_id}")
    
    def _on_widget_selected(self):
        """Handle widget selection"""
        selected = self.widget_list.currentItem()
        if not selected:
            self.properties_group.setVisible(False)
            return
        
        self.current_widget_id = selected.data(Qt.UserRole)
        self._show_widget_properties(self.current_widget_id)
    
    def _show_widget_properties(self, widget_id: str):
        """Show properties for selected widget"""
        # Clear existing properties
        while self.properties_layout.count():
            child = self.properties_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if widget_id not in self.widgets:
            return
        
        properties = self.widgets[widget_id]
        widget_type = properties.get("type", "unknown")
        
        # Add properties based on widget type
        if widget_type == "metric":
            self._add_metric_properties(properties)
        elif widget_type == "text":
            self._add_text_properties(properties)
        # Add other widget types here
        
        self.properties_group.setVisible(True)
        self.properties_group.setTitle(f"Properties: {widget_id}")
    
    def _add_metric_properties(self, properties: Dict[str, Any]):
        """Add metric widget property controls"""
        # Metric type
        type_combo = QComboBox()
        type_combo.addItems(["CPU Usage", "GPU Usage", "RAM Usage", "Network", "Temperature"])
        type_combo.setCurrentText(properties.get("label", "CPU"))
        type_combo.currentTextChanged.connect(
            lambda text: self._update_property("label", text)
        )
        self.properties_layout.addRow("Metric:", type_combo)
        
        # Unit
        unit_edit = QLineEdit(properties.get("unit", "%"))
        unit_edit.textChanged.connect(
            lambda text: self._update_property("unit", text)
        )
        self.properties_layout.addRow("Unit:", unit_edit)
    
    def _add_text_properties(self, properties: Dict[str, Any]):
        """Add text widget property controls"""
        # Text content
        text_edit = QLineEdit(properties.get("text", "Sample Text"))
        text_edit.textChanged.connect(
            lambda text: self._update_property("text", text)
        )
        self.properties_layout.addRow("Text:", text_edit)
        
        # Font size
        size_spin = QSpinBox()
        size_spin.setRange(8, 72)
        size_spin.setValue(properties.get("font_size", 16))
        size_spin.valueChanged.connect(
            lambda value: self._update_property("font_size", value)
        )
        self.properties_layout.addRow("Font Size:", size_spin)
    
    def _update_property(self, key: str, value: Any):
        """Update property of current widget"""
        if self.current_widget_id and self.current_widget_id in self.widgets:
            self.widgets[self.current_widget_id][key] = value
            self.widget_updated.emit(self.current_widget_id, self.widgets[self.current_widget_id])
    
    def _update_widget_list(self):
        """Update widget list display"""
        self.widget_list.clear()
        for widget_id, properties in self.widgets.items():
            item = QListWidgetItem(f"{properties.get('type', 'unknown')}: {properties.get('label', widget_id)}")
            item.setData(Qt.UserRole, widget_id)
            self.widget_list.addItem(item)
    
    def load_widgets(self, widgets: Dict[str, Dict[str, Any]]):
        """Load widgets from configuration"""
        self.widgets = widgets.copy()
        self._update_widget_list()
    
    def get_widgets(self) -> Dict[str, Dict[str, Any]]:
        """Get all widgets configuration"""
        return self.widgets.copy()