# Widget Positioning Offset Issue - December 2025

## Issue Summary
**Problem**: Widgets appear correctly positioned in the GUI preview but are shifted when displayed on the physical USB LCD device.

**Current Status**: Widgets are offset by approximately -52px horizontally (left) and -6px vertically (up) from their expected positions.

**Impact**: WYSIWYG (What You See Is What You Get) positioning is broken, making accurate widget placement impossible.

## Detailed Analysis

### Test Results
1. **Widget placed at GUI center** (scene coordinates: 240,180)
   - **Expected device position**: (160,120)
   - **Actual device position**: (108,114)
   - **Offset**: (-52px, -6px)

2. **Widget placed at GUI top-left** (scene coordinates: 0,0)
   - **Expected device position**: (0,0)
   - **Actual device position**: (0,0) ✓
   - **Offset**: (0,0) ✓

### Coordinate System Analysis
- **Device coordinates**: (0,0) to (320,240) - Physical LCD display
- **Scene coordinates**: (0,0) to (480,360) - GUI preview (1.5× scaled)
- **Scale factor**: 1.5 (480/320 = 360/240 = 1.5)

### Mathematical Analysis
For widget at scene position (240,180):
- Expected: `device = scene / scale = (240/1.5, 180/1.5) = (160,120)`
- Actual: (108,114)
- Calculated offset in scene coordinates: (78,9)

**Transformation formula**:
```
device_x = (scene_x - 78) / 1.5
device_y = (scene_y - 9) / 1.5
```

## Root Cause Investigation

### Possible Causes (Ranked by Likelihood)

#### 1. **Viewport/Scene Alignment Issue** (Most Likely)
- QGraphicsView may have margins, borders, or viewport insets
- Scene might not be aligned to viewport origin (0,0)
- View might be centering content instead of top-left alignment

#### 2. **Widget Origin Point Mismatch**
- Widgets might use center or different origin point
- Bounding box vs position calculation differences

#### 3. **Coordinate System Transformation**
- Missing transformation in UnifiedGraphicsView setup
- `fitInView()` or similar causing unintended offsets

#### 4. **Adapter Scaling Logic Error**
- `UnifiedToDisplayAdapter._position_to_device()` might have incorrect math
- Missing viewport offset compensation

## Current Workaround (NOT IMPLEMENTED - FOR REFERENCE ONLY)

**⚠️ DO NOT IMPLEMENT THIS QUICK FIX - IT'S A HACK ⚠️**

If we were to implement a quick fix (which we shouldn't), it would be:

```python
# In UnifiedToDisplayAdapter._date_to_config() and similar methods:
device_x = int((pos.x() - 78) / scale)  # BAD HACK
device_y = int((pos.y() - 9) / scale)   # BAD HACK
```

**Why this is bad**:
1. Magic numbers (78, 9) with no clear origin
2. Masks the real problem
3. Will break if viewport configuration changes
4. Not a proper solution

## Required Investigation Steps

### 1. Debug Viewport Configuration
```python
# Add to unified_controller.py setup_preview_area():
print(f"View viewport rect: {self.unified_view.view.viewport().rect()}")
print(f"View scene rect: {self.unified_view.view.sceneRect()}")
print(f"View transformation: {self.unified_view.view.transform()}")
print(f"View alignment: {self.unified_view.view.alignment()}")
```

### 2. Check Widget Scene Position
```python
# Add to widget creation:
print(f"Widget scene pos: {widget.scenePos()}")
print(f"Widget bounding rect: {widget.boundingRect()}")
print(f"Widget mapToScene(0,0): {widget.mapToScene(0, 0)}")
```

### 3. Verify Coordinate Systems
- Confirm scene rect is exactly (0,0,480,360)
- Confirm viewport is exactly (0,0,480,360) with no margins
- Check for any `centerOn()`, `fitInView()`, or `setAlignment()` calls

### 4. Test Specific Positions
Create test cases:
- Top-left (0,0) - ✓ Working
- Center (240,180) - ✗ Broken
- Top-right (479,0)
- Bottom-left (0,359)
- Bottom-right (479,359)

## Files to Investigate

### Primary Suspects:
1. `src/thermalright_lcd_control/gui/unified_controller.py`
   - `setup_preview_area()` method
   - View and scene configuration

2. `src/thermalright_lcd_control/gui/widgets/unified/__init__.py`
   - `UnifiedGraphicsView` class
   - Viewport and scene setup

3. `src/thermalright_lcd_control/gui/widgets/unified/adapter.py`
   - `_position_to_device()` logic
   - Coordinate conversion

### Secondary Checks:
4. `src/thermalright_lcd_control/gui/main_window.py`
   - Preview area widget setup
   - Layout constraints

## Testing Procedure

### Step 1: Add Debug Logging
Add comprehensive logging to track coordinate transformations at each stage.

### Step 2: Manual Testing
1. Place widget at known positions in GUI
2. Save configuration
3. Check saved YAML for device positions
4. Compare with expected values

### Step 3: Automated Test Positions
Create a test script that:
1. Places widgets at grid positions
2. Generates config
3. Compares expected vs actual positions
4. Calculates offset pattern

## Success Criteria

**Fixed when**:
- Widget at GUI center (240,180) → device (160,120) ±1px
- Widget at GUI corners map correctly to device corners
- Linear relationship: `device = scene / 1.5` for all positions
- No magic number offsets in code

## Priority

**High Priority** - This blocks:
- Accurate widget placement
- WYSIWYG functionality
- User trust in the GUI
- Future widget additions

## Related Documentation
- `WIDGET_POSITIONING_FIXES.md` - Previous fixes for visibility issues
- `UNIFIED_WIDGET_MIGRATION_PLAN.md` - Overall migration strategy

## Next Actions

1. **Immediate**: Add debug logging to identify exact offset source
2. **Short-term**: Fix viewport/scene alignment
3. **Long-term**: Add unit tests for coordinate transformations

**Assigned To**: Development Team
**Target Resolution Date**: Before Phase 3 (Metric Widgets) implementation
**Status**: INVESTIGATING