"""
Widget Configuration - Metadata for all available widgets in the palette.
"""
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum


class WidgetCategory(Enum):
    """Categories for widget organization."""
    CPU = "CPU Metrics"
    GPU = "GPU Metrics"
    RAM = "RAM Metrics"
    SYSTEM = "System"
    TEXT = "Text"
    GRAPHS = "Graphs"


@dataclass
class WidgetMetadata:
    """Metadata for a widget type."""
    widget_type: str
    display_name: str
    description: str
    category: WidgetCategory
    icon_color: str
    default_properties: Dict[str, Any]
    icon_letter: str = None
    
    def __post_init__(self):
        """Set default icon letter if not provided."""
        if self.icon_letter is None:
            self.icon_letter = self.display_name[0].upper()


# Widget metadata for all available widgets
WIDGET_METADATA: Dict[str, WidgetMetadata] = {}

# CPU Widgets
WIDGET_METADATA.update({
    "cpu_usage": WidgetMetadata(
        widget_type="cpu_usage",
        display_name="CPU Usage",
        description="CPU utilization percentage",
        category=WidgetCategory.CPU,
        icon_color="#FF6B6B",
        default_properties={
            "type": "metric",
            "label": "CPU",
            "metric_type": "cpu_usage",
            "unit": "%",
            "position": (160, 120),  # Center of 320x240 preview
            "size": (120, 30),
            "font_size": 16,
        }
    ),
    "cpu_temperature": WidgetMetadata(
        widget_type="cpu_temperature",
        display_name="CPU Temp",
        description="CPU temperature",
        category=WidgetCategory.CPU,
        icon_color="#FF8E53",
        default_properties={
            "type": "metric",
            "label": "CPU",
            "metric_type": "cpu_temperature",
            "unit": "°C",
            "position": (160, 120),
            "size": (120, 30),
            "font_size": 16,
        }
    ),
    "cpu_frequency": WidgetMetadata(
        widget_type="cpu_frequency",
        display_name="CPU Freq",
        description="CPU frequency",
        category=WidgetCategory.CPU,
        icon_color="#FFA726",
        default_properties={
            "type": "metric",
            "label": "CPU",
            "metric_type": "cpu_frequency",
            "unit": " MHz",
            "position": (160, 120),
            "size": (120, 30),
            "font_size": 16,
        }
    ),
    "cpu_name": WidgetMetadata(
        widget_type="cpu_name",
        display_name="CPU Name",
        description="CPU model name",
        category=WidgetCategory.CPU,
        icon_color="#FFCC80",
        default_properties={
            "type": "metric",
            "label": "",
            "metric_type": "cpu_name",
            "unit": "",
            "position": (160, 120),
            "size": (200, 30),  # Wider for names
            "font_size": 14,
        }
    ),
})

# GPU Widgets
WIDGET_METADATA.update({
    "gpu_usage": WidgetMetadata(
        widget_type="gpu_usage",
        display_name="GPU Usage",
        description="GPU utilization percentage",
        category=WidgetCategory.GPU,
        icon_color="#4ECDC4",
        default_properties={
            "type": "metric",
            "label": "GPU",
            "metric_type": "gpu_usage",
            "unit": "%",
            "position": (160, 120),
            "size": (120, 30),
            "font_size": 16,
        }
    ),
    "gpu_temperature": WidgetMetadata(
        widget_type="gpu_temperature",
        display_name="GPU Temp",
        description="GPU temperature",
        category=WidgetCategory.GPU,
        icon_color="#45B7D1",
        default_properties={
            "type": "metric",
            "label": "GPU",
            "metric_type": "gpu_temperature",
            "unit": "°C",
            "position": (160, 120),
            "size": (120, 30),
            "font_size": 16,
        }
    ),
    "gpu_frequency": WidgetMetadata(
        widget_type="gpu_frequency",
        display_name="GPU Freq",
        description="GPU frequency",
        category=WidgetCategory.GPU,
        icon_color="#A3D9FF",
        default_properties={
            "type": "metric",
            "label": "GPU",
            "metric_type": "gpu_frequency",
            "unit": " MHz",
            "position": (160, 120),
            "size": (120, 30),
            "font_size": 16,
        }
    ),
    "gpu_name": WidgetMetadata(
        widget_type="gpu_name",
        display_name="GPU Name",
        description="GPU model name",
        category=WidgetCategory.GPU,
        icon_color="#96DED1",
        default_properties={
            "type": "metric",
            "label": "",
            "metric_type": "gpu_name",
            "unit": "",
            "position": (160, 120),
            "size": (200, 30),
            "font_size": 14,
        }
    ),
    "gpu_memory": WidgetMetadata(
        widget_type="gpu_memory",
        display_name="GPU Memory",
        description="GPU memory usage",
        category=WidgetCategory.GPU,
        icon_color="#88D8B0",
        default_properties={
            "type": "metric",
            "label": "GPU Mem",
            "metric_type": "gpu_mem_percent",
            "unit": "%",
            "position": (160, 120),
            "size": (150, 30),
            "font_size": 16,
        }
    ),
})

# RAM Widgets
WIDGET_METADATA.update({
    "ram_percent": WidgetMetadata(
        widget_type="ram_percent",
        display_name="RAM Usage",
        description="RAM utilization percentage",
        category=WidgetCategory.RAM,
        icon_color="#96CEB4",
        default_properties={
            "type": "metric",
            "label": "RAM",
            "metric_type": "ram_percent",
            "unit": "%",
            "position": (160, 120),
            "size": (120, 30),
            "font_size": 16,
        }
    ),
    "ram_used": WidgetMetadata(
        widget_type="ram_used",
        display_name="RAM Used",
        description="RAM used/total",
        category=WidgetCategory.RAM,
        icon_color="#88D8B0",
        default_properties={
            "type": "metric",
            "label": "RAM",
            "metric_type": "ram_used",
            "unit": " GB",
            "position": (160, 120),
            "size": (150, 30),
            "font_size": 16,
        }
    ),
})

# System Widgets
WIDGET_METADATA.update({
    "date": WidgetMetadata(
        widget_type="date",
        display_name="Date",
        description="Current date",
        category=WidgetCategory.SYSTEM,
        icon_color="#AA96DA",
        default_properties={
            "type": "date",
            "date_format": "%d/%m",
            "position": (160, 120),
            "size": (100, 30),
            "font_size": 16,
        }
    ),
    "time": WidgetMetadata(
        widget_type="time",
        display_name="Time",
        description="Current time",
        category=WidgetCategory.SYSTEM,
        icon_color="#C5B5E6",
        default_properties={
            "type": "time",
            "time_format": "%H:%M",
            "position": (160, 120),
            "size": (100, 30),
            "font_size": 16,
        }
    ),
})

# Text Widget
WIDGET_METADATA.update({
    "text": WidgetMetadata(
        widget_type="text",
        display_name="Text",
        description="Custom text",
        category=WidgetCategory.TEXT,
        icon_color="#FFEAA7",
        default_properties={
            "type": "text",
            "text": "Sample Text",
            "position": (160, 120),
            "size": (100, 30),
            "font_size": 16,
        }
    ),
})

# Graph Widgets
WIDGET_METADATA.update({
    "bar_graph": WidgetMetadata(
        widget_type="bar_graph",
        display_name="Bar Graph",
        description="Bar chart for metrics",
        category=WidgetCategory.GRAPHS,
        icon_color="#FF6B9D",
        default_properties={
            "type": "graph",
            "graph_type": "bar",
            "metric_type": "cpu_usage",
            "label": "CPU Usage",
            "position": (160, 120),
            "size": (120, 60),
            "font_size": 12,
            "bar_color": "#FF6B6B",
            "background_color": "#333333",
        }
    ),
    "circular_graph": WidgetMetadata(
        widget_type="circular_graph",
        display_name="Circular Graph",
        description="Pie/donut chart for metrics",
        category=WidgetCategory.GRAPHS,
        icon_color="#4ECDC4",
        default_properties={
            "type": "graph",
            "graph_type": "circular",
            "metric_type": "cpu_usage",
            "label": "CPU Usage",
            "position": (160, 120),
            "size": (80, 80),
            "font_size": 12,
            "fill_color": "#4ECDC4",
            "background_color": "#333333",
            "show_percentage": True,
        }
    ),
})


def get_widgets_by_category() -> Dict[WidgetCategory, List[WidgetMetadata]]:
    """Get all widgets organized by category."""
    widgets_by_category = {category: [] for category in WidgetCategory}
    
    for widget_meta in WIDGET_METADATA.values():
        widgets_by_category[widget_meta.category].append(widget_meta)
    
    return widgets_by_category


def get_widget_metadata(widget_type: str) -> WidgetMetadata:
    """Get metadata for a specific widget type."""
    if widget_type not in WIDGET_METADATA:
        raise ValueError(f"Unknown widget type: {widget_type}")
    return WIDGET_METADATA[widget_type]


def get_all_widget_types() -> List[str]:
    """Get list of all available widget types."""
    return list(WIDGET_METADATA.keys())


# Category display order
CATEGORY_ORDER = [
    WidgetCategory.CPU,
    WidgetCategory.GPU,
    WidgetCategory.RAM,
    WidgetCategory.SYSTEM,
    WidgetCategory.TEXT,
    WidgetCategory.GRAPHS,
]