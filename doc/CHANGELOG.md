# Changelog

All notable changes to Thermalright LCD Control will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2025-12-18

### Added
- **Enhanced Metric Data Collection**: Added CPU name, GPU name, GPU frequency, GPU memory, and RAM used metrics
- **Dynamic GUI Layout**: Equal column layout with preview at top, controls in middle, and screen settings at bottom
- **Improved Widget System**: Fixed widget creation errors and enhanced metric data display
- **Comprehensive System Monitoring**: Real-time display of all major system metrics (CPU, GPU, RAM)

### Changed
- **GUI Layout Reorganization**: 
  - Equal column distribution (1:1 stretch ratio)
  - Preview area positioned at top of left column
  - Action controls (buttons) in middle section
  - Screen controls at bottom of left column
  - Added minimum window size (1000x700) for dynamic resizing
- **Metric Data Manager**: Enhanced to handle both numeric and string metrics properly
- **Widget Creation**: Fixed variable reference errors in unified controller

### Fixed
- **Widget Creation Errors**: Resolved NameError and TypeError in widget instantiation
- **Missing Metric Display**: Widgets now properly display CPU name, GPU metrics, and RAM usage
- **Layout Responsiveness**: GUI now resizes properly with equal column distribution
- **Metric Data Types**: Proper handling of string metrics (CPU/GPU names) vs numeric metrics

### Technical Details

#### GUI Layout Overhaul
- **Problem**: Unequal columns and poor control organization
- **Solution**: Equal column layout with logical control stacking
- **Files Modified**:
  - `src/thermalright_lcd_control/gui/main_window.py`
  - Reorganized QVBoxLayout stacking in left column
  - Added minimum window size constraints
  - Implemented 1:1 stretch factors for equal columns

#### Metric Data Integration
- **Problem**: Widgets not displaying real system data
- **Solution**: Comprehensive metric collection and proper data type handling
- **Files Modified**:
  - `src/thermalright_lcd_control/gui/metrics/metric_data_manager.py`
  - `src/thermalright_lcd_control/gui/unified_controller.py`
  - Added CPU_NAME, GPU_NAME, GPU_FREQUENCY, GPU_MEMORY, RAM_USED metrics
  - Fixed widget creation with corrected **properties usage

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