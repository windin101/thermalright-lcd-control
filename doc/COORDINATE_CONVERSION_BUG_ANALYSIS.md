# Coordinate Conversion Issues Analysis

**Date**: 17 December 2025
**Status**: Critical Bug Identified
**Impact**: High - Widget positioning completely broken

## Problem Description

Users reported that widgets in the unified preview system appear offset towards the bottom-left on the actual USB display, and widgets moved to preview corners render outside the physical screen area.

## Root Cause Analysis

### Issue #1: Incorrect Scale Factor in Coordinate Conversion
**Location**: `src/thermalright_lcd_control/gui/unified_controller.py` `_update_preview_manager()` method

**Problem**: The coordinate conversion from preview (scene) coordinates to device coordinates uses a hardcoded scale factor of `1.0` instead of the actual preview scale.

**Code**:
```python
# WRONG - hardcoded 1.0 scale
configs = UnifiedToDisplayAdapter.get_all_configs_from_view(
    self.unified_view, 1.0
)
```

**Impact**:
- Preview scale is set to 1.5x (480x360 preview for 320x240 device)
- When user drags widget to preview center (240, 180), conversion uses scale=1.0
- Result: device coordinates = (240, 180) instead of correct (160, 120)
- Widget appears 1.5x offset towards bottom-right

### Issue #2: Incorrect Initial Widget Positioning
**Location**: `src/thermalright_lcd_control/gui/unified_controller.py` `create_initial_widgets()` method

**Problem**: Initial widgets are created using device coordinates, but the widget system expects scene coordinates.

**Code**:
```python
# Device coordinates passed to scene coordinate system
center_x = self.device_width // 2      # 160 for 320x240
center_y = self.device_height // 2     # 120 for 320x240
self.unified_view.create_date_widget(x=center_x, y=center_y, ...)
```

**Impact**: Initial widgets appear at wrong positions in the scaled preview.

## Coordinate System Architecture

The system operates with two coordinate systems:

1. **Device Coordinates**: (0,0) to (320,240)
   - Coordinates sent to USB display
   - Origin at top-left of physical screen

2. **Scene Coordinates**: (0,0) to (480,360) [scaled by 1.5x]
   - Coordinates used in preview QGraphicsView
   - Origin at top-left of preview area

**Conversion Logic**:
- Scene → Device: `device_coord = scene_coord / preview_scale`
- Device → Scene: `scene_coord = device_coord * preview_scale`

### Issue #3: QGraphicsView Not Fitting Scene (ROOT CAUSE)
**Location**: `src/thermalright_lcd_control/gui/unified_controller.py` `setup_preview_area()` method

**Problem**: The QGraphicsView was displaying the scene at 1:1 scale without fitting it to the view size. Since the scene is 480x360 (scaled) but the view widget is smaller, users were only seeing a cropped portion of the scene.

**Impact**:
- User sees partial scene, thinks they're positioning widgets in center
- Mouse coordinates were correct for the visible portion, but wrong relative to full scene
- Coordinate conversion worked correctly, but input coordinates were wrong

**Root Cause**: QGraphicsView default behavior shows scene at 1:1 without scaling to fit the view.
**File**: `src/thermalright_lcd_control/gui/unified_controller.py`
**Method**: `_update_preview_manager()`

**Change**:
```python
# BEFORE
configs = UnifiedToDisplayAdapter.get_all_configs_from_view(
    self.unified_view, 1.0
)

# AFTER
configs = UnifiedToDisplayAdapter.get_all_configs_from_view(
    self.unified_view, self.preview_scale
)
```

### Fix #3: Fit Scene to View
**File**: `src/thermalright_lcd_control/gui/unified_controller.py`
**Method**: `setup_preview_area()`

**Change**:
```python
# Fit the entire scene in the view
self.unified_view.view.fitInView(
    self.unified_view.scene.sceneRect(), 
    Qt.AspectRatioMode.KeepAspectRatio
)
```

**Impact**: View now shows entire scaled scene, mouse coordinates match visual positioning.

## Expected Results

After fixes:
- Widgets dragged to preview center appear at device center
- Widgets dragged to preview corners appear at device corners
- No offset towards bottom-left
- Widgets stay within physical screen boundaries
- Initial widgets positioned correctly

## Testing Procedure

1. Build and run application
2. Drag widget to exact center of preview area
3. Generate configuration
4. Verify widget appears at center of USB display
5. Drag widget to each corner of preview area
6. Verify widget appears at corresponding corner of USB display
7. Verify widget does not go outside screen boundaries

## Implementation Summary

**Date Fixed**: 17 December 2025

### Changes Made

1. **Fixed coordinate conversion scale** in `unified_controller.py`:
   - Changed hardcoded `1.0` to `self.preview_scale` in `_update_preview_manager()`
   - Now correctly converts scene coordinates to device coordinates

2. **Fixed initial widget positioning** in `unified_controller.py`:
   - Changed device coordinates to scene coordinates in `create_initial_widgets()`
   - Center position now: `(device_width/2 * scale, device_height/2 * scale)`

3. **Fixed view scaling** in `unified_controller.py`:
   - Added `fitInView()` call to make QGraphicsView show entire scaled scene
   - Mouse coordinates now match visual widget positions

### Files Modified

- `src/thermalright_lcd_control/gui/unified_controller.py` (3 fixes)
- `doc/COORDINATE_CONVERSION_BUG_ANALYSIS.md` (this documentation)

## Status

- Analysis: Complete ✅
- Fixes: Implemented ✅ (All 3 issues fixed)
- Testing: Ready for user verification