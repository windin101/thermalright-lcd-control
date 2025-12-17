# Changelog

All notable changes to Thermalright LCD Control will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-12-17

### Added
- **Theme Management System**: Save and load reusable themes through the Themes tab
- **Video Background Support**: Full support for video backgrounds with thumbnail previews
- **Preview-Only Mode**: Changes to preview don't automatically update the device
- **Theme Naming Dialog**: User-friendly dialog for saving themes with custom names
- **Path Portability System**: Cross-environment compatibility for different installations

### Changed
- **Save/Apply Button Behavior**:
  - **Save Button**: Now saves themes to themes directory (visible in Themes tab)
  - **Apply Button**: Sends configuration to USB device
  - **Preview Changes**: No longer automatically update the device
- **Video Background Preview**: Videos now show thumbnails instead of black/empty preview
- **User Experience**: Clear separation between theme creation and device updates
- **Import System**: Converted relative imports to absolute imports for better portability

### Fixed
- **Video Background Preview**: GUI preview now correctly shows video thumbnails
- **Background Type Detection**: Proper handling of image, video, and GIF backgrounds
- **Automatic Device Updates**: Preview changes no longer spam the USB device
- **Missing QImage Import**: Fixed import error in unified controller
- **Theme Loading**: Fixed theme selection not working in Themes tab
- **Path Resolution**: Themes now load correctly across different installation environments
- **Cross-Environment Compatibility**: Application works on machines with different user home folders

### Technical Details

#### Video Background Preview Fix
- **Problem**: Video backgrounds played on device but showed black in GUI preview
- **Solution**: Added OpenCV-based thumbnail extraction for video previews
- **Files Modified**:
  - `src/thermalright_lcd_control/gui/unified_controller.py`
  - Added `_set_video_background()` and `_set_video_placeholder()` methods
  - Enhanced background type detection
- **Dependencies**: OpenCV (optional, with graceful fallback)

#### Save/Apply Button Update
- **Problem**: Both buttons did the same thing, preview changes auto-updated device
- **Solution**: Distinct functionality with preview isolation
- **Files Modified**:
  - `src/thermalright_lcd_control/gui/components/config_generator_unified.py`
  - `src/thermalright_lcd_control/gui/unified_controller.py`
  - `src/thermalright_lcd_control/gui/main_window.py`
  - `src/thermalright_lcd_control/gui/components/controls_manager.py`
- **New Methods**: `generate_theme_yaml()`, `save_theme()`, `update_preview_only()`

#### Path Portability Implementation
- **Problem**: Hardcoded paths in themes failed on different installations/user environments
- **Solution**: Dynamic path resolution system with automatic installation detection
- **Files Modified**:
  - `src/thermalright_lcd_control/gui/utils/path_resolver.py` (NEW)
  - `src/thermalright_lcd_control/device_controller/display/config_loader.py`
  - `src/thermalright_lcd_control/gui/main_window.py`
  - `src/thermalright_lcd_control/gui/components/config_generator_unified.py`
- **New Features**: Cross-environment theme compatibility, automatic path resolution

#### Theme Loading Fix
- **Problem**: Clicking themes in Themes tab didn't load them
- **Solution**: Added missing signal connection and implemented `on_theme_selected()` method
- **Files Modified**:
  - `src/thermalright_lcd_control/gui/main_window.py`
  - Added theme selection signal connection and handler method

#### Import System Update
- **Problem**: Relative imports failed in installed environments
- **Solution**: Converted all relative imports to absolute imports
- **Files Modified**: Multiple files across the codebase
- **Impact**: Improved portability and deployment reliability

### Documentation
- Added `VIDEO_BACKGROUND_PREVIEW_FIX.md`
- Added `SAVE_APPLY_BUTTONS_UPDATE.md`
- Added `PATH_PORTABILITY_IMPLEMENTATION.md`
- Added `THEME_LOADING_IMPLEMENTATION.md`
- Added `IMPORT_SYSTEM_MODERNIZATION.md`
- Updated `README.md` with video background feature
- Updated cross-references between documentation files

## [1.2.0] - Previous Version

### Features
- Initial video background support (device-only, no GUI preview)
- Basic theme system with preset configurations
- USB device communication and configuration
- GUI with media selection and preview

### Known Issues (Now Fixed)
- Video backgrounds not visible in GUI preview
- Save/Apply buttons had overlapping functionality
- Automatic device updates on every preview change

---

## Development Notes

### File Structure
```
doc/
├── PATH_PORTABILITY_IMPLEMENTATION.md   # Cross-environment compatibility
├── THEME_LOADING_IMPLEMENTATION.md      # Theme selection and loading
├── IMPORT_SYSTEM_MODERNIZATION.md       # Absolute import conversion
├── VIDEO_BACKGROUND_PREVIEW_FIX.md     # Video thumbnail implementation
├── SAVE_APPLY_BUTTONS_UPDATE.md        # Button behavior changes
├── CONFIG_SAVING_BUG_FIX.md           # Configuration saving fixes
├── PREVIEW_BACKGROUND_COLOR_FIX.md    # Color picker fixes
├── TEXT_COLOR_PICKER_FIX.md           # Text styling fixes
├── UNIFIED_WIDGET_MIGRATION_PLAN.md   # Architecture migration
├── USB_DISPLAY_BLACK_SCREEN_FIX.md    # Device communication fixes
├── WIDGET_POSITIONING_FIXES.md        # Layout fixes
├── COORDINATE_CONVERSION_BUG_ANALYSIS.md # Coordinate system fixes
└── HOWTO.md                           # User guide and setup instructions
```

### Testing
- All changes tested with multiple video formats (MP4, AVI, MOV)
- Theme saving/loading verified across different resolutions (320x240, 320x320, 480x480)
- Path portability tested across development, user, and system installations
- Cross-environment compatibility verified with different user home directories
- Backward compatibility maintained with existing configurations
- GUI functionality verified without breaking existing features

### Dependencies
- **OpenCV**: Optional for video thumbnail generation (falls back gracefully)
- **PySide6**: Enhanced GUI components for theme dialogs
- **PyYAML**: Configuration file handling (unchanged)

---

## Future Plans
- [ ] GIF background thumbnail support
- [ ] Theme sharing/export functionality
- [ ] Advanced video playback controls in preview
- [ ] Theme categories and organization
- [ ] Undo/redo functionality for configuration changes</content>
<parameter name="filePath">/home/leeo/Documents/code/thermalright-lcd-control/doc/CHANGELOG.md