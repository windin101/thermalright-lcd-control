# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Controls manager for UI composition controls"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QLabel, QLineEdit, QPushButton,
                               QSpinBox, QCheckBox, QApplication)
from PySide6.QtWidgets import QSlider

from ..widgets.draggable_widget import TextStyleConfig
from ...common.logging_config import get_gui_logger


class ControlsManager:
    """Manages all UI controls for composition"""

    def __init__(self, parent, text_style: TextStyleConfig, metric_widgets: dict):
        self.parent = parent
        self.logger = get_gui_logger()
        self.text_style = text_style
        self.metric_widgets = metric_widgets

        # Control widgets
        self.opacity_input = None
        self.opacity_value_label = None
        self.font_size_spin = None
        self.color_btn = None
        self.show_date_checkbox = None
        self.show_time_checkbox = None
        self.metric_checkboxes = {}
        self.metric_label_inputs = {}
        self.metric_unit_inputs = {}
        
        # Rotation controls
        self.rotation_buttons = {}
        self.no_rotation_btn = None
        self.rotate_90_btn = None
        self.rotate_180_btn = None
        self.rotate_270_btn = None

    def create_controls_widget(self) -> QScrollArea:
        """Create and return the controls widget"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        controls_container = QWidget()
        controls_layout = QVBoxLayout(controls_container)

        # Add all control sections
        controls_layout.addWidget(self._create_opacity_controls())
        controls_layout.addWidget(self._create_screen_controls())
        controls_layout.addWidget(self._create_text_style_controls())

        scroll_area.setWidget(controls_container)
        return scroll_area

    def _create_opacity_controls(self) -> QGroupBox:
        """Create foreground opacity controls"""
        opacity_group = QGroupBox("Foreground Opacity")
        opacity_layout = QVBoxLayout(opacity_group)  # Changé en VBoxLayout

        # Layout horizontal pour le label et la valeur
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("Opacity:"))
        label_layout.addStretch()  # Pousse la valeur vers la droite

        self.opacity_value_label = QLabel("100%")
        label_layout.addWidget(self.opacity_value_label)

        # Slider qui prend toute la largeur
        self.opacity_input = QSlider(Qt.Horizontal)
        self.opacity_input.setRange(0, 100)
        self.opacity_input.setValue(100)  # Default to fully opaque
        self.opacity_input.setTickPosition(QSlider.TicksBelow)
        self.opacity_input.setTickInterval(10)

        self.opacity_input.valueChanged.connect(self._on_opacity_slider_changed)
        self.opacity_input.sliderReleased.connect(self.parent.on_opacity_editing_finished)

        # Ajouter les layouts
        opacity_layout.addLayout(label_layout)
        opacity_layout.addWidget(self.opacity_input)

        return opacity_group



    def _on_opacity_slider_changed(self, value):
        """Handle slider value change"""
        self.opacity_value_label.setText(f"{value}%")
        self.parent.on_opacity_text_changed(str(value))


    def _create_screen_controls(self) -> QGroupBox:
        """Create screen/background controls"""
        screen_group = QGroupBox("Screen Controls")
        screen_layout = QVBoxLayout(screen_group)
        
        # Rotation controls at the top
        rotation_layout = QHBoxLayout()
        rotation_label = QLabel("Rotation:")
        rotation_label.setFixedWidth(60)
        rotation_layout.addWidget(rotation_label)
        
        # Rotation buttons
        self.rotation_buttons = {}
        
        # No Rotation (0°)
        self.no_rotation_btn = QPushButton("0°")
        self.no_rotation_btn.setFixedSize(50, 30)
        self.no_rotation_btn.setCheckable(True)
        self.no_rotation_btn.clicked.connect(lambda: self._set_rotation(0))
        rotation_layout.addWidget(self.no_rotation_btn)
        self.rotation_buttons[0] = self.no_rotation_btn
        
        # 90° Clockwise
        self.rotate_90_btn = QPushButton("90°")
        self.rotate_90_btn.setFixedSize(50, 30)
        self.rotate_90_btn.setCheckable(True)
        self.rotate_90_btn.clicked.connect(lambda: self._set_rotation(90))
        rotation_layout.addWidget(self.rotate_90_btn)
        self.rotation_buttons[90] = self.rotate_90_btn
        
        # Upside Down (180°)
        self.rotate_180_btn = QPushButton("180°")
        self.rotate_180_btn.setFixedSize(50, 30)
        self.rotate_180_btn.setCheckable(True)
        self.rotate_180_btn.clicked.connect(lambda: self._set_rotation(180))
        rotation_layout.addWidget(self.rotate_180_btn)
        self.rotation_buttons[180] = self.rotate_180_btn
        
        # 90° Counterclockwise (270°)
        self.rotate_270_btn = QPushButton("270°")
        self.rotate_270_btn.setFixedSize(50, 30)
        self.rotate_270_btn.setCheckable(True)
        self.rotate_270_btn.clicked.connect(lambda: self._set_rotation(270))
        rotation_layout.addWidget(self.rotate_270_btn)
        self.rotation_buttons[270] = self.rotate_270_btn
        
        rotation_layout.addStretch()
        screen_layout.addLayout(rotation_layout)
        
        # Background color picker
        bg_color_layout = QHBoxLayout()
        bg_color_label = QLabel("Background Color:")
        bg_color_label.setFixedWidth(120)
        bg_color_layout.addWidget(bg_color_label)
        
        # Color button
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(60, 30)
        self.bg_color_btn.setStyleSheet("""
            QPushButton { background-color: #000000; border: 1px solid #666; 
                          padding: 5px; color: white; }
        """)
        self.bg_color_btn.clicked.connect(self._choose_background_color)
        bg_color_layout.addWidget(self.bg_color_btn)
        
        # Color hex display
        self.bg_color_label = QLabel("#000000")
        self.bg_color_label.setFixedWidth(80)
        bg_color_layout.addWidget(self.bg_color_label)
        
        bg_color_layout.addStretch()
        screen_layout.addLayout(bg_color_layout)
        
        # Background image visibility checkbox
        bg_image_layout = QHBoxLayout()
        self.show_bg_image_checkbox = QCheckBox("Show Background Image")
        self.show_bg_image_checkbox.setChecked(True)  # Default to showing image
        self.show_bg_image_checkbox.stateChanged.connect(self._on_bg_image_toggled)
        bg_image_layout.addWidget(self.show_bg_image_checkbox)
        bg_image_layout.addStretch()
        screen_layout.addLayout(bg_image_layout)
        
        # Screen info
        info_label = QLabel(f"Screen: {self.parent.device_width}x{self.parent.device_height}")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        screen_layout.addWidget(info_label)
        
        screen_layout.addStretch()
        
        # Initialize rotation button states
        self._update_rotation_buttons()
        
        # Initialize background image checkbox
        self._update_bg_image_checkbox()
        
        return screen_group
    
    def _choose_background_color(self):
        """Open color dialog for background color"""
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        
        current_color = getattr(self.parent.preview_manager, "background_color", None)
        if not current_color:
            current_color = QColor(0, 0, 0)
        color = QColorDialog.getColor(current_color, self.parent, "Choose Background Color")
        
        if color.isValid():
            # Store in preview manager
            self.parent.preview_manager.background_color = color
            
            # Update button
            self._update_background_color_button()
            
            # Update unified controller background
            if hasattr(self.parent, 'unified'):
                self.parent.unified.set_background(self.parent.preview_manager, None)  # Will use color
    
    def _update_background_color_button(self):
        """Update background color button appearance"""
        if hasattr(self, 'bg_color_btn') and hasattr(self.parent.preview_manager, 'background_color'):
            color = self.parent.preview_manager.background_color
            if not color:
                color = QColor(0, 0, 0)
            if isinstance(color, tuple):
                color = QColor(*color)
            
            # Update button style
            self.bg_color_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {color.name()}; border: 1px solid #666; 
                              padding: 5px; color: {'black' if color.lightness() > 128 else 'white'}; }}
            """)
            
            # Update label
            if hasattr(self, 'bg_color_label'):
                self.bg_color_label.setText(color.name())

    def _set_rotation(self, degrees: int):
        """Set screen rotation"""
        
        # Update preview manager rotation (for device config)
        self.parent.preview_manager.current_rotation = degrees
        
        # Update button states
        self._update_rotation_buttons()
        
        # Apply rotation to the unified graphics view (for GUI preview)
        if hasattr(self.parent, 'unified') and hasattr(self.parent.unified, 'unified_view'):
            self._apply_rotation_to_unified_view(degrees)
        
        # Recreate display generator with new rotation setting
        if hasattr(self.parent.preview_manager, 'create_display_generator'):
            self.parent.preview_manager.create_display_generator()
        
        # Force immediate preview refresh with new rotation
        if hasattr(self.parent.preview_manager, 'update_preview_frame'):
            self.parent.preview_manager.update_preview_frame()
        
        # Update preview only (don't send to device)
        if hasattr(self.parent, 'update_preview_only'):
            self.parent.update_preview_only()
    
    def _update_rotation_buttons(self):
        """Update rotation button checked states"""
        current_rotation = getattr(self.parent.preview_manager, 'current_rotation', 0)
        
        for rotation, button in self.rotation_buttons.items():
            button.setChecked(rotation == current_rotation)
    
    def _on_bg_image_toggled(self, state):
        """Handle background image visibility toggle"""
        show_image = state == Qt.CheckState.Checked
        self.logger.info(f"Background image checkbox toggled to: {show_image}")
        
        # Update preview manager
        self.parent.preview_manager.show_background_image = show_image
        
        # Update unified controller background
        if hasattr(self.parent, 'unified'):
            self.parent.unified.set_background(self.parent.preview_manager, 
                                             self.parent.preview_manager.current_background_path)
        
        # Update preview only (don't send to device)
        if hasattr(self.parent, 'update_preview_only'):
            self.parent.update_preview_only()
    
    def _update_bg_image_checkbox(self):
        """Update background image checkbox state"""
        if hasattr(self, 'show_bg_image_checkbox'):
            show_image = getattr(self.parent.preview_manager, 'show_background_image', True)
            self.show_bg_image_checkbox.setChecked(show_image)

    def _apply_rotation_to_unified_view(self, degrees: int):
        """Apply rotation transformation to the entire preview container (like a PC monitor)"""
        try:
            from PySide6.QtGui import QTransform
            
            # Find the preview container widget (the one that holds the graphics view)
            # This simulates rotating the entire monitor
            preview_container = None
            if hasattr(self.parent, 'centralWidget'):
                central_widget = self.parent.centralWidget()
                if central_widget and central_widget.layout():
                    # The preview container is the first widget in the left column
                    left_column = central_widget.layout().itemAt(0).widget()
                    if left_column and left_column.layout():
                        preview_container = left_column.layout().itemAt(0).widget()
            
            if preview_container:
                # Store original size
                original_size = preview_container.size()
                
                # Create transform for rotation
                transform = QTransform()
                
                if degrees == 90:
                    transform.rotate(90)
                    # Swap dimensions for 90/270 degree rotation
                    new_width = original_size.height()
                    new_height = original_size.width()
                elif degrees == 180:
                    transform.rotate(180)
                    new_width = original_size.width()
                    new_height = original_size.height()
                elif degrees == 270:
                    transform.rotate(270)
                    # Swap dimensions for 90/270 degree rotation
                    new_width = original_size.height()
                    new_height = original_size.width()
                else:  # 0 degrees
                    transform.rotate(0)
                    # Reset to original size
                    new_width = 480
                    new_height = 360
                
                # Apply new size
                if degrees in [90, 270]:
                    # Portrait mode
                    preview_container.setFixedSize(360, 480)
                elif degrees in [0, 180]:
                    # Landscape mode
                    preview_container.setFixedSize(480, 360)
                
                # Apply transform to the entire preview container
                preview_container.setTransform(transform)
                
                # Force layout update
                preview_container.adjustSize()
                if preview_container.parent() and preview_container.parent().layout():
                    preview_container.parent().layout().invalidate()
                    preview_container.parent().layout().update()
                if central_widget and central_widget.layout():
                    central_widget.layout().invalidate()
                    central_widget.layout().update()
                
                # Force update
                preview_container.update()
                central_widget.update()
                
                # Also update the graphics view to match
                if hasattr(self.parent, 'unified') and hasattr(self.parent.unified, 'unified_view'):
                    graphics_view = self.parent.unified.unified_view.view
                    graphics_view.setTransform(QTransform())  # Reset graphics view transform
            else:
                # Fallback to graphics view rotation
                if hasattr(self.parent, 'unified') and hasattr(self.parent.unified, 'unified_view'):
                    graphics_view = self.parent.unified.unified_view.view
                    transform = QTransform()
                    if degrees == 90:
                        transform.rotate(90)
                    elif degrees == 180:
                        transform.rotate(180)
                    elif degrees == 270:
                        transform.rotate(270)
                    graphics_view.setTransform(transform)
            
        except Exception as e:
            pass

    def _create_text_style_controls(self) -> QGroupBox:
        """Create text style controls"""
        style_group = QGroupBox("Text Style")
        style_layout = QHBoxLayout(style_group)

        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(self.text_style.font_size)
        self.font_size_spin.valueChanged.connect(self.parent.on_font_size_changed)

        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Size:"))
        font_layout.addWidget(self.font_size_spin)
        font_layout.addStretch(1)

        # Color
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.clicked.connect(self.parent.choose_color)
        self.update_color_button()

        color_layout.addWidget(QLabel("Choose Colors:"))
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch(1)

        style_layout.addLayout(font_layout)
        style_layout.addLayout(color_layout)

        return style_group

    def update_color_button(self):
        """Update text color button appearance"""
        if hasattr(self, 'color_btn') and hasattr(self, 'text_style'):
            color = self.text_style.color
            if isinstance(color, (list, tuple)) and len(color) >= 3:
                from PySide6.QtGui import QColor
                qcolor = QColor(*color)
            else:
                qcolor = QColor(255, 255, 255)  # Default white
            
            # Update button style
            self.color_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {qcolor.name()}; border: 1px solid #666; 
                              padding: 5px; color: {'black' if qcolor.lightness() > 128 else 'white'}; }}
            """)

    def _create_overlay_controls(self) -> QGroupBox:
        """Create overlay widget controls"""
        overlay_group = QGroupBox("Overlay Widgets")
        overlay_layout = QVBoxLayout(overlay_group)

        # Date/Time controls
        datetime_layout = QHBoxLayout()
        self.show_date_checkbox = QCheckBox("Show Date")
        self.show_date_checkbox.setChecked(True)
        self.show_date_checkbox.toggled.connect(self.parent.on_show_date_changed)

        self.show_time_checkbox = QCheckBox("Show Time")
        self.show_time_checkbox.setChecked(False)
        self.show_time_checkbox.toggled.connect(self.parent.on_show_time_changed)

        datetime_layout.addWidget(self.show_date_checkbox)
        datetime_layout.addWidget(self.show_time_checkbox)
        overlay_layout.addLayout(datetime_layout)

        # Metric controls
        cpu_metrics_layout = QHBoxLayout()
        cpu_metrics_layout.addWidget(QLabel("CPU Metrics:"))
        gpu_metrics_layout = QHBoxLayout()
        gpu_metrics_layout.addWidget(QLabel("GPU Metrics:"))

        cpu_metric_labels = {
            "cpu_temperature": "Temp",
            "cpu_usage": "Usage",
            "cpu_frequency": "Frequency"
        }

        gpu_metric_labels = {
            "gpu_temperature": "Temp",
            "gpu_usage": "Usage",
            "gpu_frequency": "Frequency"
        }

        for metric_name, display_name in cpu_metric_labels.items():
            metric_layout = self._create_metric_layout(display_name, metric_name)
            cpu_metrics_layout.addLayout(metric_layout)

        for metric_name, display_name in gpu_metric_labels.items():
            metric_layout = self._create_metric_layout(display_name, metric_name)
            gpu_metrics_layout.addLayout(metric_layout)

        overlay_layout.addLayout(cpu_metrics_layout)
        overlay_layout.addLayout(gpu_metrics_layout)
        return overlay_group

    def _create_metric_layout(self, display_name, metric_name):
        metric_layout = QHBoxLayout()
        # Checkbox
        checkbox = QCheckBox(display_name)
        checkbox.setChecked(False)
        checkbox.setStyleSheet(self._get_smart_checkbox_style())
        checkbox.toggled.connect(lambda checked, name=metric_name: self.parent.on_metric_toggled(name, checked))
        self.metric_checkboxes[metric_name] = checkbox
        metric_layout.addWidget(checkbox)
        # Label input
        metric_layout.addWidget(QLabel("Label:"))
        label_input = QLineEdit()
        label_input.setPlaceholderText(self.metric_widgets[metric_name]._get_default_label())
        label_input.textChanged.connect(
            lambda text, name=metric_name: self.parent.on_metric_label_changed(name, text))
        label_input.setMaximumWidth(60)
        self.metric_label_inputs[metric_name] = label_input
        metric_layout.addWidget(label_input)
        # Unit input
        metric_layout.addWidget(QLabel("Unit:"))
        unit_input = QLineEdit()
        unit_input.setPlaceholderText(self.metric_widgets[metric_name]._get_default_unit())
        unit_input.textChanged.connect(
            lambda text, name=metric_name: self.parent.on_metric_unit_changed(name, text))
        unit_input.setMaximumWidth(40)
        self.metric_unit_inputs[metric_name] = unit_input
        metric_layout.addWidget(unit_input)
        metric_layout.addStretch()
        return metric_layout

    def _create_action_controls(self) -> QGroupBox:
        """Create action buttons"""
        actions_group = QGroupBox()
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.addStretch()
        actions_layout.setSpacing(10)
        save_config_btn = QPushButton("Save")
        save_config_btn.clicked.connect(self.parent.save_theme)
        save_config_btn.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; font-weight: bold; 
                         padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #45a049; }
        """)
        save_config_btn.setFixedSize(100, 35)

        preview_config_btn = QPushButton("Apply")
        preview_config_btn.clicked.connect(self.parent.generate_preview)
        preview_config_btn.setStyleSheet("""
                QPushButton { background-color: #4CAF50; color: white; font-weight: bold; 
                             padding: 8px; border-radius: 4px; }
                QPushButton:hover { background-color: #45a049; }
            """)
        preview_config_btn.setFixedSize(100, 35)

        actions_layout.addWidget(save_config_btn, alignment=Qt.AlignmentFlag.AlignRight)
        actions_layout.addWidget(preview_config_btn, alignment=Qt.AlignmentFlag.AlignRight)

        return actions_group

    def update_color_button(self):
        """Update color button appearance"""
        from PySide6.QtGui import QColor
        
        # Handle color as tuple or QColor
        if isinstance(self.text_style.color, tuple):
            if len(self.text_style.color) == 4:
                color = QColor(self.text_style.color[0], self.text_style.color[1], self.text_style.color[2], self.text_style.color[3])
            else:
                color = QColor(self.text_style.color[0], self.text_style.color[1], self.text_style.color[2])
        else:
            color = self.text_style.color
        
        self.color_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {color.name()}; border: 1px solid #666; 
                          padding: 5px; color: {'black' if color.lightness() > 128 else 'white'}; }}
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
