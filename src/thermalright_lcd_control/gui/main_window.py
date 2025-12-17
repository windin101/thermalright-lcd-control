"""
CLEAN Main Window - Minimal UI layer that delegates to unified controller.
Target: Keep under 300 lines.
"""
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import QTabWidget, QFrame, QMessageBox

from .components.config_generator_unified import ConfigGeneratorUnified as ConfigGenerator
from .components.text_style_manager import TextStyleManager
from .components.controls_manager import ControlsManager
from .components.preview_manager import PreviewManager
from .unified_controller import UnifiedController
from .utils.config_loader import load_config
from ..common.logging_config import get_gui_logger


class MediaPreviewUI(QMainWindow):
    """Minimal main window - delegates to unified controller"""
    
    def __init__(self, config_file_path=None, connected_device=None):
        super().__init__()
        self.logger = get_gui_logger()
        self.config = load_config(config_file_path)
        self.connected_device = connected_device
        
        # Get paths from config
        paths = self.config.get('paths', {})
        self.backgrounds_dir = paths.get('backgrounds_dir', './themes/backgrounds')
        
        # Get device dimensions
        if connected_device:
            self.device_width = connected_device.get('width', 320)
            self.device_height = connected_device.get('height', 240)
            title_info = f"{hex(connected_device['vid'])}-{hex(connected_device['pid'])} | {self.device_width}x{self.device_height}"
        else:
            self.device_width = 320
            self.device_height = 240
            title_info = "No Device | 320x240"
        
        self.setWindowTitle(f"ThermalRight LCD Control: {title_info}")
        
        # Initialize components
        self.text_style_manager = TextStyleManager()
        self.text_style = self.text_style_manager.config  # Backward compatibility
        self.config_generator = ConfigGenerator(self.config)
        
        # Unified controller (does ALL the work)
        self.unified = UnifiedController()
        self.unified.setup(self.device_width, self.device_height, 1.5)
        
        # Connect text style manager to unified controller
        self.text_style_manager.set_unified_controller(self.unified)
        # Dummy metric widgets for controls manager compatibility
        self.metric_widgets = {}
        metric_names = [
            "cpu_temperature", "gpu_temperature",
            "cpu_usage", "gpu_usage", 
            "cpu_frequency", "gpu_frequency"
        ]
        for name in metric_names:
            class DummyMetricWidget:
                def _get_default_label(self):
                    if "temperature" in name:
                        return "Temp"
                    elif "usage" in name:
                        return "Usage"
                    elif "frequency" in name:
                        return "Freq"
                    return name.replace("_", " ").title()
                
                def _get_default_unit(self):
                    if "temperature" in name:
                        return "°C"
                    elif "usage" in name:
                        return "%"
                    elif "frequency" in name:
                        return "MHz"
                    return ""
                
                @property
                def enabled(self):
                    return False
                
                def get_label(self):
                    return self._get_default_label()
                
                def get_unit(self):
                    return self._get_default_unit()
            
            self.metric_widgets[name] = DummyMetricWidget()

        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Minimal UI setup - just layout"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Left panel (controls)
        left_widget = QWidget()
        left_widget.setMinimumWidth(350)
        left_layout = QHBoxLayout(left_widget)
        
        # Controls manager
        self.controls_manager = ControlsManager(self, self.text_style, self.metric_widgets)
        left_layout.addWidget(self.controls_manager.create_controls_widget(), 6)
        
        # Right panel (preview)
        right_widget = QWidget()
        right_widget.setMinimumWidth(500)
        right_layout = QVBoxLayout(right_widget)
        
        # Setup preview area via unified controller
        self.setup_preview_area(right_layout)
        
        # Add panels to main layout
        main_layout.addWidget(left_widget, 4)
        main_layout.addWidget(right_widget, 6)
        
        # Setup tabs area
        self.setup_tabs_area(right_layout)
    
    def setup_preview_area(self, parent_layout):
        """Setup preview area - delegates to unified controller"""
        # Create preview area widget
        preview_area = QWidget()
        preview_layout = QVBoxLayout(preview_area)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # Set minimum size for preview area
        preview_area.setMinimumSize(480, 360)
        
        # Let unified controller setup the preview
        if self.unified.setup_preview_area(preview_area):
            # Create initial widgets
            self.unified.create_initial_widgets()
            
            # Setup preview manager
            self.setup_preview_manager()
        
        parent_layout.addWidget(preview_area, 8)
    

    def setup_preview_manager(self):
        """Setup preview manager and connect to unified controller"""
        # Create hidden label for preview manager
        from PySide6.QtWidgets import QLabel
        hidden_label = QLabel()
        hidden_label.hide()
        
        # Create preview manager
        self.preview_manager = PreviewManager(self.config, hidden_label, self.text_style)
        self.preview_manager.device_width = self.device_width
        self.preview_manager.device_height = self.device_height
        self.preview_manager.preview_scale = self.unified.preview_scale
        
        # Add missing attributes for unified system compatibility
        self.preview_manager.current_rotation = 0  # Default rotation
        self.preview_manager.background_color = None  # Will be set by color picker
        self.preview_manager.current_background_path = None
        self.preview_manager.current_foreground_path = None
        self.preview_manager.background_opacity = 1.0
        self.preview_manager.foreground_opacity = 1.0
        self.preview_manager.refresh_interval = 1.0
        
        # Add update_widget_configs method if missing
        if not hasattr(self.preview_manager, 'update_widget_configs'):
            def update_widget_configs(date_config=None, time_config=None, 
                                     metrics_configs=None, text_configs=None,
                                     bar_configs=None, circular_configs=None,
                                     shape_configs=None, force_update=False):
                """Update widget configs for unified system compatibility"""
                # Store configs for later use by config generator
                self.preview_manager.date_config = date_config
                self.preview_manager.time_config = time_config
                self.preview_manager.metrics_configs = metrics_configs or []
                self.preview_manager.text_configs = text_configs or []
                self.preview_manager.bar_configs = bar_configs or []
                self.preview_manager.circular_configs = circular_configs or []
                self.preview_manager.shape_configs = shape_configs or []
            
            self.preview_manager.update_widget_configs = update_widget_configs
            
            # Add other missing methods as stubs
            def is_background_enabled():
                return True
            self.preview_manager.is_background_enabled = is_background_enabled
            
            def is_foreground_enabled():
                return False
            self.preview_manager.is_foreground_enabled = is_foreground_enabled
            
            def determine_background_type(path):
                # Simple implementation
                if path and (path.endswith('.mp4') or path.endswith('.avi') or path.endswith('.mov')):
                    class BgType:
                        value = "video"
                    return BgType()
                elif path and (path.endswith('.png') or path.endswith('.jpg') or path.endswith('.jpeg')):
                    class BgType:
                        value = "image"
                    return BgType()
                else:
                    class BgType:
                        value = "color"
                    return BgType()
            self.preview_manager.determine_background_type = determine_background_type
            
            def get_background_scale_mode():
                return "scaled_fill"
            self.preview_manager.get_background_scale_mode = get_background_scale_mode
            
            def get_background_color():
                from PySide6.QtGui import QColor
                if self.preview_manager.background_color:
                    color = self.preview_manager.background_color
                    if isinstance(color, QColor):
                        return (color.red(), color.green(), color.blue())
                    elif isinstance(color, (list, tuple)) and len(color) >= 3:
                        return (color[0], color[1], color[2])
                    elif isinstance(color, dict):
                        return (color.get("r", 0), color.get("g", 0), color.get("b", 0))
                return (0, 0, 0)  # Black
            self.preview_manager.get_background_color = get_background_color
            
            self.preview_manager.update_widget_configs = update_widget_configs
        
        # Initialize configs
        self.preview_manager.date_config = None
        self.preview_manager.time_config = None
        self.preview_manager.metrics_configs = []
        self.preview_manager.text_configs = []
        self.preview_manager.bar_configs = []
        self.preview_manager.circular_configs = []
        self.preview_manager.shape_configs = []
        
        # Connect unified controller to preview manager
        self.unified.preview_manager = self.preview_manager
        self.unified.config_generator = self.config_generator
        
        # Set default background
        self.unified.set_background(None)

    def setup_tabs_area(self, parent_layout):
        """Setup tabs area"""
        self.tab_widget = QTabWidget()
        
        # Media tab
        from .tabs.media_tab import MediaTab
        media_tab = MediaTab(self.backgrounds_dir, self.config, "Media")
        # Connect media tab signals
        media_tab.thumbnail_clicked.connect(self._on_media_selected)
        media_tab.media_added.connect(self._on_media_added)
        self.tab_widget.addTab(media_tab, "Media")
        
        # Themes tab  
        from .tabs.themes_tab import ThemesTab
        from .tabs.widgets_tab import WidgetsTab
        themes_dir = f"{self.config.get('paths', {}).get('themes_dir', './themes')}/{self.device_width}{self.device_height}"
        themes_tab = ThemesTab(themes_dir, dev_width=self.device_width, dev_height=self.device_height)
        themes_tab.theme_selected.connect(self.on_theme_selected)  # Connect theme selection signal
        self.tab_widget.addTab(themes_tab, "Themes")
        
        # Widgets tab
        widgets_tab = WidgetsTab(self)
        widgets_tab.widget_added.connect(self._on_widget_added)
        widgets_tab.widget_removed.connect(self._on_widget_removed)
        widgets_tab.widget_updated.connect(self._on_widget_updated)
        self.tab_widget.addTab(widgets_tab, "Widgets")
        
        parent_layout.addWidget(self.tab_widget, 2)
    
    def _on_media_selected(self, file_path: str):
        """Handle media file selection from media tab"""
        self.logger.info(f"Media selected: {file_path}")
        
        # Update preview manager
        if hasattr(self, 'preview_manager'):
            self.preview_manager.current_background_path = file_path
            
            # Determine background type from file extension
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                self.preview_manager.background_type = "image"
            elif file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                self.preview_manager.background_type = "video"
            elif file_path.lower().endswith('.gif'):
                self.preview_manager.background_type = "gif"
            
            # Update unified controller background
            if hasattr(self, 'unified'):
                self.unified.set_background(self.preview_manager, file_path)
            
            # Update preview only (don't send to device)
            self.update_preview_only()
    
    def _on_media_added(self, file_path: str):
        """Handle new media added via media tab"""
        self.logger.info(f"New media added: {file_path}")
        # Could update UI or show notification
    
    def _on_widget_added(self, widget_type: str, properties: dict):
        """Handle new widget added via widgets tab"""
        self.logger.info(f"Widget added: {widget_type} - {properties}")
        
        # Create actual widget in unified controller
        if hasattr(self, 'unified') and hasattr(self.unified, 'create_widget'):
            widget_id = self.unified.create_widget(widget_type, properties)
            if widget_id:
                # Store reference
                if not hasattr(self, 'active_widgets'):
                    self.active_widgets = {}
                self.active_widgets[widget_id] = properties
    
    def _on_widget_removed(self, widget_id: str):
        """Handle widget removal via widgets tab"""
        self.logger.info(f"Widget removed: {widget_id}")
        
        # Remove widget from unified controller
        if hasattr(self, 'unified') and hasattr(self.unified, 'remove_widget'):
            self.unified.remove_widget(widget_id)
        
        # Remove from active widgets
        if hasattr(self, 'active_widgets') and widget_id in self.active_widgets:
            del self.active_widgets[widget_id]
    
    def _on_widget_updated(self, widget_id: str, properties: dict):
        """Handle widget property updates via widgets tab"""
        self.logger.info(f"Widget updated: {widget_id} - {properties}")
        
        # Update widget in unified controller
        if hasattr(self, 'unified') and hasattr(self.unified, 'update_widget'):
            self.unified.update_widget(widget_id, properties)
        
        # Update active widgets
        if hasattr(self, 'active_widgets') and widget_id in self.active_widgets:
            self.active_widgets[widget_id] = properties
        parent_layout.addWidget(self.tab_widget, 2)
    
    def generate_preview(self):
        """Generate preview/config - delegates to unified controller"""
        self.logger.info("Generate preview called")
        
        try:
            import traceback
            self.logger.info("=== GENERATE PREVIEW START ===")
            result = self.unified.generate_config(self.preview_manager, self.text_style)
            self.logger.info(f"Result from unified.generate_config: {result}")
            
            if result:
                msg = QMessageBox()
                msg.setWindowTitle("Success")
                msg.setText(f"Configuration saved.\nService should send to USB display.")
                msg.setIcon(QMessageBox.Information)
                msg.exec()
            else:
                msg = QMessageBox()
                msg.setWindowTitle("Error")
                msg.setText("Failed to save configuration.")
                msg.setIcon(QMessageBox.Critical)
                msg.exec()
                
        except Exception as e:
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            self.logger.error(f"Error: {e}")
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText(f"Failed: {str(e)}")
            msg.setIcon(QMessageBox.Critical)
            msg.exec()
    
    # Minimal event handlers (delegated to controls manager)
    def on_show_date_changed(self, checked):
        """Date visibility changed"""
        pass  # Handled by unified controller via widget properties
    
    def on_show_time_changed(self, checked):
        """Time visibility changed"""
        pass  # Handled by unified controller via widget properties
    
    def on_metric_toggled(self, metric_name, checked):
        """Metric toggled"""
        pass  # TODO: When we add metric widgets
    
    def on_opacity_editing_finished(self):
        """Opacity editing finished"""
        pass  # TODO: Implement opacity handling
    
    def on_opacity_text_changed(self, text):
        """Opacity text changed"""
        pass  # TODO: Implement opacity handling
    def on_font_size_changed(self, size):
        """Font size changed"""
        # Update via text style manager
        self.text_style_manager.set_font_size(size)
        
        # Update preview only (don't send to device)
        self.update_preview_only()
    
    def choose_color(self):
        """Choose text color for all widgets"""
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        
        # Get current color
        current_color = QColor(*self.text_style.color)
        
        # Open color dialog
        color = QColorDialog.getColor(current_color, self, "Choose Text Color")
        if color.isValid():
            # Update via text style manager
            self.text_style_manager.set_color(color)
            
            # Update controls manager button
            if hasattr(self, "controls_manager") and hasattr(self.controls_manager, "update_color_button"):
                self.controls_manager.update_color_button()
            
            # Update preview
            self.generate_preview()
    def choose_color(self):
        """Choose text color for all widgets"""
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        
        # Get current color
        current_color = QColor(*self.text_style.color)
        
        # Open color dialog
        color = QColorDialog.getColor(current_color, self, "Choose Text Color")
        if color.isValid():
            # Update via text style manager
            self.text_style_manager.set_color(color)
            
            # Update controls manager button
            if hasattr(self, "controls_manager") and hasattr(self.controls_manager, "update_color_button"):
                self.controls_manager.update_color_button()
            
            # Update preview only (don't send to device)
            self.update_preview_only()
    
    def on_metric_label_changed(self, metric_name, text):
        """Metric label changed"""
        pass  # TODO: Implement metric label handling
    
    def on_metric_unit_changed(self, metric_name, text):
        """Metric unit changed"""
        pass  # TODO: Implement metric unit handling
    
    def update_preview_only(self):
        """Update preview display without sending to device"""
        try:
            self.logger.info("Update preview only called")
            # Update preview manager
            if hasattr(self, 'unified'):
                self.unified._update_preview_manager()
            
            # Update unified controller background if needed
            if hasattr(self, 'unified') and hasattr(self, 'preview_manager'):
                if self.preview_manager.current_background_path:
                    self.unified.set_background(self.preview_manager, self.preview_manager.current_background_path)
            
        except Exception as e:
            self.logger.error(f"Error updating preview: {e}")
            import traceback
            traceback.print_exc()

    def save_theme(self):
        """Save current configuration as a theme"""
        from PySide6.QtWidgets import QInputDialog, QMessageBox
        
        # Get theme name from user
        theme_name, ok = QInputDialog.getText(
            self, "Save Theme", "Enter theme name:",
            text=f"Theme_{self.device_width}x{self.device_height}"
        )
        
        if not ok or not theme_name.strip():
            return
        
        # Clean theme name (replace spaces with underscores, remove special chars)
        theme_name = "".join(c for c in theme_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        theme_name = theme_name.replace(' ', '_')
        
        if not theme_name:
            QMessageBox.warning(self, "Invalid Name", "Theme name must contain at least one alphanumeric character.")
            return
        
        try:
            self.logger.info(f"Saving theme: {theme_name}")
            result = self.unified.generate_theme(self.preview_manager, self.text_style, theme_name)
            self.logger.info(f"Result from unified.generate_theme: {result}")
            
            if result:
                # Refresh themes tab to show the new theme
                if hasattr(self, 'tab_widget'):
                    for i in range(self.tab_widget.count()):
                        tab = self.tab_widget.widget(i)
                        if hasattr(tab, 'refresh_themes'):
                            tab.refresh_themes()
                            break
                
                msg = QMessageBox()
                msg.setWindowTitle("Success")
                msg.setText(f"Theme '{theme_name}' saved successfully.\nAvailable in Themes tab.")
                msg.setIcon(QMessageBox.Information)
                msg.exec()
            else:
                msg = QMessageBox()
                msg.setWindowTitle("Error")
                msg.setText("Failed to save theme.")
                msg.setIcon(QMessageBox.Critical)
                msg.exec()
                
        except Exception as e:
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            self.logger.error(f"Error: {e}")
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to save theme: {str(e)}")
            msg.setIcon(QMessageBox.Critical)
            msg.exec()

    def on_theme_selected(self, theme_path: str):
        """Handle theme selection from themes tab"""
        self.logger.info(f"Loading theme: {theme_path}")
        try:
            # Load theme configuration using ConfigLoader
            from thermalright_lcd_control.device_controller.display.config_loader import ConfigLoader
            from .utils.path_resolver import get_path_resolver
            
            config_loader = ConfigLoader()
            path_resolver = get_path_resolver()
            
            theme_config = config_loader.load_config(theme_path, self.device_width, self.device_height)
            
            # Apply theme configuration to preview manager
            if hasattr(self, 'preview_manager'):
                # Set background - resolve path dynamically
                if theme_config.background_path:
                    background_path = path_resolver.resolve_background_path(theme_config.background_path)
                    
                    self.preview_manager.current_background_path = background_path
                    self.preview_manager.background_type = theme_config.background_type.value
                    
                    # Update background color if it's a color background
                    if theme_config.background_type.value == "color":
                        from PySide6.QtGui import QColor
                        bg_color = theme_config.background_color
                        if bg_color:
                            color = QColor(bg_color[0], bg_color[1], bg_color[2])
                            self.preview_manager.background_color = color
                
                # Set text style
                if hasattr(theme_config, 'font_family'):
                    self.text_style_manager.set_font_size(theme_config.font_size or 12)
                    # Note: Color setting would need more work for unified system
                
                # Update widget configurations
                self.preview_manager.date_config = theme_config.date_config
                self.preview_manager.time_config = theme_config.time_config
                self.preview_manager.metrics_configs = theme_config.metrics_configs
                if hasattr(theme_config, "bar_configs"):
                    self.preview_manager.bar_configs = theme_config.bar_configs
                if hasattr(theme_config, "circular_configs"):
                    self.preview_manager.circular_configs = theme_config.circular_configs
                if hasattr(theme_config, "shape_configs"):
                    self.preview_manager.shape_configs = theme_config.shape_configs
            
            # Update unified controller background
            if hasattr(self, 'unified') and theme_config.background_path:
                # Use the converted path
                background_path = self.preview_manager.current_background_path
                self.unified.set_background(self.preview_manager, background_path)
            
            # Update preview display
            self.update_preview_only()
            
            self.logger.info(f"Theme loaded successfully: {theme_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading theme {theme_path}: {e}")
            import traceback
            traceback.print_exc()
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Theme Load Error", f"Failed to load theme:\n{str(e)}")


