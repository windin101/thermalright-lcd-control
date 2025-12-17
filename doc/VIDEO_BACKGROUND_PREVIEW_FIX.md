# Video Background Preview Fix

## Problem Description

When selecting a video background in the Media tab, the video would correctly play on the USB device but the GUI preview area would not update to show the video. The preview would remain showing the previous background or default to black, creating a disconnect between what users saw in the preview and what actually played on the device.

## Root Cause Analysis

### Technical Context
- **Media Selection Flow**: Media tab → `thumbnail_clicked` → `_on_media_selected` → `preview_manager` updates → `unified.set_background()` → `generate_preview()`
- **Background Types**: System supports `image`, `video`, and `gif` backgrounds
- **Preview Rendering**: GUI uses QGraphicsScene with static backgrounds (no video playback)
- **Device Rendering**: Service handles actual video playback from file paths

### Root Cause
The `UnifiedController.set_background()` method only handled image backgrounds:

```python
if image_path and os.path.exists(image_path):
    pixmap = QPixmap(image_path)  # Only works for images
    if not pixmap.isNull():
        # Set as background
```

**Issues:**
1. **No Video Type Detection**: Method didn't check `preview_manager.background_type`
2. **Image-Only Logic**: Tried to load videos as QPixmap, which fails silently
3. **No Video Preview**: No mechanism to show video thumbnails or placeholders in preview
4. **Type Mismatch**: Video files fell through to color background logic

### Code Flow Analysis
```
Video Selected → preview_manager.background_type = "video"
                                      ↓
set_background() → QPixmap(video_path) → fails → color background
                                      ↓
Preview: Black/Color | Device: Video Plays ✅
```

## Solution Implementation

### Changes Made

#### 1. Enhanced `UnifiedController.set_background()` Method
**File:** `src/thermalright_lcd_control/gui/unified_controller.py`

Added background type detection and specialized handling:

```python
def set_background(self, preview_manager, image_path: Optional[str] = None):
    if image_path and os.path.exists(image_path):
        # Determine background type
        background_type = getattr(preview_manager, 'background_type', 'image')
        
        if background_type == 'image':
            # Handle image backgrounds (existing logic)
        elif background_type == 'video':
            # Handle video backgrounds - show thumbnail
            self._set_video_background(image_path)
        elif background_type == 'gif':
            # Handle GIF backgrounds
        else:
            # Fallback logic
```

#### 2. Added Video Background Preview Methods

**Video Thumbnail Extraction:**
```python
def _set_video_background(self, video_path):
    """Extract and display video thumbnail"""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        
        if cap.isOpened():
            # Seek to 10% of video duration
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if frame_count > 10:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 10)
            
            ret, frame = cap.read()
            if ret:
                # Convert to QPixmap and scale
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # ... convert to QImage → QPixmap → scale
                scene.setBackgroundBrush(QBrush(scaled_pixmap))
                
        cap.release()
    except Exception as e:
        self._set_video_placeholder()
```

**Fallback Placeholder:**
```python
def _set_video_placeholder(self):
    """Dark placeholder when thumbnail extraction fails"""
    placeholder_color = QColor(32, 32, 32)  # Dark gray
    scene.setBackgroundBrush(QBrush(placeholder_color))
```

#### 3. Refactored Color Background Logic
Extracted color background handling into separate method `_set_color_background()` for better organization.

### Technical Details

#### Video Thumbnail Generation
- **Library**: Uses OpenCV (`cv2`) for frame extraction
- **Position**: Seeks to 10% of video duration for representative frame
- **Format**: Converts BGR → RGB → QImage → QPixmap → scaled
- **Fallback**: Dark placeholder if OpenCV unavailable or extraction fails

#### Background Type Detection
- **Source**: `preview_manager.background_type` set by main window
- **Types**: `image`, `video`, `gif` based on file extensions
- **Default**: Falls back to image handling for unknown types

#### Preview vs Device Rendering
- **Preview**: Static thumbnail/placeholder in QGraphicsScene
- **Device**: Full video playback by service from file path
- **Synchronization**: Both use same `preview_manager.current_background_path`

## Verification

### Testing Performed
1. **Video Selection**: Verified video files trigger correct background_type setting
2. **Thumbnail Extraction**: Tested OpenCV frame extraction and QPixmap conversion
3. **Fallback Handling**: Ensured graceful degradation when OpenCV unavailable
4. **Preview Updates**: Confirmed preview area updates immediately on video selection
5. **Device Playback**: Verified device still plays videos correctly

### Expected Behavior
- **Video Selection**: Preview shows video thumbnail or dark placeholder
- **Image Selection**: Preview shows scaled image (unchanged)
- **GIF Selection**: Preview shows GIF first frame
- **Device Output**: All background types play correctly on USB device
- **Synchronization**: Preview and device show consistent backgrounds

## Impact Assessment

### Positive Impacts
- ✅ **WYSIWYG Compliance**: Preview now matches device output for videos
- ✅ **User Experience**: Immediate visual feedback for video selections
- ✅ **Robust Fallbacks**: Graceful handling when video processing fails
- ✅ **Performance**: Efficient thumbnail extraction without full video loading

### No Breaking Changes
- Existing image background functionality preserved
- Device video playback unchanged
- Backward compatible with existing configurations

## Related Issues
- Background color picker fixes (PREVIEW_BACKGROUND_COLOR_FIX.md)
- Text color picker fixes (TEXT_COLOR_PICKER_FIX.md)
- Configuration saving fixes (CONFIG_SAVING_BUG_FIX.md)
- Save/Apply Button Behavior Changes (SAVE_APPLY_BUTTONS_UPDATE.md)

## Files Modified
- `src/thermalright_lcd_control/gui/unified_controller.py`

## Dependencies
- **OpenCV**: Optional for video thumbnail extraction (falls back gracefully)
- **PySide6**: QPixmap, QImage for image processing
- **Existing**: QGraphicsScene background brush system

## Status
✅ **RESOLVED** - Video backgrounds now show thumbnails/placeholders in GUI preview

## Completion Summary

### Implementation Completed
- ✅ Background type detection added to `UnifiedController.set_background()`
- ✅ Video thumbnail extraction using OpenCV implemented
- ✅ Fallback placeholder handling for video processing failures
- ✅ Missing QImage import fixed
- ✅ Color background logic refactored for better organization

### Testing Results
- ✅ Video selection triggers correct background_type detection
- ✅ OpenCV frame extraction works for multiple video files (a001.mp4, a002.mp4, etc.)
- ✅ QPixmap conversion and scaling functions correctly
- ✅ Preview area updates immediately on video selection
- ✅ Device video playback remains unaffected
- ✅ Graceful fallback when OpenCV unavailable
- ✅ All background types (image, video, GIF) work in preview

### Files Modified
- `src/thermalright_lcd_control/gui/unified_controller.py`
  - Added background type detection logic
  - Implemented `_set_video_background()` method
  - Added `_set_video_placeholder()` fallback method
  - Refactored `_set_color_background()` method
  - Fixed missing QImage import

### Key Technical Details
- **Thumbnail Position**: Seeks to 10% of video duration for representative frame
- **Format Conversion**: BGR → RGB → QImage → QPixmap → scaled to preview size
- **Error Handling**: Falls back to dark placeholder if video processing fails
- **Performance**: Efficient extraction without loading entire video
- **Compatibility**: Maintains backward compatibility with existing image handling</content>
<parameter name="filePath">/home/leeo/Documents/code/thermalright-lcd-control/doc/VIDEO_BACKGROUND_PREVIEW_FIX.md