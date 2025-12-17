# ThermalRight LCD Control - Project Overview

## Introduction

ThermalRight LCD Control is a Python-based desktop application designed to manage and display custom content on USB-connected LCD displays, particularly those manufactured by ThermalRight. The application provides a graphical user interface (GUI) for configuring display settings, including backgrounds, foregrounds, text overlays, and real-time system metrics, while running a background service that continuously generates and transmits image frames to the connected device.

The project supports multiple display resolutions (320x240, 320x320, 480x480) and various background types (static images, GIFs, videos, image collections, and solid colors). It features live metric display (CPU/GPU usage, temperature, frequency) and customizable text elements (date, time).

## Architecture Overview

The application follows a client-service architecture:

- **GUI (Client)**: PySide6-based desktop application for configuration and preview
- **Service (Background Process)**: USB communication and frame generation daemon
- **Device**: USB-connected LCD display hardware

Key technologies:
- **GUI Framework**: PySide6 (Qt for Python)
- **Image Processing**: PIL (Pillow)
- **USB Communication**: PyUSB with HID and bulk transfer support
- **Configuration**: YAML-based config files
- **System Metrics**: psutil for CPU/GPU monitoring

## GUI Components

### Main Application Entry Point
- **`run_gui.sh`**: Shell script that launches the GUI application
- **`src/thermalright_lcd_control/main_gui.py`**: Main GUI application entry point, initializes the MediaPreviewUI

### Core GUI Classes

#### MediaPreviewUI (`src/thermalright_lcd_control/gui/main_window.py`)
The main application window that orchestrates all GUI functionality:
- Initializes device detection and resolution settings
- Sets up tabbed interface (Media, Themes, etc.)
- Manages the preview area and apply/save operations
- Handles configuration generation and service communication

Key methods:
- `setup_ui()`: Creates the main window layout
- `setup_preview_manager()`: Initializes the preview system
- `generate_preview()`: Triggers configuration generation and preview update
- `apply_config()`: Saves configuration and signals the service to reload

#### PreviewManager (`src/thermalright_lcd_control/gui/components/preview_manager.py`)
Manages the display preview and current configuration state:
- Maintains current background, foreground, and text settings
- Generates preview images using DisplayGenerator
- Handles background type detection and loading
- Updates preview QLabel with rendered frames

Key attributes:
- `current_background_path`: Path to selected background
- `current_foreground_path`: Path to overlay image
- `preview_width/height`: Device resolution
- `display_generator`: Instance of DisplayGenerator for preview rendering

#### ConfigGenerator (`src/thermalright_lcd_control/gui/components/config_generator.py`)
Converts GUI state into YAML configuration files:
- `generate_config_data()`: Builds configuration dictionary from current settings
- `generate_config_yaml()`: Writes YAML to service config directory
- Handles widget positioning, colors, and formatting
- Supports multiple background types and metric configurations

#### UnifiedController (`src/thermalright_lcd_control/gui/unified_controller.py`)
Manages widget lifecycle and configuration:
- Creates, updates, and removes display widgets
- Coordinates between GUI components and configuration generation
- Handles widget positioning and property updates
- Integrates with PreviewManager for live updates

### Tab System
Located in `src/thermalright_lcd_control/gui/tabs/`:
- **Media Tab**: Background and foreground selection
- **Themes Tab**: Preset configurations
- Additional tabs for advanced settings

### Widget System
Located in `src/thermalright_lcd_control/gui/widgets/`:
- Draggable widgets for positioning text and metrics
- Real-time preview updates
- Property panels for customization

## Service Components

### Service Entry Point
- **`run_service.sh`**: Shell script that launches the service with sudo privileges
- **`src/thermalright_lcd_control/service.py`**: Service application entry point

### Device Controller (`src/thermalright_lcd_control/device_controller/device_controller.py`)
Main service orchestrator:
- `run_service()`: Initializes device and starts the display loop
- Monitors configuration file changes
- Handles device reset and error recovery

### Display Device Classes

#### Base DisplayDevice (`src/thermalright_lcd_control/device_controller/display/display_device.py`)
Abstract base class for all display devices:
- `_encode_image()`: Converts PIL Image to device-specific byte format
- `_prepare_frame_packets()`: Splits data into USB packets
- `run()`: Main display loop that generates and sends frames
- `_get_generator()`: Manages DisplayGenerator lifecycle and config reloading

#### HID Devices (`src/thermalright_lcd_control/device_controller/display/hid_devices.py`)
HID (Human Interface Device) protocol implementations:
- **DisplayDevice04165302**: 320x240 ThermalRight display
- **DisplayDevice04185304**: 480x480 ThermalRight display
- Uses HID reports for data transmission

#### USB Devices (`src/thermalright_lcd_control/device_controller/display/usb_devices.py`)
Bulk USB transfer implementations:
- **DisplayDevice87AD70DB**: ChiZhu Tech 320x320 display
- Uses bulk endpoints with zero-length packet (ZLP) signaling

### Frame Generation System

#### DisplayGenerator (`src/thermalright_lcd_control/device_controller/display/generator.py`)
Orchestrates frame creation:
- `generate_frame_with_metrics()`: Combines background, foreground, text, and metrics
- `get_frame_with_duration()`: Returns frame and display duration
- Manages text rendering and metric integration

#### FrameManager (`src/thermalright_lcd_control/device_controller/display/frame_manager.py`)
Handles background content management:
- Loads and manages different background types (image, GIF, video, collection, color)
- Provides current frame based on timing
- Collects real-time system metrics
- Supports animated content with proper timing

#### Text Rendering (`src/thermalright_lcd_control/device_controller/display/text_renderer.py`)
Handles text overlay rendering:
- Renders date, time, and metric text
- Supports custom fonts, colors, and positioning
- Integrates with PIL for image composition

### Configuration Management

#### ConfigLoader (`src/thermalright_lcd_control/device_controller/display/config_loader.py`)
Loads YAML configurations:
- `load_config()`: Parses YAML into DisplayConfig objects
- Handles path resolution and validation
- Supports metric and text configurations

#### DisplayConfig (`src/thermalright_lcd_control/device_controller/display/config.py`)
Configuration data structures:
- Defines background, foreground, metrics, and text settings
- Supports multiple background types and resolutions

## Data Flow and Interactions

### GUI to Service Communication
1. User configures settings in GUI (backgrounds, widgets, metrics)
2. `generate_preview()` called, which:
   - Updates PreviewManager state
   - Calls ConfigGenerator to create YAML
   - Saves config to service directory (`./resources/config/config_{width}{height}.yaml`)
3. Service detects config file modification via `_get_generator()`
4. Service reloads DisplayGenerator with new configuration
5. Frame generation continues with updated settings

### Frame Generation Process
1. **Background Loading**: FrameManager loads background based on type:
   - Static images: Single PIL Image
   - GIFs: Sequence of frames with durations
   - Videos: Frame extraction with timing
   - Collections: Rotating image sets
   - Colors: Solid color images

2. **Metric Collection**: FrameManager collects system metrics:
   - CPU: usage, temperature, frequency
   - GPU: usage, temperature, frequency, vendor info

3. **Frame Composition**: DisplayGenerator combines elements:
   - Base background frame
   - Foreground overlay (if enabled)
   - Text rendering (date, time)
   - Metric text overlays
   - Alpha blending for transparency

4. **Encoding**: DisplayDevice converts PIL Image to device format:
   - Pixel traversal (column-major, bottom-to-top for current implementation)
   - RGB565 color conversion
   - Little-endian byte ordering
   - Padding for packet alignment

### USB Communication
1. **Device Detection**: DeviceLoader scans for supported USB devices by VID/PID
2. **Interface Setup**: 
   - HID devices: Claim HID interface
   - USB devices: Find bulk endpoints, claim interface
3. **Data Transmission**:
   - Header + encoded image data
   - Split into packets (512 bytes for HID)
   - Send via HID reports or bulk transfers
   - Zero-length packets for frame commit (USB devices)

### Service Loop
```python
while True:
    img, delay = generator.get_frame_with_duration()
    header = device.get_header()
    encoded = device._encode_image(img)
    packets = device._prepare_frame_packets(header + encoded)
    for packet in packets:
        device.send_packet(packet)
    time.sleep(delay)
```

## Configuration Management

### Path Resolution
- **PathResolver** (`src/thermalright_lcd_control/gui/utils/path_resolver.py`): Handles path differences between development and installed environments
- Resolves relative paths to absolute locations
- Supports system-wide installations

### Configuration Files
- **Service Configs**: `resources/config/config_{width}{height}.yaml`
- **User Themes**: `resources/themes/{resolution}/`
- **System Resources**: Installation-dependent paths

### Dynamic Configuration
- Service monitors config file modification times
- Automatic generator reloading on config changes
- No service restart required for most changes

## Utilities and Common Code

### Logging (`src/thermalright_lcd_control/common/logging_config.py`)
- Centralized logging configuration
- Separate loggers for GUI and service
- Configurable log levels and output

### Metric Collectors
- **CPU Metrics** (`src/thermalright_lcd_control/device_controller/metrics/cpu_metrics.py`): psutil-based CPU monitoring
- **GPU Metrics** (`src/thermalright_lcd_control/device_controller/metrics/gpu_metrics.py`): System GPU information

## Build and Installation

### Build System
- **`build.sh`**: Creates distributable packages
- **`create_package.sh`**: Generates RPM/DEB packages
- **`pyproject.toml`**: Python project configuration

### Installation
- **`install.sh`**: User-space installation script
- **`uninstall.sh`**: Removal script
- Supports both system-wide and user installations

## Current Issues and Known Limitations

### Display Issues
- Image encoding may not match all device firmware expectations
- Potential rotation/orientation mismatches
- Metric widgets can cause display initialization failures

### Performance Considerations
- Real-time metric collection may impact frame rates
- Large background images can cause encoding delays
- USB transfer overhead for high-resolution displays

### Compatibility
- Limited to specific USB device models
- Requires sudo for USB access
- Platform-specific (Linux-focused)

## Future Enhancements

- Support for additional USB devices
- Improved error handling and recovery
- Enhanced animation and transition effects
- Network-based configuration sharing
- Plugin system for custom metrics and backgrounds

This overview provides a comprehensive understanding of the ThermalRight LCD Control system's architecture, components, and operational flow. The modular design allows for easy extension and maintenance of individual components while maintaining clear separation between GUI configuration and background service operation.