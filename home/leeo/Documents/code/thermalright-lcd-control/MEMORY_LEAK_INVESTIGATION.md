# Memory Leak Investigation and Fix Guide

## Problem Description
The Thermalright LCD Control GUI is experiencing severe memory leaks, consuming up to 10GB of RAM after being opened/closed multiple times or left running for extended periods.

## Immediate Steps to Diagnose

### 1. Run the Memory Monitor
```bash
# Make the script executable
chmod +x memory_monitor.py

# Run it (it will auto-detect the GUI process)
python3 memory_monitor.py --interval 2 --log gui_memory.log

# Or monitor a specific PID
python3 memory_monitor.py --pid $(pgrep -f thermalright-lcd-control-gui)
```

### 2. Run the Memory Leak Tests
```bash
# Test individual components
python3 test_memory_leak.py
```

### 3. Apply the Memory Leak Fixes
```bash
# Apply the patches
git apply memory_leak_fixes.patch
git apply usability_improvements.patch

# Or apply manually by examining the patches and implementing changes
```

## Key Issues Identified

### 1. **ThreadPoolExecutor Not Shutdown**
- Location: `gui/components/preview_manager.py`
- Issue: `ThreadPoolExecutor` created but never shut down
- Fix: Add `shutdown()` call in `cleanup()` method

### 2. **Video Frame Accumulation**
- Location: `device_controller/display/frame_manager.py`
- Issue: All video frames loaded into memory at once
- Fix: Implement lazy loading or streaming

### 3. **Missing Cleanup in Destructors**
- Issue: `__del__` methods may not be called reliably
- Fix: Add explicit `cleanup()` calls and track cleanup state

### 4. **Qt Signal/Slot Leaks**
- Issue: Qt connections not disconnected
- Fix: Store connections and disconnect in cleanup

### 5. **Image Conversion Overhead**
- Issue: Repeated PIL↔Qt image conversions
- Fix: Implement image caching

## Recommended Fix Priority

### Phase 1: Critical Fixes (Immediate)
1. **Add proper cleanup to PreviewManager**
   - Shutdown ThreadPoolExecutor
   - Stop all QTimer instances
   - Clear image caches

2. **Fix FrameManager memory usage**
   - Release video capture resources
   - Clear frame arrays in cleanup
   - Implement `__del__` safety

3. **Add cleanup tracking**
   - Add `_cleanup_called` flag to prevent double cleanup
   - Ensure cleanup in destructors

### Phase 2: Performance Improvements
1. **Image caching**
   - Cache converted QPixmap objects
   - Limit cache size
   - Clear cache on configuration changes

2. **Widget pooling**
   - Reuse widget instances
   - Implement proper lifecycle management

3. **Memory monitoring**
   - Add periodic memory checks
   - Warn users about high memory usage
   - Implement automatic cleanup

### Phase 3: Advanced Optimizations
1. **Lazy video loading**
   - Stream video frames instead of loading all
   - Implement frame-by-frame decoding

2. **Qt connection management**
   - Track all signal/slot connections
   - Automatic disconnection

3. **Memory profiling**
   - Add detailed memory usage logging
   - Identify specific leak patterns

## Testing Procedure

### 1. Baseline Test
```bash
# Start with clean system
# Launch GUI
# Monitor memory for 5 minutes
# Note baseline memory usage
```

### 2. Stress Test
```bash
# Repeatedly:
# 1. Add/remove widgets
# 2. Change backgrounds
# 3. Switch themes
# 4. Open/close GUI
# Monitor memory growth
```

### 3. Long-running Test
```bash
# Leave GUI running for 1+ hours
# Monitor memory usage pattern
# Check for steady increase
```

## Debugging Tools

### 1. Python Memory Profiler
```bash
pip install memory-profiler

# Add to code:
from memory_profiler import profile

@profile
def suspicious_function():
    # code here
```

### 2. objgraph for Reference Cycles
```bash
pip install objgraph

# In code:
import objgraph
objgraph.show_most_common_types(limit=20)
objgraph.show_growth()
```

### 3. Qt Debugging
```bash
# Enable Qt debug output
export QT_DEBUG_PLUGINS=1
export QT_LOGGING_RULES="*.debug=true"
```

## Common Qt Memory Leak Patterns

### 1. **Parent-Child Relationships**
```python
# BAD: Widget without parent
widget = QWidget()

# GOOD: Widget with parent
widget = QWidget(parent_widget)
```

### 2. **Signal Connections**
```python
# BAD: Lambda captures causing cycles
button.clicked.connect(lambda: self.do_something())

# GOOD: Use weak references or method references
from PySide6.QtCore import Slot

@Slot()
def on_button_clicked(self):
    self.do_something()

button.clicked.connect(self.on_button_clicked)
```

### 3. **QTimer Management**
```python
# BAD: Timer not stopped
timer = QTimer()
timer.start(1000)

# GOOD: Stop timer in cleanup
def cleanup(self):
    if self.timer.isActive():
        self.timer.stop()
```

## Emergency Memory Recovery

If the GUI is using excessive memory:

1. **Manual cleanup trigger** (add to GUI):
```python
def force_memory_cleanup(self):
    import gc
    gc.collect()
    
    # Clear caches
    if hasattr(self, 'preview_manager'):
        self.preview_manager.cleanup()
    
    # Recreate components if needed
    self.reinitialize_components()
```

2. **Automatic cleanup** (add to main window):
```python
def check_memory_and_cleanup(self):
    import psutil
    process = psutil.Process()
    rss_mb = process.memory_info().rss / 1024 / 1024
    
    if rss_mb > 2000:  # 2GB threshold
        self.force_memory_cleanup()
        print(f"Auto-cleaned at {rss_mb:.1f}MB")
```

## Monitoring in Production

Add to `main_gui.py`:
```python
def main(config_file=None):
    # ... existing code ...
    
    # Add memory monitoring
    memory_timer = QTimer()
    memory_timer.timeout.connect(lambda: monitor_memory_usage(window))
    memory_timer.start(30000)  # Every 30 seconds
    
    # ... rest of main function ...
```

## Next Steps

1. Apply the provided patches
2. Run the memory monitor to establish baseline
3. Test with the memory leak test script
4. Monitor memory usage over time
5. Iterate on fixes based on results

## Contact for Support

If issues persist after applying fixes:
- Check the memory logs for patterns
- Run the test scripts to identify specific components
- Consider using more advanced profiling tools
- Review Qt object lifecycle in the codebase
