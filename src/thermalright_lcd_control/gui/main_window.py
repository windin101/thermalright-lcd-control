# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Main window for Media Preview application"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import (QTabWidget, QFrame, QColorDialog, QMessageBox)

from thermalright_lcd_control.gui.components.config_generator import ConfigGenerator
from thermalright_lcd_control.gui.components.controls_manager import ControlsManager
from thermalright_lcd_control.gui.components.preview_manager import PreviewManager
from thermalright_lcd_control.gui.tabs.media_tab import MediaTab
from thermalright_lcd_control.gui.tabs.themes_tab import ThemesTab
from thermalright_lcd_control.gui.utils.config_loader import load_config
from thermalright_lcd_control.gui.widgets.draggable_widget import *
from thermalright_lcd_control.gui.styles import MODERN_STYLESHEET
from thermalright_lcd_control.common.logging_config import get_gui_logger
from thermalright_lcd_control.device_controller.metrics.cpu_metrics import CpuMetrics
from thermalright_lcd_control.device_controller.metrics.gpu_metrics import GpuMetrics


class MediaPreviewUI(QMainWindow):

    def __init__(self, config_file_path=None, detected_device: dict = None):
        super().__init__()
        self.logger = get_gui_logger()
        # Initialize configuration and device
        self.config = load_config(config_file_path)
        self.cpu_metric = CpuMetrics()
        self.gpu_metric = GpuMetrics()
        title_info = (f"{hex(detected_device['vid'])}-{hex(detected_device['pid'])} | "
                      f"{detected_device['width']}x{detected_device['height']}")

        self.setWindowTitle(f"ThermalRight LCD Control:  {title_info}")

        self.detected_device = detected_device
        self.dev_width = detected_device['width'] if detected_device else 320
        self.dev_height = detected_device['height'] if detected_device else 240

        # Initialize paths
        paths = self.config.get('paths', {})
        self.backgrounds_dir = f"{paths.get('backgrounds_dir', './themes/backgrounds')}"
        self.foregrounds_dir = f"{paths.get('foregrounds_dir', './themes/foregrounds')}/{self.dev_width}{self.dev_height}"

        # Initialize components
        self.text_style = TextStyleConfig()
        self.media_tabs = []
        self.current_rotation = 0  # Default rotation

        # UI Components will be initialized in setup_ui
        self.preview_label = None
        self.preview_manager = None
        self.controls_manager = None
        self.config_generator = ConfigGenerator(self.config)
        
        # Overlay widgets
        self.date_widget = None
        self.time_widget = None
        self.metric_widgets = {}
        self.text_widgets = {}  # Free text widgets

        # Initialize UI
        self.setup_window()
        self.setup_ui()

    def setup_window(self):
        """Configure window size and properties"""
        # Apply modern stylesheet
        self.setStyleSheet(MODERN_STYLESHEET)
        
        window_config = self.config.get('window', {})
        default_width = window_config.get('default_width', 1200)
        default_height = window_config.get('default_height', 600)

        min_width = max(window_config.get('min_width', 800), self.dev_width + 580)
        min_height = max(window_config.get('min_height', 600), self.dev_height + 200)

        self.setGeometry(100, 100, max(default_width, min_width), max(default_height, min_height))
        self.setMinimumSize(min_width, min_height)

    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Left side (preview + controls) - use vertical layout
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Preview area (compact, no stretches)
        self.setup_preview_area(left_layout)

        # Create overlay widgets first
        self.create_overlay_widgets()

        # Controls (now that metric_widgets exists) - takes remaining space
        self.controls_manager = ControlsManager(self, self.text_style, self.metric_widgets)
        
        # Action buttons stay fixed at top (outside scroll area)
        left_layout.addWidget(self.controls_manager.create_action_buttons())
        
        # Scrollable controls
        left_layout.addWidget(self.controls_manager.create_controls_widget(), 1)

        # Right side (tabs)
        right_widget = QWidget()
        right_widget.setMinimumWidth(400)
        right_widget.setMaximumWidth(550)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.setup_tabs_area(right_layout)

        main_layout.addWidget(left_widget, 6)
        main_layout.addWidget(right_widget, 4)
        self.themes_tab.auto_load_first_theme()

    def setup_preview_area(self, parent_layout):
        """Configure preview area with device-specific size"""
        # Use 1:1 scale - preview matches LCD exactly for accurate positioning
        base_width = self.detected_device['width'] if self.detected_device else 320
        base_height = self.detected_device['height'] if self.detected_device else 240
        self.preview_scale = 1.0
        preview_width = int(base_width * self.preview_scale)
        preview_height = int(base_height * self.preview_scale)

        # Preview frame
        frame_width, frame_height = preview_width + 4, preview_height + 4
        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        preview_frame.setFixedSize(frame_width, frame_height)

        # Preview widget and label - use light background
        self.preview_widget = QWidget(preview_frame)
        self.preview_widget.setGeometry(2, 2, preview_width, preview_height)
        self.preview_widget.setStyleSheet("background-color: #ecf0f1;")

        self.preview_label = QLabel(self.preview_widget)
        self.preview_label.setGeometry(0, 0, preview_width, preview_height)
        self.preview_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.preview_label.setStyleSheet(
            "QLabel { background-color: #ecf0f1; color: #7f8c8d; border: none; font-size: 12px; }")
        self.preview_label.setText("Initializing preview...")

        # Create draggable foreground widget (on top of preview_label)
        self.foreground_widget = DraggableForegroundWidget(self.preview_widget, preview_width, preview_height)
        self.foreground_widget.set_preview_scale(self.preview_scale)
        self.foreground_widget.positionChanged.connect(self.on_foreground_dragged)

        # Create grid overlay for snap-to-grid visualization
        self.grid_overlay = GridOverlayWidget(self.preview_widget)
        self.grid_overlay.setGeometry(0, 0, preview_width, preview_height)
        self.grid_overlay.set_grid_size(DraggableWidget.get_grid_size())

        # Initialize preview manager with actual components (use base device dimensions)
        self.preview_manager = PreviewManager(self.config, self.preview_label, self.text_style)
        self.preview_manager.set_preview_scale(self.preview_scale)
        self.preview_manager.set_device_dimensions(base_width, base_height)

        # Add preview frame directly (aligned to top)
        parent_layout.addWidget(preview_frame, 0, Qt.AlignTop | Qt.AlignHCenter)

    def create_overlay_widgets(self):
        """Create all overlay widgets"""
        # Date widget
        self.date_widget = DateWidget(self.preview_widget)
        self.date_widget.move(200, 10)
        self.date_widget.apply_style(self.text_style)
        self.date_widget.set_enabled(True)
        self.date_widget.positionChanged.connect(lambda pos: self.on_widget_position_changed('date', pos))

        # Time widget
        self.time_widget = TimeWidget(self.preview_widget)
        self.time_widget.move(200, 40)
        self.time_widget.apply_style(self.text_style)
        self.time_widget.set_enabled(False)
        self.time_widget.positionChanged.connect(lambda pos: self.on_widget_position_changed('time', pos))

        # Metric widgets
        metrics_config = [
            "cpu_temperature", "gpu_temperature",
            "cpu_usage", "gpu_usage",
            "cpu_frequency", "gpu_frequency"
        ]

        self.metric_widgets = {}
        for metric_name in metrics_config:
            metric = self.cpu_metric if metric_name.startswith("cpu_") else self.gpu_metric
            widget = MetricWidget(metric=metric, parent=self.preview_widget, metric_name=metric_name)
            widget.apply_style(self.text_style)
            widget.set_enabled(False)
            widget.positionChanged.connect(lambda pos, name=metric_name: self.on_widget_position_changed(name, pos))
            self.metric_widgets[metric_name] = widget

        # Free text widgets
        self.text_widgets = {}
        for i in range(1, 5):
            widget_name = f"text{i}"
            widget = FreeTextWidget(parent=self.preview_widget, widget_name=widget_name)
            widget.apply_style(self.text_style)
            widget.set_enabled(False)
            widget.positionChanged.connect(lambda pos, name=widget_name: self.on_widget_position_changed(name, pos))
            self.text_widgets[widget_name] = widget

        # Ensure overlay widgets are above the foreground drag handle
        self._raise_overlay_widgets()

    def _raise_overlay_widgets(self):
        """Raise all overlay widgets above the foreground widget for proper z-order"""
        # Stack order (bottom to top): preview_label -> foreground_widget -> overlay widgets
        
        # First, raise the foreground widget above the preview_label
        if self.foreground_widget and self.preview_label:
            self.foreground_widget.raise_()
        
        # Then raise all overlay widgets above everything
        if self.date_widget:
            self.date_widget.raise_()
        if self.time_widget:
            self.time_widget.raise_()
        for widget in self.metric_widgets.values():
            if widget:
                widget.raise_()
        for widget in self.text_widgets.values():
            if widget:
                widget.raise_()

    def apply_style_to_all_widgets(self):
        """Apply current text style to all overlay widgets"""
        for widget in [self.date_widget, self.time_widget] + list(self.metric_widgets.values()) + list(self.text_widgets.values()):
            if widget:
                widget.apply_style(self.text_style)

    def setup_tabs_area(self, parent_layout):
        """Configure tabs area for media files"""
        self.tab_widget = QTabWidget()

        # Themes tab (moved to first position)

        themes_dir = f"{self.config.get('paths', {}).get('themes_dir', './themes')}/{self.dev_width}{self.dev_height}"
        self.themes_tab = ThemesTab(themes_dir, dev_width=self.dev_width, dev_height=self.dev_height)
        self.themes_tab.theme_selected.connect(self.on_theme_selected)
        self.media_tabs.append(self.themes_tab)
        self.tab_widget.addTab(self.themes_tab, "Themes")

        # Media tabs (Backgrounds and Foregrounds)
        for tab_name, media_dir, callback in [("Backgrounds", self.backgrounds_dir, self.on_background_clicked),
                                              ("Foregrounds", self.foregrounds_dir, self.on_foreground_clicked)]:
            tab = MediaTab(media_dir=media_dir, config=self.config, tab_name=tab_name)
            tab.thumbnail_clicked.connect(callback)
            if tab_name == "Backgrounds":
                tab.collection_created.connect(self.on_collection_created)

            self.media_tabs.append(tab)
            self.tab_widget.addTab(tab, tab_name)

        parent_layout.addWidget(self.tab_widget)

    def on_theme_selected(self, theme_path: str):
        """Handle theme selection"""
        self.logger.debug(f"on_theme_selected called with: {theme_path}")
        try:
            import yaml
            from pathlib import Path
            from PySide6.QtGui import QColor

            # Load theme configuration
            with open(theme_path, 'r', encoding='utf-8') as f:
                theme_config = yaml.safe_load(f)

            display_config = theme_config.get('display', {})
            self.logger.debug(f"Display config loaded: {display_config.keys()}")

            # Load rotation if specified
            rotation = display_config.get('rotation', 0)
            self.current_rotation = rotation
            if self.controls_manager and self.controls_manager.rotation_combo:
                # Find and set the correct index
                index = self.controls_manager.rotation_combo.findData(rotation)
                if index >= 0:
                    self.controls_manager.rotation_combo.setCurrentIndex(index)
            if self.preview_manager:
                self.preview_manager.set_rotation(rotation)

            # Load font family if specified
            font_family = display_config.get('font_family')
            if font_family:
                self.text_style.font_family = font_family
                if self.preview_manager:
                    self.preview_manager.text_style.font_family = font_family
                if self.controls_manager and self.controls_manager.font_combo:
                    from PySide6.QtGui import QFont
                    self.controls_manager.font_combo.setCurrentFont(QFont(font_family))

            # Load background
            background_config = display_config.get('background', {})
            self.logger.debug(f"Background config: {background_config}")
            background_path = background_config.get('path')
            background_scale_mode = background_config.get('scale_mode', 'stretch')
            background_enabled = background_config.get('enabled', True)
            background_color_config = background_config.get('color', {})
            background_color = (
                background_color_config.get('r', 0),
                background_color_config.get('g', 0),
                background_color_config.get('b', 0)
            )
            self.logger.debug(f"Background path: {background_path}")
            self.logger.debug(f"Preview manager exists: {self.preview_manager is not None}")

            if background_path and self.preview_manager:
                self.logger.debug(f"Setting background: {background_path}")
                self.preview_manager.set_background(background_path)
                self.preview_manager.set_background_scale_mode(background_scale_mode)
                self.preview_manager.set_background_enabled(background_enabled)
                self.preview_manager.set_background_color(background_color)
                # Update scale mode combo in controls
                if self.controls_manager and self.controls_manager.background_scale_combo:
                    index = self.controls_manager.background_scale_combo.findData(background_scale_mode)
                    if index >= 0:
                        self.controls_manager.background_scale_combo.setCurrentIndex(index)
                # Update background enabled checkbox
                if self.controls_manager and self.controls_manager.background_enabled_checkbox:
                    self.controls_manager.background_enabled_checkbox.setChecked(background_enabled)
                # Update background color button
                if self.controls_manager:
                    self.controls_manager.set_background_color(background_color)
            else:
                if not background_path:
                    self.logger.debug("Background path is empty or None")
                if not self.preview_manager:
                    self.logger.debug("Preview manager is None")

            # Load foreground if enabled
            foreground_config = display_config.get('foreground', {})
            foreground_enabled = foreground_config.get('enabled', False)
            
            # Update foreground enabled checkbox
            if self.controls_manager and self.controls_manager.foreground_enabled_checkbox:
                self.controls_manager.foreground_enabled_checkbox.setChecked(foreground_enabled)
            if self.preview_manager:
                self.preview_manager.set_foreground_enabled(foreground_enabled)
            
            if foreground_enabled:
                foreground_path = foreground_config.get('path').format(
                    resolution=f"{self.dev_width}{self.dev_height}")
                foreground_alpha = foreground_config.get('alpha', 1.0)
                foreground_position = foreground_config.get('position', {})
                self.logger.debug(f"Foreground path: {foreground_path}, alpha: {foreground_alpha}")

                if foreground_path and self.preview_manager:
                    self.preview_manager.set_foreground(foreground_path)
                    self.preview_manager.set_foreground_opacity(foreground_alpha)
                    
                    # Apply foreground position (device coordinates)
                    fg_x = foreground_position.get('x', 0)
                    fg_y = foreground_position.get('y', 0)
                    self.preview_manager.set_foreground_position(fg_x, fg_y)

                    # Update the draggable foreground widget (convert to preview coordinates)
                    if hasattr(self, 'foreground_widget') and self.foreground_widget:
                        self.foreground_widget.set_foreground_image(foreground_path, foreground_alpha)
                        # Scale position from device to preview coordinates
                        preview_x = int(fg_x * self.preview_scale)
                        preview_y = int(fg_y * self.preview_scale)
                        self.foreground_widget.move(preview_x, preview_y)
                        self._raise_overlay_widgets()  # Ensure overlays stay on top

                    # Update opacity controls
                    if self.controls_manager:
                        opacity_percentage = int(foreground_alpha * 100)
                        self.controls_manager.opacity_input.setValue(opacity_percentage)
                        
                        # Update position controls
                        if self.controls_manager.foreground_x_spin:
                            self.controls_manager.foreground_x_spin.setValue(fg_x)
                        if self.controls_manager.foreground_y_spin:
                            self.controls_manager.foreground_y_spin.setValue(fg_y)

            # Apply date widget configuration
            date_config = display_config.get('date', {})
            if date_config and self.date_widget:
                self.apply_widget_config(self.date_widget, date_config)

            # Apply time widget configuration
            time_config = display_config.get('time', {})
            if time_config and self.time_widget:
                self.apply_widget_config(self.time_widget, time_config)

            # Apply text effects configuration
            text_effects_config = display_config.get('text_effects', {})
            if text_effects_config:
                self.apply_text_effects_config(text_effects_config)

            # Apply metrics configurations
            metrics_config = display_config.get('metrics', {})
            if metrics_config and 'configs' in metrics_config:
                self.apply_metrics_config(metrics_config['configs'])

            # Apply custom text configurations
            custom_texts_config = display_config.get('custom_texts', [])
            if custom_texts_config:
                self.apply_custom_texts_config(custom_texts_config)

            # Update controls to reflect current widget states
            self.update_controls_from_widgets()

            self.logger.debug(f"Theme loaded: {Path(theme_path).name}")

        except Exception as e:
            self.logger.error(f"Exception in on_theme_selected: {e}")
            QMessageBox.warning(self, "Theme Load Error", f"Failed to load theme:\n{str(e)}")

    def apply_widget_config(self, widget, config):
        """Apply configuration to a date/time widget"""
        try:
            # Apply enabled state
            enabled = config.get('enabled', False)
            widget.set_enabled(enabled)

            # Apply position (1:1 scale - no conversion needed)
            position = config.get('position', {})
            if position:
                x = position.get('x', 0)
                y = position.get('y', 0)
                widget.move(x, y)

            # Apply font size
            font_size = config.get('font_size')
            if font_size:
                widget.set_font_size(font_size)
                # Update corresponding spinbox in controls
                if self.controls_manager:
                    widget_name = getattr(widget, 'name', '')
                    if widget_name == 'date' and hasattr(self.controls_manager, 'date_font_size_spin'):
                        self.controls_manager.date_font_size_spin.setValue(font_size)
                    elif widget_name == 'time' and hasattr(self.controls_manager, 'time_font_size_spin'):
                        self.controls_manager.time_font_size_spin.setValue(font_size)

            # Apply color
            color_hex = config.get('color')
            if color_hex:
                color = self.hex_to_qcolor(color_hex)
                if color:
                    self.text_style.color = color

            # Apply date-specific format options
            widget_name = getattr(widget, 'name', '')
            if widget_name == 'date':
                if 'show_weekday' in config and hasattr(widget, 'set_show_weekday'):
                    widget.set_show_weekday(config['show_weekday'])
                    if hasattr(self.controls_manager, 'show_weekday_checkbox'):
                        self.controls_manager.show_weekday_checkbox.setChecked(config['show_weekday'])
                if 'show_year' in config and hasattr(widget, 'set_show_year'):
                    widget.set_show_year(config['show_year'])
                    if hasattr(self.controls_manager, 'show_year_checkbox'):
                        self.controls_manager.show_year_checkbox.setChecked(config['show_year'])
                if 'date_format' in config and hasattr(widget, 'set_date_format'):
                    widget.set_date_format(config['date_format'])
                    if hasattr(self.controls_manager, 'date_format_combo'):
                        idx = self.controls_manager.date_format_combo.findData(config['date_format'])
                        if idx >= 0:
                            self.controls_manager.date_format_combo.setCurrentIndex(idx)

            # Apply time-specific format options
            if widget_name == 'time':
                if 'use_24_hour' in config and hasattr(widget, 'set_use_24_hour'):
                    widget.set_use_24_hour(config['use_24_hour'])
                    if hasattr(self.controls_manager, 'use_24_hour_checkbox'):
                        self.controls_manager.use_24_hour_checkbox.setChecked(config['use_24_hour'])
                if 'show_seconds' in config and hasattr(widget, 'set_show_seconds'):
                    widget.set_show_seconds(config['show_seconds'])
                    if hasattr(self.controls_manager, 'show_seconds_checkbox'):
                        self.controls_manager.show_seconds_checkbox.setChecked(config['show_seconds'])
                if 'show_am_pm' in config and hasattr(widget, 'set_show_am_pm'):
                    widget.set_show_am_pm(config['show_am_pm'])
                    if hasattr(self.controls_manager, 'show_am_pm_checkbox'):
                        self.controls_manager.show_am_pm_checkbox.setChecked(config['show_am_pm'])

            # Apply style to widget
            widget.apply_style(self.text_style)

        except Exception as e:
            self.logger.error(f"Error applying widget config: {e}")

    def apply_text_effects_config(self, text_effects_config):
        """Apply text effects configuration (shadow, outline, gradient)"""
        try:
            # Apply shadow settings
            shadow_config = text_effects_config.get('shadow', {})
            if shadow_config:
                self.text_style.shadow_enabled = shadow_config.get('enabled', False)
                shadow_color_hex = shadow_config.get('color', '#00000080')
                self.text_style.shadow_color = self.hex_to_qcolor(shadow_color_hex) or QColor(0, 0, 0, 128)
                self.text_style.shadow_offset_x = shadow_config.get('offset_x', 2)
                self.text_style.shadow_offset_y = shadow_config.get('offset_y', 2)
                self.text_style.shadow_blur = shadow_config.get('blur', 3)
                
                # Update UI controls
                if self.controls_manager:
                    if hasattr(self.controls_manager, 'shadow_enabled_checkbox'):
                        self.controls_manager.shadow_enabled_checkbox.setChecked(self.text_style.shadow_enabled)
                    if hasattr(self.controls_manager, 'shadow_x_spin'):
                        self.controls_manager.shadow_x_spin.setValue(self.text_style.shadow_offset_x)
                    if hasattr(self.controls_manager, 'shadow_y_spin'):
                        self.controls_manager.shadow_y_spin.setValue(self.text_style.shadow_offset_y)
                    if hasattr(self.controls_manager, 'shadow_blur_spin'):
                        self.controls_manager.shadow_blur_spin.setValue(self.text_style.shadow_blur)
                    if hasattr(self.controls_manager, '_update_shadow_color_button'):
                        self.controls_manager._update_shadow_color_button()

            # Apply outline settings
            outline_config = text_effects_config.get('outline', {})
            if outline_config:
                self.text_style.outline_enabled = outline_config.get('enabled', False)
                outline_color_hex = outline_config.get('color', '#000000FF')
                self.text_style.outline_color = self.hex_to_qcolor(outline_color_hex) or QColor(0, 0, 0)
                self.text_style.outline_width = outline_config.get('width', 1)
                
                # Update UI controls
                if self.controls_manager:
                    if hasattr(self.controls_manager, 'outline_enabled_checkbox'):
                        self.controls_manager.outline_enabled_checkbox.setChecked(self.text_style.outline_enabled)
                    if hasattr(self.controls_manager, 'outline_width_spin'):
                        self.controls_manager.outline_width_spin.setValue(self.text_style.outline_width)
                    if hasattr(self.controls_manager, '_update_outline_color_button'):
                        self.controls_manager._update_outline_color_button()

            # Apply gradient settings
            gradient_config = text_effects_config.get('gradient', {})
            if gradient_config:
                self.text_style.gradient_enabled = gradient_config.get('enabled', False)
                gradient_color1_hex = gradient_config.get('color1', '#FFFFFFFF')
                gradient_color2_hex = gradient_config.get('color2', '#6464FFFF')
                self.text_style.gradient_color1 = self.hex_to_qcolor(gradient_color1_hex) or QColor(255, 255, 255)
                self.text_style.gradient_color2 = self.hex_to_qcolor(gradient_color2_hex) or QColor(100, 100, 255)
                self.text_style.gradient_direction = gradient_config.get('direction', 'vertical')
                
                # Update UI controls
                if self.controls_manager:
                    if hasattr(self.controls_manager, 'gradient_enabled_checkbox'):
                        self.controls_manager.gradient_enabled_checkbox.setChecked(self.text_style.gradient_enabled)
                    if hasattr(self.controls_manager, 'gradient_direction_combo'):
                        idx = self.controls_manager.gradient_direction_combo.findData(self.text_style.gradient_direction)
                        if idx >= 0:
                            self.controls_manager.gradient_direction_combo.setCurrentIndex(idx)
                    if hasattr(self.controls_manager, '_update_gradient_color1_button'):
                        self.controls_manager._update_gradient_color1_button()
                    if hasattr(self.controls_manager, '_update_gradient_color2_button'):
                        self.controls_manager._update_gradient_color2_button()

            # Apply styles to all widgets
            self.apply_style_to_all_widgets()

        except Exception as e:
            self.logger.error(f"Error applying text effects config: {e}")

    def apply_metrics_config(self, metrics_configs):
        """Apply configurations to metric widgets"""
        try:
            # First disable all metrics
            for metric_widget in self.metric_widgets.values():
                metric_widget.set_enabled(False)

            # Apply configuration for each metric
            for metric_config in metrics_configs:
                metric_name = metric_config.get('name')
                if metric_name not in self.metric_widgets:
                    continue

                widget = self.metric_widgets[metric_name]

                # Apply enabled state
                enabled = metric_config.get('enabled', False)
                widget.set_enabled(enabled)

                # Apply position (1:1 scale - no conversion needed)
                position = metric_config.get('position', {})
                if position:
                    x = position.get('x', 0)
                    y = position.get('y', 0)
                    widget.move(x, y)

                # Apply custom label and unit
                label = metric_config.get('label', '')
                self.logger.debug(f"metric: {metric_name} Label: {label}")
                unit = metric_config.get('unit', '')
                widget.set_custom_label(label)
                widget.set_custom_unit(unit)

                # Apply label position
                label_position = metric_config.get('label_position', 'left')
                widget.set_label_position(label_position)
                
                # Update label position combo in controls
                if self.controls_manager and metric_name in self.controls_manager.metric_label_position_combos:
                    combo = self.controls_manager.metric_label_position_combos[metric_name]
                    index = combo.findData(label_position)
                    if index >= 0:
                        combo.setCurrentIndex(index)

                # Apply font size and color (create a temporary style for this metric)
                font_size = metric_config.get('font_size')
                label_font_size = metric_config.get('label_font_size')
                color_hex = metric_config.get('color')

                if font_size:
                    widget.set_font_size(font_size)
                    # Update font size spinbox in controls
                    if self.controls_manager and hasattr(self.controls_manager, 'metric_font_size_spins'):
                        if metric_name in self.controls_manager.metric_font_size_spins:
                            self.controls_manager.metric_font_size_spins[metric_name].setValue(font_size)

                if label_font_size:
                    widget.set_label_font_size(label_font_size)
                    # Update label font size spinbox in controls
                    if self.controls_manager and hasattr(self.controls_manager, 'metric_label_font_size_spins'):
                        if metric_name in self.controls_manager.metric_label_font_size_spins:
                            self.controls_manager.metric_label_font_size_spins[metric_name].setValue(label_font_size)

                # Apply frequency format for frequency metrics
                if 'frequency' in metric_name:
                    freq_format = metric_config.get('freq_format', 'mhz')
                    if hasattr(widget, 'set_freq_format'):
                        widget.set_freq_format(freq_format)
                    # Update frequency format combo in controls
                    if self.controls_manager and hasattr(self.controls_manager, 'metric_freq_format_combos'):
                        if metric_name in self.controls_manager.metric_freq_format_combos:
                            combo = self.controls_manager.metric_freq_format_combos[metric_name]
                            index = combo.findData(freq_format)
                            if index >= 0:
                                combo.setCurrentIndex(index)

                if font_size or color_hex:
                    # Create a copy of the current text style for this metric
                    metric_style = TextStyleConfig()
                    metric_style.font_size = font_size if font_size else self.text_style.font_size

                    if color_hex:
                        color = self.hex_to_qcolor(color_hex)
                        metric_style.color = color if color else self.text_style.color
                    else:
                        metric_style.color = self.text_style.color

                    widget.apply_style(metric_style)
                else:
                    widget.apply_style(self.text_style)

                # Update widget display
                widget.update_display()

        except Exception as e:
            self.logger.error(f"Error applying metrics config: {e}")

    def apply_custom_texts_config(self, texts_configs):
        """Apply configurations to custom text widgets"""
        try:
            # First disable all text widgets
            for text_widget in self.text_widgets.values():
                text_widget.set_enabled(False)

            # Apply configuration for each text widget
            for text_config in texts_configs:
                text_name = text_config.get('name')
                if text_name not in self.text_widgets:
                    continue

                widget = self.text_widgets[text_name]

                # Apply enabled state
                enabled = text_config.get('enabled', False)
                widget.set_enabled(enabled)

                # Apply position (1:1 scale - no conversion needed)
                position = text_config.get('position', {})
                if position:
                    x = position.get('x', 0)
                    y = position.get('y', 0)
                    widget.move(x, y)

                # Apply text content
                text = text_config.get('text', '')
                widget.set_text(text)

                # Apply font size
                font_size = text_config.get('font_size')
                if font_size:
                    widget.set_font_size(font_size)
                    if self.controls_manager and hasattr(self.controls_manager, 'text_font_size_spins'):
                        if text_name in self.controls_manager.text_font_size_spins:
                            self.controls_manager.text_font_size_spins[text_name].setValue(font_size)

                # Update controls
                if self.controls_manager:
                    if hasattr(self.controls_manager, 'text_checkboxes') and text_name in self.controls_manager.text_checkboxes:
                        self.controls_manager.text_checkboxes[text_name].setChecked(enabled)
                    if hasattr(self.controls_manager, 'text_inputs') and text_name in self.controls_manager.text_inputs:
                        self.controls_manager.text_inputs[text_name].setText(text)

                widget.apply_style(self.text_style)
                widget.update_display()

        except Exception as e:
            self.logger.error(f"Error applying custom texts config: {e}")

    def update_controls_from_widgets(self):
        """Update control interface to reflect current widget states"""
        try:
            if not self.controls_manager:
                return

            # Update date checkbox and font size
            if hasattr(self.controls_manager, 'show_date_checkbox'):
                self.controls_manager.show_date_checkbox.setChecked(
                    self.date_widget.enabled if self.date_widget else False)
            if self.date_widget and hasattr(self.controls_manager, 'date_font_size_spin'):
                self.controls_manager.date_font_size_spin.setValue(self.date_widget.get_font_size())

            # Update time checkbox and font size
            if hasattr(self.controls_manager, 'show_time_checkbox'):
                self.controls_manager.show_time_checkbox.setChecked(
                    self.time_widget.enabled if self.time_widget else False)
            if self.time_widget and hasattr(self.controls_manager, 'time_font_size_spin'):
                self.controls_manager.time_font_size_spin.setValue(self.time_widget.get_font_size())

            for metric_name, widget in self.metric_widgets.items():
                # Update checkbox
                if hasattr(self.controls_manager, 'metric_checkboxes'):
                    checkbox = self.controls_manager.metric_checkboxes[metric_name]
                    checkbox.setChecked(widget.enabled)

                if hasattr(self.controls_manager, 'metric_unit_inputs') and widget.enabled:
                    label_input = self.controls_manager.metric_label_inputs[metric_name]
                    label_input.setText(widget.get_label())

                # Update unit input
                if hasattr(self.controls_manager, 'metric_unit_inputs') and widget.enabled:
                    unit_input = self.controls_manager.metric_unit_inputs[metric_name]
                    unit_input.setText(widget.get_unit())

                # Update font size spinbox
                if hasattr(self.controls_manager, 'metric_font_size_spins'):
                    if metric_name in self.controls_manager.metric_font_size_spins:
                        self.controls_manager.metric_font_size_spins[metric_name].setValue(widget.get_font_size())

                # Update label font size spinbox
                if hasattr(self.controls_manager, 'metric_label_font_size_spins'):
                    if metric_name in self.controls_manager.metric_label_font_size_spins:
                        self.controls_manager.metric_label_font_size_spins[metric_name].setValue(widget.get_label_font_size())

            # Update font size control
            if hasattr(self.controls_manager, 'font_size_spin'):
                self.controls_manager.font_size_spin.setValue(self.text_style.font_size)

            # Update color button
            if hasattr(self.controls_manager, 'update_color_button'):
                self.controls_manager.update_color_button()

        except Exception as e:
            self.logger.error(f"Error updating controls from widgets: {e}")

    def hex_to_qcolor(self, hex_color: str) -> QColor:
        """Convert hex color string to QColor"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')

            # Handle different hex formats
            if len(hex_color) == 6:  # RGB
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return QColor(r, g, b)
            elif len(hex_color) == 8:  # RGBA
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                a = int(hex_color[6:8], 16)
                return QColor(r, g, b, a)
            else:
                self.logger.error(f"Invalid hex color format: {hex_color}")
                return None

        except ValueError as e:
            self.logger.error(f"Error parsing hex color {hex_color}: {e}")
            return None

    # Event handlers
    def choose_color(self):
        """Open color chooser dialog"""
        color = QColorDialog.getColor(self.text_style.color, self)
        if color.isValid():
            self.text_style.color = color
            self.controls_manager.update_color_button()
            self.apply_style_to_all_widgets()

    # Shadow handlers
    def on_shadow_enabled_changed(self, enabled):
        """Handle shadow enabled toggle"""
        self.text_style.shadow_enabled = enabled
        self.apply_style_to_all_widgets()

    def choose_shadow_color(self):
        """Open shadow color chooser dialog"""
        color = QColorDialog.getColor(self.text_style.shadow_color, self)
        if color.isValid():
            self.text_style.shadow_color = color
            self.controls_manager._update_shadow_color_button()
            self.apply_style_to_all_widgets()

    def on_shadow_offset_x_changed(self, value):
        """Handle shadow X offset change"""
        self.text_style.shadow_offset_x = value
        self.apply_style_to_all_widgets()

    def on_shadow_offset_y_changed(self, value):
        """Handle shadow Y offset change"""
        self.text_style.shadow_offset_y = value
        self.apply_style_to_all_widgets()

    def on_shadow_blur_changed(self, value):
        """Handle shadow blur change"""
        self.text_style.shadow_blur = value
        self.apply_style_to_all_widgets()

    # Outline handlers
    def on_outline_enabled_changed(self, enabled):
        """Handle outline enabled toggle"""
        self.text_style.outline_enabled = enabled
        self.apply_style_to_all_widgets()

    def choose_outline_color(self):
        """Open outline color chooser dialog"""
        color = QColorDialog.getColor(self.text_style.outline_color, self)
        if color.isValid():
            self.text_style.outline_color = color
            self.controls_manager._update_outline_color_button()
            self.apply_style_to_all_widgets()

    def on_outline_width_changed(self, value):
        """Handle outline width change"""
        self.text_style.outline_width = value
        self.apply_style_to_all_widgets()

    # Gradient handlers
    def on_gradient_enabled_changed(self, enabled):
        """Handle gradient enabled toggle"""
        self.text_style.gradient_enabled = enabled
        self.apply_style_to_all_widgets()

    def choose_gradient_color1(self):
        """Open gradient color 1 chooser dialog"""
        color = QColorDialog.getColor(self.text_style.gradient_color1, self)
        if color.isValid():
            self.text_style.gradient_color1 = color
            self.controls_manager._update_gradient_color1_button()
            self.apply_style_to_all_widgets()

    def choose_gradient_color2(self):
        """Open gradient color 2 chooser dialog"""
        color = QColorDialog.getColor(self.text_style.gradient_color2, self)
        if color.isValid():
            self.text_style.gradient_color2 = color
            self.controls_manager._update_gradient_color2_button()
            self.apply_style_to_all_widgets()

    def on_gradient_direction_changed(self, direction):
        """Handle gradient direction change"""
        self.text_style.gradient_direction = direction
        self.apply_style_to_all_widgets()

    def on_rotation_changed(self, rotation):
        """Handle rotation change"""
        self.current_rotation = rotation
        if self.preview_manager:
            self.preview_manager.set_rotation(rotation)

    def on_snap_to_grid_changed(self, enabled):
        """Handle snap-to-grid toggle"""
        if hasattr(self, 'grid_overlay'):
            self.grid_overlay.set_visible(enabled)

    def on_grid_size_changed(self, size):
        """Handle grid size change"""
        if hasattr(self, 'grid_overlay'):
            self.grid_overlay.set_grid_size(size)

    def on_background_scale_changed(self, scale_mode):
        """Handle background scaling mode change"""
        if self.preview_manager:
            self.preview_manager.set_background_scale_mode(scale_mode)

    def on_background_enabled_changed(self, enabled):
        """Handle background enabled/disabled toggle"""
        if self.preview_manager:
            self.preview_manager.set_background_enabled(enabled)

    def on_background_opacity_changed(self, opacity):
        """Handle background opacity change"""
        if self.preview_manager:
            self.preview_manager.set_background_opacity(opacity)

    def on_background_color_changed(self, color):
        """Handle background color change"""
        if self.preview_manager:
            self.preview_manager.set_background_color(color)

    def on_foreground_enabled_changed(self, enabled):
        """Handle foreground enabled/disabled toggle"""
        if self.preview_manager:
            self.preview_manager.set_foreground_enabled(enabled)
        # Also show/hide the foreground drag widget
        if hasattr(self, 'foreground_widget') and self.foreground_widget:
            if enabled:
                self.foreground_widget.show()
            else:
                self.foreground_widget.hide()

    def on_widget_position_changed(self, widget_name, pos):
        """Handle widget position change from dragging"""
        # Convert scaled position to device coordinates
        device_x = int(pos.x() / self.preview_scale)
        device_y = int(pos.y() / self.preview_scale)
        self.logger.debug(f"Widget {widget_name} moved to device coords ({device_x}, {device_y})")
        # Update position labels in controls if they exist
        if self.controls_manager:
            if widget_name == 'date' and hasattr(self.controls_manager, 'date_position_label'):
                if self.controls_manager.date_position_label:
                    self.controls_manager.date_position_label.setText(f"({device_x}, {device_y})")
            elif widget_name == 'time' and hasattr(self.controls_manager, 'time_position_label'):
                if self.controls_manager.time_position_label:
                    self.controls_manager.time_position_label.setText(f"({device_x}, {device_y})")
            elif widget_name in self.controls_manager.metric_position_labels:
                label = self.controls_manager.metric_position_labels.get(widget_name)
                if label:
                    label.setText(f"({device_x}, {device_y})")

    def on_foreground_dragged(self, x, y):
        """Handle foreground widget being dragged in preview"""
        # Convert scaled position to device coordinates
        device_x = int(x / self.preview_scale)
        device_y = int(y / self.preview_scale)
        self.logger.debug(f"Foreground dragged to device coords ({device_x}, {device_y})")
        if self.preview_manager:
            self.preview_manager.set_foreground_position(device_x, device_y)
        # Update the position spinboxes in controls
        if self.controls_manager:
            if self.controls_manager.foreground_x_spin:
                self.controls_manager.foreground_x_spin.blockSignals(True)
                self.controls_manager.foreground_x_spin.setValue(device_x)
                self.controls_manager.foreground_x_spin.blockSignals(False)
            if self.controls_manager.foreground_y_spin:
                self.controls_manager.foreground_y_spin.blockSignals(True)
                self.controls_manager.foreground_y_spin.setValue(device_y)
                self.controls_manager.foreground_y_spin.blockSignals(False)

    def on_foreground_position_changed(self, x, y):
        """Handle foreground position change from controls (x, y are in device coordinates)"""
        self.logger.debug(f"Foreground position changed to ({x}, {y})")
        if self.preview_manager:
            self.preview_manager.set_foreground_position(x, y)
        # Also update the draggable foreground widget position (convert to preview coordinates)
        if hasattr(self, 'foreground_widget') and self.foreground_widget:
            self.foreground_widget.blockSignals(True)
            preview_x = int(x * self.preview_scale)
            preview_y = int(y * self.preview_scale)
            self.foreground_widget.move(preview_x, preview_y)
            self.foreground_widget.blockSignals(False)

    def on_font_size_changed(self, size):
        """Handle global font size change"""
        self.text_style.font_size = size
        self.apply_style_to_all_widgets()

    def on_font_family_changed(self, font_family):
        """Handle font family change"""
        self.text_style.font_family = font_family
        self.apply_style_to_all_widgets()
        # Update the preview manager's text style for config generation
        if self.preview_manager:
            self.preview_manager.text_style.font_family = font_family

    def on_widget_font_size_changed(self, widget_name, size):
        """Handle individual widget font size change"""
        if widget_name == 'date' and self.date_widget:
            self.date_widget.set_font_size(size)
        elif widget_name == 'time' and self.time_widget:
            self.time_widget.set_font_size(size)

    def on_metric_font_size_changed(self, metric_name, size):
        """Handle individual metric font size change"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_font_size(size)

    def on_metric_label_font_size_changed(self, metric_name, size):
        """Handle individual metric label font size change"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_label_font_size(size)

    # Free text widget handlers
    def on_text_toggled(self, text_name, enabled):
        """Handle free text widget toggle"""
        if text_name in self.text_widgets:
            self.text_widgets[text_name].set_enabled(enabled)

    def on_text_changed(self, text_name, text):
        """Handle free text content change"""
        if text_name in self.text_widgets:
            self.text_widgets[text_name].set_text(text)

    def on_text_font_size_changed(self, text_name, size):
        """Handle free text font size change"""
        if text_name in self.text_widgets:
            self.text_widgets[text_name].set_font_size(size)

    def on_opacity_text_changed(self, text):
        """Handle opacity text input change (real-time)"""
        if text and text.replace('.', '').isdigit():
            try:
                value = float(text)
                if 0 <= value <= 100:
                    self.preview_manager.set_foreground_opacity(value / 100.0)
            except ValueError:
                pass

    def on_opacity_editing_finished(self):
        """Handle opacity input when editing is finished"""
        value = self.controls_manager.opacity_input.value()
        if not value:
            self.controls_manager.opacity_input.setValue(50)
            self.preview_manager.set_foreground_opacity(0.5)
        else:
            try:
                value = max(0, min(100, float(value)))
                self.controls_manager.opacity_input.setValue(int(value))
                self.preview_manager.set_foreground_opacity(value / 100.0)
            except ValueError:
                current_percentage = int(self.preview_manager.foreground_opacity * 100)
                self.controls_manager.opacity_input.setValue(current_percentage)

    def on_show_date_changed(self, checked):
        """Handle show date checkbox change"""
        if self.date_widget:
            self.date_widget.set_enabled(checked)

    def on_show_time_changed(self, checked):
        """Handle show time checkbox change"""
        if self.time_widget:
            self.time_widget.set_enabled(checked)

    # Date format options
    def on_date_format_changed(self, format_type):
        """Handle date format change"""
        if self.date_widget:
            self.date_widget.set_date_format(format_type)

    def on_show_weekday_changed(self, checked):
        """Handle show weekday checkbox change"""
        if self.date_widget:
            self.date_widget.set_show_weekday(checked)

    def on_show_year_changed(self, checked):
        """Handle show year checkbox change"""
        if self.date_widget:
            self.date_widget.set_show_year(checked)

    # Time format options
    def on_use_24_hour_changed(self, checked):
        """Handle 24-hour format checkbox change"""
        if self.time_widget:
            self.time_widget.set_use_24_hour(checked)
            # Disable AM/PM when using 24-hour format
            if hasattr(self.controls_manager, 'show_am_pm_checkbox'):
                self.controls_manager.show_am_pm_checkbox.setEnabled(not checked)

    def on_show_seconds_changed(self, checked):
        """Handle show seconds checkbox change"""
        if self.time_widget:
            self.time_widget.set_show_seconds(checked)

    def on_show_am_pm_changed(self, checked):
        """Handle show AM/PM checkbox change"""
        if self.time_widget:
            self.time_widget.set_show_am_pm(checked)

    def on_metric_toggled(self, metric_name, checked):
        """Handle metric checkbox toggle"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_enabled(checked)

    def on_metric_label_changed(self, metric_name, text):
        """Handle metric label change"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_custom_label(text.strip())

    def on_metric_unit_changed(self, metric_name, text):
        """Handle metric unit change"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_custom_unit(text.strip())

    def on_metric_freq_format_changed(self, metric_name, format_type):
        """Handle metric frequency format change (MHz/GHz)"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_freq_format(format_type)
            self.logger.debug(f"Metric {metric_name} frequency format changed to {format_type}")

    def on_metric_label_position_changed(self, metric_name, position):
        """Handle metric label position change"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_label_position(position)
            self.logger.debug(f"Metric {metric_name} label position changed to {position}")

    def on_collection_created(self, collection_path):
        """Handle collection creation"""
        self.on_background_clicked(collection_path)

    def on_background_clicked(self, file_path):
        """Handle background thumbnail click"""
        self.preview_manager.set_background(file_path)

    def on_foreground_clicked(self, file_path):
        """Handle foreground thumbnail click"""
        from pathlib import Path
        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix.lower()
        supported_formats = self.config.get('supported_formats', {})
        image_extensions = set(supported_formats.get('images', []))

        if extension in image_extensions or extension == '.gif':
            self.preview_manager.set_foreground(file_path)
            # Update the draggable foreground widget
            if hasattr(self, 'foreground_widget') and self.foreground_widget:
                opacity = self.preview_manager.foreground_opacity
                self.foreground_widget.set_foreground_image(file_path, opacity)
                # Reset position to current preview manager position (convert to preview coordinates)
                pos = self.preview_manager.get_foreground_position()
                preview_x = int(pos[0] * self.preview_scale)
                preview_y = int(pos[1] * self.preview_scale)
                self.foreground_widget.move(preview_x, preview_y)
                self._raise_overlay_widgets()  # Ensure overlays stay on top
        else:
            self.preview_label.setText("Only images are supported\nfor foreground overlay")

    def clear_background(self):
        """Clear background media"""
        self.preview_manager.clear_background(self.backgrounds_dir)

    def clear_foreground(self):
        """Clear foreground media"""
        self.preview_manager.clear_foreground()
        # Also clear the draggable foreground widget
        if hasattr(self, 'foreground_widget') and self.foreground_widget:
            self.foreground_widget.clear_foreground()

    def clear_all(self):
        """Clear all media"""
        self.preview_manager.clear_all(self.backgrounds_dir)

    def generate_config_yaml(self):
        """Generate YAML configuration file"""
        config_path = self.config_generator.generate_config_yaml(
            self.preview_manager, self.text_style, self.metric_widgets,
            self.date_widget, self.time_widget, self.text_widgets
        )
        if config_path:
            self.themes_tab.refresh_themes()

    def generate_preview(self):
        """Generate YAML configuration file"""
        self.config_generator.generate_config_yaml(
            self.preview_manager, self.text_style, self.metric_widgets,
            self.date_widget, self.time_widget, self.text_widgets, preview=True
        )

    def closeEvent(self, event):
        """Cleanup on close"""
        # Stop overlay widget timers
        for widget in [self.date_widget, self.time_widget]:
            if widget and hasattr(widget, 'update_timer'):
                widget.update_timer.stop()

        if self.preview_manager:
            self.preview_manager.cleanup()

        for tab in self.media_tabs:
            if hasattr(tab, 'cleanup_thumbnails'):
                tab.cleanup_thumbnails()

        super().closeEvent(event)
