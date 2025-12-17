"""
Unified system integration for MVP.
Contains all unified widget -> backend integration code.
"""
from thermalright_lcd_control.gui.widgets.unified.adapter import UnifiedToDisplayAdapter


class UnifiedIntegration:
    """Handles integration between unified widgets and backend display system"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.unified_view = None
        self.preview_manager = None
        
    def setup(self, unified_view, preview_manager):
        """Setup integration with unified view and preview manager"""
        self.unified_view = unified_view
        self.preview_manager = preview_manager
        
    def update_preview_from_unified(self):
        """Update preview manager with unified widget configs"""
        if not self.preview_manager or not self.unified_view:
            return
        
        try:
            # Get configs from unified widgets
            configs = UnifiedToDisplayAdapter.get_all_configs_from_view(
                self.unified_view, self.main_window.unified.preview_scale
            )
            
            # Update preview manager
            self.preview_manager.update_widget_configs(
                date_config=configs.get("date_config"),
                time_config=configs.get("time_config"),
                metrics_configs=configs.get("metrics_configs", []),
                text_configs=configs.get("text_configs", []),
                bar_configs=configs.get("bar_configs", []),
                circular_configs=configs.get("circular_configs", []),
                shape_configs=configs.get("shape_configs", [])
            )
            
        except Exception as e:
            if hasattr(self.main_window, "logger"):
                self.main_window.logger.error(f"Error updating preview from unified: {e}")
    
    def on_unified_widget_position_changed(self, widget_name, pos):
        """Handle unified widget position change"""
        # Convert scene coordinates to device coordinates
        device_x = int(pos.x() / self.main_window.unified.preview_scale)
        device_y = int(pos.y() / self.main_window.unified.preview_scale)
        
        if hasattr(self.main_window, "logger"):
            self.main_window.logger.debug(f"Unified widget {widget_name} moved to ({device_x}, {device_y})")
        
        # Update preview when widget moves
        self.update_preview_from_unified()
