"""
CLEAN Main Window - Minimal UI layer that delegates to unified controller.
Target: Keep under 300 lines.
"""
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import QTabWidget, QFrame, QMessageBox

from .components.config_generator import ConfigGenerator
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
        self.text_style = TextStyleConfig()
        self.config_generator = ConfigGenerator(self.config)
        
        # Unified controller (does ALL the work)
        self.unified = UnifiedController()
        self.unified.setup(self.device_width, self.device_height)
        
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
        self.controls_manager = ControlsManager(self, self.text_style, {})
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
        media_tab = MediaTab(self, self.config)
        self.tab_widget.addTab(media_tab, "Media")
        
        # Themes tab  
        from .tabs.themes_tab import ThemesTab
        themes_tab = ThemesTab(self, self.config)
        self.tab_widget.addTab(themes_tab, "Themes")
        
        parent_layout.addWidget(self.tab_widget, 2)
    
    def generate_preview(self):
        """Generate preview/config - delegates to unified controller"""
        self.logger.info("Generate preview called")
        
        try:
            result = self.unified.generate_config(self.preview_manager, self.text_style)
            
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


# Minimal text style config (moved from draggable_widget)
class TextStyleConfig:
    """Minimal text style configuration"""
    def __init__(self):
        self.font_family = "Arial"
        self.font_size = 16
        self.color = (255, 255, 255, 255)
        self.bold = False
        # Text effects (for config generation)
        self.shadow_enabled = False
        self.shadow_color = (0, 0, 0, 128)
        self.shadow_offset_x = 2
        self.shadow_offset_y = 2
        self.shadow_blur = 3
        self.outline_enabled = False
        self.outline_color = (0, 0, 0, 255)
        self.outline_width = 1
        self.gradient_enabled = False
        self.gradient_color1 = (255, 255, 255, 255)
        self.gradient_color2 = (107, 105, 108, 255)
        self.gradient_direction = "vertical"