"""
CLEAN Main Window - Minimal UI layer that delegates to unified controller.
Target: Keep under 300 lines.
"""
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import QTabWidget, QFrame, QMessageBox

from .components.config_generator_unified import ConfigGeneratorUnified as ConfigGenerator
from .components.text_style_manager import TextStyleManager
from .metrics.metric_data_manager import get_metric_manager
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
        self.foregrounds_dir = paths.get('foregrounds_dir', './themes/foregrounds')
        
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
        
        # Set minimum window size for proper layout
        self.setMinimumSize(1000, 700)  # Allow dynamic resizing
        
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
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # ========== LEFT COLUMN - Preview + Controls ==========
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setSpacing(10)
        
        # Preview area at top
        preview_container = QWidget()
        preview_container.setMinimumSize(480, 360)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # Setup preview area via unified controller
        if self.unified.setup_preview_area(preview_container):
            # Create initial widgets
            self.unified.create_initial_widgets()
            
            # Setup preview manager
            self.setup_preview_manager()
        
        left_layout.addWidget(preview_container, 6)  # Preview takes most space
        
        # Action buttons below preview
        self.controls_manager = ControlsManager(self, self.text_style, self.metric_widgets)
        action_controls = self.controls_manager._create_action_controls()
        left_layout.addWidget(action_controls, 0)  # Action buttons
        
        # Screen controls below action buttons
        screen_controls = self.controls_manager.create_controls_widget()
        left_layout.addWidget(screen_controls, 4)  # Screen controls
        
        # ========== RIGHT COLUMN - Tabs ==========
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        
        # Setup tabs area
        self.setup_tabs_area(right_layout)
        
        # ========== ADD COLUMNS TO MAIN LAYOUT ==========
        main_layout.addWidget(left_column, 1)  # 50% width
        main_layout.addWidget(right_column, 1)  # 50% width
    
    def setup_preview_area(self, parent_widget):
        """
        Setup preview area in a widget container.
        Used by unified controller.
        
        Args:
            parent_widget: The widget to contain the preview area
        """
        # Let unified controller setup the preview in the provided widget
        if self.unified.setup_preview_area(parent_widget):
            # Create initial widgets
            self.unified.create_initial_widgets()
            
            # Setup preview manager
            self.setup_preview_manager()
            return True
        return False
    

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
        self.preview_manager.foreground_position = (0, 0)  # (x, y) position
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
                return (self.preview_manager.current_background_path is not None and 
                       getattr(self.preview_manager, 'show_background_image', True))
            self.preview_manager.is_background_enabled = is_background_enabled
            
            def is_foreground_enabled():
                return self.preview_manager.current_foreground_path is not None and getattr(self.preview_manager, 'show_foreground_image', True)
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
        
        # Initialize default background to create display generator
        self.preview_manager.initialize_default_background(self.backgrounds_dir)
        
        # Set default background
        self.logger.info(f"Setting initial background with path: {self.preview_manager.current_background_path}")
        self.unified.set_background(self.preview_manager, self.preview_manager.current_background_path)
    
    def closeEvent(self, event):
        """Handle application close - cleanup resources"""
        try:
            # Cleanup unified controller (stops metric manager)
            if hasattr(self, 'unified'):
                self.unified.cleanup()
                self.logger.info("Unified controller cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        # Accept the close event
        event.accept()

    def setup_tabs_area(self, parent_layout):
        """Setup tabs area"""
        self.tab_widget = QTabWidget()
        
        # ========== TAB ORDER: Themes → Media → Foregrounds → Widgets ==========
        
        # Themes tab (FIRST)
        from .tabs.themes_tab import ThemesTab
        themes_dir = f"{self.config.get('paths', {}).get('themes_dir', './themes')}/{self.device_width}{self.device_height}"
        themes_tab = ThemesTab(themes_dir, dev_width=self.device_width, dev_height=self.device_height)
        themes_tab.theme_selected.connect(self.on_theme_selected)  # Connect theme selection signal
        self.tab_widget.addTab(themes_tab, "Themes")
        
        # Media tab (SECOND)
        from .tabs.media_tab import MediaTab
        media_tab = MediaTab(self.backgrounds_dir, self.config, "Backgrounds")
        # Connect media tab signals
        media_tab.thumbnail_clicked.connect(self._on_media_selected)
        media_tab.media_added.connect(self._on_media_added)
        self.tab_widget.addTab(media_tab, "Backgrounds")
        
        # Foregrounds tab (THIRD)
        foregrounds_tab = MediaTab(f"{self.foregrounds_dir}/{self.device_width}{self.device_height}", self.config, "Foregrounds")
        # Connect foregrounds tab signals
        foregrounds_tab.thumbnail_clicked.connect(self._on_foreground_selected)
        self.tab_widget.addTab(foregrounds_tab, "Foregrounds")
        
        # Widgets tab (FOURTH)
        from .tabs.widgets_tab import WidgetsTab
        widgets_tab = WidgetsTab(self)
        widgets_tab.widget_added.connect(self._on_widget_added)
        widgets_tab.widget_updated.connect(self._on_widget_updated)
        self.tab_widget.addTab(widgets_tab, "Widgets")
        
        # Add tab widget to layout
        parent_layout.addWidget(self.tab_widget)
    
    def _on_media_selected(self, file_path: str):
        """Handle media file selection from media tab"""
        self.logger.info(f"Media selected: {file_path}")
        
        # Update preview manager
        if hasattr(self, 'preview_manager'):
            self.preview_manager.current_background_path = file_path
            # When a background is selected, it should be shown!
            self.preview_manager.show_background_image = True
            self.logger.info(f"Set show_background_image to True")
            
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
            
            # DON'T call update_preview_only() - set_background() already updates the display
            # self.update_preview_only()
    
    def _on_media_added(self, file_path: str):
        """Handle new media added via media tab"""
        self.logger.info(f"New media added: {file_path}")
        # Could update UI or show notification
    
    def _on_foreground_selected(self, file_path: str):
        """Handle foreground file selection from foregrounds tab"""
        self.logger.info(f"Foreground selected: {file_path}")
        
        # Update preview manager
        if hasattr(self, 'preview_manager'):
            self.preview_manager.current_foreground_path = file_path
            # When a foreground is selected, it should be shown!
            self.preview_manager.show_foreground_image = True
            self.logger.info(f"Set show_foreground_image to True")
            
            # Update unified controller foreground
            if hasattr(self, 'unified'):
                self.unified.set_foreground(self.preview_manager, file_path)
            
            # Update controls manager foreground checkbox
            if hasattr(self, 'controls_manager'):
                self.controls_manager._update_fg_image_checkbox()
            
            # DON'T call update_preview_only() - set_foreground() already updates the display
            # self.update_preview_only()
    
    def _on_widget_added(self, widget_id: str, widget_type: str, properties: dict):
        """Handle new widget added via widgets tab"""
        self.logger.info(f"Widget added: {widget_id} ({widget_type}) - {properties}")
        
        # Update preview
        self.update_preview_only()
        
        # Create actual widget in unified controller with the same ID
        # Use widget type from properties (e.g., "metric", "text", "date", "time")
        # not the palette widget type (e.g., "cpu_usage", "gpu_temperature")
        widget_type_from_props = properties.get('type', 'metric')
        if hasattr(self, 'unified') and hasattr(self.unified, 'create_widget'):
            unified_widget_id = self.unified.create_widget(widget_type_from_props, properties, widget_id=widget_id)
            if unified_widget_id:
                # Store reference
                if not hasattr(self, 'active_widgets'):
                    self.active_widgets = {}
                self.active_widgets[widget_id] = properties
    
    def _on_widget_removed(self, widget_id: str):
        """Handle widget removal via widgets tab"""
        self.logger.info(f"Widget removed: {widget_id}")
        
        # Update preview
        self.update_preview_only()
        
        # Remove widget from unified controller
        if hasattr(self, 'unified') and hasattr(self.unified, 'remove_widget'):
            self.unified.remove_widget(widget_id)
        
        # Remove from active widgets
        if hasattr(self, 'active_widgets') and widget_id in self.active_widgets:
            del self.active_widgets[widget_id]
    
    def _on_widget_updated(self, widget_id: str, properties: dict):
        """Handle widget property updates via widgets tab"""
        self.logger.info(f"Widget updated: {widget_id} - {properties}")
        
        # Update preview
        self.update_preview_only()
        
        # Update widget in unified controller
        if hasattr(self, 'unified') and hasattr(self.unified, 'update_widget'):
            self.unified.update_widget(widget_id, properties)
        
        # Update active widgets
        if hasattr(self, 'active_widgets') and widget_id in self.active_widgets:
            self.active_widgets[widget_id] = properties
    
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
        if hasattr(self, 'controls_manager') and self.controls_manager.opacity_input:
            opacity = self.controls_manager.opacity_input.value() / 100.0
            if hasattr(self, 'preview_manager'):
                self.preview_manager.set_foreground_opacity(opacity)
            if hasattr(self, 'unified'):
                self.unified.set_foreground_opacity(opacity)
    
    def on_opacity_text_changed(self, text):
        """Opacity text changed"""
        # Update preview manager opacity
        try:
            opacity = float(text) / 100.0
            if hasattr(self, 'preview_manager'):
                self.preview_manager.set_foreground_opacity(opacity)
            if hasattr(self, 'unified'):
                self.unified.set_foreground_opacity(opacity)
        except ValueError:
            pass
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
                
                # Also update foreground if needed
                if self.preview_manager.current_foreground_path:
                    self.unified.set_foreground(self.preview_manager, self.preview_manager.current_foreground_path)
            
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


