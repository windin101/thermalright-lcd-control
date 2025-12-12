#!/bin/bash
# Quick memory leak fixes for Thermalright LCD Control

echo "Applying memory leak fixes..."

# 1. Fix PreviewManager
PREVIEW_FILE="src/thermalright_lcd_control/gui/components/preview_manager.py"
if [ -f "$PREVIEW_FILE" ]; then
    echo "Fixing PreviewManager..."
    
    # Add _cleanup_called attribute
    sed -i '/self._debug_task_pending = False/a\        self._cleanup_called = False' "$PREVIEW_FILE"
    
    # Add ThreadPoolExecutor shutdown to cleanup
    sed -i '/if self.display_generator:/a\        \n        # Shutdown ThreadPoolExecutor\n        if hasattr(self, "_debug_executor"):\n            self._debug_executor.shutdown(wait=False)\n        \n        self._cleanup_called = True' "$PREVIEW_FILE"
    
    # Add __del__ method
    if ! grep -q "def __del__" "$PREVIEW_FILE"; then
        echo -e "\n    def __del__(self):\n        \"\"\"Destructor to ensure cleanup\"\"\"\n        if not getattr(self, '_cleanup_called', False):\n            self.cleanup()" >> "$PREVIEW_FILE"
    fi
    
    echo "✓ PreviewManager fixed"
else
    echo "⚠️ PreviewManager file not found"
fi

echo ""
echo "Done! Now run: sudo ./build.sh"
echo "Then test with: python3 memory_monitor.py"