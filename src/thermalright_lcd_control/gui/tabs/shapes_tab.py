# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""
Tab widget for decorative shape elements (borders, separators, backgrounds)
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QCheckBox, QSpinBox, QComboBox, QPushButton, QScrollArea,
    QColorDialog, QGridLayout, QFrame
)
from PySide6.QtGui import QColor


class ShapesTab(QWidget):
    """Tab widget for shape element configuration"""
    
    # Signals for shape changes
    shape_enabled_changed = Signal(str, bool)  # shape_name, enabled
    shape_property_changed = Signal(str, str, object)  # shape_name, property_name, value

    def __init__(self, parent, shape_widgets: dict):
        super().__init__()
        self.parent = parent
        self.shape_widgets = shape_widgets
        
        # Control widgets storage for each shape
        self.shape_checkboxes = {}
        self.shape_type_combos = {}
        self.shape_width_spins = {}
        self.shape_height_spins = {}
        self.shape_rotation_spins = {}
        self.shape_filled_checkboxes = {}
        self.shape_fill_color_btns = {}
        self.shape_fill_alpha_spins = {}
        self.shape_border_color_btns = {}
        self.shape_border_width_spins = {}
        self.shape_corner_radius_spins = {}
        self.shape_corner_radius_labels = {}
        self.shape_arrow_head_spins = {}
        self.shape_arrow_head_labels = {}
        
        # Shape type options
        self.shape_types = [
            ("Rectangle", "rectangle"),
            ("Rounded Rect", "rounded_rectangle"),
            ("Circle", "circle"),
            ("Ellipse", "ellipse"),
            ("Line", "line"),
            ("Triangle", "triangle"),
            ("Arrow", "arrow"),
        ]
        
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)
        
        # Create shape controls for each slot
        for i in range(1, 5):  # 4 shape slots
            shape_name = f"shape{i}"
            shape_group = self._create_shape_group(shape_name, i)
            layout.addWidget(shape_group)
        
        layout.addStretch()
        
        scroll_area.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    def _create_shape_group(self, shape_name: str, index: int) -> QGroupBox:
        """Create a group box with all controls for a single shape"""
        group = QGroupBox(f"Shape {index}")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(8)
        
        # Row 1: Enable checkbox + Shape type
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        
        # Enable checkbox
        checkbox = QCheckBox("Enable")
        checkbox.setChecked(False)
        checkbox.toggled.connect(lambda checked, name=shape_name: self._on_shape_enabled(name, checked))
        self.shape_checkboxes[shape_name] = checkbox
        row1.addWidget(checkbox)
        
        row1.addSpacing(10)
        
        # Shape type
        type_label = QLabel("Type:")
        type_label.setFixedWidth(35)
        row1.addWidget(type_label)
        
        type_combo = QComboBox()
        for display_name, value in self.shape_types:
            type_combo.addItem(display_name, value)
        type_combo.setFixedWidth(110)
        type_combo.currentIndexChanged.connect(
            lambda idx, name=shape_name, combo=type_combo: self._on_type_changed(name, combo.currentData()))
        self.shape_type_combos[shape_name] = type_combo
        row1.addWidget(type_combo)
        
        row1.addStretch()
        layout.addLayout(row1)
        
        # Row 2: Dimensions
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        
        # Width
        width_label = QLabel("Width:")
        width_label.setFixedWidth(40)
        row2.addWidget(width_label)
        
        width_spin = QSpinBox()
        width_spin.setRange(10, 500)
        width_spin.setValue(80)
        width_spin.setFixedWidth(60)
        width_spin.valueChanged.connect(lambda val, name=shape_name: self._on_width_changed(name, val))
        self.shape_width_spins[shape_name] = width_spin
        row2.addWidget(width_spin)
        
        row2.addSpacing(10)
        
        # Height
        height_label = QLabel("Height:")
        height_label.setFixedWidth(45)
        row2.addWidget(height_label)
        
        height_spin = QSpinBox()
        height_spin.setRange(5, 500)
        height_spin.setValue(50)
        height_spin.setFixedWidth(60)
        height_spin.valueChanged.connect(lambda val, name=shape_name: self._on_height_changed(name, val))
        self.shape_height_spins[shape_name] = height_spin
        row2.addWidget(height_spin)
        
        row2.addSpacing(10)
        
        # Rotation
        rotation_label = QLabel("Rotation:")
        rotation_label.setFixedWidth(55)
        row2.addWidget(rotation_label)
        
        rotation_spin = QSpinBox()
        rotation_spin.setRange(0, 359)
        rotation_spin.setValue(0)
        rotation_spin.setSuffix("°")
        rotation_spin.setFixedWidth(65)
        rotation_spin.valueChanged.connect(lambda val, name=shape_name: self._on_rotation_changed(name, val))
        self.shape_rotation_spins[shape_name] = rotation_spin
        row2.addWidget(rotation_spin)
        
        row2.addStretch()
        layout.addLayout(row2)
        
        # Row 3: Fill settings
        row3 = QHBoxLayout()
        row3.setSpacing(8)
        
        # Filled checkbox
        filled_checkbox = QCheckBox("Filled")
        filled_checkbox.setChecked(True)
        filled_checkbox.toggled.connect(lambda checked, name=shape_name: self._on_filled_changed(name, checked))
        self.shape_filled_checkboxes[shape_name] = filled_checkbox
        row3.addWidget(filled_checkbox)
        
        row3.addSpacing(10)
        
        # Fill color
        fill_color_label = QLabel("Fill:")
        fill_color_label.setFixedWidth(25)
        row3.addWidget(fill_color_label)
        
        fill_color_btn = QPushButton()
        fill_color_btn.setFixedSize(30, 24)
        fill_color_btn.setStyleSheet("background-color: rgb(100, 100, 100); border: 1px solid #555;")
        fill_color_btn.clicked.connect(lambda _, name=shape_name: self._on_fill_color_clicked(name))
        self.shape_fill_color_btns[shape_name] = fill_color_btn
        row3.addWidget(fill_color_btn)
        
        row3.addSpacing(5)
        
        # Fill alpha
        alpha_label = QLabel("Alpha:")
        alpha_label.setFixedWidth(40)
        row3.addWidget(alpha_label)
        
        alpha_spin = QSpinBox()
        alpha_spin.setRange(0, 255)
        alpha_spin.setValue(128)
        alpha_spin.setFixedWidth(55)
        alpha_spin.valueChanged.connect(lambda val, name=shape_name: self._on_fill_alpha_changed(name, val))
        self.shape_fill_alpha_spins[shape_name] = alpha_spin
        row3.addWidget(alpha_spin)
        
        row3.addStretch()
        layout.addLayout(row3)
        
        # Row 4: Border settings
        row4 = QHBoxLayout()
        row4.setSpacing(8)
        
        # Border color
        border_color_label = QLabel("Border:")
        border_color_label.setFixedWidth(45)
        row4.addWidget(border_color_label)
        
        border_color_btn = QPushButton()
        border_color_btn.setFixedSize(30, 24)
        border_color_btn.setStyleSheet("background-color: rgb(255, 255, 255); border: 1px solid #555;")
        border_color_btn.clicked.connect(lambda _, name=shape_name: self._on_border_color_clicked(name))
        self.shape_border_color_btns[shape_name] = border_color_btn
        row4.addWidget(border_color_btn)
        
        row4.addSpacing(10)
        
        # Border width
        border_width_label = QLabel("Width:")
        border_width_label.setFixedWidth(40)
        row4.addWidget(border_width_label)
        
        border_width_spin = QSpinBox()
        border_width_spin.setRange(0, 20)
        border_width_spin.setValue(2)
        border_width_spin.setSuffix("px")
        border_width_spin.setFixedWidth(60)
        border_width_spin.valueChanged.connect(lambda val, name=shape_name: self._on_border_width_changed(name, val))
        self.shape_border_width_spins[shape_name] = border_width_spin
        row4.addWidget(border_width_spin)
        
        row4.addStretch()
        layout.addLayout(row4)
        
        # Row 5: Shape-specific settings (Corner radius, Arrow head)
        row5 = QHBoxLayout()
        row5.setSpacing(8)
        
        # Corner radius (for rounded rectangle)
        corner_label = QLabel("Corner Radius:")
        corner_label.setFixedWidth(85)
        self.shape_corner_radius_labels[shape_name] = corner_label
        row5.addWidget(corner_label)
        
        corner_spin = QSpinBox()
        corner_spin.setRange(0, 100)
        corner_spin.setValue(10)
        corner_spin.setSuffix("px")
        corner_spin.setFixedWidth(65)
        corner_spin.valueChanged.connect(lambda val, name=shape_name: self._on_corner_radius_changed(name, val))
        self.shape_corner_radius_spins[shape_name] = corner_spin
        row5.addWidget(corner_spin)
        
        row5.addSpacing(15)
        
        # Arrow head size (for arrow)
        arrow_label = QLabel("Arrow Head:")
        arrow_label.setFixedWidth(75)
        self.shape_arrow_head_labels[shape_name] = arrow_label
        row5.addWidget(arrow_label)
        
        arrow_spin = QSpinBox()
        arrow_spin.setRange(5, 50)
        arrow_spin.setValue(10)
        arrow_spin.setSuffix("px")
        arrow_spin.setFixedWidth(65)
        arrow_spin.valueChanged.connect(lambda val, name=shape_name: self._on_arrow_head_changed(name, val))
        self.shape_arrow_head_spins[shape_name] = arrow_spin
        row5.addWidget(arrow_spin)
        
        row5.addStretch()
        layout.addLayout(row5)
        
        # Initially hide conditional controls
        self._update_conditional_controls(shape_name, "rectangle")
        
        return group

    def _update_conditional_controls(self, shape_name: str, shape_type: str):
        """Show/hide controls based on shape type"""
        # Corner radius: only for rounded_rectangle
        show_corner = shape_type == "rounded_rectangle"
        self.shape_corner_radius_labels[shape_name].setVisible(show_corner)
        self.shape_corner_radius_spins[shape_name].setVisible(show_corner)
        
        # Arrow head: only for arrow
        show_arrow = shape_type == "arrow"
        self.shape_arrow_head_labels[shape_name].setVisible(show_arrow)
        self.shape_arrow_head_spins[shape_name].setVisible(show_arrow)
        
        # Filled checkbox: hide for line and arrow (they don't have fill)
        show_filled = shape_type not in ["line", "arrow"]
        self.shape_filled_checkboxes[shape_name].setVisible(show_filled)
        self.shape_fill_color_btns[shape_name].setVisible(show_filled)
        self.shape_fill_alpha_spins[shape_name].setVisible(show_filled)
        # Also hide the labels - find them by looking at parent layout
        # For simplicity, we'll just disable instead
        self.shape_filled_checkboxes[shape_name].setEnabled(show_filled)

    # Signal handlers
    def _on_shape_enabled(self, shape_name: str, enabled: bool):
        """Handle shape enable/disable"""
        if shape_name in self.shape_widgets:
            self.shape_widgets[shape_name].set_enabled(enabled)
        self.shape_enabled_changed.emit(shape_name, enabled)
        if hasattr(self.parent, 'update_preview_widget_configs'):
            self.parent.update_preview_widget_configs()

    def _on_type_changed(self, shape_name: str, shape_type: str):
        """Handle shape type change"""
        if shape_name in self.shape_widgets:
            self.shape_widgets[shape_name].set_shape_type(shape_type)
        self._update_conditional_controls(shape_name, shape_type)
        self.shape_property_changed.emit(shape_name, "shape_type", shape_type)
        if hasattr(self.parent, 'update_preview_widget_configs'):
            self.parent.update_preview_widget_configs()

    def _on_width_changed(self, shape_name: str, value: int):
        """Handle width change"""
        if shape_name in self.shape_widgets:
            self.shape_widgets[shape_name].set_width(value)
        self.shape_property_changed.emit(shape_name, "width", value)
        if hasattr(self.parent, 'update_preview_widget_configs'):
            self.parent.update_preview_widget_configs()

    def _on_height_changed(self, shape_name: str, value: int):
        """Handle height change"""
        if shape_name in self.shape_widgets:
            self.shape_widgets[shape_name].set_height(value)
        self.shape_property_changed.emit(shape_name, "height", value)
        if hasattr(self.parent, 'update_preview_widget_configs'):
            self.parent.update_preview_widget_configs()

    def _on_rotation_changed(self, shape_name: str, value: int):
        """Handle rotation change"""
        if shape_name in self.shape_widgets:
            self.shape_widgets[shape_name].set_rotation(value)
        self.shape_property_changed.emit(shape_name, "rotation", value)
        if hasattr(self.parent, 'update_preview_widget_configs'):
            self.parent.update_preview_widget_configs()

    def _on_filled_changed(self, shape_name: str, filled: bool):
        """Handle filled checkbox change"""
        if shape_name in self.shape_widgets:
            self.shape_widgets[shape_name].set_filled(filled)
        # Update fill controls visibility
        self.shape_fill_color_btns[shape_name].setEnabled(filled)
        self.shape_fill_alpha_spins[shape_name].setEnabled(filled)
        self.shape_property_changed.emit(shape_name, "filled", filled)
        if hasattr(self.parent, 'update_preview_widget_configs'):
            self.parent.update_preview_widget_configs()

    def _on_fill_color_clicked(self, shape_name: str):
        """Handle fill color button click"""
        current_color = self.shape_widgets[shape_name].get_fill_color() if shape_name in self.shape_widgets else QColor(100, 100, 100)
        color = QColorDialog.getColor(current_color, self, "Select Fill Color", QColorDialog.ShowAlphaChannel)
        if color.isValid():
            if shape_name in self.shape_widgets:
                self.shape_widgets[shape_name].set_fill_color(color)
            # Update button style
            self.shape_fill_color_btns[shape_name].setStyleSheet(
                f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); border: 1px solid #555;")
            # Update alpha spin
            self.shape_fill_alpha_spins[shape_name].setValue(color.alpha())
            self.shape_property_changed.emit(shape_name, "fill_color", color)
            if hasattr(self.parent, 'update_preview_widget_configs'):
                self.parent.update_preview_widget_configs()

    def _on_fill_alpha_changed(self, shape_name: str, value: int):
        """Handle fill alpha change"""
        if shape_name in self.shape_widgets:
            current_color = self.shape_widgets[shape_name].get_fill_color()
            current_color.setAlpha(value)
            self.shape_widgets[shape_name].set_fill_color(current_color)
        self.shape_property_changed.emit(shape_name, "fill_alpha", value)
        if hasattr(self.parent, 'update_preview_widget_configs'):
            self.parent.update_preview_widget_configs()

    def _on_border_color_clicked(self, shape_name: str):
        """Handle border color button click"""
        current_color = self.shape_widgets[shape_name].get_border_color() if shape_name in self.shape_widgets else QColor(255, 255, 255)
        color = QColorDialog.getColor(current_color, self, "Select Border Color")
        if color.isValid():
            if shape_name in self.shape_widgets:
                self.shape_widgets[shape_name].set_border_color(color)
            self.shape_border_color_btns[shape_name].setStyleSheet(
                f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); border: 1px solid #555;")
            self.shape_property_changed.emit(shape_name, "border_color", color)
            if hasattr(self.parent, 'update_preview_widget_configs'):
                self.parent.update_preview_widget_configs()

    def _on_border_width_changed(self, shape_name: str, value: int):
        """Handle border width change"""
        if shape_name in self.shape_widgets:
            self.shape_widgets[shape_name].set_border_width(value)
        self.shape_property_changed.emit(shape_name, "border_width", value)
        if hasattr(self.parent, 'update_preview_widget_configs'):
            self.parent.update_preview_widget_configs()

    def _on_corner_radius_changed(self, shape_name: str, value: int):
        """Handle corner radius change"""
        if shape_name in self.shape_widgets:
            self.shape_widgets[shape_name].set_corner_radius(value)
        self.shape_property_changed.emit(shape_name, "corner_radius", value)
        if hasattr(self.parent, 'update_preview_widget_configs'):
            self.parent.update_preview_widget_configs()

    def _on_arrow_head_changed(self, shape_name: str, value: int):
        """Handle arrow head size change"""
        if shape_name in self.shape_widgets:
            self.shape_widgets[shape_name].set_arrow_head_size(value)
        self.shape_property_changed.emit(shape_name, "arrow_head_size", value)
        if hasattr(self.parent, 'update_preview_widget_configs'):
            self.parent.update_preview_widget_configs()

    # Public methods for external updates
    def set_shape_enabled(self, shape_name: str, enabled: bool):
        """Set shape enabled state from external source"""
        if shape_name in self.shape_checkboxes:
            self.shape_checkboxes[shape_name].blockSignals(True)
            self.shape_checkboxes[shape_name].setChecked(enabled)
            self.shape_checkboxes[shape_name].blockSignals(False)

    def update_from_widget(self, shape_name: str):
        """Update tab controls from widget state"""
        if shape_name not in self.shape_widgets:
            return
        
        widget = self.shape_widgets[shape_name]
        
        # Block signals during update
        for control_dict in [self.shape_checkboxes, self.shape_type_combos, 
                            self.shape_width_spins, self.shape_height_spins,
                            self.shape_rotation_spins, self.shape_filled_checkboxes,
                            self.shape_fill_alpha_spins, self.shape_border_width_spins,
                            self.shape_corner_radius_spins, self.shape_arrow_head_spins]:
            if shape_name in control_dict:
                control_dict[shape_name].blockSignals(True)
        
        # Update controls
        if shape_name in self.shape_checkboxes:
            self.shape_checkboxes[shape_name].setChecked(widget.enabled)
        
        if shape_name in self.shape_type_combos:
            combo = self.shape_type_combos[shape_name]
            index = combo.findData(widget.get_shape_type())
            if index >= 0:
                combo.setCurrentIndex(index)
            self._update_conditional_controls(shape_name, widget.get_shape_type())
        
        if shape_name in self.shape_width_spins:
            self.shape_width_spins[shape_name].setValue(widget.get_width())
        
        if shape_name in self.shape_height_spins:
            self.shape_height_spins[shape_name].setValue(widget.get_height())
        
        if shape_name in self.shape_rotation_spins:
            self.shape_rotation_spins[shape_name].setValue(widget.get_rotation())
        
        if shape_name in self.shape_filled_checkboxes:
            self.shape_filled_checkboxes[shape_name].setChecked(widget.get_filled())
        
        if shape_name in self.shape_fill_color_btns:
            color = widget.get_fill_color()
            self.shape_fill_color_btns[shape_name].setStyleSheet(
                f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); border: 1px solid #555;")
        
        if shape_name in self.shape_fill_alpha_spins:
            self.shape_fill_alpha_spins[shape_name].setValue(widget.get_fill_color().alpha())
        
        if shape_name in self.shape_border_color_btns:
            color = widget.get_border_color()
            self.shape_border_color_btns[shape_name].setStyleSheet(
                f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); border: 1px solid #555;")
        
        if shape_name in self.shape_border_width_spins:
            self.shape_border_width_spins[shape_name].setValue(widget.get_border_width())
        
        if shape_name in self.shape_corner_radius_spins:
            self.shape_corner_radius_spins[shape_name].setValue(widget.get_corner_radius())
        
        if shape_name in self.shape_arrow_head_spins:
            self.shape_arrow_head_spins[shape_name].setValue(widget.get_arrow_head_size())
        
        # Unblock signals
        for control_dict in [self.shape_checkboxes, self.shape_type_combos,
                            self.shape_width_spins, self.shape_height_spins,
                            self.shape_rotation_spins, self.shape_filled_checkboxes,
                            self.shape_fill_alpha_spins, self.shape_border_width_spins,
                            self.shape_corner_radius_spins, self.shape_arrow_head_spins]:
            if shape_name in control_dict:
                control_dict[shape_name].blockSignals(False)
