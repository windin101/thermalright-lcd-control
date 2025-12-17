# Save/Apply Button Behavior Update

## Problem Description

The original Save and Apply buttons had overlapping functionality and caused automatic updates to the USB device whenever the preview area changed. This created confusion about when changes would be sent to the device and made it difficult to experiment with configurations without immediately affecting the display.

## Root Cause Analysis

### Original Behavior
- **Save Button**: Saved configuration and sent to USB device
- **Apply Button**: Also saved configuration and sent to USB device  
- **Preview Changes**: Every change (media selection, color changes, etc.) automatically triggered `generate_preview()` which saved config and sent to device

### Issues
1. **No Theme Saving**: No way to save reusable themes visible in Themes tab
2. **Automatic Device Updates**: Any preview change immediately affected the physical display
3. **Confusing UX**: Users couldn't experiment with settings without device updates

## Solution Implementation

### New Button Behavior
- **Save Button**: Saves current configuration as a theme file in the themes directory, visible in Themes tab
- **Apply Button**: Saves configuration to service config and sends updates to USB device
- **Preview Changes**: Updates only the GUI preview, no automatic device updates

### Changes Made

#### 1. Enhanced Config Generator (`config_generator_unified.py`)
**Added `generate_theme_yaml()` method:**
```python
def generate_theme_yaml(self, preview_manager, text_style, theme_name: str) -> Optional[str]:
    """Generate theme YAML file in themes directory"""
    # Saves to: {themes_dir}/{width}{height}/{theme_name}.yaml
```

**Added `_get_theme_config_path()` method:**
```python
def _get_theme_config_path(self, width: int, height: int, theme_name: str) -> Path:
    """Get theme config file path"""
    themes_dir = self.config.get('paths', {}).get('themes_dir', './themes')
    return Path(f"{themes_dir}/{width}{height}/{theme_name}.yaml")
```

#### 2. Enhanced Unified Controller (`unified_controller.py`)
**Added `generate_theme()` method:**
```python
def generate_theme(self, preview_manager, text_style, theme_name: str) -> Optional[str]:
    """Generate theme YAML - returns file path or None"""
    # Calls config_generator.generate_theme_yaml()
```

#### 3. Updated Main Window (`main_window.py`)
**Added `save_theme()` method:**
```python
def save_theme(self):
    """Save current configuration as a theme"""
    # Shows dialog for theme name input
    # Calls unified.generate_theme()
    # Refreshes themes tab to show new theme
```

**Added `update_preview_only()` method:**
```python
def update_preview_only(self):
    """Update preview display without sending to device"""
    # Updates GUI preview only, no device communication
```

**Modified preview change handlers:**
- `_on_media_selected()`: Now calls `update_preview_only()` instead of `generate_preview()`
- `on_font_size_changed()`: Now calls `update_preview_only()` instead of `generate_preview()`
- `choose_color()`: Now calls `update_preview_only()` instead of `generate_preview()`

#### 4. Updated Controls Manager (`controls_manager.py`)
**Changed Save button connection:**
```python
save_config_btn.clicked.connect(self.parent.save_theme)  # Was: generate_config_yaml
```

## Technical Details

### Theme Saving Process
1. User clicks "Save" button
2. Dialog prompts for theme name
3. Theme name is sanitized (spaces → underscores, special chars removed)
4. Configuration saved to: `{themes_dir}/{width}{height}/{theme_name}.yaml`
5. Themes tab automatically refreshes to show new theme

### Apply Process
1. User clicks "Apply" button
2. Configuration saved to service config: `{service_config}/config_{width}{height}.yaml`
3. Service detects config change and sends to USB device

### Preview-Only Updates
- Changes to media, colors, fonts update GUI immediately
- No config files written
- No communication with USB device
- Purely visual feedback for user experimentation

## Verification

### Testing Performed
1. **Theme Saving**: Verified themes save to correct directory with proper YAML structure
2. **Theme Loading**: Confirmed saved themes appear in Themes tab
3. **Apply Functionality**: Verified Apply button still sends updates to device
4. **Preview Isolation**: Confirmed preview changes don't affect device until Apply clicked
5. **Backward Compatibility**: Existing functionality preserved

### Expected Behavior
- **Save Button**: Creates theme file, shows success message, refreshes Themes tab
- **Apply Button**: Sends configuration to device, shows success message
- **Preview Changes**: Immediate GUI updates, no device communication
- **Theme Selection**: Loads theme configuration into preview (still requires Apply to send to device)

## Impact Assessment

### Positive Impacts
- ✅ **Theme Management**: Users can now save and reuse configurations
- ✅ **Experimentation**: Preview changes don't affect device until explicitly applied
- ✅ **Clear UX**: Distinct separation between saving themes vs applying to device
- ✅ **Performance**: Reduced unnecessary device communication

### No Breaking Changes
- Existing configurations still work
- Service config path unchanged
- Device communication still works via Apply button

## Files Modified
- `src/thermalright_lcd_control/gui/components/config_generator_unified.py`
- `src/thermalright_lcd_control/gui/unified_controller.py`
- `src/thermalright_lcd_control/gui/main_window.py`
- `src/thermalright_lcd_control/gui/components/controls_manager.py`

## Dependencies
- **Existing**: PySide6 QInputDialog for theme naming
- **Existing**: YAML config generation system
- **Existing**: Themes directory structure

## Status
✅ **COMPLETED** - Save/Apply buttons now have distinct, clear functionality</content>
<parameter name="filePath">/home/leeo/Documents/code/thermalright-lcd-control/doc/SAVE_APPLY_BUTTONS_UPDATE.md