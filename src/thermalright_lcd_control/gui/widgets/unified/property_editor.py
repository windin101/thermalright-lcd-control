"""
Unified Widget System - Property Editor

Provides a UI for editing widget properties in real-time.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
                               QCheckBox, QPushButton, QColorDialog, QGroupBox,
                               QScrollArea, QFormLayout, QTabWidget)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont
from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class PropertyEditor(QWidget):
    """
    Widget property editor UI.
    
    Dynamically creates controls based on widget properties.
    """
    
    # Signal emitted when a property changes
    propertyChanged = Signal(dict)  # {property_name: value}
    
    def __init__(self, parent=None):
        """Initialize property editor."""
        super().__init__(parent)
        
        self._current_widget = None
        self._property_widgets = {}  # property_name -> QWidget
        self._ignore_changes = False
        
        self._setup_ui()
        
        logger.debug("PropertyEditor initialized")
    
    def _setup_ui(self):
        """Setup the UI layout."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Widget Properties")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Widget info
        self._widget_info_label = QLabel("No widget selected")
        self._widget_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._widget_info_label)
        
        # Scroll area for properties
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Properties container
        self._properties_container = QWidget()
        self._properties_layout = QFormLayout(self._properties_container)
        scroll_area.setWidget(self._properties_container)
        
        layout.addWidget(scroll_area)
        
        # Apply button
        self._apply_button = QPushButton("Apply Changes")
        self._apply_button.clicked.connect(self._apply_changes)
        self._apply_button.setEnabled(False)
        layout.addWidget(self._apply_button)
        
        # Set layout
        self.setLayout(layout)
    
    def set_widget(self, widget):
        """
        Set the widget to edit.
        
        Args:
            widget: UnifiedBaseItem instance or None to clear
        """
        self._current_widget = widget
        self._clear_properties()
        
        if widget is None:
            self._widget_info_label.setText("No widget selected")
            self._apply_button.setEnabled(False)
            return
        
        # Update widget info
        widget_type = getattr(widget, 'widget_type', 'unknown')
        widget_name = getattr(widget, 'widget_name', 'unnamed')
        self._widget_info_label.setText(f"{widget_type}: {widget_name}")
        
        # Get widget properties
        try:
            properties = widget.get_properties()
            self._create_property_controls(properties)
            self._apply_button.setEnabled(True)
        except Exception as e:
            logger.error(f"Failed to get widget properties: {e}")
            self._widget_info_label.setText(f"Error: {str(e)}")
            self._apply_button.setEnabled(False)
    
    def _clear_properties(self):
        """Clear all property controls."""
        # Remove all widgets from layout
        while self._properties_layout.rowCount() > 0:
            self._properties_layout.removeRow(0)
        
        self._property_widgets.clear()
    
    def _create_property_controls(self, properties: Dict[str, Any]):
        """Create UI controls for each property."""
        self._ignore_changes = True
        
        # Group properties by category
        basic_props = {}
        visual_props = {}
        data_props = {}
        
        for prop_name, prop_value in properties.items():
            if prop_name in ['widget_name', 'widget_type', 'x', 'y', 'width', 'height']:
                basic_props[prop_name] = prop_value
            elif prop_name in ['font_family', 'font_size', 'bold', 'text_color',
                              'fill_color', 'border_color', 'border_width',
                              'grid_color', 'show_grid']:
                visual_props[prop_name] = prop_value
            elif prop_name in ['text', 'date_format', 'metric_type', 'data',
                              'orientation', 'chart_type', 'value_format', 'metric_name']:
                data_props[prop_name] = prop_value
            else:
                basic_props[prop_name] = prop_value
        
        # Create tabs for different property categories
        tab_widget = QTabWidget()
        
        # Basic properties tab
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)
        self._add_properties_to_layout(basic_props, basic_layout)
        tab_widget.addTab(basic_tab, "Basic")
        
        # Visual properties tab
        if visual_props:
            visual_tab = QWidget()
            visual_layout = QFormLayout(visual_tab)
            self._add_properties_to_layout(visual_props, visual_layout)
            tab_widget.addTab(visual_tab, "Visual")
        
        # Data properties tab
        if data_props:
            data_tab = QWidget()
            data_layout = QFormLayout(data_tab)
            self._add_properties_to_layout(data_props, data_layout)
            tab_widget.addTab(data_tab, "Data")
        
        self._properties_layout.addRow(tab_widget)
        
        self._ignore_changes = False
    
    def _add_properties_to_layout(self, properties: Dict[str, Any], layout: QFormLayout):
        """Add property controls to a layout."""
        for prop_name, prop_value in properties.items():
            # Skip some internal properties
            if prop_name.startswith('_') or prop_name in ['preview_scale', 'selected']:
                continue
            
            # Create label
            label = QLabel(self._format_property_name(prop_name))
            
            # Create appropriate control based on property type and name
            control = self._create_property_control(prop_name, prop_value)
            
            if control:
                layout.addRow(label, control)
                self._property_widgets[prop_name] = control
    
    def _format_property_name(self, name: str) -> str:
        """Format property name for display."""
        # Convert snake_case to Title Case
        return name.replace('_', ' ').title()
    
    def _create_property_control(self, prop_name: str, prop_value: Any) -> Optional[QWidget]:
        """Create appropriate control for a property."""
        # Determine control type based on property name and value type
        if prop_name in ['enabled', 'visible', 'bold', 'show_grid', 'show_values',
                        'show_labels', 'show_percentages', 'exploded']:
            # Boolean properties
            checkbox = QCheckBox()
            checkbox.setChecked(bool(prop_value))
            checkbox.stateChanged.connect(lambda: self._on_property_changed())
            return checkbox
        
        elif prop_name in ['font_size', 'border_width', 'animation_duration']:
            # Integer properties
            spinbox = QSpinBox()
            spinbox.setRange(0, 1000)
            spinbox.setValue(int(prop_value))
            spinbox.valueChanged.connect(lambda: self._on_property_changed())
            return spinbox
        
        elif prop_name in ['x', 'y', 'width', 'height', 'bar_spacing', 'hole_size',
                          'explode_distance']:
            # Float properties
            spinbox = QDoubleSpinBox()
            spinbox.setRange(0.0, 10000.0)
            spinbox.setDecimals(2)
            spinbox.setValue(float(prop_value))
            spinbox.valueChanged.connect(lambda: self._on_property_changed())
            return spinbox
        
        elif prop_name in ['text_color', 'fill_color', 'border_color', 'grid_color']:
            # Color properties
            if isinstance(prop_value, (list, tuple)) and len(prop_value) == 4:
                color = QColor(*prop_value)
            else:
                color = QColor(prop_value) if prop_value else QColor(0, 0, 0, 255)
            
            color_button = QPushButton()
            color_button.setStyleSheet(f"background-color: {color.name()};")
            color_button.clicked.connect(
                lambda checked, btn=color_button, pn=prop_name: 
                self._choose_color(btn, pn)
            )
            return color_button
        
        elif prop_name in ['font_family', 'date_format', 'metric_type', 'orientation',
                          'chart_type', 'value_format', 'metric_name']:
            # String properties (some with limited choices)
            if prop_name == 'orientation' and self._current_widget:
                # Bar graph orientation
                combo = QComboBox()
                combo.addItems(['vertical', 'horizontal'])
                combo.setCurrentText(str(prop_value))
                combo.currentTextChanged.connect(lambda: self._on_property_changed())
                return combo
            
            elif prop_name == 'chart_type' and self._current_widget:
                # Chart type
                combo = QComboBox()
                combo.addItems(['pie', 'donut'])
                combo.setCurrentText(str(prop_value))
                combo.currentTextChanged.connect(lambda: self._on_property_changed())
                return combo
            
            elif prop_name == 'value_format' and self._current_widget:
                # Value format for graphs
                combo = QComboBox()
                format_options = [
                    '{:.0f}',    # No decimals
                    '{:.1f}',    # 1 decimal
                    '{:.2f}',    # 2 decimals
                    '{:.0%}',    # Percentage, no decimals
                    '{:.1%}',    # Percentage, 1 decimal
                    '{:.2%}',    # Percentage, 2 decimals
                ]
                combo.addItems(format_options)
                combo.setCurrentText(str(prop_value))
                combo.currentTextChanged.connect(lambda: self._on_property_changed())
                return combo
            
            elif prop_name == 'metric_name' and self._current_widget:
                # Metric name for graphs
                combo = QComboBox()
                metric_options = [
                    'cpu_temperature', 'gpu_temperature',
                    'cpu_usage', 'gpu_usage',
                    'cpu_frequency', 'gpu_frequency'
                ]
                combo.addItems(metric_options)
                combo.setCurrentText(str(prop_value))
                combo.currentTextChanged.connect(lambda: self._on_property_changed())
                return combo
            
            elif prop_name == 'metric_type' and self._current_widget:
                # Metric type
                combo = QComboBox()
                # Common metric types
                metric_types = [
                    'cpu_temperature', 'gpu_temperature',
                    'cpu_usage', 'gpu_usage',
                    'cpu_frequency', 'gpu_frequency',
                    'cpu_name', 'gpu_name',
                    'ram_percent', 'ram_total',
                    'gpu_mem_percent', 'gpu_mem_total'
                ]
                combo.addItems(metric_types)
                combo.setCurrentText(str(prop_value))
                combo.currentTextChanged.connect(lambda: self._on_property_changed())
                return combo
            
            elif prop_name == 'date_format' and self._current_widget:
                # Date format for DateWidget
                combo = QComboBox()
                date_formats = [
                    'dd/MM', 'MM/dd', 'dd-MM', 'MM-dd', 'dd.MM', 'MM.dd',
                    'yyyy-MM-dd', 'dd/MM/yyyy', 'MM/dd/yyyy'
                ]
                combo.addItems(date_formats)
                combo.setCurrentText(str(prop_value))
                combo.currentTextChanged.connect(lambda: self._on_property_changed())
                return combo
            
            elif prop_name == 'time_format' and self._current_widget:
                # Time format for TimeWidget
                combo = QComboBox()
                time_formats = [
                    'HH:mm', 'hh:mm', 'HH:mm:ss', 'hh:mm:ss',
                    'HH:mm AP', 'hh:mm AP', 'HH:mm:ss AP', 'hh:mm:ss AP'
                ]
                combo.addItems(time_formats)
                combo.setCurrentText(str(prop_value))
                combo.currentTextChanged.connect(lambda: self._on_property_changed())
                return combo
            
            elif prop_name == 'font_family' and self._current_widget:
                # Font family - use system fonts
                from PySide6.QtGui import QFontDatabase
                combo = QComboBox()
                font_db = QFontDatabase()
                combo.addItems(sorted(font_db.families()))
                combo.setCurrentText(str(prop_value))
                combo.currentTextChanged.connect(lambda: self._on_property_changed())
                return combo
            
            else:
                # Generic string
                line_edit = QLineEdit(str(prop_value))
                line_edit.textChanged.connect(lambda: self._on_property_changed())
                return line_edit
        
        elif prop_name == 'text' and self._current_widget:
            # Multi-line text for FreeTextWidget
            from PySide6.QtWidgets import QTextEdit
            text_edit = QTextEdit()
            text_edit.setPlainText(str(prop_value))
            text_edit.textChanged.connect(lambda: self._on_property_changed())
            return text_edit
        
        elif prop_name == 'alignment' and self._current_widget:
            # Text alignment
            combo = QComboBox()
            combo.addItems(['left', 'center', 'right'])
            combo.setCurrentText(str(prop_value))
            combo.currentTextChanged.connect(lambda: self._on_property_changed())
            return combo
        
        else:
            # Default: string representation
            line_edit = QLineEdit(str(prop_value))
            line_edit.textChanged.connect(lambda: self._on_property_changed())
            return line_edit
    
    def _choose_color(self, button: QPushButton, property_name: str):
        """Open color dialog for color properties."""
        current_color = button.palette().button().color()
        color = QColorDialog.getColor(current_color, self, f"Choose {property_name}")
        
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()};")
            self._on_property_changed()
    
    def _on_property_changed(self):
        """Called when any property control changes."""
        if self._ignore_changes:
            return
        
        # Enable apply button
        self._apply_button.setEnabled(True)
    
    def _apply_changes(self):
        """Apply all property changes to the widget."""
        if self._current_widget is None:
            return
        
        try:
            # Collect changed properties
            changed_props = {}
            
            for prop_name, control in self._property_widgets.items():
                if isinstance(control, QCheckBox):
                    value = control.isChecked()
                elif isinstance(control, QSpinBox):
                    value = control.value()
                elif isinstance(control, QDoubleSpinBox):
                    value = control.value()
                elif isinstance(control, QLineEdit):
                    value = control.text()
                elif isinstance(control, QComboBox):
                    value = control.currentText()
                elif isinstance(control, QPushButton):
                    # Color button - get color from stylesheet
                    style = control.styleSheet()
                    if 'background-color:' in style:
                        color_str = style.split('background-color:')[1].split(';')[0].strip()
                        color = QColor(color_str)
                        value = (color.red(), color.green(), color.blue(), color.alpha())
                    else:
                        continue  # Skip if no color set
                elif hasattr(control, 'toPlainText'):  # QTextEdit
                    value = control.toPlainText()
                else:
                    continue
                
                changed_props[prop_name] = value
            
            # Apply properties to widget
            if changed_props:
                self._current_widget.set_properties(changed_props)
                logger.debug(f"Applied properties: {changed_props}")
                
                # Emit signal
                self.propertyChanged.emit(changed_props)
                
                # Disable apply button
                self._apply_button.setEnabled(False)
                
        except Exception as e:
            logger.error(f"Failed to apply properties: {e}")
            self._widget_info_label.setText(f"Error applying: {str(e)}")
    
    def update_from_widget(self):
        """Update editor controls from current widget properties."""
        if self._current_widget:
            self.set_widget(self._current_widget)
