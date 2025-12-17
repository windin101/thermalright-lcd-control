"""
Text Style Manager - Handles text styling for unified widgets
"""
from typing import Optional, Dict, Any
from PySide6.QtGui import QColor


class TextStyleConfig:
    """Text style configuration for all widgets"""
    
    def __init__(self):
        self.font_family = "Arial"
        self.font_size = 16
        self.color = (255, 255, 255, 255)  # RGBA tuple
        self.bold = False
        self.italic = False
        
        # Text effects
        self.shadow_enabled = False
        self.shadow_color = (0, 0, 0, 128)
        self.shadow_offset_x = 2
        self.shadow_offset_y = 2
        self.shadow_blur = 3
        
        self.outline_enabled = True
        self.outline_color = (0, 0, 0, 255)
        self.outline_width = 1
        
        self.gradient_enabled = True
        self.gradient_color1 = (255, 255, 255, 255)
        self.gradient_color2 = (107, 105, 108, 255)
        self.gradient_direction = "vertical"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for config generation"""
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "color": self.color,
            "bold": self.bold,
            "italic": self.italic,
            "shadow_enabled": self.shadow_enabled,
            "shadow_color": self.shadow_color,
            "shadow_offset_x": self.shadow_offset_x,
            "shadow_offset_y": self.shadow_offset_y,
            "shadow_blur": self.shadow_blur,
            "outline_enabled": self.outline_enabled,
            "outline_color": self.outline_color,
            "outline_width": self.outline_width,
            "gradient_enabled": self.gradient_enabled,
            "gradient_color1": self.gradient_color1,
            "gradient_color2": self.gradient_color2,
            "gradient_direction": self.gradient_direction,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextStyleConfig':
        """Create from dictionary"""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config


class TextStyleManager:
    """Manages text styling for unified widgets"""
    
    def __init__(self, unified_controller=None):
        self.unified_controller = unified_controller
        self.config = TextStyleConfig()
    
    def set_unified_controller(self, unified_controller):
        """Set unified controller reference"""
        self.unified_controller = unified_controller
    
    def apply_to_all_widgets(self):
        """Apply current text style to all unified widgets"""
        if not self.unified_controller or not hasattr(self.unified_controller, 'unified_view'):
            return
        
        unified_view = self.unified_controller.unified_view
        if not unified_view:
            return
        
        widgets = unified_view.get_all_widgets()
        for widget in widgets.values():
            self._apply_to_widget(widget)
    
    def _apply_to_widget(self, widget):
        """Apply text style to a single widget"""
        from PySide6.QtGui import QColor
        
        # Apply text color
        if hasattr(widget, 'text_color'):
            color = QColor(*self.config.color)
            widget.text_color = color
        
        # Apply font size
        if hasattr(widget, 'font_size'):
            widget.font_size = self.config.font_size
        
        # Apply font family
        if hasattr(widget, 'font_family'):
            widget.font_family = self.config.font_family
        
        # Apply bold/italic
        if hasattr(widget, 'bold'):
            widget.bold = self.config.bold
        
        if hasattr(widget, 'italic'):
            widget.italic = self.config.italic
    
    def set_color(self, color):
        """Set text color and apply to widgets"""
        if isinstance(color, QColor):
            self.config.color = (color.red(), color.green(), color.blue(), color.alpha())
        elif isinstance(color, (list, tuple)) and len(color) >= 3:
            if len(color) == 3:
                self.config.color = (color[0], color[1], color[2], 255)
            else:
                self.config.color = tuple(color)
        self.apply_to_all_widgets()
    
    def set_font_size(self, size: int):
        """Set font size and apply to widgets"""
        self.config.font_size = size
        self.apply_to_all_widgets()
    
    def set_font_family(self, font_family: str):
        """Set font family and apply to widgets"""
        self.config.font_family = font_family
        self.apply_to_all_widgets()
    
    def set_opacity(self, opacity: float):
        """Set text opacity (0.0 to 1.0)"""
        r, g, b, _ = self.config.color
        self.config.color = (r, g, b, int(opacity * 255))
        self.apply_to_all_widgets()
    
    def hex_to_qcolor(self, hex_color: str) -> QColor:
        """Convert hex string to QColor"""
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        
        if len(hex_color) == 8:  # RGBA
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = int(hex_color[6:8], 16)
            return QColor(r, g, b, a)
        elif len(hex_color) == 6:  # RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return QColor(r, g, b, 255)
        else:
            return QColor(255, 255, 255, 255)  # Default white
    
    def qcolor_to_hex(self, color: QColor) -> str:
        """Convert QColor to hex string"""
        return f"#{color.red():02x}{color.green():02x}{color.blue():02x}{color.alpha():02x}"
