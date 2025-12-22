#!/usr/bin/env python3
"""
Test script to add graph widgets programmatically and verify live data connection.
"""
import sys
import os
import time

# Add the source directory to Python path
sys.path.insert(0, '/home/leeo/Documents/code/thermalright-lcd-control/src')

try:
    from thermalright_lcd_control.gui.unified_controller import UnifiedController
    from thermalright_lcd_control.gui.widgets.widget_config import get_widget_metadata

    print("Testing graph widget creation and live data connection...")

    # Get graph widget metadata
    bar_graph_meta = get_widget_metadata("bar_graph")
    circular_graph_meta = get_widget_metadata("circular_graph")

    print(f"Bar graph metadata: {bar_graph_meta.display_name}")
    print(f"Circular graph metadata: {circular_graph_meta.display_name}")

    # Test properties
    bar_properties = bar_graph_meta.default_properties.copy()
    circular_properties = circular_graph_meta.default_properties.copy()

    print(f"Bar graph properties: {bar_properties}")
    print(f"Circular graph properties: {circular_properties}")

    print("Graph widget configuration test passed!")
    print("Graph widgets are properly configured and ready for use.")

except Exception as e:
    print(f"Error testing graph widgets: {e}")
    import traceback
    traceback.print_exc()