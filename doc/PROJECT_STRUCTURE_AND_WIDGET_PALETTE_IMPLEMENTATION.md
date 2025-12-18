# Project Structure & Widget Palette Implementation

## Overview
This document details the complete file and folder structure of the Thermalright LCD Control project, with specific focus on the newly implemented Widget Palette system.

## Project Root Structure
```
/home/leeo/Documents/code/thermalright-lcd-control/
├── src/                          # Source code (Python src/ layout)
├── doc/                          # Documentation (this folder)
├── resources/                    # Application resources (images, themes, configs)
├── build/                        # Build artifacts and distribution packages
├── .continue/                    # IDE/Editor configuration rules
├── .git/                         # Version control
├── .venv/                        # Python virtual environment
├── debian/                       # Debian package build files
├── pyproject.toml               # Python project configuration
├── README.md                    # Project overview
├── LICENSE                      # Apache 2.0 License
└── Various build/install scripts
```

## Source Code Structure (`src/thermalright_lcd_control/`)
The project uses Python's `src/` layout where source code is separated from distribution.

### Core Package Structure
```
src/thermalright_lcd_control/
├── common/                       # Common utilities
│   ├── __init__.py
│   └── logging_config.py        # Logging configuration
│
├── device_controller/           # Hardware interaction
│   ├── display/                 # Display device control
│   │   ├── config.py           # Display configuration
│   │   ├── config_unified.py   # Unified configuration system
│   │   ├── text_renderer.py    # Text rendering for USB display
│   │   ├── font_manager.py     # Font management
│   │   └── ... (other display modules)
│   │
│   └── metrics/                 # System metrics collection
│       ├── cpu_metrics.py      # CPU monitoring
│       ├── gpu_metrics.py      # GPU monitoring
│       └── ...
│
├── gui/                         # Graphical User Interface
│   ├── main_window.py          # Main application window
│   │
│   ├── tabs/                   # Application tabs
│   │   ├── widgets_tab.py      # Widget management tab (UPDATED)
│   │   ├── media_tab.py        # Media/background management
│   │   ├── themes_tab.py       # Theme management
│   │   └── __init__.py
│   │
│   ├── widgets/                # Widget system
│   │   ├── __init__.py
│   │   ├── draggable_widget.py # Legacy draggable widgets
│   │   ├── thumbnail_widget.py # Thumbnail display widgets
│   │   │
│   │   ├── widget_config.py    # NEW: Widget metadata & definitions
│   │   ├── widget_card.py      # NEW: Individual widget cards
│   │   ├── widget_palette.py   # NEW: Main widget palette UI
│   │   │
│   │   └── unified/           # Unified widget system
│   │       ├── __init__.py
│   │       ├── base.py        # UnifiedBaseItem, UnifiedGraphicsView
│   │       ├── metric_widgets.py # Metric display widgets
│   │       ├── text_widgets.py  # Text, Date, Time widgets
│   │       ├── adapter.py      # Adapter for USB display
│   │       └── ...
│   │
│   ├── unified_controller.py   # Coordinates unified widget system
│   ├── unified_integration.py  # Integration layer
│   └── components/             # GUI components
│       ├── config_generator.py
│       ├── preview_manager.py
│       └── ...
│
├── main_gui.py                 # Application entry point
└── service.py                  # Background service
```

## Widget Palette Implementation

### New Files Added
1. **`widget_config.py`** - Widget metadata and definitions
   - Defines `WidgetMetadata` dataclass
   - Categorizes widgets (CPU, GPU, RAM, System, Text)
   - Sets default properties for each widget type
   - Defines color schemes and icons

2. **`widget_card.py`** - Individual widget cards
   - `WidgetCard` class extending `QPushButton`
   - Visual representation with icon, name, description
   - Click handling with visual feedback
   - Emits `widgetClicked` signal

3. **`widget_palette.py`** - Main palette UI
   - `WidgetPalette` class extending `QWidget`
   - Categorized sections (CPU, GPU, RAM, System, Text)
   - Grid layout with widget cards
   - Search/filter functionality
   - Emits `widgetSelected` signal

### Updated Files
1. **`widgets_tab.py`** - Complete redesign
   - Replaced dropdown-based widget addition
   - New split layout: Palette (left) vs Widget List (right)
   - Added `_on_widget_palette_selected()` method
   - Added `_delete_selected_widget()` method
   - Preserves existing widget property editing

### Import Structure
```
widgets_tab.py (in gui/tabs/)
    ↓ imports
widget_palette.py (in gui/widgets/)
    ↓ imports
widget_card.py (in gui/widgets/)
    ↓ imports  
widget_config.py (in gui/widgets/)
```

**Key Import Paths:**
- `widgets_tab.py`: `from ..widgets.widget_palette import WidgetPalette`
- `widget_palette.py`: `from .widget_config import ...` and `from .widget_card import WidgetCard`
- All imports use relative paths within the package

## Widget Categories & Types

### CPU Metrics
- `cpu_usage` - CPU utilization percentage
- `cpu_temperature` - CPU temperature
- `cpu_frequency` - CPU frequency
- `cpu_name` - CPU model name

### GPU Metrics  
- `gpu_usage` - GPU utilization percentage
- `gpu_temperature` - GPU temperature
- `gpu_frequency` - GPU frequency
- `gpu_name` - GPU model name
- `gpu_memory` - GPU memory usage

### RAM Metrics
- `ram_percent` - RAM utilization percentage
- `ram_used` - RAM used/total

### System
- `date` - Current date
- `time` - Current time

### Text
- `text` - Custom text widget

## Color Scheme
- **CPU**: Reds/Oranges (#FF6B6B, #FF8E53, #FFA726, #FFCC80)
- **GPU**: Blues (#4ECDC4, #45B7D1, #A3D9FF, #96DED1, #88D8B0)
- **RAM**: Greens (#96CEB4, #88D8B0)
- **System**: Purples (#AA96DA, #C5B5E6)
- **Text**: Yellows (#FFEAA7)

## Interaction Flow
1. User clicks widget card in palette
2. `WidgetCard` emits `widgetClicked` signal
3. `WidgetPalette` forwards as `widgetSelected` signal
4. `WidgetsTab._on_widget_palette_selected()` handles:
   - Generates unique widget ID
   - Creates widget with default properties
   - Adds to widget list
   - Emits `widget_added` signal for preview area
5. Widget appears in preview at default position (center)
6. User can drag widget to desired location

## Build & Distribution Structure

### Build Artifacts (`build/`)
```
build/thermalright-lcd-control-1.3.0/
├── thermalright_lcd_control/    # Package for distribution
├── resources/                   # Copied resources
└── usr/                         # System installation files
```

### Resources (`resources/`)
```
resources/
├── config/                     # Configuration templates
├── themes/                     # Theme definitions
│   ├── backgrounds/           # Background images
│   ├── foregrounds/           # Foreground overlays
│   └── presets/               # Theme presets
└── icon sizes/                # Application icons
    ├── 32x32/
    ├── 48x48/
    ├── 64x64/
    ├── 128x128/
    └── 256x256/
```

## Key Design Decisions

### 1. `src/` Layout
- Uses Python's recommended `src/` layout
- Separates source code from distribution
- Cleaner import paths within package
- Better isolation for testing

### 2. Widget Palette vs Old System
**Old System:**
- Dropdown menu for widget type
- Another dropdown for metric type
- Widget appears at fixed position (50, 50)
- Two-step process, no visual preview

**New System:**
- Visual widget cards with icons
- Categorized organization
- Click-to-add interaction
- Widget appears centered in preview
- Immediate visual feedback

### 3. Import Strategy
- All imports use relative paths
- No absolute paths in source code
- Consistent with Python package structure
- Works regardless of installation location

### 4. Backward Compatibility
- Preserves existing widget property editing
- Maintains same signal interface (`widget_added`, `widget_updated`)
- Existing widgets continue to work
- Only UI layer changed, not backend

## Common Issues & Solutions

### 1. Import Errors
**Problem**: `ModuleNotFoundError: No module named 'thermalright_lcd_control.widgets'`
**Solution**: Ensure imports use correct relative paths:
- From `gui/tabs/` to `gui/widgets/`: `from ..widgets.widget_palette import WidgetPalette`
- Not `...widgets.widget_palette` (three dots goes too far up)

### 2. File Location Issues
**Problem**: Files created in wrong location (nested paths)
**Solution**: 
- Always work from project root: `/home/leeo/Documents/code/thermalright-lcd-control/`
- Use `pwd` to verify location before file operations
- Source files belong in `src/thermalright_lcd_control/`

### 3. Permission Issues  
**Problem**: Cannot write to files/folders
**Solution**: If needing root permissions, you're in the wrong location
- Source files should be owned by user, not root
- Build artifacts may be owned by root (ignore these)

## Testing the Implementation

### Syntax Check
```bash
# Check all widget palette files
python3 -m py_compile src/thermalright_lcd_control/gui/widgets/widget_*.py
python3 -m py_compile src/thermalright_lcd_control/gui/tabs/widgets_tab.py
```

### Run Tests
1. Launch application
2. Navigate to Widgets tab
3. Verify:
   - Widget palette appears on left
   - Categories are expandable/collapsible
   - Widget cards show icons, names, descriptions
   - Clicking widget adds it to "Added Widgets" list
   - Widget appears in preview area
   - Existing functionality (drag, properties) still works

## Future Enhancements

### Planned Features
1. **True Drag-and-Drop**: Drag widget from palette directly to preview
2. **More Widget Types**: Shapes, graphs, progress bars
3. **Widget Previews**: Live preview while dragging
4. **Smart Positioning**: Snap to grid, alignment guides
5. **Widget Libraries**: Save/load widget collections

### Technical Improvements
1. **Virtual Scrolling**: For large widget collections
2. **Custom Widget Creation**: User-defined widgets
3. **Import/Export**: Share widget configurations
4. **Undo/Redo**: Action history for widget manipulation

---

*Document Version: 1.0*  
*Last Updated: 2025-12-18*  
*Author: Project Development Team*