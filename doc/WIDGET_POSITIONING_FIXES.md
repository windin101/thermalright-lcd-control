# Widget Positioning and Display Fixes - December 2025

## Overview

This document details the comprehensive fixes implemented to resolve critical issues with widget positioning and display in the ThermalRight LCD Control GUI. The fixes ensure accurate WYSIWYG (What You See Is What You Get) positioning between the GUI preview and the physical USB LCD display.

## Issues Identified and Fixed

### Issue #1: Preview Size Scaling Problem
**Problem**: The preview area appeared larger than the intended 480x360 pixels due to QGraphicsView's fitInView() scaling behavior.

**Root Cause**: `fitInView()` scales the scene to fit the available view area, causing the preview to appear larger than the physical device dimensions.

**Impact**: Users couldn't accurately position widgets because the preview didn't match the physical display size.

**Fix Applied**:
- Removed `fitInView()` call
- Set QGraphicsView to fixed size (480x360) matching scene dimensions
- Set size policy to `Fixed` to prevent layout resizing
- Ensured 1:1 pixel mapping between scene and view

### Issue #2: Widget Visibility (Black Screen)
**Problem**: Widgets were created successfully but not visible in the preview area.

**Root Cause**: Multiple layout and parenting issues prevented the QGraphicsView from displaying the scene:
- Preview area widget lacked minimum size constraints
- QGraphicsView not properly parented in widget hierarchy
- Layout resizing interfering with view dimensions

**Impact**: Complete loss of widget visibility despite successful creation.

**Fix Applied**:
- Set minimum size (480x360) on preview area container widget
- Properly parent UnifiedGraphicsView to preview widget
- Set view size to match scene dimensions
- Configure size policy to prevent unwanted resizing

### Issue #3: Text Alignment Issues
**Problem**: Text appeared left-aligned instead of center-aligned within widgets.

**Root Cause**: Incorrect text positioning calculation in the paint method using `painter.boundingRect()` with alignment flags.

**Impact**: Text positioning inconsistent between GUI preview and display output.

**Fix Applied**:
- Modified text drawing to calculate proper centered position
- Removed reliance on boundingRect alignment flags
- Calculate center position based on text metrics

### Issue #4: Coordinate System Mismatch
**Problem**: Widgets positioned correctly in GUI preview but appeared offset on physical display.

**Root Cause**: GUI widgets use top-left positioning with centered text, while display rendering expects text baseline positioning. Additionally, display text was left-aligned from the specified position.

**Impact**: Systematic offset between preview and display positioning, text appeared left-aligned on display.

**Fix Applied**:
- Modified coordinate conversion to account for text centering
- Calculate display position as widget center rather than top-left
- Updated display rendering to use `anchor='mm'` for center-center text alignment
- Ensure consistent text positioning between GUI and display

### Issue #5: ShapeConfig Missing Rotation Field
**Problem**: Runtime error when generating configurations: `ShapeConfig.__init__() got an unexpected keyword argument 'rotation'`

**Root Cause**: ShapeConfig dataclass was missing the `rotation` field that the adapter was trying to pass.

**Impact**: Configuration generation failed, preventing proper device programming.

**Fix Applied**:
- Added `rotation: int = 0` field to ShapeConfig dataclass
- Ensured compatibility with existing configuration system

## Technical Implementation Details

### Coordinate System Architecture

The system operates with two coordinate systems:

1. **Device Coordinates**: (0,0) to (320,240) - Physical LCD display coordinates
2. **Scene Coordinates**: (0,0) to (480,360) - GUI preview coordinates (1.5x scaled)

**Conversion Logic**:
- Scene → Device: `device_coord = scene_coord / scale_factor`
- Device → Scene: `scene_coord = device_coord * scale_factor`

### View Setup Changes

**Before (Broken)**:
```python
# fitInView caused unwanted scaling
self.unified_view.view.fitInView(
    self.unified_view.scene.sceneRect(),
    Qt.AspectRatioMode.KeepAspectRatio
)
```

**After (Fixed)**:
```python
# Set fixed size matching scene dimensions
view_width = int(self.device_width * self.preview_scale)  # 480
view_height = int(self.device_height * self.preview_scale)  # 360
self.unified_view.view.resize(view_width, view_height)

# Prevent layout resizing
from PySide6.QtWidgets import QSizePolicy
self.unified_view.view.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

# Ensure proper parenting
self.unified_view = UnifiedGraphicsView(preview_area_widget)
```

### Widget Boundary Constraints

**Movement Constraints**: Added boundary checking in `UnifiedBaseItem.mouseMoveEvent()` to prevent widgets from being dragged outside the scene rectangle, ensuring they stay within the physical device area.

**Position Validation**: Implemented position validation in `itemChange()` to enforce scene boundaries.

### Configuration System Updates

**ShapeConfig Enhancement**:
```python
@dataclass
class ShapeConfig:
    # ... existing fields ...
    rotation: int = 0  # Added missing field
```

## Files Modified

### Core GUI Components
- `src/thermalright_lcd_control/gui/unified_controller.py`
  - Fixed view sizing and parenting
  - Removed problematic fitInView scaling
  - Added proper size constraints
  - Enhanced debug logging (later removed)

- `src/thermalright_lcd_control/gui/main_window.py`
  - Set minimum size on preview area widget
  - Ensured proper widget hierarchy

- `src/thermalright_lcd_control/gui/widgets/unified/base.py`
  - Added movement boundary constraints
  - Enhanced position validation

### Widget Rendering
- `src/thermalright_lcd_control/gui/widgets/unified/text_widgets.py`
  - Fixed text alignment calculation
  - Improved centering logic for text positioning

### Display Rendering
- `src/thermalright_lcd_control/device_controller/display/text_renderer.py`
  - Added `anchor='mm'` parameter to all `draw.text()` calls
  - Changed text alignment from left-aligned to center-aligned on display

## Testing and Validation

### Test Results
- ✅ Preview area displays at correct size (480x360)
- ✅ Widgets are visible and properly positioned
- ✅ Text alignment corrected (center-aligned in both preview and display)
- ✅ Coordinate conversion accounts for text centering
- ✅ Configuration generation succeeds without errors
- ✅ WYSIWYG positioning improved between GUI and display
- ✅ Boundary constraints prevent invalid positioning

### Validation Procedure
1. Launch GUI application
2. Verify preview area dimensions (480x360)
3. Confirm time widget is visible with centered text
4. Drag widget to preview corners
5. Generate configuration
6. Verify widget positions account for centering on display
7. Confirm text appears center-aligned in both preview and display

### Coordinate System Validation
- **GUI Preview**: Widget top-left at scene coordinates, text centered within widget bounds
- **Display Output**: Text positioned at widget center coordinates with center-center alignment
- **Conversion**: Scene coordinates → centered scene coordinates → scaled device coordinates
- **Alignment**: Both GUI and display use center alignment for consistent positioning

## Performance Impact

**Minimal Performance Impact**:
- View sizing changes are one-time setup operations
- Boundary checking adds negligible computational overhead
- No impact on rendering performance
- Configuration generation maintains existing performance

## Backward Compatibility

**Fully Backward Compatible**:
- All existing configurations remain valid
- No breaking changes to API
- Enhanced ShapeConfig with default rotation value
- Existing widget positioning preserved

## Lessons Learned

1. **QGraphicsView Scaling**: `fitInView()` can cause unexpected scaling when view and scene sizes differ
2. **Widget Parenting**: Proper parent-child relationships are critical for Qt widget visibility
3. **Layout Constraints**: Size policies and minimum sizes prevent unwanted layout behavior
4. **Configuration Schema**: Dataclass fields must match adapter expectations
5. **Boundary Validation**: UI constraints should mirror physical device limitations

## Future Considerations

- Consider adding visual feedback for boundary limits
- Implement snap-to-grid functionality for precise positioning
- Add zoom controls for detailed widget editing
- Implement undo/redo for widget operations

## Status

- **Analysis**: Complete ✅
- **Implementation**: Complete ✅ (5 major issues fixed)
- **Testing**: Complete ✅
- **Documentation**: Complete ✅

**Date Fixed**: 17 December 2025
**Resolution**: All identified issues resolved with comprehensive fixes
**Key Achievement**: Accurate WYSIWYG positioning between GUI preview and physical LCD display with proper text alignment</content>
<parameter name="filePath">/home/leeo/Documents/code/thermalright-lcd-control/doc/WIDGET_POSITIONING_FIXES.md