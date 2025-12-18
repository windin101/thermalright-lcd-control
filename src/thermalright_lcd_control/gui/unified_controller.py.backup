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
from thermalright_lcd_control.gui.metrics.metric_data_manager import get_metric_manager
from thermalright_lcd_control.common.logging_config import get_gui_logger


class UnifiedController:
    """Controller for ALL unified widget functionality"""
    
    def __init__(self):
        self.logger = get_gui_logger()
        
        # Unified system
        self.unified_view = None
        self.unified_integration = None
        self.widgets_tab = None  # Reference to WidgetsTab for sync
        
        # Metric data manager for live system metrics
        self.metric_manager = get_metric_manager()
        
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
        
        # Start metric data collection
        self.metric_manager.start()
        self.logger.info("Metric data manager started")
        
        self.unified_integration = UnifiedIntegration(self)
        self.logger.info("Unified controller setup complete")
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'metric_manager') and self.metric_manager:
            self.metric_manager.stop()
            self.logger.info("Metric data manager stopped")
    
    def set_widgets_tab(self, widgets_tab):
        """Set reference to WidgetsTab for synchronization."""
        self.widgets_tab = widgets_tab
        self.logger.debug("WidgetsTab reference set in UnifiedController")
        
        # Connect deletion signal if unified_view exists
        if self.unified_view and hasattr(self.unified_view, 'widgetDeleted'):
            self.unified_view.widgetDeleted.connect(self._on_widget_deleted)
            self.logger.debug("Connected widgetDeleted signal")
    
    def _on_widget_deleted_from_widget(self, widget_id: str):
        """Handle widget deletion directly from widget signal."""
        print(f"[DEBUG] _on_widget_deleted_from_widget called: {widget_id}")
        
        # Remove from WidgetsTab
        if self.widgets_tab:
            success = self.widgets_tab.remove_widget(widget_id)
            if success:
                self.logger.info(f"Removed widget {widget_id} from WidgetsTab")
            else:
                self.logger.warning(f"Failed to remove widget {widget_id} from WidgetsTab")
        
        # Remove from our internal storage
        if hasattr(self, 'widgets') and widget_id in self.widgets:
            del self.widgets[widget_id]
            self.logger.info(f"Removed widget {widget_id} from UnifiedController storage")
    
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
            
            # Connect deletion signal if widgets_tab is set
            if self.widgets_tab and hasattr(self.unified_view, 'widgetDeleted'):
                # Note: Widget deletion is now handled directly from widget signals
                # self.unified_view.widgetDeleted.connect(self._on_widget_deleted, Qt.QueuedConnection)
                pass
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
            
            # Fit view to scene to ensure proper display
            self.unified_view.view.fitInView(self.unified_view.scene.sceneRect(), Qt.KeepAspectRatio)
            
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
    def create_widget(self, widget_type: str, properties: dict, widget_id: str = None) -> Optional[str]:
        """Create a new widget in the unified view"""
        if not self.unified_view:
            return None
        
        try:
            import uuid
            if widget_id is None:
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
            
            # Create widget using appropriate UnifiedGraphicsView method
            widget = None
            
            if widget_type == "metric":
                # Determine metric type and create appropriate widget
                metric_type = properties.get('metric_type', 'cpu_usage')
                label = properties.get('label', 'CPU')
                
                if 'temperature' in metric_type.lower() or 'temp' in label.lower():
                    widget = self.unified_view.create_temperature_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
                elif 'usage' in metric_type.lower() or 'cpu' in label.lower() or 'gpu' in label.lower():
                    widget = self.unified_view.create_usage_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
                elif 'frequency' in metric_type.lower() or 'freq' in label.lower():
                    widget = self.unified_view.create_frequency_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
                elif 'ram' in metric_type.lower() or 'memory' in label.lower():
                    widget = self.unified_view.create_ram_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
                elif 'gpu' in label.lower() and 'memory' in label.lower():
                    widget = self.unified_view.create_gpu_memory_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
                elif 'name' in metric_type.lower():
                    widget = self.unified_view.create_name_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
                else:
                    # Generic metric widget
                    widget = self.unified_view.create_metric_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
                    
            elif widget_type == "text":
                # Create free text widget
                widget = self.unified_view.create_free_text_widget(
                    widget_name=widget_id,
                    x=scene_x,
                    y=scene_y,
                    width=scene_width,
                    height=scene_height,
                    enabled=True,
                    **properties
                )
                
            elif widget_type == "date":
                widget = self.unified_view.create_date_widget(
                    widget_name=widget_id,
                    x=scene_x,
                    y=scene_y,
                    width=scene_width,
                    height=scene_height,
                    enabled=True,
                    **properties
                )
                
            elif widget_type == "time":
                widget = self.unified_view.create_time_widget(
                    widget_name=widget_id,
                    x=scene_x,
                    y=scene_y,
                    width=scene_width,
                    height=scene_height,
                    enabled=True,
                    **properties
                )
                # Determine shape type
                shape_type = properties.get('shape_type', 'rectangle')
                if shape_type == 'circle':
                    widget = self.unified_view.create_circle_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
                elif shape_type == 'rounded_rectangle':
                    widget = self.unified_view.create_rounded_rectangle_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
                else:  # rectangle
                    widget = self.unified_view.create_rectangle_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
                    
            elif widget_type == "graph":
                # Determine graph type
                graph_type = properties.get('graph_type', 'bar')
                if graph_type == 'circular':
                    widget = self.unified_view.create_circular_graph_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
                elif graph_type == 'bar':
                    widget = self.unified_view.create_bar_graph_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
                else:
                    widget = self.unified_view.create_graph_widget(
                        widget_name=widget_id,
                        x=scene_x,
                        y=scene_y,
                        width=scene_width,
                        height=scene_height,
                        enabled=True,
                        **properties
                    )
            
            if widget:
                # Connect metric widgets to live data
                if widget_type == "metric" and hasattr(widget, 'set_metrics_provider'):
                    self.logger.info(f"Connecting metric widget {widget_id} to metric manager...")
                    widget.set_metrics_provider(self.metric_manager)
                    # Subscribe for live updates
                    self.metric_manager.subscribe(widget_id, self._create_metric_update_callback(widget))
                    self.logger.info(f"Connected metric widget {widget_id} to live data")
                else:
                    self.logger.debug(f"Widget {widget_id} is not a metric widget or doesn't have set_metrics_provider")
                
                # Store widget reference for management
                if not hasattr(self, 'widgets'):
                    self.widgets = {}
                self.widgets[widget_id] = {
                    'widget': widget,
                    'type': widget_type,
                    'properties': properties
                }
                
                # Connect widget deletion signal directly to controller
                widget.deleteRequested.connect(lambda wid=widget_id: self._on_widget_deleted_from_widget(wid))
                
                self.logger.info(f"Created unified widget: {widget_id} ({widget_type}) at ({x},{y})")
                return widget_id
            else:
                self.logger.error(f"Failed to create widget of type: {widget_type}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error creating widget: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def remove_widget(self, widget_id: str) -> bool:
        """Remove a widget from the unified view"""
        if not hasattr(self, 'widgets') or widget_id not in self.widgets:
            return False
        
        try:
            widget_data = self.widgets[widget_id]
            
            # Unsubscribe from metric updates if it's a metric widget
            if widget_data.get('type') == 'metric':
                self.metric_manager.unsubscribe(widget_id)
                self.logger.debug(f"Unsubscribed metric widget {widget_id} from live data")
            
            # Remove from unified view using its remove_widget method
            if self.unified_view and 'widget' in widget_data:
                self.unified_view.remove_widget(widget_id)
            
            # Clean up our reference
            del self.widgets[widget_id]
            self.logger.info(f"Removed widget: {widget_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing widget {widget_id}: {e}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing widget: {e}")
        
        return False
    
    def update_widget(self, widget_id: str, properties: dict) -> bool:
        """Update widget properties"""
        if not hasattr(self, 'widgets') or widget_id not in self.widgets:
            return False
        
        try:
            widget_data = self.widgets[widget_id]
            widget = widget_data.get('widget')
            
            if not widget:
                return False
            
            # Convert position and size to scene coordinates for the widget
            update_props = properties.copy()
            
            if 'position' in properties:
                x, y = properties['position']
                update_props['x'] = int(x * self.preview_scale)
                update_props['y'] = int(y * self.preview_scale)
                del update_props['position']
            
            if 'size' in properties:
                width, height = properties['size']
                update_props['width'] = int(width * self.preview_scale)
                update_props['height'] = int(height * self.preview_scale)
                del update_props['size']
            
            # Update widget properties using its set_properties method
            widget.set_properties(update_props)
            
            # Update stored properties
            widget_data['properties'].update(properties)
            
            self.logger.info(f"Updated widget: {widget_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating widget {widget_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_metric_update_callback(self, widget):
        """Create a callback for metric widget updates"""
        def update_callback():
            """Update widget when metrics change"""
            try:
                # Trigger metric update on the widget
                # This will run on the metric manager's thread, so we need to be careful
                from PySide6.QtCore import QTimer, Qt
                # Use a single-shot timer to ensure the update happens on the main thread
                QTimer.singleShot(0, widget._update_metric)
            except Exception as e:
                self.logger.error(f"Error in metric update callback: {e}")
        
        return update_callback
