"""
Unified Widget System

A clean, modern widget system to replace the old QLabel-based widgets.
All widgets inherit from UnifiedBaseItem and are managed by UnifiedGraphicsView.
"""

from .base import UnifiedBaseItem, UnifiedGraphicsView
from .text_widgets import DateWidget, TimeWidget, FreeTextWidget
from .shape_widgets import RectangleWidget, RoundedRectangleWidget, CircleWidget
from .metric_widgets import MetricWidget, TemperatureWidget, UsageWidget, FrequencyWidget, NameWidget, RAMWidget, GPUMemoryWidget
from .graph_widgets import GraphWidget, BarGraphWidget, CircularGraphWidget
from .property_editor import PropertyEditor
from .property_editor_dialog import PropertyEditorDialog
from .layout_manager import LayoutManager

__all__ = [
    'UnifiedBaseItem',
    'UnifiedGraphicsView',
    'DateWidget',
    'TimeWidget',
    'FreeTextWidget',
    'RectangleWidget',
    'RoundedRectangleWidget',
    'CircleWidget',
    'MetricWidget',
    'TemperatureWidget',
    'UsageWidget',
    'FrequencyWidget',
    'NameWidget',
    'RAMWidget',
    'GPUMemoryWidget',
    'GraphWidget',
    'BarGraphWidget',
    'CircularGraphWidget',
    'PropertyEditor',
    'PropertyEditorDialog',
    'LayoutManager',
]

# Version information
__version__ = '1.4.3'
__author__ = 'Thermalright LCD Control Team'
__description__ = 'Unified widget system for thermalright-lcd-control'
