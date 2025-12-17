"""
Unified Controller - Handles ALL unified widget functionality.
Keeps main_window.py minimal by moving everything here.
"""
import os
from typing import Dict, Any, Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PySide6.QtGui import QBrush, QColor, QPixmap

from thermalright_lcd_control.gui.widgets.unified import UnifiedGraphicsView
from thermalright_lcd_control.gui.widgets.unified.adapter import UnifiedToDisplayAdapter
from thermalright_lcd_control.gui.unified_integration import UnifiedIntegration
from thermalright_lcd_control.common.logging_config import get_gui_logger


class UnifiedController:
    """Controller for ALL unified widget functionality"""
    
    def __init__(self):
        self.logger = get_gui_logger()
        
        # Unified system
        self.unified_view = None
        self.unified_integration = None
        
        # State
        self.device_width = 320
        self.device_height = 240
        self.preview_scale = 1.5
        
        # Timer for updates
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(100)
        self._update_timer.timeout.connect(self._update_preview_manager)
    
    def setup(self, device_width: int, device_height: int, preview_scale: float = 1.5):
        """Setup unified system"""
        self.device_width = device_width
        self.device_height = device_height
        self.preview_scale = preview_scale
        
        self.unified_integration = UnifiedIntegration(self)
        self.logger.info("Unified controller setup complete")
    
    def setup_preview_area(self, preview_area_widget: QWidget) -> bool:
        """Setup unified preview area - returns success"""
        try:
            # Clear layout
            layout = preview_area_widget.layout()
            if layout:
                while layout.count():
                    item = layout.takeAt(0)
                    if item.widget():
                        item.widget().hide()
            
            # Create unified view
            self.unified_view = UnifiedGraphicsView()
            self.unified_view.set_scene_rect(
                0, 0, 
                self.device_width * self.preview_scale,
                self.device_height * self.preview_scale
            )
            self.unified_view.set_preview_scale(self.preview_scale)
            
            # Black background
            scene = self.unified_view.scene
            if scene:
                scene.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
            
            # Add to layout
            layout.addWidget(self.unified_view.view)
            
            self.logger.info("Unified preview area setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup preview area: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_initial_widgets(self):
        """Create initial date/time widgets"""
        if not self.unified_view:
            return
        
        try:
            # Date widget (red for visibility)
            self.unified_view.create_date_widget(
                widget_name="date",
                        # Date widget (white, reasonable position)
        self.unified_view.create_date_widget(
            widget_name="date",
            x=int(40 * self.preview_scale),  # Within 320 width
            y=int(30 * self.preview_scale),  # Within 240 height
            width=150,
            height=30,
            enabled=True,
            font_size=18,  # Reasonable size
            text_color=(255, 255, 255, 255)  # White
        )
                y=int(50 * self.preview_scale),
                width=150,
                height=30,
                enabled=True,
                font_size=20,
                text_color=(255, 0, 0, 255)
            )
            
            # Time widget (green for visibility)
            self.unified_view.create_time_widget(
                widget_name="time",
                        # Time widget (white, below date)
        self.unified_view.create_time_widget(
            widget_name="time",
            x=int(40 * self.preview_scale),  # Same X as date
            y=int(80 * self.preview_scale),  # Below date
            width=150,
            height=30,
            enabled=True,
            font_size=24,  # Slightly larger than date
            text_color=(255, 255, 255, 255)  # White
        )
                y=int(100 * self.preview_scale),
                width=150,
                height=30,
                enabled=True,
                font_size=20,
                text_color=(0, 255, 0, 255)
            )
            
            self.logger.info("Created initial unified widgets")
            
        except Exception as e:
            self.logger.error(f"Error creating widgets: {e}")
    
    def update_preview(self):
        """Update preview manager with current widget configs"""
        if not self.unified_view:
            return
        
        # Debounce
        if self._update_timer.isActive():
            self._update_timer.stop()
        self._update_timer.start()
    
    def _update_preview_manager(self):
        """Actually update preview manager (called by timer)"""
        if not self.unified_view or not hasattr(self, 'preview_manager'):
            return
        
        try:
            configs = UnifiedToDisplayAdapter.get_all_configs_from_view(
                self.unified_view, self.preview_scale
            )
            
            if hasattr(self, 'preview_manager'):
                self.preview_manager.update_widget_configs(
                    date_config=configs.get("date_config"),
                    time_config=configs.get("time_config"),
                    metrics_configs=configs.get("metrics_configs", []),
                    text_configs=configs.get("text_configs", []),
                    bar_configs=configs.get("bar_configs", []),
                    circular_configs=configs.get("circular_configs", []),
                    shape_configs=configs.get("shape_configs", []),
                    force_update=True
                )
            
            self.logger.debug("Updated preview manager")
            
        except Exception as e:
            self.logger.error(f"Error updating preview manager: {e}")
    
    def generate_config(self, preview_manager, text_style) -> Optional[str]:
        """Generate config YAML - returns file path or None"""
        try:
            # Update preview manager first
            self._update_preview_manager()
            
            # Use config generator (passed from main_window)
            if hasattr(self, 'config_generator'):
                result = self.config_generator.generate_config_yaml(
                    preview_manager, text_style, preview=True
                )
                return result
                
        except Exception as e:
            self.logger.error(f"Error generating config: {e}")
        
        return None
    
    def set_background(self, image_path: Optional[str] = None):
        """Set background image or color"""
        if not self.unified_view:
            return
        
        try:
            scene = self.unified_view.scene
            if not scene:
                return
            
            if image_path and os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        int(self.device_width * self.preview_scale),
                        int(self.device_height * self.preview_scale)
                    )
                    scene.setBackgroundBrush(QBrush(scaled_pixmap))
            else:
                scene.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
                
        except Exception as e:
            self.logger.error(f"Error setting background: {e}")
    
    # Property accessors for main_window
    @property
    def view_widget(self):
        """Get view widget for adding to layouts"""
        if self.unified_view:
            return self.unified_view.view
        return None
    
    @property
    def widget_count(self):
        """Number of widgets"""
        if not self.unified_view:
            return 0
        return len(self.unified_view.get_all_widgets())