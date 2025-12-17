#!/usr/bin/env python3
"""
Test script for MetricDataManager
"""
import sys
import time
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from thermalright_lcd_control.gui.metrics.metric_data_manager import get_metric_manager, MetricType

def test_metric_manager():
    """Test metric data manager functionality"""
    print("=== Testing MetricDataManager ===")
    
    # Get metric manager
    manager = get_metric_manager()
    
    # Start metric collection
    print("Starting metric manager...")
    manager.start()
    
    # Wait for initial collection
    print("Waiting for initial metric collection...")
    time.sleep(2)
    
    # Test getting metrics
    print("\n=== Current Metrics ===")
    
    # Try CPU metrics
    cpu_usage = manager.get_metric(MetricType.CPU_USAGE)
    if cpu_usage:
        print(f"CPU Usage: {cpu_usage.value:.1f}{cpu_usage.unit}")
    else:
        print("CPU Usage: Not available")
    
    cpu_temp = manager.get_metric(MetricType.CPU_TEMPERATURE)
    if cpu_temp:
        print(f"CPU Temp: {cpu_temp.value:.1f}{cpu_temp.unit}")
    else:
        print("CPU Temp: Not available")
    
    # Try RAM metrics
    ram_usage = manager.get_metric(MetricType.RAM_USAGE)
    if ram_usage:
        print(f"RAM Usage: {ram_usage.value:.1f}{ram_usage.unit}")
    else:
        print("RAM Usage: Not available")
    
    # Try GPU metrics
    gpu_usage = manager.get_metric(MetricType.GPU_USAGE)
    if gpu_usage:
        print(f"GPU Usage: {gpu_usage.value:.1f}{gpu_usage.unit}")
    else:
        print("GPU Usage: Not available")
    
    # Get all metrics
    print("\n=== All Metrics ===")
    all_metrics = manager.get_all_metrics()
    for metric_type, data in all_metrics.items():
        print(f"{metric_type}: {data['value']:.1f}{data['unit']} ({data['label']})")
    
    # Test subscription
    print("\n=== Testing Subscription ===")
    
    def test_callback():
        cpu = manager.get_metric(MetricType.CPU_USAGE)
        if cpu:
            print(f"Callback: CPU Usage updated to {cpu.value:.1f}{cpu.unit}")
    
    manager.subscribe("test_widget", test_callback)
    print("Subscribed test widget to updates")
    
    # Wait for a few updates
    print("Waiting for updates (5 seconds)...")
    time.sleep(5)
    
    # Unsubscribe
    manager.unsubscribe("test_widget")
    print("Unsubscribed test widget")
    
    # Stop manager
    print("\nStopping metric manager...")
    manager.stop()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    try:
        test_metric_manager()
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()