# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Main window for Media Preview application"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtWidgets import (QTabWidget, QFrame, QColorDialog, QMessageBox, QInputDialog, QComboBox, QLabel as QWidgetLabel)
from PySide6.QtCore import QTimer

from thermalright_lcd_control.gui.components.config_generator import ConfigGenerator
from thermalright_lcd_control.gui.components.controls_manager import ControlsManager
from thermalright_lcd_control.gui.components.preview_manager import PreviewManager
from thermalright_lcd_control.gui.tabs.media_tab import MediaTab
from thermalright_lcd_control.gui.tabs.themes_tab import ThemesTab
from thermalright_lcd_control.gui.tabs.cpu_tab import CPUTab
from thermalright_lcd_control.gui.tabs.gpu_tab import GPUTab
from thermalright_lcd_control.gui.tabs.info_tab import InfoTab
from thermalright_lcd_control.gui.utils.config_loader import load_config
from thermalright_lcd_control.gui.widgets.draggable_widget import *
from thermalright_lcd_control.gui.widgets.widget_palette import WidgetPalette
from thermalright_lcd_control.gui.widgets.drop_preview import DropPreviewWidget
from thermalright_lcd_control.common.logging_config import get_gui_logger
from thermalright_lcd_control.device_controller.metrics.cpu_metrics import CpuMetrics
from thermalright_lcd_control.device_controller.metrics.gpu_metrics import GpuMetrics
from thermalright_lcd_control.device_controller.display.config import DateConfig, TimeConfig, MetricConfig, TextConfig, LabelPosition, BarGraphConfig, CircularGraphConfig


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
        self.refresh_interval = 1.0  # Default LCD refresh interval in seconds

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
        self.bar_widgets = {}   # Bar graph widgets
        self.arc_widgets = {}   # Circular graph widgets
        
        # Track currently loaded theme for save/update
        self.current_theme_path = None
        
        # Debounce timer for position updates during dragging
        self._position_update_timer = QTimer()
        self._position_update_timer.setSingleShot(True)
        self._position_update_timer.setInterval(50)  # 50ms debounce
        self._position_update_timer.timeout.connect(self._do_update_preview_widget_configs)

        # Initialize UI
        self.setup_window()
        self.setup_ui()

    def setup_window(self):
        """Configure window size and properties"""
        # No stylesheet - using Fusion style + palette set in main_gui.py
        
        window_config = self.config.get('window', {})
        default_width = window_config.get('default_width', 1400)
        default_height = window_config.get('default_height', 600)

        min_width = max(window_config.get('min_width', 1000), self.dev_width + 720)
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

        # Connect application focus change to track widget selection
        from PySide6.QtWidgets import QApplication
        QApplication.instance().focusChanged.connect(self._on_app_focus_changed)

        # Initialize widget configs for preview rendering
        self.update_preview_widget_configs()

        # Controls (now that metric_widgets exists) - takes remaining space
        self.controls_manager = ControlsManager(self, self.text_style, self.metric_widgets)
        
        # Widget palette (collapsible, expands upward) - above action buttons
        self.widget_palette = WidgetPalette(expand_upward=True)
        left_layout.addWidget(self.widget_palette)
        
        # Action buttons stay fixed at top (outside scroll area)
        left_layout.addWidget(self.controls_manager.create_action_buttons())
        
        # Scrollable controls
        left_layout.addWidget(self.controls_manager.create_controls_widget(), 1)

        # Right side (tabs)
        right_widget = QWidget()
        right_widget.setMinimumWidth(1020)
        right_widget.setMaximumWidth(1100)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.setup_tabs_area(right_layout)

        main_layout.addWidget(left_widget, 6)
        main_layout.addWidget(right_widget, 4)
        
        # Load the initial theme
        self.themes_tab.auto_load_first_theme()

    def setup_preview_area(self, parent_layout):
        """Configure preview area with device-specific size"""
        # Store base device dimensions for scaling calculations
        self.base_device_width = self.detected_device['width'] if self.detected_device else 320
        self.base_device_height = self.detected_device['height'] if self.detected_device else 240
        
        # Default to 1.5x scale for better visibility
        self.preview_scale = 1.5
        preview_width = int(self.base_device_width * self.preview_scale)
        preview_height = int(self.base_device_height * self.preview_scale)

        # Container for preview and zoom controls
        preview_container = QWidget()
        preview_container_layout = QVBoxLayout(preview_container)
        preview_container_layout.setContentsMargins(0, 0, 0, 0)
        preview_container_layout.setSpacing(4)
        
        # Zoom controls row
        zoom_row = QWidget()
        zoom_layout = QHBoxLayout(zoom_row)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.setSpacing(4)
        
        # Create zoom button group
        self.zoom_buttons = {}
        zoom_btn_style_normal = """
            QPushButton {
                background-color: #ecf0f1;
                border: 1px solid #dcdde1;
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: 500;
                color: #2c3e50;
                min-width: 45px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
        """
        zoom_btn_style_active = """
            QPushButton {
                background-color: #3498db;
                border: 1px solid #2980b9;
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: bold;
                color: white;
                min-width: 45px;
            }
        """
        
        for zoom_value, label in [(1.0, "100%"), (1.5, "150%"), (2.0, "200%")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(zoom_btn_style_normal)
            btn.clicked.connect(lambda checked, z=zoom_value: self._on_zoom_button_clicked(z))
            self.zoom_buttons[zoom_value] = btn
        
        # Set default (150%) as active
        self.zoom_buttons[1.5].setChecked(True)
        self.zoom_buttons[1.5].setStyleSheet(zoom_btn_style_active)
        
        # Store styles for later use
        self._zoom_btn_style_normal = zoom_btn_style_normal
        self._zoom_btn_style_active = zoom_btn_style_active
        
        zoom_layout.addStretch()
        for zoom_value in [1.0, 1.5, 2.0]:
            zoom_layout.addWidget(self.zoom_buttons[zoom_value])
        zoom_layout.addStretch()
        
        preview_container_layout.addWidget(zoom_row)

        # Preview frame
        frame_width, frame_height = preview_width + 4, preview_height + 4
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("previewFrame")
        self.preview_frame.setFixedSize(frame_width, frame_height)

        # Preview widget - use DropPreviewWidget to accept widget palette drops
        self.preview_widget = DropPreviewWidget(self.preview_frame)
        self.preview_widget.setGeometry(2, 2, preview_width, preview_height)
        self.preview_widget.setStyleSheet("background-color: #ecf0f1;")
        self.preview_widget.widget_dropped.connect(self._on_palette_widget_dropped)

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

        # Create resize handle manager for resizing selected widgets
        self.resize_handle_manager = ResizeHandleManager(self.preview_widget)
        self.resize_handle_manager.set_preview_scale(self.preview_scale)
        self.resize_handle_manager.sizeChanged.connect(self._on_widget_size_changed)
        self.resize_handle_manager.rotationChanged.connect(self._on_widget_rotation_changed)

        # Initialize preview manager with actual components (use base device dimensions)
        self.preview_manager = PreviewManager(self.config, self.preview_label, self.text_style)
        self.preview_manager.set_preview_scale(self.preview_scale)
        self.preview_manager.set_device_dimensions(self.base_device_width, self.base_device_height)

        # Add preview frame to container
        preview_container_layout.addWidget(self.preview_frame, 0, Qt.AlignHCenter)
        
        parent_layout.addWidget(preview_container, 0, Qt.AlignTop | Qt.AlignHCenter)

    def _on_zoom_button_clicked(self, zoom_value: float):
        """Handle zoom button click"""
        # Update button styles
        for z, btn in self.zoom_buttons.items():
            if z == zoom_value:
                btn.setChecked(True)
                btn.setStyleSheet(self._zoom_btn_style_active)
            else:
                btn.setChecked(False)
                btn.setStyleSheet(self._zoom_btn_style_normal)
        
        # Apply the zoom change
        self._apply_zoom(zoom_value)

    def _apply_zoom(self, new_scale: float):
        
        if new_scale == self.preview_scale:
            return
        
        old_scale = self.preview_scale
        self.preview_scale = new_scale
        
        # Calculate new preview dimensions
        preview_width = int(self.base_device_width * self.preview_scale)
        preview_height = int(self.base_device_height * self.preview_scale)
        
        # Resize preview frame and widget
        self.preview_frame.setFixedSize(preview_width + 4, preview_height + 4)
        self.preview_widget.setGeometry(2, 2, preview_width, preview_height)
        self.preview_label.setGeometry(0, 0, preview_width, preview_height)
        
        # Resize grid overlay
        self.grid_overlay.setGeometry(0, 0, preview_width, preview_height)
        
        # Update foreground widget bounds and scale
        self.foreground_widget.setGeometry(0, 0, preview_width, preview_height)
        self.foreground_widget.set_preview_scale(self.preview_scale)
        self.foreground_widget._preview_bounds = (preview_width, preview_height)
        
        # Update preview manager scale
        self.preview_manager.set_preview_scale(self.preview_scale)
        
        # Rescale all widget positions (convert from old scale to new scale)
        scale_ratio = new_scale / old_scale
        
        # Date widget - update scale and position
        if hasattr(self, 'date_widget') and self.date_widget:
            old_pos = self.date_widget.pos()
            new_x = int(old_pos.x() * scale_ratio)
            new_y = int(old_pos.y() * scale_ratio)
            self.date_widget.set_preview_scale(self.preview_scale)
            self.date_widget.move(new_x, new_y)
        
        # Time widget - update scale and position
        if hasattr(self, 'time_widget') and self.time_widget:
            old_pos = self.time_widget.pos()
            new_x = int(old_pos.x() * scale_ratio)
            new_y = int(old_pos.y() * scale_ratio)
            self.time_widget.set_preview_scale(self.preview_scale)
            self.time_widget.move(new_x, new_y)
        
        # Metric widgets - update scale and position
        for widget in self.metric_widgets.values():
            old_pos = widget.pos()
            new_x = int(old_pos.x() * scale_ratio)
            new_y = int(old_pos.y() * scale_ratio)
            widget.set_preview_scale(self.preview_scale)
            widget.move(new_x, new_y)
        
        # Text widgets - update scale and position
        for widget in self.text_widgets.values():
            old_pos = widget.pos()
            new_x = int(old_pos.x() * scale_ratio)
            new_y = int(old_pos.y() * scale_ratio)
            widget.set_preview_scale(self.preview_scale)
            widget.move(new_x, new_y)
        
        # Bar widgets - update scale and position
        for widget in self.bar_widgets.values():
            old_pos = widget.pos()
            new_x = int(old_pos.x() * scale_ratio)
            new_y = int(old_pos.y() * scale_ratio)
            widget.set_preview_scale(self.preview_scale)
            widget.move(new_x, new_y)
        
        # Arc widgets - update scale and position
        for widget in self.arc_widgets.values():
            old_pos = widget.pos()
            new_x = int(old_pos.x() * scale_ratio)
            new_y = int(old_pos.y() * scale_ratio)
            widget.set_preview_scale(self.preview_scale)
            widget.move(new_x, new_y)
        
        # Update resize handle manager scale and positions
        if hasattr(self, 'resize_handle_manager'):
            self.resize_handle_manager.set_preview_scale(self.preview_scale)
        
        # Refresh preview to apply new scale
        self.preview_manager.create_display_generator()
        
        self.logger.info(f"Preview zoom changed to {int(new_scale * 100)}%")

    def create_overlay_widgets(self):
        """Create all overlay widgets"""
        # Date widget - scale initial position and set preview scale
        self.date_widget = DateWidget(self.preview_widget)
        self.date_widget.set_preview_scale(self.preview_scale)
        self.date_widget.move(int(200 * self.preview_scale), int(10 * self.preview_scale))
        self.date_widget.apply_style(self.text_style)
        self.date_widget.set_enabled(True)
        self.date_widget.positionChanged.connect(lambda pos: self.on_widget_position_changed('date', pos))

        # Time widget - scale initial position and set preview scale
        self.time_widget = TimeWidget(self.preview_widget)
        self.time_widget.set_preview_scale(self.preview_scale)
        self.time_widget.move(int(200 * self.preview_scale), int(40 * self.preview_scale))
        self.time_widget.apply_style(self.text_style)
        self.time_widget.set_enabled(False)
        self.time_widget.positionChanged.connect(lambda pos: self.on_widget_position_changed('time', pos))

        # Metric widgets
        metrics_config = [
            "cpu_temperature", "gpu_temperature",
            "cpu_usage", "gpu_usage",
            "cpu_frequency", "gpu_frequency",
            "cpu_name", "gpu_name",
            "ram_total", "ram_percent",
            "gpu_mem_total", "gpu_mem_percent"
        ]

        self.metric_widgets = {}
        for metric_name in metrics_config:
            # RAM metrics use CPU metrics class, GPU metrics use GPU metrics class
            if metric_name.startswith("cpu_") or metric_name.startswith("ram_"):
                metric = self.cpu_metric
            else:
                metric = self.gpu_metric
            widget = MetricWidget(metric=metric, parent=self.preview_widget, metric_name=metric_name)
            widget.set_preview_scale(self.preview_scale)
            widget.apply_style(self.text_style)
            widget.set_enabled(False)
            widget.positionChanged.connect(lambda pos, name=metric_name: self.on_widget_position_changed(name, pos))
            self.metric_widgets[metric_name] = widget

        # Free text widgets
        self.text_widgets = {}
        for i in range(1, 5):
            widget_name = f"text{i}"
            widget = FreeTextWidget(parent=self.preview_widget, widget_name=widget_name)
            widget.set_preview_scale(self.preview_scale)
            widget.apply_style(self.text_style)
            widget.set_enabled(False)
            widget.positionChanged.connect(lambda pos, name=widget_name: self.on_widget_position_changed(name, pos))
            self.text_widgets[widget_name] = widget

        # Bar graph widgets (CPU and GPU)
        self.bar_widgets = {}
        for prefix in ["cpu", "gpu"]:
            for i in range(1, 3):  # 2 bars each for CPU and GPU
                widget_name = f"{prefix}_bar{i}"
                widget = BarGraphWidget(parent=self.preview_widget, widget_name=widget_name)
                widget.set_preview_scale(self.preview_scale)
                widget.set_enabled(False)
                widget.positionChanged.connect(lambda pos, name=widget_name: self.on_widget_position_changed(name, pos))
                self.bar_widgets[widget_name] = widget

        # Circular graph widgets (CPU and GPU)
        self.arc_widgets = {}
        for prefix in ["cpu", "gpu"]:
            for i in range(1, 3):  # 2 arcs each for CPU and GPU
                widget_name = f"{prefix}_arc{i}"
                widget = CircularGraphWidget(parent=self.preview_widget, widget_name=widget_name)
                widget.set_preview_scale(self.preview_scale)
                widget.set_enabled(False)
                widget.positionChanged.connect(lambda pos, name=widget_name: self.on_widget_position_changed(name, pos))
                self.arc_widgets[widget_name] = widget

        # Create property popups for double-click editing
        self._create_property_popups()
        
        # Connect double-click signals to show popups
        self._connect_double_click_handlers()

        # Ensure overlay widgets are above the foreground drag handle
        self._raise_overlay_widgets()

    def _create_property_popups(self):
        """Create property popup instances for each widget type"""
        self.text_property_popup = TextPropertyPopup()
        self.text_property_popup.propertyChanged.connect(self._on_popup_property_changed)
        
        self.metric_property_popup = MetricPropertyPopup()
        self.metric_property_popup.propertyChanged.connect(self._on_popup_property_changed)
        
        self.bar_property_popup = BarGraphPropertyPopup()
        self.bar_property_popup.propertyChanged.connect(self._on_popup_property_changed)
        
        self.arc_property_popup = ArcGraphPropertyPopup()
        self.arc_property_popup.propertyChanged.connect(self._on_popup_property_changed)

    def _connect_double_click_handlers(self):
        """Connect double-click signals from widgets to show property popups"""
        # Date and Time widgets use text popup
        if self.date_widget:
            self.date_widget.doubleClicked.connect(
                lambda w, pos: self.text_property_popup.show_for_widget(w, pos))
        if self.time_widget:
            self.time_widget.doubleClicked.connect(
                lambda w, pos: self.text_property_popup.show_for_widget(w, pos))
        
        # Metric widgets use metric popup
        for widget in self.metric_widgets.values():
            widget.doubleClicked.connect(
                lambda w, pos: self.metric_property_popup.show_for_widget(w, pos))
        
        # Free text widgets use text popup
        for widget in self.text_widgets.values():
            widget.doubleClicked.connect(
                lambda w, pos: self.text_property_popup.show_for_widget(w, pos))
        
        # Bar widgets use bar popup
        for widget in self.bar_widgets.values():
            widget.doubleClicked.connect(
                lambda w, pos: self.bar_property_popup.show_for_widget(w, pos))
        
        # Arc widgets use arc popup
        for widget in self.arc_widgets.values():
            widget.doubleClicked.connect(
                lambda w, pos: self.arc_property_popup.show_for_widget(w, pos))

    def _on_popup_property_changed(self, widget, property_name, value):
        """Handle property changes from popup - update config and trigger preview refresh"""
        self.logger.debug(f"Property changed via popup: {widget} {property_name} = {value}")
        # Schedule config update
        self.update_preview_widget_configs()

    def _on_palette_widget_dropped(self, widget_type: str, x: int, y: int):
        """Handle widget dropped from palette - create new widget at drop position"""
        self.logger.info(f"Widget dropped from palette: {widget_type} at ({x}, {y})")
        
        # Convert preview coordinates to device coordinates
        device_x = int(x / self.preview_scale)
        device_y = int(y / self.preview_scale)
        
        # Create widget based on type
        if widget_type == "date":
            self._enable_or_create_date_widget(x, y)
        elif widget_type == "time":
            self._enable_or_create_time_widget(x, y)
        elif widget_type == "free_text":
            self._create_new_text_widget(x, y)
        elif widget_type in ["cpu_usage", "cpu_temperature", "cpu_frequency", "cpu_name",
                            "gpu_usage", "gpu_temperature", "gpu_frequency", "gpu_name",
                            "ram_percent", "ram_total", "gpu_mem_percent", "gpu_mem_total"]:
            self._enable_or_create_metric_widget(widget_type, x, y)
        elif widget_type == "bar_graph":
            self._create_new_bar_widget(x, y)
        elif widget_type == "arc_graph":
            self._create_new_arc_widget(x, y)
        else:
            self.logger.warning(f"Unknown widget type dropped: {widget_type}")
    
    def _enable_or_create_date_widget(self, x: int, y: int):
        """Enable date widget and move to position"""
        if self.date_widget:
            self.date_widget.set_enabled(True)
            self.date_widget.move(x, y)
            self.date_widget.show()
            self.date_widget.raise_()
            self.update_preview_widget_configs()
    
    def _enable_or_create_time_widget(self, x: int, y: int):
        """Enable time widget and move to position"""
        if self.time_widget:
            self.time_widget.set_enabled(True)
            self.time_widget.move(x, y)
            self.time_widget.show()
            self.time_widget.raise_()
            self.update_preview_widget_configs()
    
    def _enable_or_create_metric_widget(self, metric_name: str, x: int, y: int):
        """Enable metric widget and move to position"""
        if metric_name in self.metric_widgets:
            widget = self.metric_widgets[metric_name]
            widget.set_enabled(True)
            widget.move(x, y)
            widget.show()
            widget.raise_()
            self.update_preview_widget_configs()
            
            # Also enable in the appropriate tab
            tab = self._get_tab_for_metric(metric_name)
            if tab and hasattr(tab, 'set_metric_enabled'):
                tab.set_metric_enabled(metric_name, True)
    
    def _create_new_text_widget(self, x: int, y: int):
        """Create a new free text widget or enable first disabled one"""
        # Prompt for text first
        text, ok = QInputDialog.getText(
            self, "Add Text Widget",
            "Enter the text to display:",
            text="Sample Text"
        )
        
        if not ok or not text.strip():
            return  # User cancelled or entered empty text
        
        # Find first disabled text widget
        for widget_name, widget in self.text_widgets.items():
            if not widget.enabled:
                widget.set_enabled(True)
                widget.set_text(text.strip())
                widget.move(x, y)
                widget.show()
                widget.raise_()
                self.update_preview_widget_configs()
                return
        
        # All text widgets in use - show message
        QMessageBox.information(
            self, "Text Widget Limit",
            "All 4 text widgets are already in use. Please disable one to add another."
        )
    
    def _create_new_bar_widget(self, x: int, y: int):
        """Create a new bar graph widget or enable first disabled one"""
        # Find first disabled bar widget
        for widget_name, widget in self.bar_widgets.items():
            if not widget.enabled:
                widget.set_enabled(True)
                widget.move(x, y)
                widget.show()
                widget.raise_()
                self.update_preview_widget_configs()
                
                # Also enable in the appropriate tab
                tab = self._get_tab_for_bar(widget_name)
                if tab and hasattr(tab, 'set_bar_enabled'):
                    tab.set_bar_enabled(widget_name, True)
                return
        
        # All bar widgets in use
        QMessageBox.information(
            self, "Bar Graph Limit",
            "All 4 bar graph widgets are already in use. Please disable one to add another."
        )
    
    def _create_new_arc_widget(self, x: int, y: int):
        """Create a new arc/circular graph widget or enable first disabled one"""
        # Find first disabled arc widget
        for widget_name, widget in self.arc_widgets.items():
            if not widget.enabled:
                widget.set_enabled(True)
                widget.move(x, y)
                widget.show()
                widget.raise_()
                self.update_preview_widget_configs()
                
                # Also enable in the appropriate tab
                tab = self._get_tab_for_arc(widget_name)
                if tab and hasattr(tab, 'set_arc_enabled'):
                    tab.set_arc_enabled(widget_name, True)
                return
        
        # All arc widgets in use
        QMessageBox.information(
            self, "Arc Graph Limit",
            "All 4 arc graph widgets are already in use. Please disable one to add another."
        )

    def _raise_overlay_widgets(self):
        """Raise all overlay widgets in proper z-order hierarchy.
        
        Stack order (bottom to top):
        1. preview_label (background image)
        2. foreground_widget (foreground overlay - back layer)
        3. bar_widgets (bar graphs - middle layer)
        4. arc_widgets (circular graphs - middle layer)
        5. text_widgets (free text - front layer)
        6. metric_widgets (metric displays - front layer)
        7. date_widget / time_widget (topmost - front layer)
        
        This ensures smaller text widgets are always accessible above larger graph widgets.
        """
        # 1. Foreground widget (lowest overlay layer)
        if self.foreground_widget:
            self.foreground_widget.raise_()
        
        # 2. Bar graph widgets (middle layer)
        for widget in self.bar_widgets.values():
            if widget:
                widget.raise_()
        
        # 3. Circular graph widgets (middle layer)
        for widget in self.arc_widgets.values():
            if widget:
                widget.raise_()
        
        # 4. Free text widgets (front layer)
        for widget in self.text_widgets.values():
            if widget:
                widget.raise_()
        
        # 5. Metric widgets (front layer)
        for widget in self.metric_widgets.values():
            if widget:
                widget.raise_()
        
        # 6. Date and time widgets (topmost)
        if self.date_widget:
            self.date_widget.raise_()
        if self.time_widget:
            self.time_widget.raise_()

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
        self.themes_tab = ThemesTab(themes_dir, dev_width=self.dev_width, dev_height=self.dev_height, config=self.config)
        self.themes_tab.theme_selected.connect(self.on_theme_selected)
        self.themes_tab.new_theme_requested.connect(self.create_new_theme)
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

        # CPU Tab - metrics and graphs for CPU
        self.cpu_tab = CPUTab(self, self.metric_widgets)
        self.tab_widget.addTab(self.cpu_tab, "CPU")

        # GPU Tab - metrics and graphs for GPU
        self.gpu_tab = GPUTab(self, self.metric_widgets)
        self.tab_widget.addTab(self.gpu_tab, "GPU")

        # Info Tab - Time, Date, Custom Text, RAM
        self.info_tab = InfoTab(self, self.metric_widgets)
        self.tab_widget.addTab(self.info_tab, "Info")

        parent_layout.addWidget(self.tab_widget)

    def _get_tab_for_bar(self, bar_name):
        """Get the tab that contains controls for a bar graph"""
        if bar_name.startswith("cpu_"):
            return self.cpu_tab if hasattr(self, 'cpu_tab') else None
        elif bar_name.startswith("gpu_"):
            return self.gpu_tab if hasattr(self, 'gpu_tab') else None
        return None

    def _get_tab_for_arc(self, arc_name):
        """Get the tab that contains controls for a circular graph"""
        if arc_name.startswith("cpu_"):
            return self.cpu_tab if hasattr(self, 'cpu_tab') else None
        elif arc_name.startswith("gpu_"):
            return self.gpu_tab if hasattr(self, 'gpu_tab') else None
        return None

    def _get_tab_for_metric(self, metric_name):
        """Get the tab that contains controls for a metric"""
        if metric_name.startswith("cpu_"):
            return self.cpu_tab if hasattr(self, 'cpu_tab') else None
        elif metric_name.startswith("gpu_"):
            return self.gpu_tab if hasattr(self, 'gpu_tab') else None
        elif metric_name.startswith("ram_"):
            return self.info_tab if hasattr(self, 'info_tab') else None
        return None

    def on_theme_selected(self, theme_path: str):
        """Handle theme selection"""
        self.logger.debug(f"on_theme_selected called with: {theme_path}")
        try:
            import yaml
            from pathlib import Path
            from PySide6.QtGui import QColor

            # Track the currently loaded theme path
            self.current_theme_path = theme_path
            self.logger.debug(f"Set current_theme_path to: {theme_path}")

            # Load theme configuration
            with open(theme_path, 'r', encoding='utf-8') as f:
                theme_config = yaml.safe_load(f)

            display_config = theme_config.get('display', {})
            self.logger.debug(f"Display config loaded: {display_config.keys()}")

            # Load rotation if specified
            rotation = display_config.get('rotation', 0)
            self.current_rotation = rotation
            if self.controls_manager:
                self.controls_manager.set_rotation(rotation)
            if self.preview_manager:
                self.preview_manager.set_rotation(rotation)
                self._update_preview_dimensions_for_rotation(rotation)

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

            # Apply bar graph configurations (always call to clear old graphs if empty)
            bar_graphs_config = display_config.get('bar_graphs', [])
            self.apply_bar_graphs_config(bar_graphs_config)

            # Apply circular graph configurations (always call to clear old graphs if empty)
            circular_graphs_config = display_config.get('circular_graphs', [])
            self.apply_circular_graphs_config(circular_graphs_config)

            # Update controls to reflect current widget states
            self.update_controls_from_widgets()

            # Update preview manager with all widget configs for PIL rendering
            self.update_preview_widget_configs()
            
            # Force a display generator rebuild to render text widgets
            if self.preview_manager:
                self.preview_manager.create_display_generator()
            
            # Ensure proper z-order after enabling widgets
            self._raise_overlay_widgets()

            self.logger.debug(f"Theme loaded: {Path(theme_path).name}")

        except Exception as e:
            self.logger.error(f"Exception in on_theme_selected: {e}")
            QMessageBox.warning(self, "Theme Load Error", f"Failed to load theme:\n{str(e)}")

    def apply_widget_config(self, widget, config):
        """Apply configuration to a date/time widget"""
        try:
            # Set preview scale for proper display sizing
            widget.set_preview_scale(self.preview_scale)
            
            # Apply enabled state
            enabled = config.get('enabled', False)
            widget.set_enabled(enabled)

            # Apply position (convert device coords to preview coords)
            position = config.get('position', {})
            if position:
                x = int(position.get('x', 0) * self.preview_scale)
                y = int(position.get('y', 0) * self.preview_scale)
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
                
                # Set preview scale for proper display sizing
                widget.set_preview_scale(self.preview_scale)

                # Apply enabled state
                enabled = metric_config.get('enabled', False)
                widget.set_enabled(enabled)

                # Apply position (convert device coords to preview coords)
                position = metric_config.get('position', {})
                if position:
                    x = int(position.get('x', 0) * self.preview_scale)
                    y = int(position.get('y', 0) * self.preview_scale)
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
                
                # Update label position combo in the appropriate tab
                tab = self._get_tab_for_metric(metric_name)
                if tab and metric_name in tab.metric_label_position_combos:
                    combo = tab.metric_label_position_combos[metric_name]
                    index = combo.findData(label_position)
                    if index >= 0:
                        combo.setCurrentIndex(index)

                # Apply label offsets
                label_offset_x = metric_config.get('label_offset_x', 0)
                label_offset_y = metric_config.get('label_offset_y', 0)
                widget.set_label_offset_x(label_offset_x)
                widget.set_label_offset_y(label_offset_y)
                
                # Update offset spinboxes in the appropriate tab
                if tab:
                    if hasattr(tab, 'metric_label_offset_x_spins') and metric_name in tab.metric_label_offset_x_spins:
                        tab.metric_label_offset_x_spins[metric_name].setValue(label_offset_x)
                    if hasattr(tab, 'metric_label_offset_y_spins') and metric_name in tab.metric_label_offset_y_spins:
                        tab.metric_label_offset_y_spins[metric_name].setValue(label_offset_y)

                # Apply font size and color (create a temporary style for this metric)
                font_size = metric_config.get('font_size')
                label_font_size = metric_config.get('label_font_size')
                color_hex = metric_config.get('color')

                if font_size:
                    widget.set_font_size(font_size)
                    # Update font size spinbox in the appropriate tab
                    if tab and hasattr(tab, 'metric_font_size_spins'):
                        if metric_name in tab.metric_font_size_spins:
                            tab.metric_font_size_spins[metric_name].setValue(font_size)

                if label_font_size:
                    widget.set_label_font_size(label_font_size)
                    # Update label font size spinbox in the appropriate tab
                    if tab and hasattr(tab, 'metric_label_font_size_spins'):
                        if metric_name in tab.metric_label_font_size_spins:
                            tab.metric_label_font_size_spins[metric_name].setValue(label_font_size)

                # Apply frequency format for frequency metrics
                if 'frequency' in metric_name:
                    freq_format = metric_config.get('freq_format', 'mhz')
                    if hasattr(widget, 'set_freq_format'):
                        widget.set_freq_format(freq_format)
                    # Update frequency format combo in the appropriate tab
                    if tab and hasattr(tab, 'metric_freq_format_combos'):
                        if metric_name in tab.metric_freq_format_combos:
                            combo = tab.metric_freq_format_combos[metric_name]
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
                
                # Set preview scale for proper display sizing
                widget.set_preview_scale(self.preview_scale)

                # Apply enabled state
                enabled = text_config.get('enabled', False)
                widget.set_enabled(enabled)

                # Apply position (convert device coords to preview coords)
                position = text_config.get('position', {})
                if position:
                    x = int(position.get('x', 0) * self.preview_scale)
                    y = int(position.get('y', 0) * self.preview_scale)
                    widget.move(x, y)

                # Apply text content
                text = text_config.get('text', '')
                widget.set_text(text)

                # Apply font size
                font_size = text_config.get('font_size')
                if font_size:
                    widget.set_font_size(font_size)
                    if hasattr(self, 'info_tab') and self.info_tab and hasattr(self.info_tab, 'text_font_size_spins'):
                        if text_name in self.info_tab.text_font_size_spins:
                            self.info_tab.text_font_size_spins[text_name].setValue(font_size)

                # Update controls in the Info tab
                if hasattr(self, 'info_tab') and self.info_tab:
                    if hasattr(self.info_tab, 'text_checkboxes') and text_name in self.info_tab.text_checkboxes:
                        self.info_tab.text_checkboxes[text_name].setChecked(enabled)
                    if hasattr(self.info_tab, 'text_inputs') and text_name in self.info_tab.text_inputs:
                        self.info_tab.text_inputs[text_name].setText(text)

                widget.apply_style(self.text_style)
                widget.update_display()

        except Exception as e:
            self.logger.error(f"Error applying custom texts config: {e}")

    def apply_bar_graphs_config(self, bar_configs):
        """Apply configurations to bar graph widgets"""
        if bar_configs is None:
            bar_configs = []
        try:
            from PySide6.QtGui import QColor
            
            # First disable all bar widgets and update their checkboxes
            for bar_name, bar_widget in self.bar_widgets.items():
                bar_widget.set_enabled(False)
                # Also update the checkbox in the appropriate tab
                tab = self._get_tab_for_bar(bar_name)
                if tab and bar_name in tab.bar_checkboxes:
                    tab.bar_checkboxes[bar_name].blockSignals(True)
                    tab.bar_checkboxes[bar_name].setChecked(False)
                    tab.bar_checkboxes[bar_name].blockSignals(False)

            # Apply configuration for each bar widget
            for bar_config in bar_configs:
                bar_name = bar_config.get('name')
                if bar_name not in self.bar_widgets:
                    continue

                widget = self.bar_widgets[bar_name]
                
                # Set preview scale for widget drawing
                widget.set_preview_scale(self.preview_scale)

                # Apply enabled state
                enabled = bar_config.get('enabled', False)
                widget.set_enabled(enabled)

                # Apply position (convert from device to preview coordinates)
                position = bar_config.get('position', {})
                if position:
                    x = int(position.get('x', 0) * self.preview_scale)
                    y = int(position.get('y', 0) * self.preview_scale)
                    # Account for border padding in widget
                    border_padding = 4
                    widget.move(x - border_padding, y - border_padding)

                # Apply metric
                metric_name = bar_config.get('metric_name', 'cpu_usage')
                widget.set_metric_name(metric_name)

                # Apply dimensions
                widget.set_width(bar_config.get('width', 100))
                widget.set_height(bar_config.get('height', 16))
                widget.set_orientation(bar_config.get('orientation', 'horizontal'))
                widget.set_rotation(bar_config.get('rotation', 0))
                widget.set_corner_radius(bar_config.get('corner_radius', 0))

                # Apply colors (use hex_to_qcolor to properly parse RRGGBBAA format)
                fill_color = bar_config.get('fill_color', '#00FF00FF')
                bg_color = bar_config.get('background_color', '#323232FF')
                border_color = bar_config.get('border_color', '#FFFFFFFF')
                widget.set_fill_color(self.hex_to_qcolor(fill_color) or QColor(0, 255, 0))
                widget.set_background_color(self.hex_to_qcolor(bg_color) or QColor(50, 50, 50))
                widget.set_border_color(self.hex_to_qcolor(border_color) or QColor(255, 255, 255))

                # Update controls in the appropriate tab
                tab = self._get_tab_for_bar(bar_name)
                if tab:
                    if bar_name in tab.bar_checkboxes:
                        tab.bar_checkboxes[bar_name].setChecked(enabled)
                    if bar_name in tab.bar_metric_combos:
                        idx = tab.bar_metric_combos[bar_name].findData(metric_name)
                        if idx >= 0:
                            tab.bar_metric_combos[bar_name].setCurrentIndex(idx)
                    if bar_name in tab.bar_width_spins:
                        tab.bar_width_spins[bar_name].setValue(bar_config.get('width', 100))
                    if bar_name in tab.bar_height_spins:
                        tab.bar_height_spins[bar_name].setValue(bar_config.get('height', 16))
                    if bar_name in tab.bar_corner_radius_spins:
                        tab.bar_corner_radius_spins[bar_name].setValue(bar_config.get('corner_radius', 0))
                    if bar_name in tab.bar_orientation_combos:
                        orientation = bar_config.get('orientation', 'horizontal')
                        idx = tab.bar_orientation_combos[bar_name].findData(orientation)
                        if idx >= 0:
                            tab.bar_orientation_combos[bar_name].setCurrentIndex(idx)
                    if bar_name in tab.bar_rotation_spins:
                        tab.bar_rotation_spins[bar_name].setValue(bar_config.get('rotation', 0))
                    if bar_name in tab.bar_fill_color_btns:
                        tab.bar_fill_color_btns[bar_name].setStyleSheet(
                            f"background-color: {fill_color[:7]}; border: 1px solid #888; border-radius: 3px;")
                    if bar_name in tab.bar_bg_color_btns:
                        tab.bar_bg_color_btns[bar_name].setStyleSheet(
                            f"background-color: {bg_color[:7]}; border: 1px solid #888; border-radius: 3px;")

                # Apply gradient settings
                use_gradient = bar_config.get('use_gradient', False)
                widget.set_use_gradient(use_gradient)
                
                gradient_colors = bar_config.get('gradient_colors')
                if gradient_colors:
                    # Convert from YAML format to widget format
                    converted = []
                    for gc in gradient_colors:
                        threshold = gc.get('threshold', 0)
                        color_hex = gc.get('color', '#00FF00FF')
                        rgba = self.hex_to_rgba(color_hex)
                        converted.append((threshold, rgba))
                    widget.set_gradient_colors(converted)
                    
                    # Update gradient UI controls in the appropriate tab
                    if tab:
                        # Update threshold spinboxes
                        if len(converted) > 1 and bar_name in tab.bar_gradient_mid_spins:
                            tab.bar_gradient_mid_spins[bar_name].blockSignals(True)
                            tab.bar_gradient_mid_spins[bar_name].setValue(int(converted[1][0]))
                            tab.bar_gradient_mid_spins[bar_name].blockSignals(False)
                        if len(converted) > 2 and bar_name in tab.bar_gradient_high_spins:
                            tab.bar_gradient_high_spins[bar_name].blockSignals(True)
                            tab.bar_gradient_high_spins[bar_name].setValue(int(converted[2][0]))
                            tab.bar_gradient_high_spins[bar_name].blockSignals(False)
                        # Update color buttons
                        if len(converted) > 0 and bar_name in tab.bar_gradient_low_color_btns:
                            c = converted[0][1]
                            tab.bar_gradient_low_color_btns[bar_name].setStyleSheet(
                                f"background-color: rgb({c[0]},{c[1]},{c[2]}); border: 1px solid #888; border-radius: 3px;")
                        if len(converted) > 1 and bar_name in tab.bar_gradient_mid_color_btns:
                            c = converted[1][1]
                            tab.bar_gradient_mid_color_btns[bar_name].setStyleSheet(
                                f"background-color: rgb({c[0]},{c[1]},{c[2]}); border: 1px solid #888; border-radius: 3px;")
                        if len(converted) > 2 and bar_name in tab.bar_gradient_high_color_btns:
                            c = converted[2][1]
                            tab.bar_gradient_high_color_btns[bar_name].setStyleSheet(
                                f"background-color: rgb({c[0]},{c[1]},{c[2]}); border: 1px solid #888; border-radius: 3px;")
                
                if tab and bar_name in tab.bar_gradient_checkboxes:
                    tab.bar_gradient_checkboxes[bar_name].setChecked(use_gradient)
                    # Show/hide gradient row based on loaded state
                    if bar_name in tab.bar_gradient_rows:
                        if use_gradient:
                            tab.bar_gradient_rows[bar_name].show()
                        else:
                            tab.bar_gradient_rows[bar_name].hide()

                widget.update_display()

        except Exception as e:
            self.logger.error(f"Error applying bar graphs config: {e}")

    def apply_circular_graphs_config(self, arc_configs):
        """Apply configurations to circular graph widgets"""
        if arc_configs is None:
            arc_configs = []
        try:
            from PySide6.QtGui import QColor
            
            # First disable all arc widgets and update their checkboxes
            for arc_name, arc_widget in self.arc_widgets.items():
                arc_widget.set_enabled(False)
                # Also update the checkbox in controls
                tab = self._get_tab_for_arc(arc_name)
                if tab and arc_name in tab.arc_checkboxes:
                    tab.arc_checkboxes[arc_name].blockSignals(True)
                    tab.arc_checkboxes[arc_name].setChecked(False)
                    tab.arc_checkboxes[arc_name].blockSignals(False)

            # Apply configuration for each arc widget
            for arc_config in arc_configs:
                arc_name = arc_config.get('name')
                if arc_name not in self.arc_widgets:
                    continue

                widget = self.arc_widgets[arc_name]
                
                # Set preview scale for widget drawing
                widget.set_preview_scale(self.preview_scale)

                # Apply enabled state
                enabled = arc_config.get('enabled', False)
                widget.set_enabled(enabled)

                # Apply properties before position (so size is correct for position calc)
                radius = arc_config.get('radius', 40)
                thickness = arc_config.get('thickness', 8)
                widget.set_radius(radius)
                widget.set_thickness(thickness)

                # Apply metric
                metric_name = arc_config.get('metric_name', 'cpu_usage')
                widget.set_metric_name(metric_name)

                # Apply angles and rotation BEFORE position calculation
                # (rotation affects widget size which affects position calculation)
                widget.set_start_angle(arc_config.get('start_angle', 135))
                widget.set_sweep_angle(arc_config.get('sweep_angle', 270))
                rotation = arc_config.get('rotation', 0)
                widget.set_rotation(rotation)

                # Apply position (convert from device to preview coordinates)
                # Position is center of arc, need to convert to widget top-left
                # Must account for rotation and preview scale in size calculation
                position = arc_config.get('position', {})
                if position:
                    import math
                    center_x = int(position.get('x', 0) * self.preview_scale)
                    center_y = int(position.get('y', 0) * self.preview_scale)
                    # Widget position = center - (widget_size / 2)
                    # Widget size = diameter + thickness + border_padding * 2
                    # Account for preview scale in size calculation
                    border_padding = 4
                    scaled_radius = int(radius * self.preview_scale)
                    scaled_thickness = int(thickness * self.preview_scale)
                    diameter = scaled_radius * 2
                    base_size = diameter + scaled_thickness + border_padding * 2
                    
                    # Calculate total size accounting for rotation (must match get_position())
                    if rotation != 0:
                        angle_rad = math.radians(rotation)
                        cos_a = abs(math.cos(angle_rad))
                        sin_a = abs(math.sin(angle_rad))
                        rotated_size = int(base_size * cos_a + base_size * sin_a)
                        total_size = max(base_size, rotated_size)
                    else:
                        total_size = base_size
                    
                    widget_x = center_x - total_size // 2
                    widget_y = center_y - total_size // 2
                    widget.move(widget_x, widget_y)

                # Apply colors (use hex_to_qcolor to properly parse RRGGBBAA format)
                fill_color = arc_config.get('fill_color', '#00FF00FF')
                bg_color = arc_config.get('background_color', '#323232FF')
                border_color = arc_config.get('border_color', '#FFFFFFFF')
                widget.set_fill_color(self.hex_to_qcolor(fill_color) or QColor(0, 255, 0))
                widget.set_background_color(self.hex_to_qcolor(bg_color) or QColor(50, 50, 50))
                widget.set_border_color(self.hex_to_qcolor(border_color) or QColor(255, 255, 255))
                
                # Apply border settings
                widget.set_show_border(arc_config.get('show_border', False))
                widget.set_border_width(arc_config.get('border_width', 1))

                # Update controls in the appropriate tab
                tab = self._get_tab_for_arc(arc_name)
                if tab:
                    if arc_name in tab.arc_checkboxes:
                        tab.arc_checkboxes[arc_name].setChecked(enabled)
                    if arc_name in tab.arc_metric_combos:
                        idx = tab.arc_metric_combos[arc_name].findData(metric_name)
                        if idx >= 0:
                            tab.arc_metric_combos[arc_name].setCurrentIndex(idx)
                    if arc_name in tab.arc_radius_spins:
                        tab.arc_radius_spins[arc_name].setValue(radius)
                    if arc_name in tab.arc_thickness_spins:
                        tab.arc_thickness_spins[arc_name].setValue(thickness)
                    if arc_name in tab.arc_start_angle_spins:
                        tab.arc_start_angle_spins[arc_name].setValue(arc_config.get('start_angle', 135))
                    if arc_name in tab.arc_sweep_angle_spins:
                        tab.arc_sweep_angle_spins[arc_name].setValue(arc_config.get('sweep_angle', 270))
                    if arc_name in tab.arc_rotation_spins:
                        tab.arc_rotation_spins[arc_name].setValue(arc_config.get('rotation', 0))
                    if arc_name in tab.arc_fill_color_btns:
                        tab.arc_fill_color_btns[arc_name].setStyleSheet(
                            f"background-color: {fill_color[:7]}; border: 1px solid #888; border-radius: 3px;")
                    if arc_name in tab.arc_bg_color_btns:
                        tab.arc_bg_color_btns[arc_name].setStyleSheet(
                            f"background-color: {bg_color[:7]}; border: 1px solid #888; border-radius: 3px;")

                # Apply gradient settings
                use_gradient = arc_config.get('use_gradient', False)
                widget.set_use_gradient(use_gradient)
                
                gradient_colors = arc_config.get('gradient_colors')
                if gradient_colors:
                    # Convert from YAML format to widget format
                    converted = []
                    for gc in gradient_colors:
                        threshold = gc.get('threshold', 0)
                        color_hex = gc.get('color', '#00FF00FF')
                        rgba = self.hex_to_rgba(color_hex)
                        converted.append((threshold, rgba))
                    widget.set_gradient_colors(converted)
                    
                    # Update gradient UI controls in the appropriate tab
                    if tab:
                        # Update threshold spinboxes
                        if len(converted) > 1 and arc_name in tab.arc_gradient_mid_spins:
                            tab.arc_gradient_mid_spins[arc_name].blockSignals(True)
                            tab.arc_gradient_mid_spins[arc_name].setValue(int(converted[1][0]))
                            tab.arc_gradient_mid_spins[arc_name].blockSignals(False)
                        if len(converted) > 2 and arc_name in tab.arc_gradient_high_spins:
                            tab.arc_gradient_high_spins[arc_name].blockSignals(True)
                            tab.arc_gradient_high_spins[arc_name].setValue(int(converted[2][0]))
                            tab.arc_gradient_high_spins[arc_name].blockSignals(False)
                        # Update color buttons
                        if len(converted) > 0 and arc_name in tab.arc_gradient_low_color_btns:
                            c = converted[0][1]
                            tab.arc_gradient_low_color_btns[arc_name].setStyleSheet(
                                f"background-color: rgb({c[0]},{c[1]},{c[2]}); border: 1px solid #888; border-radius: 3px;")
                        if len(converted) > 1 and arc_name in tab.arc_gradient_mid_color_btns:
                            c = converted[1][1]
                            tab.arc_gradient_mid_color_btns[arc_name].setStyleSheet(
                                f"background-color: rgb({c[0]},{c[1]},{c[2]}); border: 1px solid #888; border-radius: 3px;")
                        if len(converted) > 2 and arc_name in tab.arc_gradient_high_color_btns:
                            c = converted[2][1]
                            tab.arc_gradient_high_color_btns[arc_name].setStyleSheet(
                                f"background-color: rgb({c[0]},{c[1]},{c[2]}); border: 1px solid #888; border-radius: 3px;")
                
                if tab and arc_name in tab.arc_gradient_checkboxes:
                    tab.arc_gradient_checkboxes[arc_name].setChecked(use_gradient)
                    # Show/hide gradient row based on loaded state
                    if arc_name in tab.arc_gradient_rows:
                        if use_gradient:
                            tab.arc_gradient_rows[arc_name].show()
                        else:
                            tab.arc_gradient_rows[arc_name].hide()

                widget.update_display()

        except Exception as e:
            self.logger.error(f"Error applying circular graphs config: {e}")

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

            # Update metric controls in their respective tabs
            for metric_name, widget in self.metric_widgets.items():
                tab = self._get_tab_for_metric(metric_name)
                if tab:
                    # Update checkbox
                    if hasattr(tab, 'metric_checkboxes') and metric_name in tab.metric_checkboxes:
                        tab.metric_checkboxes[metric_name].setChecked(widget.enabled)

                    # Update label input
                    if hasattr(tab, 'metric_label_inputs') and metric_name in tab.metric_label_inputs and widget.enabled:
                        tab.metric_label_inputs[metric_name].setText(widget.get_label())

                    # Update unit input
                    if hasattr(tab, 'metric_unit_inputs') and metric_name in tab.metric_unit_inputs and widget.enabled:
                        tab.metric_unit_inputs[metric_name].setText(widget.get_unit())

                    # Update font size spinbox
                    if hasattr(tab, 'metric_font_size_spins') and metric_name in tab.metric_font_size_spins:
                        tab.metric_font_size_spins[metric_name].setValue(widget.get_font_size())

                    # Update label font size spinbox
                    if hasattr(tab, 'metric_label_font_size_spins') and metric_name in tab.metric_label_font_size_spins:
                        tab.metric_label_font_size_spins[metric_name].setValue(widget.get_label_font_size())

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

    def hex_to_rgba(self, hex_color: str) -> tuple:
        """Convert hex color string to (r, g, b, a) tuple"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')

            # Handle different hex formats
            if len(hex_color) == 6:  # RGB
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return (r, g, b, 255)
            elif len(hex_color) == 8:  # RGBA
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                a = int(hex_color[6:8], 16)
                return (r, g, b, a)
            else:
                self.logger.error(f"Invalid hex color format: {hex_color}")
                return (0, 255, 0, 255)

        except ValueError as e:
            self.logger.error(f"Error parsing hex color {hex_color}: {e}")
            return (0, 255, 0, 255)

    # Event handlers
    def choose_color(self):
        """Open color chooser dialog"""
        color = QColorDialog.getColor(self.text_style.color, self)
        if color.isValid():
            self.text_style.color = color
            self.controls_manager.update_color_button()
            self.apply_style_to_all_widgets()
            self.update_preview_widget_configs()

    # Shadow handlers
    def on_shadow_enabled_changed(self, enabled):
        """Handle shadow enabled toggle"""
        self.text_style.shadow_enabled = enabled
        self.apply_style_to_all_widgets()
        if self.preview_manager:
            self.preview_manager.update_text_effects()

    def choose_shadow_color(self):
        """Open shadow color chooser dialog"""
        color = QColorDialog.getColor(self.text_style.shadow_color, self)
        if color.isValid():
            self.text_style.shadow_color = color
            self.controls_manager._update_shadow_color_button()
            self.apply_style_to_all_widgets()
            if self.preview_manager:
                self.preview_manager.update_text_effects()

    def on_shadow_offset_x_changed(self, value):
        """Handle shadow X offset change"""
        self.text_style.shadow_offset_x = value
        self.apply_style_to_all_widgets()
        if self.preview_manager:
            self.preview_manager.update_text_effects()

    def on_shadow_offset_y_changed(self, value):
        """Handle shadow Y offset change"""
        self.text_style.shadow_offset_y = value
        self.apply_style_to_all_widgets()
        if self.preview_manager:
            self.preview_manager.update_text_effects()

    def on_shadow_blur_changed(self, value):
        """Handle shadow blur change"""
        self.text_style.shadow_blur = value
        self.apply_style_to_all_widgets()
        if self.preview_manager:
            self.preview_manager.update_text_effects()

    # Outline handlers
    def on_outline_enabled_changed(self, enabled):
        """Handle outline enabled toggle"""
        self.text_style.outline_enabled = enabled
        self.apply_style_to_all_widgets()
        if self.preview_manager:
            self.preview_manager.update_text_effects()

    def choose_outline_color(self):
        """Open outline color chooser dialog"""
        color = QColorDialog.getColor(self.text_style.outline_color, self)
        if color.isValid():
            self.text_style.outline_color = color
            self.controls_manager._update_outline_color_button()
            self.apply_style_to_all_widgets()
            if self.preview_manager:
                self.preview_manager.update_text_effects()

    def on_outline_width_changed(self, value):
        """Handle outline width change"""
        self.text_style.outline_width = value
        self.apply_style_to_all_widgets()
        if self.preview_manager:
            self.preview_manager.update_text_effects()

    # Gradient handlers
    def on_gradient_enabled_changed(self, enabled):
        """Handle gradient enabled toggle"""
        self.text_style.gradient_enabled = enabled
        self.apply_style_to_all_widgets()
        if self.preview_manager:
            self.preview_manager.update_text_effects()

    def choose_gradient_color1(self):
        """Open gradient color 1 chooser dialog"""
        color = QColorDialog.getColor(self.text_style.gradient_color1, self)
        if color.isValid():
            self.text_style.gradient_color1 = color
            self.controls_manager._update_gradient_color1_button()
            self.apply_style_to_all_widgets()
            if self.preview_manager:
                self.preview_manager.update_text_effects()

    def choose_gradient_color2(self):
        """Open gradient color 2 chooser dialog"""
        color = QColorDialog.getColor(self.text_style.gradient_color2, self)
        if color.isValid():
            self.text_style.gradient_color2 = color
            self.controls_manager._update_gradient_color2_button()
            self.apply_style_to_all_widgets()
            if self.preview_manager:
                self.preview_manager.update_text_effects()

    def on_gradient_direction_changed(self, direction):
        """Handle gradient direction change"""
        self.text_style.gradient_direction = direction
        self.apply_style_to_all_widgets()
        if self.preview_manager:
            self.preview_manager.update_text_effects()

    def on_rotation_changed(self, rotation):
        """Handle rotation change"""
        self.current_rotation = rotation
        if self.preview_manager:
            self.preview_manager.set_rotation(rotation)
            self._update_preview_dimensions_for_rotation(rotation)

    def _update_preview_dimensions_for_rotation(self, rotation: int):
        """Resize preview panel based on rotation (90/270 swaps width/height)"""
        base_width = self.detected_device.get('width', 320) if self.detected_device else 320
        base_height = self.detected_device.get('height', 240) if self.detected_device else 240
        
        # Swap dimensions for 90 or 270 degree rotation
        if rotation in (90, 270):
            display_width, display_height = base_height, base_width
        else:
            display_width, display_height = base_width, base_height
        
        preview_width = int(display_width * self.preview_scale)
        preview_height = int(display_height * self.preview_scale)
        frame_width, frame_height = preview_width + 4, preview_height + 4
        
        # Resize preview components
        self.preview_frame.setFixedSize(frame_width, frame_height)
        self.preview_widget.setGeometry(2, 2, preview_width, preview_height)
        self.preview_label.setGeometry(0, 0, preview_width, preview_height)
        
        # Resize grid overlay
        if hasattr(self, 'grid_overlay'):
            self.grid_overlay.setGeometry(0, 0, preview_width, preview_height)
        
        # Update foreground widget bounds
        if hasattr(self, 'foreground_widget'):
            self.foreground_widget.set_preview_bounds(preview_width, preview_height)
        
        # Update preview manager dimensions
        if self.preview_manager:
            self.preview_manager.set_preview_dimensions(preview_width, preview_height)

    def on_refresh_interval_changed(self, interval):
        """Handle LCD refresh interval change"""
        self.refresh_interval = interval
        if self.preview_manager:
            self.preview_manager.refresh_interval = interval
        self.logger.debug(f"Refresh interval changed to {interval}s")

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
        
        # Update resize handle positions when widget moves
        if hasattr(self, 'resize_handle_manager') and self.resize_handle_manager._target:
            self.resize_handle_manager._update_handle_positions()
        
        # Debounce preview update - restart timer on each move
        self._position_update_timer.start()

    def _on_widget_size_changed(self, widget, property_name, new_value):
        """Handle widget size/property change from resize handles"""
        self.logger.debug(f"Widget {widget.__class__.__name__} {property_name} changed to {new_value}")
        
        # Update controls to reflect new values
        # For bar widgets
        if hasattr(widget, 'name') and widget.name in self.bar_widgets:
            if hasattr(self, 'controls_manager') and self.controls_manager:
                # The controls manager may have spinboxes for width/height
                # We'll trigger a preview update
                pass
        
        # For arc widgets
        if hasattr(widget, 'name') and widget.name in self.arc_widgets:
            pass
        
        # For text widgets - update font size display
        if property_name == 'font_size':
            # Update preview
            pass
        
        # Debounce preview update
        self._position_update_timer.start()

    def _on_widget_rotation_changed(self, widget, angle):
        """Handle widget rotation change from rotation handle"""
        self.logger.debug(f"Widget {widget.__class__.__name__} rotation changed to {angle}°")
        
        # Debounce preview update
        self._position_update_timer.start()

    def _on_widget_focus_changed(self, widget, focused):
        """Handle widget focus change to show/hide resize handles"""
        if focused:
            # Show resize handles for this widget
            if hasattr(self, 'resize_handle_manager'):
                self.resize_handle_manager.attach_to(widget)
        else:
            # Check if focus moved to another tracked widget
            # If not, detach handles
            from PySide6.QtWidgets import QApplication
            focused_widget = QApplication.focusWidget()
            
            # Check if the new focus is one of our tracked widgets
            is_tracked = False
            all_widgets = [self.date_widget, self.time_widget]
            all_widgets.extend(self.metric_widgets.values())
            all_widgets.extend(self.text_widgets.values())
            all_widgets.extend(self.bar_widgets.values())
            all_widgets.extend(self.arc_widgets.values())
            
            for w in all_widgets:
                if w == focused_widget:
                    is_tracked = True
                    break
            
            if not is_tracked:
                self.resize_handle_manager.detach()

    def _on_app_focus_changed(self, old_widget, new_widget):
        """Handle application-wide focus changes to show/hide resize handles"""
        if not hasattr(self, 'resize_handle_manager'):
            return
        
        # Get list of all tracked widgets
        all_widgets = [self.date_widget, self.time_widget]
        all_widgets.extend(self.metric_widgets.values())
        all_widgets.extend(self.text_widgets.values())
        all_widgets.extend(self.bar_widgets.values())
        all_widgets.extend(self.arc_widgets.values())
        
        # Check if new focus is a tracked widget
        if new_widget in all_widgets:
            self.resize_handle_manager.attach_to(new_widget)
        elif new_widget is None or new_widget not in all_widgets:
            # Check if the new_widget is a resize handle (shouldn't happen with NoFocus)
            if new_widget is not None and hasattr(new_widget, '_handle_type'):
                return  # Focus is on resize handle, keep handles visible
            
            # Check if focus moved to preview_widget or preview_label
            # This can happen when clicking on handles or empty space in preview
            # In this case, keep handles if we still have a target
            if new_widget in (self.preview_widget, self.preview_label):
                return  # Keep handles visible when focus is in preview area
            
            self.resize_handle_manager.detach()
    
    def _do_update_preview_widget_configs(self):
        """Actually update preview widget configs (called by debounce timer)"""
        self.update_preview_widget_configs()

    def collect_widget_configs(self):
        """Collect all widget configs for PIL rendering in preview"""
        # Helper to convert QColor to RGBA tuple
        def qcolor_to_rgba(qcolor):
            return (qcolor.red(), qcolor.green(), qcolor.blue(), qcolor.alpha())
        
        # Default text color from global style (used as fallback)
        default_text_color = qcolor_to_rgba(self.text_style.color)
        
        # Date config
        date_config = None
        if hasattr(self, 'date_widget') and self.date_widget and self.date_widget.enabled:
            pos = self.date_widget.pos()
            device_x = int(pos.x() / self.preview_scale)
            device_y = int(pos.y() / self.preview_scale)
            # Use widget's individual color if available
            widget_color = qcolor_to_rgba(self.date_widget.get_color()) if hasattr(self.date_widget, 'get_color') else default_text_color
            # Get font name and bold
            font_name = self.date_widget.get_font_name() if hasattr(self.date_widget, 'get_font_name') else None
            bold = self.date_widget.get_bold() if hasattr(self.date_widget, 'get_bold') else False
            use_gradient = self.date_widget.get_use_gradient() if hasattr(self.date_widget, 'get_use_gradient') else True
            date_config = DateConfig(
                position=(device_x, device_y),
                font_size=self.date_widget.get_font_size(),
                color=widget_color,
                font_name=font_name,
                bold=bold,
                use_gradient=use_gradient,
                enabled=True,
                show_weekday=self.date_widget.get_show_weekday(),
                show_year=self.date_widget.get_show_year(),
                date_format=self.date_widget.get_date_format()
            )
        
        # Time config
        time_config = None
        if hasattr(self, 'time_widget') and self.time_widget and self.time_widget.enabled:
            pos = self.time_widget.pos()
            device_x = int(pos.x() / self.preview_scale)
            device_y = int(pos.y() / self.preview_scale)
            # Use widget's individual color if available
            widget_color = qcolor_to_rgba(self.time_widget.get_color()) if hasattr(self.time_widget, 'get_color') else default_text_color
            # Get font name and bold
            font_name = self.time_widget.get_font_name() if hasattr(self.time_widget, 'get_font_name') else None
            bold = self.time_widget.get_bold() if hasattr(self.time_widget, 'get_bold') else False
            use_gradient = self.time_widget.get_use_gradient() if hasattr(self.time_widget, 'get_use_gradient') else True
            time_config = TimeConfig(
                position=(device_x, device_y),
                font_size=self.time_widget.get_font_size(),
                color=widget_color,
                font_name=font_name,
                bold=bold,
                use_gradient=use_gradient,
                enabled=True,
                use_24_hour=self.time_widget.get_use_24_hour(),
                show_seconds=self.time_widget.get_show_seconds(),
                show_am_pm=self.time_widget.get_show_am_pm()
            )
        
        # Metrics configs
        metrics_configs = []
        if hasattr(self, 'metric_widgets'):
            for metric_name, widget in self.metric_widgets.items():
                if widget and widget.enabled:
                    pos = widget.pos()
                    device_x = int(pos.x() / self.preview_scale)
                    device_y = int(pos.y() / self.preview_scale)
                    
                    # Map label position string to LabelPosition enum
                    label_pos_map = {
                        # Legacy positions
                        'left': LabelPosition.LEFT,
                        'right': LabelPosition.RIGHT,
                        'above': LabelPosition.ABOVE,
                        'below': LabelPosition.BELOW,
                        'none': LabelPosition.NONE,
                        # New grid-based positions
                        'above-left': LabelPosition.ABOVE_LEFT,
                        'above-center': LabelPosition.ABOVE_CENTER,
                        'above-right': LabelPosition.ABOVE_RIGHT,
                        'below-left': LabelPosition.BELOW_LEFT,
                        'below-center': LabelPosition.BELOW_CENTER,
                        'below-right': LabelPosition.BELOW_RIGHT,
                        'left-top': LabelPosition.LEFT_TOP,
                        'left-center': LabelPosition.LEFT_CENTER,
                        'left-bottom': LabelPosition.LEFT_BOTTOM,
                        'right-top': LabelPosition.RIGHT_TOP,
                        'right-center': LabelPosition.RIGHT_CENTER,
                        'right-bottom': LabelPosition.RIGHT_BOTTOM,
                    }
                    label_pos = label_pos_map.get(widget.get_label_position(), LabelPosition.LEFT)
                    
                    # Get label offsets
                    label_offset_x = widget.get_label_offset_x() if hasattr(widget, 'get_label_offset_x') else 0
                    label_offset_y = widget.get_label_offset_y() if hasattr(widget, 'get_label_offset_y') else 0
                    
                    # Get frequency format for frequency metrics
                    freq_format = widget.get_freq_format() if hasattr(widget, 'get_freq_format') else 'mhz'
                    
                    # Get character limit for name metrics
                    char_limit = widget.get_char_limit() if hasattr(widget, 'get_char_limit') else 0
                    
                    # Use widget's individual color if available
                    widget_color = qcolor_to_rgba(widget.get_color()) if hasattr(widget, 'get_color') else default_text_color
                    
                    # Get font name and bold
                    font_name = widget.get_font_name() if hasattr(widget, 'get_font_name') else None
                    bold = widget.get_bold() if hasattr(widget, 'get_bold') else False
                    use_gradient = widget.get_use_gradient() if hasattr(widget, 'get_use_gradient') else True
                    
                    metrics_configs.append(MetricConfig(
                        name=metric_name,
                        label=widget.get_label(),
                        position=(device_x, device_y),
                        font_size=widget.get_font_size(),
                        label_font_size=widget.get_label_font_size(),
                        color=widget_color,
                        font_name=font_name,
                        bold=bold,
                        use_gradient=use_gradient,
                        unit=widget.get_unit(),
                        enabled=True,
                        label_position=label_pos,
                        label_offset_x=label_offset_x,
                        label_offset_y=label_offset_y,
                        freq_format=freq_format,
                        char_limit=char_limit
                    ))
        
        # Text configs (free text widgets)
        text_configs = []
        if hasattr(self, 'text_widgets'):
            for text_name, widget in self.text_widgets.items():
                if widget and widget.enabled:
                    pos = widget.pos()
                    device_x = int(pos.x() / self.preview_scale)
                    device_y = int(pos.y() / self.preview_scale)
                    
                    # Use widget's individual color if available
                    widget_color = qcolor_to_rgba(widget.get_color()) if hasattr(widget, 'get_color') else default_text_color
                    
                    # Get font name and bold
                    font_name = widget.get_font_name() if hasattr(widget, 'get_font_name') else None
                    bold = widget.get_bold() if hasattr(widget, 'get_bold') else False
                    use_gradient = widget.get_use_gradient() if hasattr(widget, 'get_use_gradient') else True
                    
                    text_configs.append(TextConfig(
                        text=widget.get_text(),
                        position=(device_x, device_y),
                        font_size=widget.get_font_size(),
                        color=widget_color,
                        font_name=font_name,
                        bold=bold,
                        use_gradient=use_gradient,
                        enabled=True
                    ))
        
        # Bar graph configs
        bar_configs = []
        if hasattr(self, 'bar_widgets'):
            for bar_name, widget in self.bar_widgets.items():
                if widget and widget.enabled:
                    # Use get_position() which accounts for border padding
                    pos = widget.get_position()
                    device_x = int(pos[0] / self.preview_scale)
                    device_y = int(pos[1] / self.preview_scale)
                    
                    bar_configs.append(BarGraphConfig(
                        metric_name=widget.get_metric_name(),
                        position=(device_x, device_y),
                        width=widget.get_width(),
                        height=widget.get_height(),
                        orientation=widget.get_orientation(),
                        rotation=widget.get_rotation(),
                        fill_color=qcolor_to_rgba(widget.get_fill_color()),
                        background_color=qcolor_to_rgba(widget.get_background_color()),
                        border_color=qcolor_to_rgba(widget.get_border_color()),
                        show_border=widget.get_show_border(),
                        border_width=widget.get_border_width(),
                        corner_radius=widget.get_corner_radius(),
                        min_value=widget.get_min_value(),
                        max_value=widget.get_max_value(),
                        enabled=True
                    ))
        
        # Circular graph configs
        circular_configs = []
        if hasattr(self, 'arc_widgets'):
            for arc_name, widget in self.arc_widgets.items():
                if widget and widget.enabled:
                    pos = widget.get_position()
                    device_x = int(pos[0] / self.preview_scale)
                    device_y = int(pos[1] / self.preview_scale)
                    
                    circular_configs.append(CircularGraphConfig(
                        metric_name=widget.get_metric_name(),
                        position=(device_x, device_y),
                        radius=widget.get_radius(),
                        thickness=widget.get_thickness(),
                        start_angle=widget.get_start_angle(),
                        sweep_angle=widget.get_sweep_angle(),
                        rotation=widget.get_rotation(),
                        fill_color=qcolor_to_rgba(widget.get_fill_color()),
                        background_color=qcolor_to_rgba(widget.get_background_color()),
                        border_color=qcolor_to_rgba(widget.get_border_color()),
                        show_border=widget.get_show_border(),
                        border_width=widget.get_border_width(),
                        min_value=widget.get_min_value(),
                        max_value=widget.get_max_value(),
                        enabled=True
                    ))
        
        return date_config, time_config, metrics_configs, text_configs, bar_configs, circular_configs

    def update_preview_widget_configs(self):
        """Update preview manager with current widget configs.
        
        Note: bar_configs and circular_configs are NOT passed to preview_manager
        because they are rendered by the Qt overlay widgets (BarGraphWidget, CircularGraphWidget)
        in the GUI. Passing them would cause double-rendering.
        """
        if not self.preview_manager:
            return
        
        date_config, time_config, metrics_configs, text_configs, bar_configs, circular_configs = self.collect_widget_configs()
        self.preview_manager.update_widget_configs(
            date_config=date_config,
            time_config=time_config,
            metrics_configs=metrics_configs,
            text_configs=text_configs,
            bar_configs=[],  # Rendered by Qt overlay widgets
            circular_configs=[]  # Rendered by Qt overlay widgets
        )

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
        self.update_preview_widget_configs()

    def on_font_family_changed(self, font_family):
        """Handle font family change"""
        self.text_style.font_family = font_family
        self.apply_style_to_all_widgets()
        # Update the preview manager's text style for config generation
        if self.preview_manager:
            self.preview_manager.text_style.font_family = font_family
        self.update_preview_widget_configs()

    def on_widget_font_size_changed(self, widget_name, size):
        """Handle individual widget font size change"""
        if widget_name == 'date' and self.date_widget:
            self.date_widget.set_font_size(size)
        elif widget_name == 'time' and self.time_widget:
            self.time_widget.set_font_size(size)
        self.update_preview_widget_configs()

    def on_metric_font_size_changed(self, metric_name, size):
        """Handle individual metric font size change"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_font_size(size)
        self.update_preview_widget_configs()

    def on_metric_label_font_size_changed(self, metric_name, size):
        """Handle individual metric label font size change"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_label_font_size(size)
        self.update_preview_widget_configs()

    # Free text widget handlers
    def on_text_toggled(self, text_name, enabled):
        """Handle free text widget toggle"""
        if text_name in self.text_widgets:
            self.text_widgets[text_name].set_enabled(enabled)
            self.update_preview_widget_configs()

    def on_text_changed(self, text_name, text):
        """Handle free text content change"""
        if text_name in self.text_widgets:
            self.text_widgets[text_name].set_text(text)
            self.update_preview_widget_configs()

    def on_text_font_size_changed(self, text_name, size):
        """Handle free text font size change"""
        if text_name in self.text_widgets:
            self.text_widgets[text_name].set_font_size(size)
            self.update_preview_widget_configs()

    # Bar graph widget handlers
    def on_bar_toggled(self, bar_name, enabled):
        """Handle bar graph widget toggle"""
        if bar_name in self.bar_widgets:
            self.bar_widgets[bar_name].set_enabled(enabled)
            self.update_preview_widget_configs()

    def on_bar_metric_changed(self, bar_name, metric):
        """Handle bar graph metric change"""
        if bar_name in self.bar_widgets:
            self.bar_widgets[bar_name].set_metric_name(metric)
            self.update_preview_widget_configs()

    def on_bar_width_changed(self, bar_name, width):
        """Handle bar graph width change"""
        if bar_name in self.bar_widgets:
            self.bar_widgets[bar_name].set_width(width)
            self.update_preview_widget_configs()

    def on_bar_height_changed(self, bar_name, height):
        """Handle bar graph height change"""
        if bar_name in self.bar_widgets:
            self.bar_widgets[bar_name].set_height(height)
            self.update_preview_widget_configs()

    def on_bar_corner_radius_changed(self, bar_name, radius):
        """Handle bar graph corner radius change"""
        if bar_name in self.bar_widgets:
            self.bar_widgets[bar_name].set_corner_radius(radius)
            self.update_preview_widget_configs()

    def on_bar_orientation_changed(self, bar_name, orientation):
        """Handle bar graph orientation change - swap width/height when orientation changes"""
        if bar_name in self.bar_widgets:
            widget = self.bar_widgets[bar_name]
            current_orientation = widget.get_orientation()
            
            # Only swap if orientation is actually changing
            if current_orientation != orientation:
                # Get current dimensions
                current_width = widget.get_width()
                current_height = widget.get_height()
                
                # Swap width and height
                widget.set_width(current_height)
                widget.set_height(current_width)
                
                # Update the spinbox values in the appropriate tab
                tab = self._get_tab_for_bar(bar_name)
                if tab:
                    if bar_name in tab.bar_width_spins:
                        tab.bar_width_spins[bar_name].blockSignals(True)
                        tab.bar_width_spins[bar_name].setValue(current_height)
                        tab.bar_width_spins[bar_name].blockSignals(False)
                    if bar_name in tab.bar_height_spins:
                        tab.bar_height_spins[bar_name].blockSignals(True)
                        tab.bar_height_spins[bar_name].setValue(current_width)
                        tab.bar_height_spins[bar_name].blockSignals(False)
                
                # Set the new orientation
                widget.set_orientation(orientation)
            
            self.update_preview_widget_configs()

    def on_bar_rotation_changed(self, bar_name, angle):
        """Handle bar graph rotation change"""
        if bar_name in self.bar_widgets:
            self.bar_widgets[bar_name].set_rotation(angle)
            self.update_preview_widget_configs()

    def on_bar_fill_color_clicked(self, bar_name):
        """Handle bar graph fill color picker"""
        if bar_name in self.bar_widgets:
            widget = self.bar_widgets[bar_name]
            color = QColorDialog.getColor(widget.get_fill_color(), self, "Select Fill Color")
            if color.isValid():
                widget.set_fill_color(color)
                tab = self._get_tab_for_bar(bar_name)
                if tab and bar_name in tab.bar_fill_color_btns:
                    tab.bar_fill_color_btns[bar_name].setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")
                self.update_preview_widget_configs()

    def on_bar_bg_color_clicked(self, bar_name):
        """Handle bar graph background color picker"""
        if bar_name in self.bar_widgets:
            widget = self.bar_widgets[bar_name]
            color = QColorDialog.getColor(widget.get_background_color(), self, "Select Background Color")
            if color.isValid():
                widget.set_background_color(color)
                tab = self._get_tab_for_bar(bar_name)
                if tab and bar_name in tab.bar_bg_color_btns:
                    tab.bar_bg_color_btns[bar_name].setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")
                self.update_preview_widget_configs()

    def on_bar_border_color_clicked(self, bar_name):
        """Handle bar graph border color picker"""
        if bar_name in self.bar_widgets:
            widget = self.bar_widgets[bar_name]
            color = QColorDialog.getColor(widget.get_border_color(), self, "Select Border Color")
            if color.isValid():
                widget.set_border_color(color)
                tab = self._get_tab_for_bar(bar_name)
                if tab and bar_name in tab.bar_border_color_btns:
                    tab.bar_border_color_btns[bar_name].setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")
                self.update_preview_widget_configs()

    def on_bar_gradient_toggled(self, bar_name, enabled):
        """Handle bar graph gradient toggle"""
        # Show/hide gradient settings row in the appropriate tab
        tab = self._get_tab_for_bar(bar_name)
        if tab and bar_name in tab.bar_gradient_rows:
            if enabled:
                tab.bar_gradient_rows[bar_name].show()
            else:
                tab.bar_gradient_rows[bar_name].hide()
        
        # Update widget if it exists
        if bar_name in self.bar_widgets:
            self.bar_widgets[bar_name].set_use_gradient(enabled)
            self.update_preview_widget_configs()

    def on_bar_gradient_low_color_clicked(self, bar_name):
        """Handle bar graph gradient low color picker"""
        if bar_name in self.bar_widgets:
            widget = self.bar_widgets[bar_name]
            colors = widget.get_gradient_colors()
            current_color = QColor(*colors[0][1][:4]) if colors else QColor(0, 255, 0)
            color = QColorDialog.getColor(current_color, self, "Select Low Color (0%)")
            if color.isValid():
                self._update_bar_gradient_color(bar_name, 0, color)
                tab = self._get_tab_for_bar(bar_name)
                if tab and bar_name in tab.bar_gradient_low_color_btns:
                    tab.bar_gradient_low_color_btns[bar_name].setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")

    def on_bar_gradient_mid_color_clicked(self, bar_name):
        """Handle bar graph gradient mid color picker"""
        if bar_name in self.bar_widgets:
            widget = self.bar_widgets[bar_name]
            colors = widget.get_gradient_colors()
            current_color = QColor(*colors[1][1][:4]) if len(colors) > 1 else QColor(255, 255, 0)
            color = QColorDialog.getColor(current_color, self, "Select Medium Color")
            if color.isValid():
                self._update_bar_gradient_color(bar_name, 1, color)
                tab = self._get_tab_for_bar(bar_name)
                if tab and bar_name in tab.bar_gradient_mid_color_btns:
                    tab.bar_gradient_mid_color_btns[bar_name].setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")

    def on_bar_gradient_high_color_clicked(self, bar_name):
        """Handle bar graph gradient high color picker"""
        if bar_name in self.bar_widgets:
            widget = self.bar_widgets[bar_name]
            colors = widget.get_gradient_colors()
            current_color = QColor(*colors[2][1][:4]) if len(colors) > 2 else QColor(255, 0, 0)
            color = QColorDialog.getColor(current_color, self, "Select High Color")
            if color.isValid():
                self._update_bar_gradient_color(bar_name, 2, color)
                tab = self._get_tab_for_bar(bar_name)
                if tab and bar_name in tab.bar_gradient_high_color_btns:
                    tab.bar_gradient_high_color_btns[bar_name].setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")

    def on_bar_gradient_mid_threshold_changed(self, bar_name, value):
        """Handle bar graph gradient mid threshold change"""
        if bar_name in self.bar_widgets:
            self._update_bar_gradient_threshold(bar_name, 1, value)

    def on_bar_gradient_high_threshold_changed(self, bar_name, value):
        """Handle bar graph gradient high threshold change"""
        if bar_name in self.bar_widgets:
            self._update_bar_gradient_threshold(bar_name, 2, value)

    def _update_bar_gradient_color(self, bar_name, index, color):
        """Update a specific color in the bar's gradient"""
        widget = self.bar_widgets[bar_name]
        colors = list(widget.get_gradient_colors())
        if index < len(colors):
            threshold = colors[index][0]
            colors[index] = (threshold, (color.red(), color.green(), color.blue(), color.alpha()))
            widget.set_gradient_colors(colors)
            self.update_preview_widget_configs()

    def _update_bar_gradient_threshold(self, bar_name, index, value):
        """Update a specific threshold in the bar's gradient"""
        widget = self.bar_widgets[bar_name]
        colors = list(widget.get_gradient_colors())
        if index < len(colors):
            color = colors[index][1]
            colors[index] = (value, color)
            widget.set_gradient_colors(colors)
            self.update_preview_widget_configs()

    # Circular graph widget handlers
    def on_arc_toggled(self, arc_name, enabled):
        """Handle circular graph widget toggle"""
        if arc_name in self.arc_widgets:
            self.arc_widgets[arc_name].set_enabled(enabled)
            self.update_preview_widget_configs()

    def on_arc_metric_changed(self, arc_name, metric):
        """Handle circular graph metric change"""
        if arc_name in self.arc_widgets:
            self.arc_widgets[arc_name].set_metric_name(metric)
            self.update_preview_widget_configs()

    def on_arc_radius_changed(self, arc_name, radius):
        """Handle circular graph radius change"""
        if arc_name in self.arc_widgets:
            self.arc_widgets[arc_name].set_radius(radius)
            self.update_preview_widget_configs()

    def on_arc_thickness_changed(self, arc_name, thickness):
        """Handle circular graph thickness change"""
        if arc_name in self.arc_widgets:
            self.arc_widgets[arc_name].set_thickness(thickness)
            self.update_preview_widget_configs()

    def on_arc_start_angle_changed(self, arc_name, angle):
        """Handle circular graph start angle change"""
        if arc_name in self.arc_widgets:
            self.arc_widgets[arc_name].set_start_angle(angle)
            self.update_preview_widget_configs()

    def on_arc_sweep_angle_changed(self, arc_name, angle):
        """Handle circular graph sweep angle change"""
        if arc_name in self.arc_widgets:
            self.arc_widgets[arc_name].set_sweep_angle(angle)
            self.update_preview_widget_configs()

    def on_arc_rotation_changed(self, arc_name, angle):
        """Handle circular graph rotation change"""
        if arc_name in self.arc_widgets:
            self.arc_widgets[arc_name].set_rotation(angle)
            self.update_preview_widget_configs()

    def on_arc_fill_color_clicked(self, arc_name):
        """Handle circular graph fill color picker"""
        if arc_name in self.arc_widgets:
            widget = self.arc_widgets[arc_name]
            color = QColorDialog.getColor(widget.get_fill_color(), self, "Select Fill Color")
            if color.isValid():
                widget.set_fill_color(color)
                tab = self._get_tab_for_arc(arc_name)
                if tab and arc_name in tab.arc_fill_color_btns:
                    tab.arc_fill_color_btns[arc_name].setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")
                self.update_preview_widget_configs()

    def on_arc_bg_color_clicked(self, arc_name):
        """Handle circular graph background color picker"""
        if arc_name in self.arc_widgets:
            widget = self.arc_widgets[arc_name]
            color = QColorDialog.getColor(widget.get_background_color(), self, "Select Background Color")
            if color.isValid():
                widget.set_background_color(color)
                tab = self._get_tab_for_arc(arc_name)
                if tab and arc_name in tab.arc_bg_color_btns:
                    tab.arc_bg_color_btns[arc_name].setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")
                self.update_preview_widget_configs()

    def on_arc_border_color_clicked(self, arc_name):
        """Handle circular graph border color picker"""
        if arc_name in self.arc_widgets:
            widget = self.arc_widgets[arc_name]
            color = QColorDialog.getColor(widget.get_border_color(), self, "Select Border Color")
            if color.isValid():
                widget.set_border_color(color)
                widget.set_show_border(True)  # Enable border when color is selected
                tab = self._get_tab_for_arc(arc_name)
                if tab and arc_name in tab.arc_border_color_btns:
                    tab.arc_border_color_btns[arc_name].setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")
                self.update_preview_widget_configs()

    def on_arc_gradient_toggled(self, arc_name, enabled):
        """Handle circular graph gradient toggle"""
        # Show/hide gradient settings row in the appropriate tab
        tab = self._get_tab_for_arc(arc_name)
        if tab and arc_name in tab.arc_gradient_rows:
            if enabled:
                tab.arc_gradient_rows[arc_name].show()
            else:
                tab.arc_gradient_rows[arc_name].hide()
        
        # Update widget if it exists
        if arc_name in self.arc_widgets:
            self.arc_widgets[arc_name].set_use_gradient(enabled)
            self.update_preview_widget_configs()

    def on_arc_gradient_low_color_clicked(self, arc_name):
        """Handle arc gradient low color picker"""
        if arc_name in self.arc_widgets:
            widget = self.arc_widgets[arc_name]
            colors = widget.get_gradient_colors()
            current_color = QColor(*colors[0][1][:4]) if colors else QColor(0, 255, 0)
            color = QColorDialog.getColor(current_color, self, "Select Low Color (0%)")
            if color.isValid():
                self._update_arc_gradient_color(arc_name, 0, color)
                tab = self._get_tab_for_arc(arc_name)
                if tab and arc_name in tab.arc_gradient_low_color_btns:
                    tab.arc_gradient_low_color_btns[arc_name].setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")

    def on_arc_gradient_mid_color_clicked(self, arc_name):
        """Handle arc gradient mid color picker"""
        if arc_name in self.arc_widgets:
            widget = self.arc_widgets[arc_name]
            colors = widget.get_gradient_colors()
            current_color = QColor(*colors[1][1][:4]) if len(colors) > 1 else QColor(255, 255, 0)
            color = QColorDialog.getColor(current_color, self, "Select Medium Color")
            if color.isValid():
                self._update_arc_gradient_color(arc_name, 1, color)
                tab = self._get_tab_for_arc(arc_name)
                if tab and arc_name in tab.arc_gradient_mid_color_btns:
                    tab.arc_gradient_mid_color_btns[arc_name].setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")

    def on_arc_gradient_high_color_clicked(self, arc_name):
        """Handle arc gradient high color picker"""
        if arc_name in self.arc_widgets:
            widget = self.arc_widgets[arc_name]
            colors = widget.get_gradient_colors()
            current_color = QColor(*colors[2][1][:4]) if len(colors) > 2 else QColor(255, 0, 0)
            color = QColorDialog.getColor(current_color, self, "Select High Color")
            if color.isValid():
                self._update_arc_gradient_color(arc_name, 2, color)
                tab = self._get_tab_for_arc(arc_name)
                if tab and arc_name in tab.arc_gradient_high_color_btns:
                    tab.arc_gradient_high_color_btns[arc_name].setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")

    def on_arc_gradient_mid_threshold_changed(self, arc_name, value):
        """Handle arc gradient mid threshold change"""
        if arc_name in self.arc_widgets:
            self._update_arc_gradient_threshold(arc_name, 1, value)

    def on_arc_gradient_high_threshold_changed(self, arc_name, value):
        """Handle arc gradient high threshold change"""
        if arc_name in self.arc_widgets:
            self._update_arc_gradient_threshold(arc_name, 2, value)

    def _update_arc_gradient_color(self, arc_name, index, color):
        """Update a specific color in the arc's gradient"""
        widget = self.arc_widgets[arc_name]
        colors = list(widget.get_gradient_colors())
        if index < len(colors):
            threshold = colors[index][0]
            colors[index] = (threshold, (color.red(), color.green(), color.blue(), color.alpha()))
            widget.set_gradient_colors(colors)
            self.update_preview_widget_configs()

    def _update_arc_gradient_threshold(self, arc_name, index, value):
        """Update a specific threshold in the arc's gradient"""
        widget = self.arc_widgets[arc_name]
        colors = list(widget.get_gradient_colors())
        if index < len(colors):
            color = colors[index][1]
            colors[index] = (value, color)
            widget.set_gradient_colors(colors)
            self.update_preview_widget_configs()

    # Direct color change handlers (used by tabs that handle color dialog themselves)
    def on_bar_fill_color_changed(self, bar_name, color):
        """Handle bar graph fill color change (direct color)"""
        if bar_name in self.bar_widgets:
            self.bar_widgets[bar_name].set_fill_color(color)
            self.update_preview_widget_configs()

    def on_bar_bg_color_changed(self, bar_name, color):
        """Handle bar graph background color change (direct color)"""
        if bar_name in self.bar_widgets:
            self.bar_widgets[bar_name].set_background_color(color)
            self.update_preview_widget_configs()

    def on_bar_gradient_low_color_changed(self, bar_name, color):
        """Handle bar gradient low color change (direct color)"""
        if bar_name in self.bar_widgets:
            self._update_bar_gradient_color(bar_name, 0, color)

    def on_bar_gradient_mid_color_changed(self, bar_name, color):
        """Handle bar gradient mid color change (direct color)"""
        if bar_name in self.bar_widgets:
            self._update_bar_gradient_color(bar_name, 1, color)

    def on_bar_gradient_high_color_changed(self, bar_name, color):
        """Handle bar gradient high color change (direct color)"""
        if bar_name in self.bar_widgets:
            self._update_bar_gradient_color(bar_name, 2, color)

    def on_bar_gradient_mid_changed(self, bar_name, value):
        """Handle bar gradient mid threshold change"""
        if bar_name in self.bar_widgets:
            self._update_bar_gradient_threshold(bar_name, 1, value)

    def on_bar_gradient_high_changed(self, bar_name, value):
        """Handle bar gradient high threshold change"""
        if bar_name in self.bar_widgets:
            self._update_bar_gradient_threshold(bar_name, 2, value)

    def on_arc_fill_color_changed(self, arc_name, color):
        """Handle arc fill color change (direct color)"""
        if arc_name in self.arc_widgets:
            self.arc_widgets[arc_name].set_fill_color(color)
            self.update_preview_widget_configs()

    def on_arc_bg_color_changed(self, arc_name, color):
        """Handle arc background color change (direct color)"""
        if arc_name in self.arc_widgets:
            self.arc_widgets[arc_name].set_background_color(color)
            self.update_preview_widget_configs()

    def on_arc_gradient_low_color_changed(self, arc_name, color):
        """Handle arc gradient low color change (direct color)"""
        if arc_name in self.arc_widgets:
            self._update_arc_gradient_color(arc_name, 0, color)

    def on_arc_gradient_mid_color_changed(self, arc_name, color):
        """Handle arc gradient mid color change (direct color)"""
        if arc_name in self.arc_widgets:
            self._update_arc_gradient_color(arc_name, 1, color)

    def on_arc_gradient_high_color_changed(self, arc_name, color):
        """Handle arc gradient high color change (direct color)"""
        if arc_name in self.arc_widgets:
            self._update_arc_gradient_color(arc_name, 2, color)

    def on_arc_gradient_mid_changed(self, arc_name, value):
        """Handle arc gradient mid threshold change"""
        if arc_name in self.arc_widgets:
            self._update_arc_gradient_threshold(arc_name, 1, value)

    def on_arc_gradient_high_changed(self, arc_name, value):
        """Handle arc gradient high threshold change"""
        if arc_name in self.arc_widgets:
            self._update_arc_gradient_threshold(arc_name, 2, value)

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
            self.update_preview_widget_configs()

    def on_show_time_changed(self, checked):
        """Handle show time checkbox change"""
        if self.time_widget:
            self.time_widget.set_enabled(checked)
            self.update_preview_widget_configs()

    # Date format options
    def on_date_format_changed(self, format_type):
        """Handle date format change"""
        if self.date_widget:
            self.date_widget.set_date_format(format_type)
            self.update_preview_widget_configs()

    def on_show_weekday_changed(self, checked):
        """Handle show weekday checkbox change"""
        if self.date_widget:
            self.date_widget.set_show_weekday(checked)
            self.update_preview_widget_configs()

    def on_show_year_changed(self, checked):
        """Handle show year checkbox change"""
        if self.date_widget:
            self.date_widget.set_show_year(checked)
            self.update_preview_widget_configs()

    # Time format options
    def on_use_24_hour_changed(self, checked):
        """Handle 24-hour format checkbox change"""
        if self.time_widget:
            self.time_widget.set_use_24_hour(checked)
            # Disable AM/PM when using 24-hour format
            if hasattr(self.controls_manager, 'show_am_pm_checkbox'):
                self.controls_manager.show_am_pm_checkbox.setEnabled(not checked)
            self.update_preview_widget_configs()

    def on_show_seconds_changed(self, checked):
        """Handle show seconds checkbox change"""
        if self.time_widget:
            self.time_widget.set_show_seconds(checked)
            self.update_preview_widget_configs()

    def on_show_am_pm_changed(self, checked):
        """Handle show AM/PM checkbox change"""
        if self.time_widget:
            self.time_widget.set_show_am_pm(checked)
            self.update_preview_widget_configs()

    def on_metric_toggled(self, metric_name, checked):
        """Handle metric checkbox toggle"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_enabled(checked)
            self.update_preview_widget_configs()

    def on_metric_label_changed(self, metric_name, text):
        """Handle metric label change"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_custom_label(text.strip())
            self.update_preview_widget_configs()

    def on_metric_unit_changed(self, metric_name, text):
        """Handle metric unit change"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_custom_unit(text.strip())
            self.update_preview_widget_configs()

    def on_metric_freq_format_changed(self, metric_name, format_type):
        """Handle metric frequency format change (MHz/GHz)"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_freq_format(format_type)
            self.logger.debug(f"Metric {metric_name} frequency format changed to {format_type}")
            self.update_preview_widget_configs()

    def on_metric_label_position_changed(self, metric_name, position):
        """Handle metric label position change"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_label_position(position)
            self.logger.debug(f"Metric {metric_name} label position changed to {position}")
            self.update_preview_widget_configs()

    def on_metric_label_offset_x_changed(self, metric_name, offset):
        """Handle metric label X offset change"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_label_offset_x(offset)
            self.logger.debug(f"Metric {metric_name} label offset X changed to {offset}")
            self.update_preview_widget_configs()

    def on_metric_label_offset_y_changed(self, metric_name, offset):
        """Handle metric label Y offset change"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_label_offset_y(offset)
            self.logger.debug(f"Metric {metric_name} label offset Y changed to {offset}")
            self.update_preview_widget_configs()

    def on_metric_char_limit_changed(self, metric_name, limit):
        """Handle metric character limit change (for cpu_name, gpu_name)"""
        if metric_name in self.metric_widgets:
            self.metric_widgets[metric_name].set_char_limit(limit)
            self.logger.debug(f"Metric {metric_name} character limit changed to {limit}")
            self.update_preview_widget_configs()

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
        """Generate YAML configuration file - updates existing theme if loaded"""
        self.logger.info("generate_config_yaml (Save button) called")
        # If a theme is currently loaded, update it; otherwise create new
        save_path = self.current_theme_path if self.current_theme_path else None
        config_path = self.config_generator.generate_config_yaml(
            self.preview_manager, self.text_style, self.metric_widgets,
            self.date_widget, self.time_widget, self.text_widgets, self.bar_widgets,
            self.arc_widgets, existing_path=save_path
        )
        if config_path:
            self.current_theme_path = config_path  # Update path in case it was new
            self.themes_tab.refresh_themes()
    
    def create_new_theme(self):
        """Create a new blank theme - prompts for name and resets to default state"""
        # Prompt user for theme name
        theme_name, ok = QInputDialog.getText(
            self,
            "New Theme",
            "Enter a name for the new theme:",
            text="My Theme"
        )
        
        if not ok:
            return
        
        theme_name = theme_name.strip()
        if not theme_name:
            theme_name = None  # Will use timestamp fallback
        
        # Clear current theme path
        self.current_theme_path = None
        
        try:
            # Clear background and foreground
            if self.preview_manager:
                self.preview_manager.clear_all(self.backgrounds_dir)
            
            # Clear draggable foreground widget
            if hasattr(self, 'foreground_widget') and self.foreground_widget:
                self.foreground_widget.clear_foreground()
            
            # Disable all metric widgets
            for metric_name, widget in self.metric_widgets.items():
                widget.set_enabled(False)
                tab = self._get_tab_for_metric(metric_name)
                if tab:
                    checkbox = tab.metric_checkboxes.get(metric_name)
                    if checkbox:
                        checkbox.blockSignals(True)
                        checkbox.setChecked(False)
                        checkbox.blockSignals(False)
            
            # Disable date widget
            if self.date_widget:
                self.date_widget.set_enabled(False)
                if hasattr(self, 'info_tab') and self.info_tab and hasattr(self.info_tab, 'show_date_checkbox'):
                    self.info_tab.show_date_checkbox.blockSignals(True)
                    self.info_tab.show_date_checkbox.setChecked(False)
                    self.info_tab.show_date_checkbox.blockSignals(False)
            
            # Disable time widget
            if self.time_widget:
                self.time_widget.set_enabled(False)
                if hasattr(self, 'info_tab') and self.info_tab and hasattr(self.info_tab, 'show_time_checkbox'):
                    self.info_tab.show_time_checkbox.blockSignals(True)
                    self.info_tab.show_time_checkbox.setChecked(False)
                    self.info_tab.show_time_checkbox.blockSignals(False)
            
            # Disable all free text widgets
            for text_name, widget in self.text_widgets.items():
                widget.set_enabled(False)
                if hasattr(self, 'info_tab') and self.info_tab:
                    checkbox = self.info_tab.text_checkboxes.get(text_name)
                    if checkbox:
                        checkbox.blockSignals(True)
                        checkbox.setChecked(False)
                        checkbox.blockSignals(False)
            
            # Disable all bar graph widgets
            for bar_name, widget in self.bar_widgets.items():
                widget.set_enabled(False)
                tab = self._get_tab_for_bar(bar_name)
                if tab:
                    checkbox = tab.bar_checkboxes.get(bar_name)
                    if checkbox:
                        checkbox.blockSignals(True)
                        checkbox.setChecked(False)
                        checkbox.blockSignals(False)
            
            # Disable all circular graph widgets
            for arc_name, widget in self.arc_widgets.items():
                widget.set_enabled(False)
                tab = self._get_tab_for_arc(arc_name)
                if tab:
                    checkbox = tab.arc_checkboxes.get(arc_name)
                    if checkbox:
                        checkbox.blockSignals(True)
                        checkbox.setChecked(False)
                        checkbox.blockSignals(False)
        
        except Exception as e:
            self.logger.error(f"Exception during widget reset: {e}")
            return
        
        # Update preview
        self.update_preview_widget_configs()
        
        # Save the blank theme as a new file with the user-provided name
        try:
            config_path = self.config_generator.generate_config_yaml(
                self.preview_manager, self.text_style, self.metric_widgets,
                self.date_widget, self.time_widget, self.text_widgets, self.bar_widgets,
                self.arc_widgets, existing_path=None, theme_name=theme_name
            )
            if config_path:
                self.current_theme_path = config_path
                self.themes_tab.refresh_themes()
                self.logger.info(f"Created new theme: {config_path}")
        except Exception as e:
            self.logger.error(f"Exception saving new theme: {e}")

    def generate_preview(self):
        """Generate YAML configuration file"""
        self.config_generator.generate_config_yaml(
            self.preview_manager, self.text_style, self.metric_widgets,
            self.date_widget, self.time_widget, self.text_widgets, self.bar_widgets,
            self.arc_widgets, preview=True
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
