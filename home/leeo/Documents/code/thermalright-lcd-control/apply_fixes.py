#!/usr/bin/env python3
"""
Apply memory leak fixes to Thermalright LCD Control
Run this script, then run ./build.sh
"""

import os
import sys

def fix_preview_manager():
    """Fix PreviewManager memory leaks"""
    path = "src/thermalright_lcd_control/gui/components/preview_manager.py"
    
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return False
    
    print(f"🔧 Fixing {path}")
    
    with open(path, 'r') as f:
        content = f.read()
    
    # Add _cleanup_called attribute
    if 'self._debug_task_pending = False' in content and '_cleanup_called' not in content:
        content = content.replace(
            'self._debug_task_pending = False',
            'self._debug_task_pending = False\n        self._cleanup_called = False'
        )
        print("  ✓ Added _cleanup_called attribute")
    
    # Add ThreadPoolExecutor shutdown to cleanup
    cleanup_start = content.find('def cleanup(self):')
    if cleanup_start != -1:
        # Find the end of the cleanup method
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == 'def cleanup(self):':
                # Find where this method ends
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() and not lines[j].startswith(' ' * 8):
                        # Found the next method/end of class
                        # Insert before this line
                        indent = ' ' * 8
                        lines.insert(j, f'{indent}# Shutdown ThreadPoolExecutor')
                        lines.insert(j + 1, f'{indent}if hasattr(self, \'_debug_executor\'):')
                        lines.insert(j + 2, f'{indent}    self._debug_executor.shutdown(wait=False)')
                        lines.insert(j + 3, '')
                        lines.insert(j + 4, f'{indent}self._cleanup_called = True')
                        print("  ✓ Added ThreadPoolExecutor shutdown")
                        break
                break
    
    # Add __del__ method
    if 'def __del__' not in content:
        # Find the end of the class
        class_end = content.rfind('class PreviewManager')
        if class_end != -1:
            # Find the last method
            last_method = max(
                content.rfind('def cleanup'),
                content.rfind('def clear_all'),
                content.rfind('def _drag_throttled_update')
            )
            
            if last_method != -1:
                # Find the end of that method
                lines = content[last_method:].split('\n')
                method_end = 0
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() and not line.startswith(' ' * 4):
                        method_end = last_method + len('\n'.join(lines[:i]))
                        break
                
                if method_end:
                    # Insert __del__ method
                    indent = ' ' * 4
                    new_method = f'\n{indent}def __del__(self):\n{indent}    """Destructor to ensure cleanup"""\n{indent}    if not getattr(self, \'_cleanup_called\', False):\n{indent}        self.cleanup()'
                    content = content[:method_end] + new_method + content[method_end:]
                    print("  ✓ Added __del__ method")
    
    with open(path, 'w') as f:
        f.write(content)
    
    return True

def fix_frame_manager():
    """Fix FrameManager memory leaks"""
    path = "src/thermalright_lcd_control/device_controller/display/frame_manager.py"
    
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return False
    
    print(f"🔧 Fixing {path}")
    
    with open(path, 'r') as f:
        content = f.read()
    
    # Add _cleanup_called attribute to __init__
    init_start = content.find('def __init__(self, config: DisplayConfig):')
    if init_start != -1:
        # Find the end of __init__ (where we call _load_background)
        load_bg_pos = content.find('self._load_background()', init_start)
        if load_bg_pos != -1:
            # Insert before _load_background
            indent = ' ' * 8
            new_line = f'{indent}self._cleanup_called = False\n{indent}'
            content = content[:load_bg_pos] + new_line + content[load_bg_pos:]
            print("  ✓ Added _cleanup_called attribute")
    
    # Fix cleanup method to clear frames
    cleanup_start = content.find('def cleanup(self):')
    if cleanup_start != -1:
        # Find the existing cleanup content
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == 'def cleanup(self):':
                # Find where this method ends
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == 'self.logger.debug("FrameManager cleaned up")':
                        # Insert frame clearing before this line
                        indent = ' ' * 8
                        new_lines = [
                            f'{indent}# Clear background frames to free memory',
                            f'{indent}if hasattr(self, \'background_frames\'):',
                            f'{indent}    for frame in self.background_frames:',
                            f'{indent}        if hasattr(frame, \'close\'):',
                            f'{indent}            frame.close()',
                            f'{indent}    self.background_frames.clear()',
                            f'{indent}',
                            f'{indent}if hasattr(self, \'gif_durations\'):',
                            f'{indent}    self.gif_durations.clear()',
                            f'{indent}',
                            f'{indent}self._cleanup_called = True',
                            ''
                        ]
                        
                        # Insert the new lines
                        for k, new_line in enumerate(new_lines):
                            lines.insert(j + k, new_line)
                        
                        print("  ✓ Enhanced cleanup method")
                        break
                break
    
    # Fix __del__ method
    del_start = content.find('def __del__(self):')
    if del_start != -1:
        # Replace the simple __del__ with a safer version
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == 'def __del__(self):':
                # Replace the next few lines
                if i + 1 < len(lines) and lines[i + 1].strip() == 'self.cleanup()':
                    lines[i + 1] = '        if not getattr(self, \'_cleanup_called\', False):'
                    lines.insert(i + 2, '            try:')
                    lines.insert(i + 3, '                self.cleanup()')
                    lines.insert(i + 4, '            except Exception:')
                    lines.insert(i + 5, '                pass  # Avoid exceptions in destructor')
                    print("  ✓ Fixed __del__ method")
                break
    
    with open(path, 'w') as f:
        f.write(content)
    
    return True

def fix_display_generator():
    """Fix DisplayGenerator cleanup tracking"""
    path = "src/thermalright_lcd_control/device_controller/display/generator.py"
    
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return False
    
    print(f"🔧 Fixing {path}")
    
    with open(path, 'r') as f:
        content = f.read()
    
    # Add _cleanup_called attribute
    if 'self.text_renderer = TextRenderer(config)' in content and '_cleanup_called' not in content:
        # Insert after text_renderer initialization
        content = content.replace(
            'self.text_renderer = TextRenderer(config)',
            'self.text_renderer = TextRenderer(config)\n        self._cleanup_called = False'
        )
        print("  ✓ Added _cleanup_called attribute")
    
    # Update cleanup method
    if 'def cleanup(self):' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == 'def cleanup(self):':
                # Find the logger.debug line
                for j in range(i + 1, len(lines)):
                    if 'self.logger.debug("DisplayGenerator cleaned up")' in lines[j]:
                        # Insert _cleanup_called = True after this line
                        lines.insert(j + 1, '        self._cleanup_called = True')
                        print("  ✓ Updated cleanup method")
                        break
                break
    
    # Fix __del__ method
    del_start = content.find('def __del__(self):')
    if del_start != -1:
        # Check if it already has the safe pattern
        if 'getattr(self, \'_cleanup_called\'' not in content[del_start:del_start+200]:
            # Replace with safe version
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == 'def __del__(self):':
                    if i + 1 < len(lines) and lines[i + 1].strip() == 'self.cleanup()':
                        lines[i + 1] = '        if not getattr(self, \'_cleanup_called\', False):'
                        lines.insert(i + 2, '            try:')
                        lines.insert(i + 3, '                self.cleanup()')
                        lines.insert(i + 4, '            except Exception:')
                        lines.insert(i + 5, '                pass  # Avoid exceptions in destructor')
                        print("  ✓ Fixed __del__ method")
                    break
    
    with open(path, 'w') as f:
        f.write(content)
    
    return True

def main():
    print("🛠️  Applying memory leak fixes to Thermalright LCD Control")
    print("=" * 60)
    
    success = True
    
    # Apply fixes
    if not fix_preview_manager():
        success = False
    
    if not fix_frame_manager():
        success = False
    
    if not fix_display_generator():
        success = False
    
    print("=" * 60)
    
    if success:
        print("✅ All fixes applied successfully!")
        print("\nNext steps:")
        print("1. Review the changes made")
        print("2. Run ./build.sh to rebuild and reinstall")
        print("3. Test the GUI for memory usage")
        print("4. Use python3 memory_monitor.py to track memory")
    else:
        print("⚠️  Some fixes may not have been applied")
        print("Please check the errors above and apply fixes manually")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())