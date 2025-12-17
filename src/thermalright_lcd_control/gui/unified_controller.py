"""
Unified Controller - Handles ALL unified widget functionality.
Keeps main_window.py minimal by moving everything here.
"""
import os
from typing import Dict, Any, Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PySide6.QtGui import QBrush, QColor, QPixmap, QImage

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
            self.unified_view = UnifiedGraphicsView(preview_area_widget)
            self.unified_view.set_scene_rect(
                0, 0, 
                self.device_width * self.preview_scale,
                self.device_height * self.preview_scale
            )
            self.unified_view.set_preview_scale(self.preview_scale)
            
            # Set the view size to match scene size
            view_width = int(self.device_width * self.preview_scale)
            view_height = int(self.device_height * self.preview_scale)
            self.unified_view.view.resize(view_width, view_height)
            
            # Prevent layout from resizing the view
            from PySide6.QtWidgets import QSizePolicy
            self.unified_view.view.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            
            # Ensure viewport matches view size
            self.unified_view.view.viewport().resize(view_width, view_height)
            
            # Don't use fitInView - let the view show the scene at 1:1
            
            # Center the view on the scene center to ensure proper alignment
            scene_center = self.unified_view.scene.sceneRect().center()
            self.unified_view.view.centerOn(scene_center)
            
            # Debug viewport configuration
            self.logger.info(f"Viewport debugging:")
            self.logger.info(f"  View size: {self.unified_view.view.size()}")
            self.logger.info(f"  Viewport rect: {self.unified_view.view.viewport().rect()}")
            self.logger.info(f"  Scene rect: {self.unified_view.view.sceneRect()}")
            self.logger.info(f"  View alignment: {self.unified_view.view.alignment()}")
            self.logger.info(f"  View transform: {self.unified_view.view.transform()}")
            self.logger.info(f"  Scene center: {scene_center}")
            self.logger.info(f"  View center on: {self.unified_view.view.mapToScene(self.unified_view.view.viewport().rect().center())}")
            
            # Log after potential viewport resize
            self.logger.info(f"  After setup - Viewport rect: {self.unified_view.view.viewport().rect()}")
            
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
            self.logger.info(f"Creating widgets. Unified view exists: {self.unified_view is not None}")
            if self.unified_view:
                self.logger.info(f"Scene exists: {self.unified_view.scene is not None}")
                self.logger.info(f"View widget: {self.unified_view.view}")
                self.logger.info(f"View size: {self.unified_view.view.size() if self.unified_view.view else None}")
            # Center positions (device coordinates scaled to scene coordinates)
            center_x = (self.device_width // 2) * self.preview_scale
            center_y = (self.device_height // 2) * self.preview_scale
            
            self.logger.info(f"Creating widgets at center: ({center_x}, {center_y}), scene size: {self.device_width * self.preview_scale}x{self.device_height * self.preview_scale}")
            
            # Date widget (centered, disabled for now)
            date_widget = self.unified_view.create_date_widget(
                widget_name="date",
                x=int(center_x),
                y=int(center_y - 30),
                width=150,
                height=30,
                enabled=False,
                font_size=18,
                text_color=(255, 255, 255, 255)
            )
            
            self.logger.info(f"Date widget created. Scene pos: ({center_x}, {center_y - 30}), Widget: {type(date_widget).__name__ if date_widget else 'None'}")
            
            # Time widget (centered)
            time_widget = self.unified_view.create_time_widget(
                widget_name="time",
                x=int(center_x),
                y=int(center_y),
                width=150,
                height=30,
                enabled=True,
                font_size=24,
                text_color=(255, 255, 255, 255)
            )
            
            # Log widget count
            widget_count = len(self.unified_view._widgets) if hasattr(self.unified_view, '_widgets') else 0
            scene_items = len(self.unified_view.scene.items()) if self.unified_view.scene else 0
            self.logger.info(f"Created centered unified widgets - {widget_count} widgets tracked, {scene_items} items in scene")
            
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
    
    def generate_theme(self, preview_manager, text_style, theme_name: str) -> Optional[str]:
        """Generate theme YAML - returns file path or None"""
        try:
            # Update preview manager first
            self._update_preview_manager()
            
            # Use config generator (passed from main_window)
            if hasattr(self, 'config_generator'):
                result = self.config_generator.generate_theme_yaml(
                    preview_manager, text_style, theme_name
                )
                return result
                
        except Exception as e:
            self.logger.error(f"Error generating theme: {e}")
        
        return None
    
    def set_background(self, preview_manager, image_path: Optional[str] = None):
        """Set background image, video, or color"""
        if not self.unified_view:
            return
        
        try:
            scene = self.unified_view.scene
            if not scene:
                return
            
            if image_path and os.path.exists(image_path):
                # Determine background type
                background_type = getattr(preview_manager, 'background_type', 'image')
                self.logger.info(f"Setting background for {image_path}, type: {background_type}")
                
                if background_type == 'image':
                    # Handle image backgrounds
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            int(self.device_width * self.preview_scale),
                            int(self.device_height * self.preview_scale)
                        )
                        scene.setBackgroundBrush(QBrush(scaled_pixmap))
                    else:
                        self.logger.warning(f"Failed to load image: {image_path}")
                        self._set_color_background(preview_manager)
                        
                elif background_type == 'video':
                    # Handle video backgrounds - show thumbnail or placeholder
                    self._set_video_background(image_path)
                    
                elif background_type == 'gif':
                    # Handle GIF backgrounds - could show first frame or placeholder
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            int(self.device_width * self.preview_scale),
                            int(self.device_height * self.preview_scale)
                        )
                        scene.setBackgroundBrush(QBrush(scaled_pixmap))
                    else:
                        self.logger.warning(f"Failed to load GIF: {image_path}")
                        self._set_color_background(preview_manager)
                else:
                    # Unknown type, try as image
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            int(self.device_width * self.preview_scale),
                            int(self.device_height * self.preview_scale)
                        )
                        scene.setBackgroundBrush(QBrush(scaled_pixmap))
                    else:
                        self._set_color_background(preview_manager)
            else:
                # No image path, use color background
                self._set_color_background(preview_manager)
                
            # Force update to ensure background is visible
            self.unified_view.view.update()
                
        except Exception as e:
            self.logger.error(f"Error setting background: {e}")
    
    def _set_color_background(self, preview_manager):
        """Set color background from preview_manager"""
        scene = self.unified_view.scene
        if not scene:
            return
            
        background_color = QColor(0, 0, 0)  # Default to black
        if preview_manager and hasattr(preview_manager, 'background_color') and preview_manager.background_color:
            color = preview_manager.background_color
            self.logger.info(f"Setting background color from preview_manager: {color}")
            if hasattr(color, 'getRgb'):  # QColor
                background_color = color
                self.logger.info(f"Using QColor: {background_color.name()}")
            elif isinstance(color, (list, tuple)) and len(color) >= 3:
                background_color = QColor(color[0], color[1], color[2])
                self.logger.info(f"Using tuple: {background_color.name()}")
            elif isinstance(color, dict):
                background_color = QColor(
                    color.get('r', 0),
                    color.get('g', 0), 
                    color.get('b', 0)
                )
                self.logger.info(f"Using dict: {background_color.name()}")
        
        self.logger.info(f"Final background color: {background_color.name()}")
        scene.setBackgroundBrush(QBrush(background_color))
    
    def _set_video_background(self, video_path):
        """Set video background - show thumbnail or placeholder"""
        scene = self.unified_view.scene
        if not scene:
            return
            
        try:
            # Try to extract a thumbnail from the video
            import cv2
            
            cap = cv2.VideoCapture(video_path)
            thumbnail_pixmap = None
            
            if cap.isOpened():
                # Get frame count and seek to 10% of video
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if frame_count > 10:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 10)
                
                ret, frame = cap.read()
                if ret:
                    # Convert frame to QPixmap
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    height, width, channel = rgb_frame.shape
                    bytes_per_line = 3 * width
                    q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(q_image)
                    
                    # Scale to scene size
                    scaled_pixmap = pixmap.scaled(
                        int(self.device_width * self.preview_scale),
                        int(self.device_height * self.preview_scale)
                    )
                    thumbnail_pixmap = scaled_pixmap
                
                cap.release()
            
            if thumbnail_pixmap:
                scene.setBackgroundBrush(QBrush(thumbnail_pixmap))
                self.logger.info(f"Set video background thumbnail for: {video_path}")
            else:
                # Fallback to placeholder
                self._set_video_placeholder()
                
        except ImportError:
            self.logger.warning("OpenCV not available for video thumbnails")
            self._set_video_placeholder()
        except Exception as e:
            self.logger.error(f"Error creating video thumbnail: {e}")
            self._set_video_placeholder()
    
    def _set_video_placeholder(self):
        """Set a placeholder background for videos when thumbnail fails"""
        scene = self.unified_view.scene
        if not scene:
            return
            
        # Create a placeholder with dark background
        placeholder_color = QColor(32, 32, 32)  # Dark gray
        scene.setBackgroundBrush(QBrush(placeholder_color))
        
        self.logger.info("Set video placeholder background")
    
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

    # Widget management methods
    def create_widget(self, widget_type: str, properties: dict) -> Optional[str]:
        """Create a new widget in the unified view"""
        if not self.unified_view:
            return None
        
        try:
            import uuid
            widget_id = f"{widget_type}_{uuid.uuid4().hex[:8]}"
            
            # Get position from properties or use default
            x = properties.get('position', (50, 50))[0]
            y = properties.get('position', (50, 50))[1]
            width = properties.get('size', (100, 30))[0]
            height = properties.get('size', (100, 30))[1]
            
            # Convert to scene coordinates
            scene_x = int(x * self.preview_scale)
            scene_y = int(y * self.preview_scale)
            scene_width = int(width * self.preview_scale)
            scene_height = int(height * self.preview_scale)
            
            # Create widget based on type
            if widget_type == "metric":
                widget = self.unified_view.create_metric_widget(
                    widget_name=widget_id,
                    x=scene_x,
                    y=scene_y,
                    width=scene_width,
                    height=scene_height,
                    label=properties.get('label', 'CPU'),
                    metric_type=properties.get('metric_type', 'cpu_usage'),
                    unit=properties.get('unit', '%'),
                    font_size=properties.get('font_size', 16),
                    text_color=(255, 255, 255, 255)
                )
            elif widget_type == "text":
                widget = self.unified_view.create_text_widget(
                    widget_name=widget_id,
                    x=scene_x,
                    y=scene_y,
                    width=scene_width,
                    height=scene_height,
                    text=properties.get('text', 'Sample Text'),
                    font_size=properties.get('font_size', 16),
                    text_color=(255, 255, 255, 255)
                )
            else:
                self.logger.warning(f"Unsupported widget type: {widget_type}")
                return None
            
            if widget:
                # Store widget reference
                if not hasattr(self, 'widgets'):
                    self.widgets = {}
                self.widgets[widget_id] = widget
                self.logger.info(f"Created widget: {widget_id} ({widget_type})")
                return widget_id
            
        except Exception as e:
            self.logger.error(f"Error creating widget: {e}")
        
        return None
    
    def remove_widget(self, widget_id: str) -> bool:
        """Remove a widget from the unified view"""
        if not hasattr(self, 'widgets') or widget_id not in self.widgets:
            return False
        
        try:
            widget = self.widgets[widget_id]
            if self.unified_view and hasattr(self.unified_view, 'remove_widget'):
                self.unified_view.remove_widget(widget)
                del self.widgets[widget_id]
                self.logger.info(f"Removed widget: {widget_id}")
                return True
        except Exception as e:
            self.logger.error(f"Error removing widget: {e}")
        
        return False
    
    def update_widget(self, widget_id: str, properties: dict) -> bool:
        """Update widget properties"""
        if not hasattr(self, 'widgets') or widget_id not in self.widgets:
            return False
        
        try:
            widget = self.widgets[widget_id]
            
            # Update position if changed
            if 'position' in properties:
                x, y = properties['position']
                scene_x = int(x * self.preview_scale)
                scene_y = int(y * self.preview_scale)
                widget.setPos(scene_x, scene_y)
            
            # Update other properties via set_properties if available
            if hasattr(widget, 'set_properties'):
                widget.set_properties(properties)
            
            self.logger.info(f"Updated widget: {widget_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating widget: {e}")
        
        return False
