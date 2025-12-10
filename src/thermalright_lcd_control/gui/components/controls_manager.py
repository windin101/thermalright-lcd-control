# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Controls manager for UI composition controls"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QLabel, QLineEdit, QPushButton,
                               QSpinBox, QDoubleSpinBox, QCheckBox, QApplication, QComboBox,
                               QColorDialog, QFontComboBox, QFrame)
from PySide6.QtWidgets import QSlider

from thermalright_lcd_control.gui.widgets.draggable_widget import TextStyleConfig


class ControlsManager:
    """Manages all UI controls for composition"""

    def __init__(self, parent, text_style: TextStyleConfig, metric_widgets: dict):
        self.parent = parent
        self.text_style = text_style
        self.metric_widgets = metric_widgets

        # Control widgets
        self.opacity_input = None
        self.opacity_value_label = None
        self.rotation_combo = None
        self.font_combo = None
        self.font_size_spin = None
        self.color_btn = None
        self.show_date_checkbox = None
        self.show_time_checkbox = None
        self.date_font_size_spin = None
        self.time_font_size_spin = None
        self.metric_checkboxes = {}
        self.metric_label_inputs = {}
        self.metric_unit_inputs = {}
        self.metric_label_position_combos = {}  # New: label position dropdowns
        self.metric_font_size_spins = {}  # New: individual font size spinboxes
        self.metric_label_font_size_spins = {}  # New: label font size spinboxes
        self.metric_freq_format_combos = {}  # Frequency format (MHz/GHz) dropdowns
        
        # Free text widget controls
        self.text_checkboxes = {}
        self.text_inputs = {}
        self.text_font_size_spins = {}
        
        # Bar graph widget controls
        self.bar_checkboxes = {}
        self.bar_metric_combos = {}
        self.bar_orientation_combos = {}
        self.bar_width_spins = {}
        self.bar_height_spins = {}
        self.bar_fill_color_btns = {}
        self.bar_bg_color_btns = {}
        self.bar_border_color_btns = {}
        self.bar_corner_radius_spins = {}
        
        # Background scaling control
        self.background_enabled_checkbox = None
        self.background_scale_combo = None
        self.background_color_btn = None
        self.background_color = (0, 0, 0)  # Default black
        
        # Foreground controls
        self.foreground_enabled_checkbox = None
        self.foreground_x_spin = None
        self.foreground_y_spin = None
        
        # Widget position labels
        self.date_position_label = None
        self.time_position_label = None
        self.metric_position_labels = {}

    def create_controls_widget(self) -> QScrollArea:
        """Create and return the controls widget"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        controls_container = QWidget()
        controls_container.setStyleSheet("""
            QWidget { background: transparent; }
            QComboBox { 
                background-color: #ffffff; 
                color: #000000; 
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 2px 5px;
            }
            QComboBox:hover {
                border: 1px solid #3498db;
            }
            QComboBox::drop-down {
                background-color: #ecf0f1;
            }
            QComboBox QAbstractItemView { 
                background-color: #ffffff; 
                color: #000000; 
                selection-background-color: #3498db;
                selection-color: #ffffff;
                border: 1px solid #bdc3c7;
            }
        """)
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 4, 0)
        controls_layout.setSpacing(6)

        # Add all control sections (action buttons are separate, not in scroll area)
        # Rotation and Snap to Grid side by side
        rotation_snap_container = QWidget()
        rotation_snap_container.setStyleSheet("QWidget { background: transparent; }")
        rotation_snap_layout = QHBoxLayout(rotation_snap_container)
        rotation_snap_layout.setContentsMargins(0, 0, 0, 0)
        rotation_snap_layout.setSpacing(6)
        rotation_snap_layout.addWidget(self._create_rotation_controls())
        rotation_snap_layout.addWidget(self._create_snap_to_grid_controls())
        controls_layout.addWidget(rotation_snap_container)
        
        # Background and Foreground side by side
        bg_fg_container = QWidget()
        bg_fg_container.setStyleSheet("QWidget { background: transparent; }")
        bg_fg_layout = QHBoxLayout(bg_fg_container)
        bg_fg_layout.setContentsMargins(0, 0, 0, 0)
        bg_fg_layout.setSpacing(6)
        bg_fg_layout.addWidget(self._create_background_controls())
        bg_fg_layout.addWidget(self._create_foreground_controls())
        controls_layout.addWidget(bg_fg_container)
        
        controls_layout.addWidget(self._create_text_style_controls())
        controls_layout.addWidget(self._create_overlay_controls())
        controls_layout.addStretch()

        scroll_area.setWidget(controls_container)
        return scroll_area

    def _create_rotation_controls(self) -> QGroupBox:
        """Create rotation controls"""
        rotation_group = QGroupBox("Display Rotation")
        rotation_layout = QHBoxLayout(rotation_group)

        rotation_label = QLabel("Rotation:")
        rotation_layout.addWidget(rotation_label, alignment=Qt.AlignVCenter)

        self.rotation_combo = QComboBox()
        self.rotation_combo.addItem("0°", 0)
        self.rotation_combo.addItem("90°", 90)
        self.rotation_combo.addItem("180°", 180)
        self.rotation_combo.addItem("270°", 270)
        self.rotation_combo.setCurrentIndex(0)  # Default to 0°
        self.rotation_combo.currentIndexChanged.connect(self._on_rotation_changed)

        rotation_layout.addWidget(self.rotation_combo, alignment=Qt.AlignVCenter)
        rotation_layout.addStretch()

        return rotation_group

    def _on_rotation_changed(self, index):
        """Handle rotation combo box change"""
        rotation_value = self.rotation_combo.itemData(index)
        if hasattr(self.parent, 'on_rotation_changed'):
            self.parent.on_rotation_changed(rotation_value)

    def _create_snap_to_grid_controls(self) -> QGroupBox:
        """Create snap-to-grid controls"""
        from thermalright_lcd_control.gui.widgets.draggable_widget import DraggableWidget
        
        snap_group = QGroupBox("Snap to Grid")
        snap_layout = QHBoxLayout(snap_group)

        # Enable checkbox
        self.snap_to_grid_checkbox = QCheckBox("Enable")
        self.snap_to_grid_checkbox.setChecked(DraggableWidget.get_snap_to_grid())
        self.snap_to_grid_checkbox.toggled.connect(self._on_snap_to_grid_changed)
        snap_layout.addWidget(self.snap_to_grid_checkbox, alignment=Qt.AlignVCenter)

        snap_layout.addSpacing(15)

        # Grid size
        grid_size_label = QLabel("Grid Size:")
        snap_layout.addWidget(grid_size_label, alignment=Qt.AlignVCenter)
        self.grid_size_spin = QSpinBox()
        self.grid_size_spin.setRange(5, 50)
        self.grid_size_spin.setValue(DraggableWidget.get_grid_size())
        self.grid_size_spin.setSuffix(" px")
        self.grid_size_spin.setFixedWidth(60)
        self.grid_size_spin.valueChanged.connect(self._on_grid_size_changed)
        snap_layout.addWidget(self.grid_size_spin, alignment=Qt.AlignVCenter)

        snap_layout.addStretch()

        return snap_group

    def _on_snap_to_grid_changed(self, enabled):
        """Handle snap-to-grid checkbox change"""
        from thermalright_lcd_control.gui.widgets.draggable_widget import DraggableWidget
        DraggableWidget.set_snap_to_grid(enabled)
        # Notify parent to update grid overlay
        if hasattr(self.parent, 'on_snap_to_grid_changed'):
            self.parent.on_snap_to_grid_changed(enabled)

    def _on_grid_size_changed(self, size):
        """Handle grid size change"""
        from thermalright_lcd_control.gui.widgets.draggable_widget import DraggableWidget
        DraggableWidget.set_grid_size(size)
        # Notify parent to update grid overlay
        if hasattr(self.parent, 'on_grid_size_changed'):
            self.parent.on_grid_size_changed(size)

    def _on_refresh_interval_changed(self, value):
        """Handle refresh interval change"""
        if hasattr(self.parent, 'on_refresh_interval_changed'):
            self.parent.on_refresh_interval_changed(value)

    def _create_background_controls(self) -> QGroupBox:
        """Create background image controls"""
        background_group = QGroupBox("Background Image")
        background_layout = QVBoxLayout(background_group)
        background_layout.setSpacing(6)

        # Row 1: Enabled checkbox
        enabled_layout = QHBoxLayout()
        enabled_layout.setContentsMargins(0, 0, 0, 0)
        self.background_enabled_checkbox = QCheckBox("Show Background")
        self.background_enabled_checkbox.setChecked(True)
        self.background_enabled_checkbox.toggled.connect(self._on_background_enabled_changed)
        enabled_layout.addWidget(self.background_enabled_checkbox, alignment=Qt.AlignVCenter)
        enabled_layout.addStretch()
        background_layout.addLayout(enabled_layout)

        # Row 2: Opacity label and value
        opacity_layout = QHBoxLayout()
        opacity_layout.setContentsMargins(0, 0, 0, 0)
        opacity_label = QLabel("Opacity:")
        opacity_label.setFixedWidth(55)
        opacity_layout.addWidget(opacity_label, alignment=Qt.AlignVCenter)
        
        self.background_opacity_value_label = QLabel("100%")
        self.background_opacity_value_label.setFixedWidth(35)
        opacity_layout.addWidget(self.background_opacity_value_label, alignment=Qt.AlignVCenter)
        opacity_layout.addStretch()
        background_layout.addLayout(opacity_layout)

        # Row 3: Opacity slider
        self.background_opacity_slider = QSlider(Qt.Horizontal)
        self.background_opacity_slider.setRange(0, 100)
        self.background_opacity_slider.setValue(100)
        self.background_opacity_slider.setTickPosition(QSlider.TicksBelow)
        self.background_opacity_slider.setTickInterval(10)
        self.background_opacity_slider.valueChanged.connect(self._on_background_opacity_changed)
        background_layout.addWidget(self.background_opacity_slider)

        # Row 4: Scaling and Colour
        scale_color_layout = QHBoxLayout()
        scale_color_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scaling controls
        scaling_label = QLabel("Scaling:")
        scaling_label.setFixedWidth(55)
        scale_color_layout.addWidget(scaling_label, alignment=Qt.AlignVCenter)
        self.background_scale_combo = QComboBox()
        self.background_scale_combo.addItem("Stretch", "stretch")
        self.background_scale_combo.addItem("Scaled (Fit)", "scaled_fit")
        self.background_scale_combo.addItem("Scaled (Fill)", "scaled_fill")
        self.background_scale_combo.addItem("Centered", "centered")
        self.background_scale_combo.addItem("Tiled", "tiled")
        self.background_scale_combo.setCurrentIndex(0)
        self.background_scale_combo.currentIndexChanged.connect(self._on_background_scale_changed)
        self.background_scale_combo.setFixedWidth(100)
        self.background_scale_combo.setStyleSheet("""
            QComboBox { 
                background-color: #ffffff; 
                color: #000000; 
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 2px 5px;
            }
            QComboBox:hover {
                border: 1px solid #3498db;
            }
            QComboBox::drop-down {
                background-color: #ecf0f1;
            }
            QComboBox QAbstractItemView { 
                background-color: #ffffff; 
                color: #000000; 
                selection-background-color: #3498db;
                selection-color: #ffffff;
                border: 1px solid #bdc3c7;
            }
        """)
        scale_color_layout.addWidget(self.background_scale_combo, alignment=Qt.AlignVCenter)

        scale_color_layout.addSpacing(15)

        # Background colour picker
        colour_label = QLabel("Colour:")
        scale_color_layout.addWidget(colour_label, alignment=Qt.AlignVCenter)
        self.background_color_btn = QPushButton()
        self.background_color_btn.setFixedWidth(60)
        self._update_background_color_button()
        self.background_color_btn.clicked.connect(self._on_background_color_clicked)
        self.background_color_btn.setToolTip("Background color when image is hidden")
        scale_color_layout.addWidget(self.background_color_btn, alignment=Qt.AlignVCenter)
        
        scale_color_layout.addStretch()
        background_layout.addLayout(scale_color_layout)

        return background_group

    def _on_background_opacity_changed(self, value):
        """Handle background opacity slider change"""
        self.background_opacity_value_label.setText(f"{value}%")
        if hasattr(self.parent, 'on_background_opacity_changed'):
            self.parent.on_background_opacity_changed(value)

    def _on_background_enabled_changed(self, enabled):
        """Handle background enabled checkbox change - use opacity 0% to hide"""
        if enabled:
            # Restore the previous opacity value
            if hasattr(self, '_saved_opacity'):
                self.background_opacity_slider.setValue(self._saved_opacity)
            else:
                self.background_opacity_slider.setValue(100)
            self.background_opacity_slider.setEnabled(True)
        else:
            # Save current opacity and set to 0%
            self._saved_opacity = self.background_opacity_slider.value()
            self.background_opacity_slider.setValue(0)
            self.background_opacity_slider.setEnabled(False)

    def _on_background_color_clicked(self):
        """Handle background color button click"""
        current_color = QColor(*self.background_color)
        color = QColorDialog.getColor(current_color, self.parent, "Select Background Colour")
        if color.isValid():
            self.background_color = (color.red(), color.green(), color.blue())
            self._update_background_color_button()
            if hasattr(self.parent, 'on_background_color_changed'):
                self.parent.on_background_color_changed(self.background_color)

    def _update_background_color_button(self):
        """Update the background color button appearance"""
        r, g, b = self.background_color
        self.background_color_btn.setStyleSheet(
            f"background-color: rgb({r}, {g}, {b}); border: 1px solid #bdc3c7; border-radius: 6px; padding: 5px;"
        )

    def set_background_color(self, color: tuple):
        """Set the background color (r, g, b)"""
        self.background_color = color
        self._update_background_color_button()

    def _on_background_scale_changed(self, index):
        """Handle background scale combo box change"""
        scale_mode = self.background_scale_combo.itemData(index)
        if hasattr(self.parent, 'on_background_scale_changed'):
            self.parent.on_background_scale_changed(scale_mode)

    def _create_foreground_controls(self) -> QGroupBox:
        """Create foreground controls (opacity and position)"""
        foreground_group = QGroupBox("Foreground Image")
        foreground_layout = QVBoxLayout(foreground_group)
        foreground_layout.setSpacing(6)

        # Row 1: Enabled checkbox
        enabled_layout = QHBoxLayout()
        enabled_layout.setContentsMargins(0, 0, 0, 0)
        self.foreground_enabled_checkbox = QCheckBox("Show Foreground")
        self.foreground_enabled_checkbox.setChecked(True)
        self.foreground_enabled_checkbox.toggled.connect(self._on_foreground_enabled_changed)
        enabled_layout.addWidget(self.foreground_enabled_checkbox, alignment=Qt.AlignVCenter)
        enabled_layout.addStretch()
        foreground_layout.addLayout(enabled_layout)

        # Row 2: Opacity label and value
        opacity_layout = QHBoxLayout()
        opacity_layout.setContentsMargins(0, 0, 0, 0)
        opacity_label = QLabel("Opacity:")
        opacity_label.setFixedWidth(55)
        opacity_layout.addWidget(opacity_label, alignment=Qt.AlignVCenter)
        
        self.opacity_value_label = QLabel("50%")
        self.opacity_value_label.setFixedWidth(35)
        opacity_layout.addWidget(self.opacity_value_label, alignment=Qt.AlignVCenter)
        opacity_layout.addStretch()

        self.opacity_input = QSlider(Qt.Horizontal)
        self.opacity_input.setRange(0, 100)
        self.opacity_input.setValue(50)
        self.opacity_input.setTickPosition(QSlider.TicksBelow)
        self.opacity_input.setTickInterval(10)
        self.opacity_input.valueChanged.connect(self._on_opacity_slider_changed)
        self.opacity_input.sliderReleased.connect(self.parent.on_opacity_editing_finished)

        foreground_layout.addLayout(opacity_layout)
        foreground_layout.addWidget(self.opacity_input)

        # Row 4: Position controls
        position_layout = QHBoxLayout()
        position_layout.setContentsMargins(0, 0, 0, 0)
        position_label = QLabel("Position:")
        position_label.setFixedWidth(55)
        position_layout.addWidget(position_label, alignment=Qt.AlignVCenter)
        
        x_label = QLabel("X:")
        position_layout.addWidget(x_label, alignment=Qt.AlignVCenter)
        self.foreground_x_spin = QSpinBox()
        self.foreground_x_spin.setRange(-500, 500)
        self.foreground_x_spin.setValue(0)
        self.foreground_x_spin.setFixedWidth(60)
        self.foreground_x_spin.valueChanged.connect(self._on_foreground_position_changed)
        position_layout.addWidget(self.foreground_x_spin, alignment=Qt.AlignVCenter)
        
        position_layout.addSpacing(15)
        
        y_label = QLabel("Y:")
        position_layout.addWidget(y_label, alignment=Qt.AlignVCenter)
        self.foreground_y_spin = QSpinBox()
        self.foreground_y_spin.setRange(-500, 500)
        self.foreground_y_spin.setValue(0)
        self.foreground_y_spin.setFixedWidth(60)
        self.foreground_y_spin.valueChanged.connect(self._on_foreground_position_changed)
        position_layout.addWidget(self.foreground_y_spin, alignment=Qt.AlignVCenter)
        
        position_layout.addStretch()
        foreground_layout.addLayout(position_layout)

        return foreground_group

    def _on_foreground_position_changed(self):
        """Handle foreground position change"""
        x = self.foreground_x_spin.value()
        y = self.foreground_y_spin.value()
        if hasattr(self.parent, 'on_foreground_position_changed'):
            self.parent.on_foreground_position_changed(x, y)

    def _on_foreground_enabled_changed(self, enabled):
        """Handle foreground enabled checkbox change"""
        if hasattr(self.parent, 'on_foreground_enabled_changed'):
            self.parent.on_foreground_enabled_changed(enabled)

    def _on_opacity_slider_changed(self, value):
        """Handle slider value change"""
        self.opacity_value_label.setText(f"{value}%")
        self.parent.on_opacity_text_changed(str(value))


    def _create_text_style_controls(self) -> QGroupBox:
        """Create text style controls"""
        style_group = QGroupBox("Text Style")
        style_layout = QVBoxLayout(style_group)

        # Font, Size, and Colour all on one row
        font_row_layout = QHBoxLayout()
        font_row_layout.setSpacing(6)
        
        # Font family selector
        font_label = QLabel("Font:")
        font_row_layout.addWidget(font_label, alignment=Qt.AlignVCenter)
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(self.text_style.font_family)
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        font_row_layout.addWidget(self.font_combo, alignment=Qt.AlignVCenter)
        
        font_row_layout.addSpacing(15)
        
        # Font size
        size_label = QLabel("Size:")
        font_row_layout.addWidget(size_label, alignment=Qt.AlignVCenter)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(self.text_style.font_size)
        self.font_size_spin.setFixedWidth(60)
        self.font_size_spin.valueChanged.connect(self.parent.on_font_size_changed)
        font_row_layout.addWidget(self.font_size_spin, alignment=Qt.AlignVCenter)
        
        font_row_layout.addSpacing(15)

        # Colour
        colour_label = QLabel("Colour:")
        font_row_layout.addWidget(colour_label, alignment=Qt.AlignVCenter)
        self.color_btn = QPushButton()
        self.color_btn.setFixedWidth(60)
        self.color_btn.clicked.connect(self.parent.choose_color)
        self.update_color_button()
        font_row_layout.addWidget(self.color_btn, alignment=Qt.AlignVCenter)
        
        font_row_layout.addStretch()
        style_layout.addLayout(font_row_layout)

        # Text effects row - Shadow, Outline, Gradient all on one line
        effects_row = QHBoxLayout()
        effects_row.setSpacing(6)
        
        # Shadow controls
        shadow_label = QLabel("Shadow:")
        effects_row.addWidget(shadow_label, alignment=Qt.AlignVCenter)
        self.shadow_enabled_checkbox = QCheckBox()
        self.shadow_enabled_checkbox.setChecked(self.text_style.shadow_enabled)
        self.shadow_enabled_checkbox.toggled.connect(self.parent.on_shadow_enabled_changed)
        effects_row.addWidget(self.shadow_enabled_checkbox, alignment=Qt.AlignVCenter)
        self.shadow_color_btn = QPushButton()
        self.shadow_color_btn.setFixedWidth(60)
        self.shadow_color_btn.clicked.connect(self.parent.choose_shadow_color)
        self._update_shadow_color_button()
        effects_row.addWidget(self.shadow_color_btn, alignment=Qt.AlignVCenter)
        shadow_x_label = QLabel("X:")
        effects_row.addWidget(shadow_x_label, alignment=Qt.AlignVCenter)
        self.shadow_x_spin = QSpinBox()
        self.shadow_x_spin.setRange(-20, 20)
        self.shadow_x_spin.setValue(self.text_style.shadow_offset_x)
        self.shadow_x_spin.setFixedWidth(60)
        self.shadow_x_spin.valueChanged.connect(self.parent.on_shadow_offset_x_changed)
        effects_row.addWidget(self.shadow_x_spin, alignment=Qt.AlignVCenter)
        shadow_y_label = QLabel("Y:")
        effects_row.addWidget(shadow_y_label, alignment=Qt.AlignVCenter)
        self.shadow_y_spin = QSpinBox()
        self.shadow_y_spin.setRange(-20, 20)
        self.shadow_y_spin.setValue(self.text_style.shadow_offset_y)
        self.shadow_y_spin.setFixedWidth(60)
        self.shadow_y_spin.valueChanged.connect(self.parent.on_shadow_offset_y_changed)
        effects_row.addWidget(self.shadow_y_spin, alignment=Qt.AlignVCenter)
        blur_label = QLabel("Blur:")
        effects_row.addWidget(blur_label, alignment=Qt.AlignVCenter)
        self.shadow_blur_spin = QSpinBox()
        self.shadow_blur_spin.setRange(0, 20)
        self.shadow_blur_spin.setValue(self.text_style.shadow_blur)
        self.shadow_blur_spin.setFixedWidth(60)
        self.shadow_blur_spin.valueChanged.connect(self.parent.on_shadow_blur_changed)
        effects_row.addWidget(self.shadow_blur_spin, alignment=Qt.AlignVCenter)
        
        effects_row.addSpacing(15)
        
        # Outline controls
        outline_label = QLabel("Outline:")
        effects_row.addWidget(outline_label, alignment=Qt.AlignVCenter)
        self.outline_enabled_checkbox = QCheckBox()
        self.outline_enabled_checkbox.setChecked(self.text_style.outline_enabled)
        self.outline_enabled_checkbox.toggled.connect(self.parent.on_outline_enabled_changed)
        effects_row.addWidget(self.outline_enabled_checkbox, alignment=Qt.AlignVCenter)
        self.outline_color_btn = QPushButton()
        self.outline_color_btn.setFixedWidth(60)
        self.outline_color_btn.clicked.connect(self.parent.choose_outline_color)
        self._update_outline_color_button()
        effects_row.addWidget(self.outline_color_btn, alignment=Qt.AlignVCenter)
        outline_w_label = QLabel("W:")
        effects_row.addWidget(outline_w_label, alignment=Qt.AlignVCenter)
        self.outline_width_spin = QSpinBox()
        self.outline_width_spin.setRange(1, 10)
        self.outline_width_spin.setValue(self.text_style.outline_width)
        self.outline_width_spin.setFixedWidth(60)
        self.outline_width_spin.valueChanged.connect(self.parent.on_outline_width_changed)
        effects_row.addWidget(self.outline_width_spin, alignment=Qt.AlignVCenter)
        
        effects_row.addSpacing(15)
        
        # Gradient controls
        gradient_label = QLabel("Gradient:")
        effects_row.addWidget(gradient_label, alignment=Qt.AlignVCenter)
        self.gradient_enabled_checkbox = QCheckBox()
        self.gradient_enabled_checkbox.setChecked(self.text_style.gradient_enabled)
        self.gradient_enabled_checkbox.toggled.connect(self.parent.on_gradient_enabled_changed)
        effects_row.addWidget(self.gradient_enabled_checkbox, alignment=Qt.AlignVCenter)
        self.gradient_color1_btn = QPushButton()
        self.gradient_color1_btn.setFixedWidth(60)
        self.gradient_color1_btn.clicked.connect(self.parent.choose_gradient_color1)
        self._update_gradient_color1_button()
        effects_row.addWidget(self.gradient_color1_btn, alignment=Qt.AlignVCenter)
        self.gradient_color2_btn = QPushButton()
        self.gradient_color2_btn.setFixedWidth(60)
        self.gradient_color2_btn.clicked.connect(self.parent.choose_gradient_color2)
        self._update_gradient_color2_button()
        effects_row.addWidget(self.gradient_color2_btn, alignment=Qt.AlignVCenter)
        self.gradient_direction_combo = QComboBox()
        self.gradient_direction_combo.addItem("V", "vertical")
        self.gradient_direction_combo.addItem("H", "horizontal")
        self.gradient_direction_combo.addItem("D", "diagonal")
        self.gradient_direction_combo.setFixedWidth(100)
        self.gradient_direction_combo.currentIndexChanged.connect(
            lambda: self.parent.on_gradient_direction_changed(self.gradient_direction_combo.currentData()))
        effects_row.addWidget(self.gradient_direction_combo, alignment=Qt.AlignVCenter)
        
        effects_row.addStretch()
        style_layout.addLayout(effects_row)

        return style_group

    def _update_shadow_color_button(self):
        """Update shadow color button appearance"""
        color = self.text_style.shadow_color
        self.shadow_color_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {color.name()}; border: 1px solid #bdc3c7; 
                          border-radius: 6px; padding: 5px; }}
        """)

    def _update_outline_color_button(self):
        """Update outline color button appearance"""
        color = self.text_style.outline_color
        self.outline_color_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {color.name()}; border: 1px solid #bdc3c7; 
                          border-radius: 6px; padding: 5px; }}
        """)

    def _update_gradient_color1_button(self):
        """Update gradient color 1 button appearance"""
        color = self.text_style.gradient_color1
        self.gradient_color1_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {color.name()}; border: 1px solid #bdc3c7; 
                          border-radius: 6px; padding: 5px; }}
        """)

    def _update_gradient_color2_button(self):
        """Update gradient color 2 button appearance"""
        color = self.text_style.gradient_color2
        self.gradient_color2_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {color.name()}; border: 1px solid #bdc3c7; 
                          border-radius: 6px; padding: 5px; }}
        """)

    def _on_font_changed(self, font):
        """Handle font family change"""
        font_family = font.family()
        if hasattr(self.parent, 'on_font_family_changed'):
            self.parent.on_font_family_changed(font_family)

    def _create_overlay_controls(self) -> QGroupBox:
        """Create overlay widget controls"""
        overlay_group = QGroupBox("Overlay Widgets")
        overlay_layout = QVBoxLayout(overlay_group)

        # Time and Date section (grouped)
        datetime_group = QGroupBox("Time and Date")
        datetime_group_layout = QVBoxLayout(datetime_group)
        datetime_group_layout.setContentsMargins(4, 8, 4, 4)
        datetime_group_layout.setSpacing(6)
        
        # Date row
        date_layout = QHBoxLayout()
        date_layout.setSpacing(6)
        
        # Date controls - label before checkbox
        date_layout.addWidget(QLabel("Date:"), alignment=Qt.AlignVCenter)
        self.show_date_checkbox = QCheckBox()
        self.show_date_checkbox.setChecked(True)
        self.show_date_checkbox.toggled.connect(self.parent.on_show_date_changed)
        date_layout.addWidget(self.show_date_checkbox, alignment=Qt.AlignVCenter)
        
        date_layout.addWidget(QLabel("Size:"), alignment=Qt.AlignVCenter)
        self.date_font_size_spin = QSpinBox()
        self.date_font_size_spin.setRange(8, 72)
        self.date_font_size_spin.setValue(18)
        self.date_font_size_spin.setFixedWidth(60)
        self.date_font_size_spin.valueChanged.connect(
            lambda val: self.parent.on_widget_font_size_changed('date', val))
        date_layout.addWidget(self.date_font_size_spin, alignment=Qt.AlignVCenter)
        
        date_layout.addSpacing(15)
        
        # Date format combo
        date_layout.addWidget(QLabel("Format:"), alignment=Qt.AlignVCenter)
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItem("Default", "default")  # Tuesday 9 December
        self.date_format_combo.addItem("Short", "short")      # Tue Dec 9
        self.date_format_combo.addItem("Numeric", "numeric")  # 09/12
        self.date_format_combo.setFixedWidth(100)
        self.date_format_combo.currentIndexChanged.connect(
            lambda idx: self.parent.on_date_format_changed(self.date_format_combo.currentData()))
        date_layout.addWidget(self.date_format_combo, alignment=Qt.AlignVCenter)
        
        date_layout.addSpacing(15)
        
        # Show weekday checkbox
        date_layout.addWidget(QLabel("Weekday:"), alignment=Qt.AlignVCenter)
        self.show_weekday_checkbox = QCheckBox()
        self.show_weekday_checkbox.setChecked(True)
        self.show_weekday_checkbox.toggled.connect(self.parent.on_show_weekday_changed)
        date_layout.addWidget(self.show_weekday_checkbox, alignment=Qt.AlignVCenter)
        
        # Show year checkbox
        date_layout.addWidget(QLabel("Year:"), alignment=Qt.AlignVCenter)
        self.show_year_checkbox = QCheckBox()
        self.show_year_checkbox.setChecked(False)
        self.show_year_checkbox.toggled.connect(self.parent.on_show_year_changed)
        date_layout.addWidget(self.show_year_checkbox, alignment=Qt.AlignVCenter)
        
        date_layout.addStretch()
        datetime_group_layout.addLayout(date_layout)
        
        # Time row
        time_layout = QHBoxLayout()
        time_layout.setSpacing(6)
        
        # Time controls - label before checkbox
        time_layout.addWidget(QLabel("Time:"), alignment=Qt.AlignVCenter)
        self.show_time_checkbox = QCheckBox()
        self.show_time_checkbox.setChecked(False)
        self.show_time_checkbox.toggled.connect(self.parent.on_show_time_changed)
        time_layout.addWidget(self.show_time_checkbox, alignment=Qt.AlignVCenter)
        
        time_layout.addWidget(QLabel("Size:"), alignment=Qt.AlignVCenter)
        self.time_font_size_spin = QSpinBox()
        self.time_font_size_spin.setRange(8, 72)
        self.time_font_size_spin.setValue(18)
        self.time_font_size_spin.setFixedWidth(60)
        self.time_font_size_spin.valueChanged.connect(
            lambda val: self.parent.on_widget_font_size_changed('time', val))
        time_layout.addWidget(self.time_font_size_spin, alignment=Qt.AlignVCenter)
        
        time_layout.addSpacing(15)
        
        # 24-hour checkbox
        time_layout.addWidget(QLabel("24hr:"), alignment=Qt.AlignVCenter)
        self.use_24_hour_checkbox = QCheckBox()
        self.use_24_hour_checkbox.setChecked(True)
        self.use_24_hour_checkbox.toggled.connect(self.parent.on_use_24_hour_changed)
        time_layout.addWidget(self.use_24_hour_checkbox, alignment=Qt.AlignVCenter)
        
        time_layout.addSpacing(15)
        
        # Show seconds checkbox
        time_layout.addWidget(QLabel("Seconds:"), alignment=Qt.AlignVCenter)
        self.show_seconds_checkbox = QCheckBox()
        self.show_seconds_checkbox.setChecked(False)
        self.show_seconds_checkbox.toggled.connect(self.parent.on_show_seconds_changed)
        time_layout.addWidget(self.show_seconds_checkbox, alignment=Qt.AlignVCenter)
        
        time_layout.addSpacing(15)
        
        # Show AM/PM checkbox
        time_layout.addWidget(QLabel("AM/PM:"), alignment=Qt.AlignVCenter)
        self.show_am_pm_checkbox = QCheckBox()
        self.show_am_pm_checkbox.setChecked(False)
        self.show_am_pm_checkbox.toggled.connect(self.parent.on_show_am_pm_changed)
        time_layout.addWidget(self.show_am_pm_checkbox, alignment=Qt.AlignVCenter)
        
        time_layout.addStretch()
        datetime_group_layout.addLayout(time_layout)

        overlay_layout.addWidget(datetime_group)

        # CPU and GPU Metrics side by side
        metrics_container = QWidget()
        metrics_layout = QHBoxLayout(metrics_container)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(6)

        # CPU Metrics section
        cpu_group = QGroupBox("CPU Metrics")
        cpu_group_layout = QVBoxLayout(cpu_group)
        cpu_group_layout.setSpacing(6)
        cpu_group_layout.setContentsMargins(4, 8, 4, 4)

        cpu_metric_labels = {
            "cpu_temperature": ("Temp:", "Temp"),
            "cpu_usage": ("Utilization:", "Usage"),
            "cpu_frequency": ("Frequency:", "Freq")
        }

        for metric_name, (row_label, display_name) in cpu_metric_labels.items():
            metric_layout = self._create_metric_row(row_label, display_name, metric_name)
            cpu_group_layout.addLayout(metric_layout)

        metrics_layout.addWidget(cpu_group)

        # GPU Metrics section
        gpu_group = QGroupBox("GPU Metrics")
        gpu_group_layout = QVBoxLayout(gpu_group)
        gpu_group_layout.setSpacing(6)
        gpu_group_layout.setContentsMargins(4, 8, 4, 4)

        gpu_metric_labels = {
            "gpu_temperature": ("Temp:", "Temp"),
            "gpu_usage": ("Utilization:", "Usage"),
            "gpu_frequency": ("Frequency:", "Freq")
        }

        for metric_name, (row_label, display_name) in gpu_metric_labels.items():
            metric_layout = self._create_metric_row(row_label, display_name, metric_name)
            gpu_group_layout.addLayout(metric_layout)

        metrics_layout.addWidget(gpu_group)

        overlay_layout.addWidget(metrics_container)
        
        # Free text controls - all 4 on one row in a group box
        free_text_group = QGroupBox("Free Text:")
        free_text_layout = QVBoxLayout(free_text_group)
        free_text_layout.setContentsMargins(6, 6, 6, 6)
        
        text_row_layout = QHBoxLayout()
        text_row_layout.setSpacing(6)
        
        text_labels = {
            "text1": "1:",
            "text2": "2:",
            "text3": "3:",
            "text4": "4:"
        }
        
        for text_name, display_name in text_labels.items():
            # Text label in front of checkbox
            label_number = int(display_name[0])
            text_label = QLabel(f"Text {label_number}")
            text_label.setFixedWidth(50)
            text_label.setAlignment(Qt.AlignVCenter)
            text_row_layout.addWidget(text_label, alignment=Qt.AlignVCenter)
            # Checkbox
            checkbox = QCheckBox(display_name)
            checkbox.setChecked(False)
            checkbox.setStyleSheet(self._get_smart_checkbox_style())
            checkbox.toggled.connect(lambda checked, name=text_name: self.parent.on_text_toggled(name, checked))
            self.text_checkboxes[text_name] = checkbox
            text_row_layout.addWidget(checkbox, alignment=Qt.AlignVCenter)
            
            # Text input field
            text_input = QLineEdit()
            text_input.setPlaceholderText("Text...")
            text_input.textChanged.connect(
                lambda text, name=text_name: self.parent.on_text_changed(name, text))
            text_input.setFixedWidth(150)
            self.text_inputs[text_name] = text_input
            text_row_layout.addWidget(text_input, alignment=Qt.AlignVCenter)
            
            # Size label and spinbox
            size_label = QLabel("Size:")
            size_label.setFixedWidth(35)
            text_row_layout.addWidget(size_label, alignment=Qt.AlignVCenter)
            font_size_spin = QSpinBox()
            font_size_spin.setRange(8, 72)
            font_size_spin.setValue(18)
            font_size_spin.setFixedWidth(60)
            font_size_spin.valueChanged.connect(
                lambda val, name=text_name: self.parent.on_text_font_size_changed(name, val))
            self.text_font_size_spins[text_name] = font_size_spin
            text_row_layout.addWidget(font_size_spin, alignment=Qt.AlignVCenter)
        
        text_row_layout.addStretch()
        free_text_layout.addLayout(text_row_layout)
        
        overlay_layout.addWidget(free_text_group)
        
        # Bar Graph controls
        bar_group = QGroupBox("Bar Graphs:")
        bar_layout = QVBoxLayout(bar_group)
        bar_layout.setContentsMargins(6, 6, 6, 6)
        bar_layout.setSpacing(6)
        
        for i in range(1, 5):
            bar_name = f"bar{i}"
            bar_row = self._create_bar_graph_row(bar_name, i)
            bar_layout.addLayout(bar_row)
        
        overlay_layout.addWidget(bar_group)
        
        return overlay_group

    def _create_metric_row(self, row_label, display_name, metric_name):
        """Create a single-row layout for a metric widget with all controls inline"""
        row = QHBoxLayout()
        row.setSpacing(6)
        
        # Row label (Temperature:, Utilization:, Frequency:)
        label = QLabel(row_label)
        label.setFixedWidth(75)
        row.addWidget(label, alignment=Qt.AlignVCenter)
        
        # Checkbox (no text label - row_label already describes it)
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        checkbox.setStyleSheet(self._get_smart_checkbox_style())
        checkbox.toggled.connect(lambda checked, name=metric_name: self.parent.on_metric_toggled(name, checked))
        checkbox.setFixedWidth(20)
        self.metric_checkboxes[metric_name] = checkbox
        row.addWidget(checkbox, alignment=Qt.AlignVCenter)
        
        # Size spinbox
        size_label = QLabel("Size:")
        size_label.setFixedWidth(35)
        row.addWidget(size_label, alignment=Qt.AlignVCenter)
        font_size_spin = QSpinBox()
        font_size_spin.setRange(8, 72)
        font_size_spin.setValue(18)
        font_size_spin.setFixedWidth(60)
        font_size_spin.valueChanged.connect(
            lambda val, name=metric_name: self.parent.on_metric_font_size_changed(name, val))
        self.metric_font_size_spins[metric_name] = font_size_spin
        row.addWidget(font_size_spin, alignment=Qt.AlignVCenter)
        
        # Label input
        lbl_label = QLabel("Label:")
        lbl_label.setFixedWidth(45)
        row.addWidget(lbl_label, alignment=Qt.AlignVCenter)
        label_input = QLineEdit()
        label_input.setPlaceholderText(self.metric_widgets[metric_name]._get_default_label() if metric_name in self.metric_widgets else "")
        label_input.textChanged.connect(
            lambda text, name=metric_name: self.parent.on_metric_label_changed(name, text))
        label_input.setFixedWidth(80)
        self.metric_label_inputs[metric_name] = label_input
        row.addWidget(label_input, alignment=Qt.AlignVCenter)
        
        # Position dropdown
        pos_label = QLabel("Pos:")
        pos_label.setFixedWidth(35)
        row.addWidget(pos_label, alignment=Qt.AlignVCenter)
        label_pos_combo = QComboBox()
        label_pos_combo.addItem("Left", "left")
        label_pos_combo.addItem("Right", "right")
        label_pos_combo.addItem("Above", "above")
        label_pos_combo.addItem("Below", "below")
        label_pos_combo.addItem("None", "none")
        label_pos_combo.setCurrentIndex(0)
        label_pos_combo.setFixedWidth(100)
        label_pos_combo.currentIndexChanged.connect(
            lambda idx, name=metric_name, combo=label_pos_combo: 
                self.parent.on_metric_label_position_changed(name, combo.currentData()))
        self.metric_label_position_combos[metric_name] = label_pos_combo
        row.addWidget(label_pos_combo, alignment=Qt.AlignVCenter)
        
        # Label font size spinbox (after position)
        lbl_size_label = QLabel("Label Size:")
        lbl_size_label.setFixedWidth(70)
        row.addWidget(lbl_size_label, alignment=Qt.AlignVCenter)
        label_font_size_spin = QSpinBox()
        label_font_size_spin.setRange(8, 72)
        label_font_size_spin.setValue(14)
        label_font_size_spin.setFixedWidth(60)
        label_font_size_spin.valueChanged.connect(
            lambda val, name=metric_name: self.parent.on_metric_label_font_size_changed(name, val))
        self.metric_label_font_size_spins[metric_name] = label_font_size_spin
        row.addWidget(label_font_size_spin, alignment=Qt.AlignVCenter)
        
        # Unit/Format - for frequency show MHz/GHz, otherwise unit input
        if 'frequency' in metric_name:
            unit_label = QLabel("Unit:")
            unit_label.setFixedWidth(35)
            row.addWidget(unit_label, alignment=Qt.AlignVCenter)
            freq_format_combo = QComboBox()
            freq_format_combo.addItem("MHz", "mhz")
            freq_format_combo.addItem("GHz", "ghz")
            freq_format_combo.setCurrentIndex(0)
            freq_format_combo.setFixedWidth(100)
            freq_format_combo.currentIndexChanged.connect(
                lambda idx, name=metric_name, combo=freq_format_combo:
                    self.parent.on_metric_freq_format_changed(name, combo.currentData()))
            self.metric_freq_format_combos[metric_name] = freq_format_combo
            row.addWidget(freq_format_combo, alignment=Qt.AlignVCenter)
        else:
            unit_label = QLabel("Unit:")
            unit_label.setFixedWidth(35)
            row.addWidget(unit_label, alignment=Qt.AlignVCenter)
            unit_input = QLineEdit()
            unit_input.setPlaceholderText(self.metric_widgets[metric_name]._get_default_unit() if metric_name in self.metric_widgets else "")
            unit_input.textChanged.connect(
                lambda text, name=metric_name: self.parent.on_metric_unit_changed(name, text))
            unit_input.setFixedWidth(60)
            self.metric_unit_inputs[metric_name] = unit_input
            row.addWidget(unit_input, alignment=Qt.AlignVCenter)
        
        row.addStretch()
        return row

    def _create_text_layout(self, display_name, text_name):
        """Create a single-row layout for a free text widget with all controls inline"""
        text_layout = QHBoxLayout()
        text_layout.setSpacing(6)
        
        # Checkbox with text widget name
        checkbox = QCheckBox(display_name)
        checkbox.setChecked(False)
        checkbox.setStyleSheet(self._get_smart_checkbox_style())
        checkbox.toggled.connect(lambda checked, name=text_name: self.parent.on_text_toggled(name, checked))
        checkbox.setFixedWidth(60)
        self.text_checkboxes[text_name] = checkbox
        text_layout.addWidget(checkbox, alignment=Qt.AlignVCenter)
        
        # Text input field
        text_layout.addWidget(QLabel("Text:"), alignment=Qt.AlignVCenter)
        text_input = QLineEdit()
        text_input.setPlaceholderText("Enter text...")
        text_input.textChanged.connect(
            lambda text, name=text_name: self.parent.on_text_changed(name, text))
        text_input.setFixedWidth(150)
        self.text_inputs[text_name] = text_input
        text_layout.addWidget(text_input, alignment=Qt.AlignVCenter)
        
        # Font size spinbox
        text_layout.addWidget(QLabel("Size:"), alignment=Qt.AlignVCenter)
        font_size_spin = QSpinBox()
        font_size_spin.setRange(8, 72)
        font_size_spin.setValue(18)
        font_size_spin.setFixedWidth(60)
        font_size_spin.valueChanged.connect(
            lambda val, name=text_name: self.parent.on_text_font_size_changed(name, val))
        self.text_font_size_spins[text_name] = font_size_spin
        text_layout.addWidget(font_size_spin, alignment=Qt.AlignVCenter)
        
        text_layout.addStretch()
        return text_layout

    def _create_bar_graph_row(self, bar_name: str, bar_num: int):
        """Create a single-row layout for a bar graph widget with all controls inline"""
        row = QHBoxLayout()
        row.setSpacing(6)
        row.setContentsMargins(0, 2, 0, 2)
        
        # Bar label
        label = QLabel(f"Bar {bar_num}:")
        label.setFixedWidth(50)
        row.addWidget(label, alignment=Qt.AlignVCenter)
        
        # Enable checkbox
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        checkbox.setStyleSheet(self._get_smart_checkbox_style())
        checkbox.toggled.connect(lambda checked, name=bar_name: self.parent.on_bar_toggled(name, checked))
        checkbox.setFixedWidth(20)
        self.bar_checkboxes[bar_name] = checkbox
        row.addWidget(checkbox, alignment=Qt.AlignVCenter)
        
        # Metric dropdown
        metric_label = QLabel("Metric:")
        metric_label.setFixedWidth(45)
        row.addWidget(metric_label, alignment=Qt.AlignVCenter)
        metric_combo = QComboBox()
        metric_combo.addItems([
            "cpu_usage", "cpu_temperature", 
            "gpu_usage", "gpu_temperature"
        ])
        metric_combo.setFixedWidth(120)
        metric_combo.currentTextChanged.connect(
            lambda text, name=bar_name: self.parent.on_bar_metric_changed(name, text))
        self.bar_metric_combos[bar_name] = metric_combo
        row.addWidget(metric_combo, alignment=Qt.AlignVCenter)
        
        # Orientation dropdown
        orient_label = QLabel("Orientation:")
        orient_label.setFixedWidth(70)
        row.addWidget(orient_label, alignment=Qt.AlignVCenter)
        orient_combo = QComboBox()
        orient_combo.addItem("Horizontal", "horizontal")
        orient_combo.addItem("Vertical", "vertical")
        orient_combo.setFixedWidth(100)
        orient_combo.setToolTip("Bar orientation: Horizontal or Vertical")
        orient_combo.currentIndexChanged.connect(
            lambda idx, name=bar_name, combo=orient_combo: 
                self.parent.on_bar_orientation_changed(name, combo.currentData()))
        self.bar_orientation_combos[bar_name] = orient_combo
        row.addWidget(orient_combo, alignment=Qt.AlignVCenter)
        
        # Width
        width_label = QLabel("W:")
        width_label.setFixedWidth(20)
        row.addWidget(width_label, alignment=Qt.AlignVCenter)
        width_spin = QSpinBox()
        width_spin.setRange(20, 300)
        width_spin.setValue(100)
        width_spin.setFixedWidth(60)
        width_spin.valueChanged.connect(
            lambda val, name=bar_name: self.parent.on_bar_width_changed(name, val))
        self.bar_width_spins[bar_name] = width_spin
        row.addWidget(width_spin, alignment=Qt.AlignVCenter)
        
        # Height
        height_label = QLabel("H:")
        height_label.setFixedWidth(20)
        row.addWidget(height_label, alignment=Qt.AlignVCenter)
        height_spin = QSpinBox()
        height_spin.setRange(5, 50)
        height_spin.setValue(16)
        height_spin.setFixedWidth(60)
        height_spin.valueChanged.connect(
            lambda val, name=bar_name: self.parent.on_bar_height_changed(name, val))
        self.bar_height_spins[bar_name] = height_spin
        row.addWidget(height_spin, alignment=Qt.AlignVCenter)
        
        # Corner radius
        radius_label = QLabel("R:")
        radius_label.setFixedWidth(20)
        row.addWidget(radius_label, alignment=Qt.AlignVCenter)
        radius_spin = QSpinBox()
        radius_spin.setRange(0, 20)
        radius_spin.setValue(0)
        radius_spin.setFixedWidth(60)
        radius_spin.valueChanged.connect(
            lambda val, name=bar_name: self.parent.on_bar_corner_radius_changed(name, val))
        self.bar_corner_radius_spins[bar_name] = radius_spin
        row.addWidget(radius_spin, alignment=Qt.AlignVCenter)
        
        # Fill color button
        fill_btn = QPushButton()
        fill_btn.setFixedWidth(60)
        fill_btn.setStyleSheet("background-color: #00FF00; border: 1px solid #888; border-radius: 3px;")
        fill_btn.setToolTip("Fill Color")
        fill_btn.clicked.connect(lambda _, name=bar_name: self.parent.on_bar_fill_color_clicked(name))
        self.bar_fill_color_btns[bar_name] = fill_btn
        row.addWidget(fill_btn, alignment=Qt.AlignVCenter)
        
        # Background color button
        bg_btn = QPushButton()
        bg_btn.setFixedWidth(60)
        bg_btn.setStyleSheet("background-color: #323232; border: 1px solid #888; border-radius: 3px;")
        bg_btn.setToolTip("Background Color")
        bg_btn.clicked.connect(lambda _, name=bar_name: self.parent.on_bar_bg_color_clicked(name))
        self.bar_bg_color_btns[bar_name] = bg_btn
        row.addWidget(bg_btn, alignment=Qt.AlignVCenter)
        
        # Border color button
        border_btn = QPushButton()
        border_btn.setFixedWidth(60)
        border_btn.setStyleSheet("background-color: #FFFFFF; border: 1px solid #888; border-radius: 3px;")
        border_btn.setToolTip("Border Color")
        border_btn.clicked.connect(lambda _, name=bar_name: self.parent.on_bar_border_color_clicked(name))
        self.bar_border_color_btns[bar_name] = border_btn
        row.addWidget(border_btn, alignment=Qt.AlignVCenter)
        
        row.addStretch()
        return row

    def create_action_buttons(self) -> QWidget:
        """Create action buttons widget (to be placed outside scroll area)"""
        return self._create_action_controls()

    def _create_action_controls(self) -> QGroupBox:
        """Create action buttons with refresh interval on the left"""
        actions_group = QGroupBox()
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.setSpacing(15)
        actions_layout.setContentsMargins(10, 5, 10, 5)
        
        # Refresh interval on the left
        refresh_label = QLabel("LCD Refresh:")
        actions_layout.addWidget(refresh_label, alignment=Qt.AlignVCenter)
        
        self.refresh_interval_spin = QDoubleSpinBox()
        self.refresh_interval_spin.setRange(0.5, 3.0)
        self.refresh_interval_spin.setValue(1.0)
        self.refresh_interval_spin.setSingleStep(0.5)
        self.refresh_interval_spin.setDecimals(1)
        self.refresh_interval_spin.setSuffix(" sec")
        self.refresh_interval_spin.setFixedWidth(60)
        self.refresh_interval_spin.setToolTip("How often the LCD screen updates (0.5-3 seconds)")
        self.refresh_interval_spin.valueChanged.connect(self._on_refresh_interval_changed)
        actions_layout.addWidget(self.refresh_interval_spin, alignment=Qt.AlignVCenter)
        
        actions_layout.addStretch()
        
        save_config_btn = QPushButton("Save")
        save_config_btn.clicked.connect(self.parent.generate_config_yaml)
        save_config_btn.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; font-weight: bold; 
                         padding: 8px; border-radius: 6px; }
            QPushButton:hover { background-color: #219a52; }
        """)
        save_config_btn.setFixedSize(100, 35)

        preview_config_btn = QPushButton("Apply")
        preview_config_btn.clicked.connect(self.parent.generate_preview)
        preview_config_btn.setStyleSheet("""
                QPushButton { background-color: #3498db; color: white; font-weight: bold; 
                             padding: 8px; border-radius: 6px; }
                QPushButton:hover { background-color: #2980b9; }
            """)
        preview_config_btn.setFixedSize(100, 35)

        actions_layout.addWidget(save_config_btn, alignment=Qt.AlignVCenter)
        actions_layout.addWidget(preview_config_btn, alignment=Qt.AlignVCenter)

        return actions_group

    def update_color_button(self):
        """Update color button appearance"""
        self.color_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {self.text_style.color.name()}; border: 1px solid #bdc3c7; 
                          border-radius: 6px; padding: 5px; color: {'#2c3e50' if self.text_style.color.lightness() > 128 else '#ecf0f1'}; }}
        """)

    def _get_smart_checkbox_style(self):
        """Style intelligent qui détecte automatiquement le thème"""
        # Détecter si on est en mode sombre
        palette = QApplication.instance().palette()
        is_dark = palette.color(QPalette.ColorRole.Window).lightness() < 128

        if is_dark:
            return """
            QCheckBox {
                color: #ffffff;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #666666;
                border-radius: 3px;
                background-color: #2b2b2b;
            }
            QCheckBox::indicator:hover {
                border-color: #0078d4;
                background-color: #3c3c3c;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            """
        else:
            return """
            QCheckBox {
                color: #000000;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #999999;
                border-radius: 3px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:hover {
                border-color: #0078d4;
                background-color: #f0f0f0;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            """
