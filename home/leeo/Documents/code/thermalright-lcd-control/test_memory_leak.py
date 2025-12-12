#!/usr/bin/env python3
"""
Memory leak test script for Thermalright LCD Control
This script helps identify which components are causing memory leaks
"""

import sys
import os
import gc
import psutil
import time
from typing import Dict, List

# Add the project to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class MemoryLeakTester:
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = None
        self.test_results = []
        
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage in MB"""
        mem_info = self.process.memory_info()
        gc.collect()  # Force garbage collection before measuring
        
        return {
            'rss_mb': mem_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': mem_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': self.process.memory_percent(),
        }
    
    def print_memory_usage(self, label: str = "Current"):
        """Print current memory usage"""
        mem = self.get_memory_usage()
        print(f"{label}: RSS={mem['rss_mb']:.1f}MB, VMS={mem['vms_mb']:.1f}MB, %={mem['percent']:.1f}")
    
    def test_component(self, component_name: str, setup_func, teardown_func=None, iterations: int = 10):
        """Test a specific component for memory leaks"""
        print(f"\n{'='*60}")
        print(f"Testing: {component_name}")
        print(f"Iterations: {iterations}")
        
        # Get baseline memory
        self.print_memory_usage("Baseline")
        baseline = self.get_memory_usage()
        
        # Track memory after each iteration
        memory_readings = []
        
        for i in range(iterations):
            # Create component
            component = setup_func()
            
            # Force garbage collection
            gc.collect()
            
            # Measure memory
            mem = self.get_memory_usage()
            memory_readings.append(mem['rss_mb'])
            
            # Clean up
            if teardown_func:
                teardown_func(component)
            
            # Delete reference
            del component
            
            # Small delay
            time.sleep(0.1)
            
            if (i + 1) % 5 == 0:
                print(f"  Completed {i + 1}/{iterations} iterations")
        
        # Final garbage collection
        gc.collect()
        
        # Get final memory
        final = self.get_memory_usage()
        self.print_memory_usage("Final")
        
        # Calculate leak
        leak_mb = final['rss_mb'] - baseline['rss_mb']
        leak_per_iteration = leak_mb / iterations if iterations > 0 else 0
        
        # Store results
        result = {
            'component': component_name,
            'baseline_mb': baseline['rss_mb'],
            'final_mb': final['rss_mb'],
            'leak_mb': leak_mb,
            'leak_per_iteration': leak_per_iteration,
            'memory_readings': memory_readings,
        }
        
        self.test_results.append(result)
        
        # Print summary
        print(f"\nSummary for {component_name}:")
        print(f"  Baseline: {baseline['rss_mb']:.1f}MB")
        print(f"  Final:    {final['rss_mb']:.1f}MB")
        print(f"  Leak:     {leak_mb:.2f}MB ({leak_per_iteration:.3f}MB per iteration)")
        
        if leak_mb > 10:  # > 10MB leak is significant
            print(f"  ⚠️  SIGNIFICANT LEAK DETECTED!")
        elif leak_mb > 1:  # > 1MB leak is concerning
            print(f"  ⚠️  Potential leak detected")
        else:
            print(f"  ✓ No significant leak detected")
        
        return result
    
    def test_display_generator(self):
        """Test DisplayGenerator for memory leaks"""
        from thermalright_lcd_control.device_controller.display.config import DisplayConfig
        from thermalright_lcd_control.device_controller.display.generator import DisplayGenerator
        
        def setup():
            # Create a minimal config
            config = DisplayConfig(
                background_path="",
                background_type="IMAGE",
                output_width=320,
                output_height=240,
                rotation=0,
                background_scale_mode="stretch",
                background_enabled=True,
                background_color=(0, 0, 0),
                background_alpha=1.0,
                global_font_path=None,
                foreground_image_path=None,
                foreground_position=(0, 0),
                foreground_alpha=1.0,
            )
            return DisplayGenerator(config)
        
        def teardown(generator):
            if hasattr(generator, 'cleanup'):
                generator.cleanup()
        
        return self.test_component("DisplayGenerator", setup, teardown, iterations=20)
    
    def test_frame_manager(self):
        """Test FrameManager for memory leaks"""
        from thermalright_lcd_control.device_controller.display.config import DisplayConfig, BackgroundType
        from thermalright_lcd_control.device_controller.display.frame_manager import FrameManager
        
        def setup():
            # Create a minimal config
            config = DisplayConfig(
                background_path="",
                background_type=BackgroundType.IMAGE,
                output_width=320,
                output_height=240,
                rotation=0,
                background_scale_mode="stretch",
                background_enabled=True,
                background_color=(0, 0, 0),
                background_alpha=1.0,
                global_font_path=None,
                foreground_image_path=None,
                foreground_position=(0, 0),
                foreground_alpha=1.0,
            )
            return FrameManager(config)
        
        def teardown(manager):
            if hasattr(manager, 'cleanup'):
                manager.cleanup()
        
        return self.test_component("FrameManager", setup, teardown, iterations=20)
    
    def test_preview_manager(self):
        """Test PreviewManager for memory leaks"""
        from thermalright_lcd_control.gui.components.preview_manager import PreviewManager
        from PySide6.QtWidgets import QLabel, QApplication
        
        # Create Qt application if needed
        app = None
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
        
        def setup():
            # Mock config
            config = {
                'supported_formats': {
                    'images': ['.png', '.jpg', '.jpeg'],
                    'videos': ['.mp4', '.webm'],
                    'gifs': ['.gif'],
                }
            }
            
            # Create preview label
            preview_label = QLabel()
            
            # Mock text style
            class MockTextStyle:
                font_family = "Arial"
                shadow_enabled = False
                shadow_color = None
                shadow_offset_x = 0
                shadow_offset_y = 0
                shadow_blur = 0
                outline_enabled = False
                outline_color = None
                outline_width = 0
                gradient_enabled = False
                gradient_color1 = None
                gradient_color2 = None
                gradient_direction = "vertical"
            
            text_style = MockTextStyle()
            
            return PreviewManager(config, preview_label, text_style)
        
        def teardown(manager):
            if hasattr(manager, 'cleanup'):
                manager.cleanup()
        
        result = self.test_component("PreviewManager", setup, teardown, iterations=10)
        
        # Clean up Qt app
        if app:
            del app
            
        return result
    
    def run_all_tests(self):
        """Run all memory leak tests"""
        print("Memory Leak Test Suite for Thermalright LCD Control")
        print("="*60)
        
        # Test individual components
        self.test_display_generator()
        self.test_frame_manager()
        # self.test_preview_manager()  # Commented out as it requires Qt
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print("="*60)
        
        for result in self.test_results:
            status = "⚠️ LEAK" if result['leak_mb'] > 1 else "✓ OK"
            print(f"{status} {result['component']:20} Leak: {result['leak_mb']:6.2f}MB ({result['leak_per_iteration']:.3f}MB/iter)")
        
        # Save results to file
        with open("memory_leak_test_results.txt", "w") as f:
            f.write("Memory Leak Test Results\n")
            f.write("="*60 + "\n\n")
            for result in self.test_results:
                f.write(f"Component: {result['component']}\n")
                f.write(f"  Baseline: {result['baseline_mb']:.1f}MB\n")
                f.write(f"  Final:    {result['final_mb']:.1f}MB\n")
                f.write(f"  Leak:     {result['leak_mb']:.2f}MB\n")
                f.write(f"  Per iteration: {result['leak_per_iteration']:.3f}MB\n\n")
        
        print(f"\nResults saved to: memory_leak_test_results.txt")

if __name__ == "__main__":
    tester = MemoryLeakTester()
    
    try:
        tester.run_all_tests()
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()