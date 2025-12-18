"""
Widgets Tab - For adding and configuring display widgets
"""
from typing import Dict, Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QLabel, 
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QLineEdit,
    QSpinBox, QFormLayout, QListWidget,
    QListWidgetItem, QDialog, QDialogButtonBox
)

from ...common.logging_config import get_gui_logger
from ..widgets.widget_palette import WidgetPalette


class WidgetsTab(QWidget):
    """Tab for managing display widgets"""
    
    widget_added = Signal(str, str, dict)  # widget_id, widget_type, properties
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
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Widget Palette (full width)
        palette_group = QGroupBox("Widget Palette")
        palette_layout = QVBoxLayout(palette_group)
        
        self.widget_palette = WidgetPalette()
        self.widget_palette.widgetSelected.connect(self._on_widget_palette_selected)
        palette_layout.addWidget(self.widget_palette)
        
        main_layout.addWidget(palette_group, 8)  # Most of the space
        
        # Widget properties section (only shown when widget is selected)
        self.properties_group = QGroupBox("Widget Properties")
        self.properties_group.setVisible(False)
        self.properties_layout = QFormLayout(self.properties_group)
        main_layout.addWidget(self.properties_group, 2)  # Less space
        
        # Info label
        info_label = QLabel("Click widget in preview to edit properties • Right-click widget to delete")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        main_layout.addWidget(info_label)
    
    def _on_widget_palette_selected(self, widget_type: str, default_properties: dict):
        """
        Handle widget selection from palette.
        
        Args:
            widget_type: Type of widget selected (e.g., 'cpu_usage')
            default_properties: Default properties for the widget
        """
        import uuid
        
        # Generate unique widget ID
        widget_id = f"{widget_type}_{uuid.uuid4().hex[:8]}"
        
        # Add widget_name to properties for tracking
        properties = default_properties.copy()
        properties['widget_name'] = widget_id
        
        # Store widget
        self.widgets[widget_id] = properties
        self.update_widget_list()
        
        # Emit signal for preview area
        self.widget_added.emit(widget_id, widget_type, properties)
        
        self.logger.info(f"Added widget from palette: {widget_id} ({widget_type})")
    

    def show_add_widget_dialog(self):
        """Show dialog to add new widget"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Widget")
        dialog_layout = QVBoxLayout(dialog)
        
        # Widget type selection
        type_label = QLabel("Widget Type:")
        dialog_layout.addWidget(type_label)
        
        type_combo = QComboBox()
        type_combo.addItems(["Metric", "Text", "Date", "Time"])
        dialog_layout.addWidget(type_combo)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addWidget(buttons)
        
        if dialog.exec():
            widget_type = type_combo.currentText().lower()
            self.add_widget(widget_type)
    
    def add_widget(self, widget_type: str):
        """Add a new widget"""
        import uuid
        widget_id = f"{widget_type}_{uuid.uuid4().hex[:8]}"
        
        # Default properties
        if widget_type == "metric":
            properties = {
                "type": "metric",
                "label": "CPU",
                "metric_type": "cpu_usage",
                "unit": "%",
                "position": (50, 50),
                "size": (100, 30)
            }
        elif widget_type == "date":
            properties = {
                "type": "date",
                "date_format": "%d/%m",  # dd/mm format
                "font_size": 16,
                "position": (50, 150),
                "size": (100, 30)
            }
        elif widget_type == "time":
            properties = {
                "type": "time", 
                "time_format": "%H:%M",  # HH:MM format
                "font_size": 16,
                "position": (50, 200),
                "size": (100, 30)
            }
        else:  # text
            properties = {
                "type": "text",
                "text": "Sample Text",
                "font_size": 16,
                "position": (50, 100),
                "size": (100, 30)
            }
        
        self.widgets[widget_id] = properties
        self.update_widget_list()
        self.widget_added.emit(widget_id, widget_type, properties)
        self.logger.info(f"Added widget: {widget_id}")
    

    
    def show_widget_properties(self, widget_id: str):
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
            self.add_metric_properties(properties)
        elif widget_type == "text":
            self.add_text_properties(properties)
        elif widget_type == "date":
            self.add_date_properties(properties)
        elif widget_type == "time":
            self.add_time_properties(properties)
            self.add_text_properties(properties)
        
        self.properties_group.setVisible(True)
        self.properties_group.setTitle(f"Properties: {widget_id}")
    
    def add_metric_properties(self, properties: Dict[str, Any]):
        """Add metric widget property controls"""
        # Metric type
        type_combo = QComboBox()
        type_combo.addItems(["CPU Usage", "GPU Usage", "RAM Usage"])
        type_combo.setCurrentText(properties.get("label", "CPU"))
        type_combo.currentTextChanged.connect(
            lambda text: self.update_property("label", text)
        )
        self.properties_layout.addRow("Metric:", type_combo)
        
        # Unit
        unit_edit = QLineEdit(properties.get("unit", "%"))
        unit_edit.textChanged.connect(
            lambda text: self.update_property("unit", text)
        )
        self.properties_layout.addRow("Unit:", unit_edit)
    
    def add_text_properties(self, properties: Dict[str, Any]):
        """Add text widget property controls"""
        # Text content
        text_edit = QLineEdit(properties.get("text", "Sample Text"))
        text_edit.textChanged.connect(
            lambda text: self.update_property("text", text)
        )
        self.properties_layout.addRow("Text:", text_edit)
        
        # Font size
        size_spin = QSpinBox()
        size_spin.setRange(8, 72)
        size_spin.setValue(properties.get("font_size", 16))
        size_spin.valueChanged.connect(
            lambda value: self.update_property("font_size", value)
        )
        self.properties_layout.addRow("Font Size:", size_spin)
    
    def add_date_properties(self, properties: Dict[str, Any]):
        """Add date widget property controls"""
        # Date format
        format_combo = QComboBox()
        format_combo.addItems(["%d/%m", "%m/%d", "%d-%m", "%m-%d", "%d %b", "%b %d"])
        format_combo.setCurrentText(properties.get("date_format", "%d/%m"))
        format_combo.currentTextChanged.connect(
            lambda text: self.update_property("date_format", text)
        )
        self.properties_layout.addRow("Date Format:", format_combo)
        
        # Font size
        size_spin = QSpinBox()
        size_spin.setRange(8, 72)
        size_spin.setValue(properties.get("font_size", 16))
        size_spin.valueChanged.connect(
            lambda value: self.update_property("font_size", value)
        )
        self.properties_layout.addRow("Font Size:", size_spin)
        
        # Position
        pos_x = QSpinBox()
        pos_x.setRange(0, 1000)
        pos_x.setValue(properties.get("position", (50, 150))[0])
        pos_x.valueChanged.connect(
            lambda value: self._update_position("x", value)
        )
        
        pos_y = QSpinBox()
        pos_y.setRange(0, 1000)
        pos_y.setValue(properties.get("position", (50, 150))[1])
        pos_y.valueChanged.connect(
            lambda value: self._update_position("y", value)
        )
        
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(pos_x)
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(pos_y)
        self.properties_layout.addRow("Position:", pos_layout)
        
        # Size
        width_spin = QSpinBox()
        width_spin.setRange(10, 500)
        width_spin.setValue(properties.get("size", (100, 30))[0])
        width_spin.valueChanged.connect(
            lambda value: self._update_size("width", value)
        )
        
        height_spin = QSpinBox()
        height_spin.setRange(10, 500)
        height_spin.setValue(properties.get("size", (100, 30))[1])
        height_spin.valueChanged.connect(
            lambda value: self._update_size("height", value)
        )
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(width_spin)
        size_layout.addWidget(QLabel("Height:"))
        size_layout.addWidget(height_spin)
        self.properties_layout.addRow("Size:", size_layout)
    
    def add_time_properties(self, properties: Dict[str, Any]):
        """Add time widget property controls"""
        # Time format
        format_combo = QComboBox()
        format_combo.addItems(["%H:%M", "%I:%M %p", "%H:%M:%S", "%I:%M:%S %p"])
        format_combo.setCurrentText(properties.get("time_format", "%H:%M"))
        format_combo.currentTextChanged.connect(
            lambda text: self.update_property("time_format", text)
        )
        self.properties_layout.addRow("Time Format:", format_combo)
        
        # Font size
        size_spin = QSpinBox()
        size_spin.setRange(8, 72)
        size_spin.setValue(properties.get("font_size", 16))
        size_spin.valueChanged.connect(
            lambda value: self.update_property("font_size", value)
        )
        self.properties_layout.addRow("Font Size:", size_spin)
        
        # Position
        pos_x = QSpinBox()
        pos_x.setRange(0, 1000)
        pos_x.setValue(properties.get("position", (50, 200))[0])
        pos_x.valueChanged.connect(
            lambda value: self._update_position("x", value)
        )
        
        pos_y = QSpinBox()
        pos_y.setRange(0, 1000)
        pos_y.setValue(properties.get("position", (50, 200))[1])
        pos_y.valueChanged.connect(
            lambda value: self._update_position("y", value)
        )
        
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(pos_x)
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(pos_y)
        self.properties_layout.addRow("Position:", pos_layout)
        
        # Size
        width_spin = QSpinBox()
        width_spin.setRange(10, 500)
        width_spin.setValue(properties.get("size", (100, 30))[0])
        width_spin.valueChanged.connect(
            lambda value: self._update_size("width", value)
        )
        
        height_spin = QSpinBox()
        height_spin.setRange(10, 500)
        height_spin.setValue(properties.get("size", (100, 30))[1])
        height_spin.valueChanged.connect(
            lambda value: self._update_size("height", value)
        )
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(width_spin)
        size_layout.addWidget(QLabel("Height:"))
        size_layout.addWidget(height_spin)
        self.properties_layout.addRow("Size:", size_layout)

    def _update_position(self, axis: str, value: int):
        """Update position of current widget"""
        if self.current_widget_id and self.current_widget_id in self.widgets:
            properties = self.widgets[self.current_widget_id]
            current_pos = properties.get("position", (50, 50))
            if axis == "x":
                new_pos = (value, current_pos[1])
            else:  # y
                new_pos = (current_pos[0], value)
            properties["position"] = new_pos
            self.widget_updated.emit(self.current_widget_id, properties)
    
    def _update_size(self, dimension: str, value: int):
        """Update size of current widget"""
        if self.current_widget_id and self.current_widget_id in self.widgets:
            properties = self.widgets[self.current_widget_id]
            current_size = properties.get("size", (100, 30))
            if dimension == "width":
                new_size = (value, current_size[1])
            else:  # height
                new_size = (current_size[0], value)
            properties["size"] = new_size
            self.widget_updated.emit(self.current_widget_id, properties)

    def update_property(self, key: str, value: Any):
        """Update property of current widget"""
        if self.current_widget_id and self.current_widget_id in self.widgets:
            self.widgets[self.current_widget_id][key] = value
            self.widget_updated.emit(self.current_widget_id, self.widgets[self.current_widget_id])
    
    def remove_widget(self, widget_id: str):
        """Remove widget by ID."""
        print(f"[DEBUG] WidgetsTab.remove_widget called with: {widget_id}")
        print(f"[DEBUG] Current widgets in WidgetsTab: {list(self.widgets.keys())}")
        if widget_id in self.widgets:
            # Remove from dictionary
            del self.widgets[widget_id]
            
            # Update list display
            print(f"[DEBUG] Calling update_widget_list after removal")
            self.update_widget_list()
            
            # Clear properties if this was the selected widget
            if self.current_widget_id == widget_id:
                self.current_widget_id = None
                self.properties_group.setVisible(False)
            
            self.logger.info(f"Removed widget: {widget_id}")
            print(f"[DEBUG] Widget {widget_id} successfully removed from WidgetsTab")
            return True
        else:
            self.logger.warning(f"Widget {widget_id} not found in WidgetsTab")
            print(f"[DEBUG] Widget {widget_id} not found in WidgetsTab")
            return False
    def update_widget_list(self):
        """Widget tracking (list display removed)"""
        print(f"[DEBUG] Widgets tracked: {len(self.widgets)} items")
        # List display removed - widgets are visible in preview area
