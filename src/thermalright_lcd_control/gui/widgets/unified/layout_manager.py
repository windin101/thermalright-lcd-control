"""
Unified Widget System - Layout Manager

Handles saving and loading widget layouts to/from JSON files.
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LayoutManager:
    """
    Manages saving and loading widget layouts.
    """
    
    def __init__(self, unified_view):
        """
        Initialize layout manager.
        
        Args:
            unified_view: UnifiedGraphicsView instance
        """
        self._view = unified_view
        self._layouts_dir = "layouts"
        
        # Create layouts directory if it doesn't exist
        os.makedirs(self._layouts_dir, exist_ok=True)
    
    def save_layout(self, filename: str = None) -> str:
        """
        Save current widget layout to JSON file.
        
        Args:
            filename: Optional filename (default: auto-generated)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            # Generate auto filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"layout_{timestamp}.json"
        
        # Ensure .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = os.path.join(self._layouts_dir, filename)
        
        # Collect widget data
        widgets_data = []
        for widget_name, widget in self._view.get_all_widgets().items():
            try:
                widget_data = {
                    'widget_name': widget_name,
                    'widget_type': widget.widget_type,
                    'properties': widget.get_properties()
                }
                widgets_data.append(widget_data)
            except Exception as e:
                logger.error(f"Failed to serialize widget {widget_name}: {e}")
        
        # Create layout data
        layout_data = {
            'metadata': {
                'version': '1.0',
                'created': datetime.now().isoformat(),
                'widget_count': len(widgets_data)
            },
            'scene': {
                'width': self._view.scene_rect.width() if hasattr(self._view, 'scene_rect') else 800,
                'height': self._view.scene_rect.height() if hasattr(self._view, 'scene_rect') else 600
            },
            'widgets': widgets_data
        }
        
        # Save to file
        try:
            with open(filepath, 'w') as f:
                json.dump(layout_data, f, indent=2, default=self._json_serializer)
            
            logger.info(f"Layout saved to {filepath} ({len(widgets_data)} widgets)")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save layout: {e}")
            raise
    
    def load_layout(self, filepath: str) -> bool:
        """
        Load widget layout from JSON file.
        
        Args:
            filepath: Path to layout file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                layout_data = json.load(f)
            
            # Clear existing widgets
            self._view.clear_widgets()
            
            # Create widgets from data
            success_count = 0
            for widget_data in layout_data.get('widgets', []):
                try:
                    widget_name = widget_data['widget_name']
                    widget_type = widget_data['widget_type']
                    properties = widget_data['properties']
                    
                    # Extract basic properties needed for creation
                    x = properties.get('x', 0)
                    y = properties.get('y', 0)
                    width = properties.get('width', 100)
                    height = properties.get('height', 50)
                    
                    # Create widget based on type
                    widget = None
                    
                    if widget_type == 'date':
                        widget = self._view.create_date_widget(
                            widget_name=widget_name,
                            x=x, y=y, width=width, height=height,
                            enabled=properties.get('enabled', True),
                            font_family=properties.get('font_family', 'Arial'),
                            font_size=properties.get('font_size', 14),
                            bold=properties.get('bold', False),
                            text_color=properties.get('text_color', (0, 0, 0, 255)),
                            date_format=properties.get('date_format', 'dd/MM/yyyy')
                        )
                    
                    elif widget_type == 'time':
                        widget = self._view.create_time_widget(
                            widget_name=widget_name,
                            x=x, y=y, width=width, height=height,
                            enabled=properties.get('enabled', True),
                            font_family=properties.get('font_family', 'Arial'),
                            font_size=properties.get('font_size', 14),
                            bold=properties.get('bold', False),
                            text_color=properties.get('text_color', (0, 0, 0, 255)),
                            time_format=properties.get('time_format', 'HH:mm:ss')
                        )
                    
                    elif widget_type == 'free_text':
                        widget = self._view.create_free_text_widget(
                            widget_name=widget_name,
                            x=x, y=y, width=width, height=height,
                            enabled=properties.get('enabled', True),
                            font_family=properties.get('font_family', 'Arial'),
                            font_size=properties.get('font_size', 14),
                            bold=properties.get('bold', False),
                            text_color=properties.get('text_color', (0, 0, 0, 255)),
                            text=properties.get('text', ''),
                            alignment=properties.get('alignment', 'center')
                        )
                    
                    elif widget_type == 'rectangle':
                        widget = self._view.create_rectangle_widget(
                            widget_name=widget_name,
                            x=x, y=y, width=width, height=height,
                            enabled=properties.get('enabled', True),
                            fill_color=properties.get('fill_color', (200, 200, 255, 180)),
                            border_color=properties.get('border_color', (0, 0, 255, 255)),
                            border_width=properties.get('border_width', 2)
                        )
                    
                    elif widget_type == 'rounded_rectangle':
                        widget = self._view.create_rounded_rectangle_widget(
                            widget_name=widget_name,
                            x=x, y=y, width=width, height=height,
                            enabled=properties.get('enabled', True),
                            fill_color=properties.get('fill_color', (200, 200, 255, 180)),
                            border_color=properties.get('border_color', (0, 0, 255, 255)),
                            border_width=properties.get('border_width', 2),
                            corner_radius=properties.get('corner_radius', 10)
                        )
                    
                    elif widget_type == 'circle':
                        widget = self._view.create_circle_widget(
                            widget_name=widget_name,
                            x=x, y=y, width=width, height=height,
                            enabled=properties.get('enabled', True),
                            fill_color=properties.get('fill_color', (200, 200, 255, 180)),
                            border_color=properties.get('border_color', (0, 0, 255, 255)),
                            border_width=properties.get('border_width', 2)
                        )
                    
                    elif widget_type == 'metric':
                        # Metric widgets need special handling
                        metric_type = properties.get('metric_type', 'cpu_temperature')
                        
                        # Map metric type to appropriate creation method
                        if metric_type.endswith('_temperature'):
                            widget = self._view.create_temperature_widget(
                                widget_name=widget_name,
                                x=x, y=y, width=width, height=height,
                                enabled=properties.get('enabled', True),
                                font_family=properties.get('font_family', 'Arial'),
                                font_size=properties.get('font_size', 14),
                                bold=properties.get('bold', False),
                                text_color=properties.get('text_color', (255, 0, 0, 255)),
                                metric_type=metric_type,
                                unit=properties.get('unit', '°C'),
                                decimal_places=properties.get('decimal_places', 1),
                                prefix=properties.get('prefix', ''),
                                suffix=properties.get('suffix', '')
                            )
                        elif metric_type.endswith('_usage'):
                            widget = self._view.create_usage_widget(
                                widget_name=widget_name,
                                x=x, y=y, width=width, height=height,
                                enabled=properties.get('enabled', True),
                                font_family=properties.get('font_family', 'Arial'),
                                font_size=properties.get('font_size', 14),
                                bold=properties.get('bold', False),
                                text_color=properties.get('text_color', (0, 255, 0, 255)),
                                metric_type=metric_type,
                                unit=properties.get('unit', '%'),
                                decimal_places=properties.get('decimal_places', 1),
                                prefix=properties.get('prefix', ''),
                                suffix=properties.get('suffix', '')
                            )
                        elif metric_type.endswith('_frequency'):
                            widget = self._view.create_frequency_widget(
                                widget_name=widget_name,
                                x=x, y=y, width=width, height=height,
                                enabled=properties.get('enabled', True),
                                font_family=properties.get('font_family', 'Arial'),
                                font_size=properties.get('font_size', 14),
                                bold=properties.get('bold', False),
                                text_color=properties.get('text_color', (0, 0, 255, 255)),
                                metric_type=metric_type,
                                unit=properties.get('unit', 'GHz'),
                                decimal_places=properties.get('decimal_places', 2),
                                prefix=properties.get('prefix', ''),
                                suffix=properties.get('suffix', '')
                            )
                        elif metric_type.endswith('_name'):
                            widget = self._view.create_name_widget(
                                widget_name=widget_name,
                                x=x, y=y, width=width, height=height,
                                enabled=properties.get('enabled', True),
                                font_family=properties.get('font_family', 'Arial'),
                                font_size=properties.get('font_size', 14),
                                bold=properties.get('bold', False),
                                text_color=properties.get('text_color', (100, 50, 150, 255)),
                                metric_type=metric_type,
                                unit=properties.get('unit', ''),
                                decimal_places=properties.get('decimal_places', 0),
                                prefix=properties.get('prefix', ''),
                                suffix=properties.get('suffix', '')
                            )
                        elif metric_type.startswith('ram_'):
                            widget = self._view.create_ram_widget(
                                widget_name=widget_name,
                                x=x, y=y, width=width, height=height,
                                enabled=properties.get('enabled', True),
                                font_family=properties.get('font_family', 'Arial'),
                                font_size=properties.get('font_size', 14),
                                bold=properties.get('bold', False),
                                text_color=properties.get('text_color', (0, 128, 128, 255)),
                                metric_type=metric_type,
                                unit=properties.get('unit', '%' if 'percent' in metric_type else 'GB'),
                                decimal_places=properties.get('decimal_places', 1),
                                prefix=properties.get('prefix', ''),
                                suffix=properties.get('suffix', '')
                            )
                        elif metric_type.startswith('gpu_mem_'):
                            widget = self._view.create_gpu_memory_widget(
                                widget_name=widget_name,
                                x=x, y=y, width=width, height=height,
                                enabled=properties.get('enabled', True),
                                font_family=properties.get('font_family', 'Arial'),
                                font_size=properties.get('font_size', 14),
                                bold=properties.get('bold', False),
                                text_color=properties.get('text_color', (128, 0, 128, 255)),
                                metric_type=metric_type,
                                unit=properties.get('unit', '%' if 'percent' in metric_type else 'GB'),
                                decimal_places=properties.get('decimal_places', 1),
                                prefix=properties.get('prefix', ''),
                                suffix=properties.get('suffix', '')
                            )
                    
                    elif widget_type == 'bar_graph':
                        widget = self._view.create_bar_graph_widget(
                            widget_name=widget_name,
                            x=x, y=y, width=width, height=height,
                            enabled=properties.get('enabled', True),
                            show_grid=properties.get('show_grid', True),
                            grid_color=properties.get('grid_color', (200, 200, 200, 100)),
                            animation_duration=properties.get('animation_duration', 500),
                            orientation=properties.get('orientation', 'vertical'),
                            bar_spacing=properties.get('bar_spacing', 0.2),
                            show_values=properties.get('show_values', True),
                            show_labels=properties.get('show_labels', True),
                            value_format=properties.get('value_format', '{:.1f}'),
                            data=properties.get('data', [])
                        )
                    
                    elif widget_type == 'circular_graph':
                        widget = self._view.create_circular_graph_widget(
                            widget_name=widget_name,
                            x=x, y=y, width=width, height=height,
                            enabled=properties.get('enabled', True),
                            show_grid=properties.get('show_grid', True),
                            grid_color=properties.get('grid_color', (200, 200, 200, 100)),
                            animation_duration=properties.get('animation_duration', 500),
                            chart_type=properties.get('chart_type', 'pie'),
                            hole_size=properties.get('hole_size', 0.4),
                            show_percentages=properties.get('show_percentages', True),
                            exploded=properties.get('exploded', False),
                            explode_distance=properties.get('explode_distance', 10.0),
                            data=properties.get('data', [])
                        )
                    
                    # Apply remaining properties
                    if widget:
                        # Remove properties already used in creation
                        used_props = ['x', 'y', 'width', 'height', 'enabled']
                        remaining_props = {k: v for k, v in properties.items() 
                                         if k not in used_props}
                        
                        if remaining_props:
                            widget.set_properties(remaining_props)
                        
                        success_count += 1
                        logger.debug(f"Loaded widget: {widget_name} ({widget_type})")
                    
                except Exception as e:
                    logger.error(f"Failed to load widget {widget_data.get('widget_name', 'unknown')}: {e}")
            
            logger.info(f"Layout loaded from {filepath} ({success_count}/{len(layout_data.get('widgets', []))} widgets)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load layout: {e}")
            return False
    
    def list_layouts(self) -> List[Dict[str, Any]]:
        """
        List all saved layouts.
        
        Returns:
            List of layout info dictionaries
        """
        layouts = []
        
        try:
            for filename in os.listdir(self._layouts_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self._layouts_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            layout_data = json.load(f)
                        
                        layouts.append({
                            'filename': filename,
                            'filepath': filepath,
                            'created': layout_data.get('metadata', {}).get('created', ''),
                            'widget_count': layout_data.get('metadata', {}).get('widget_count', 0),
                            'size': os.path.getsize(filepath)
                        })
                    except:
                        # Skip corrupted files
                        continue
        except FileNotFoundError:
            # Directory doesn't exist yet
            pass
        
        # Sort by creation time (newest first)
        layouts.sort(key=lambda x: x.get('created', ''), reverse=True)
        
        return layouts
    
    def delete_layout(self, filename: str) -> bool:
        """
        Delete a saved layout.
        
        Args:
            filename: Layout filename
            
        Returns:
            True if successful, False otherwise
        """
        filepath = os.path.join(self._layouts_dir, filename)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted layout: {filepath}")
                return True
            else:
                logger.warning(f"Layout not found: {filepath}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete layout: {e}")
            return False
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for non-serializable objects."""
        if isinstance(obj, (tuple, list)):
            return list(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
