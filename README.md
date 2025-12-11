# Thermalright LCD Control

A powerful Linux application for controlling Thermalright LCD cooler displays with an intuitive graphical interface.

![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)
![Version](https://img.shields.io/badge/version-1.4.5-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

---

## 📖 Overview

Thermalright LCD Control is a comprehensive Linux application for customizing and managing LCD displays found on Thermalright CPU coolers. Whether you want to display system metrics, custom images, or create unique visual themes, this application provides all the tools you need through an intuitive drag-and-drop interface.

The application consists of two components:
- **GUI Application** - A full-featured graphical interface for designing and previewing your display
- **Background Service** - A systemd service that runs continuously to update your display with real-time metrics

This project is a fork that significantly extends the original with enhanced GUI features, visual effects, and improved usability. The goal is to provide a polished, professional experience for customizing your Thermalright LCD display on Linux.

---

## ✨ Features

### 🖼️ Display Composition

**Background Controls**
- Support for images (PNG, JPG, GIF) and videos (MP4, WebM) as backgrounds
- Multiple scaling modes: Stretch, Fit, Fill, Centered, Tiled
- Solid colour backgrounds with colour picker
- Background opacity control with smooth slider
- Image slideshow support - cycle through a collection of images

**Foreground Overlays**
- Draggable foreground image overlay
- Independent opacity control for foreground elements
- Precise position controls with drag-and-drop or coordinate input

### 📊 System Metrics Display

**CPU Metrics**
- Temperature monitoring
- Utilization percentage
- Frequency (MHz/GHz format selectable)
- CPU name with character limit option

**GPU Metrics**
- Temperature monitoring (AMD, NVIDIA, Intel)
- Utilization percentage
- Frequency (MHz/GHz format selectable)
- GPU name with character limit option
- VRAM usage (percentage and total)

**Memory Metrics**
- RAM usage percentage
- RAM total capacity

**Metric Customization**
- Customizable labels for each metric
- Configurable label positions (above, below, left, right with alignment options)
- Independent label font size control
- Label offset adjustments (X/Y)
- Per-metric font size control

### 📅 Date & Time Widgets

**Date Widget**
- Multiple format options: Default, Short, Numeric
- Toggle weekday display
- Toggle year display

**Time Widget**
- 12-hour or 24-hour format
- Optional seconds display
- AM/PM indicator toggle

### ✏️ Free Text Widgets

- 4 independent free text widgets
- Custom text entry with prompt on creation
- Individual font size control per widget
- Full drag-and-drop positioning

### 📈 Graph Widgets

**Bar Graphs**
- 2 CPU bar graphs + 2 GPU bar graphs
- Horizontal or vertical orientation
- Rotation control (0-360°)
- Customizable dimensions (width/height)
- Fill colour, background colour, and border colour
- Corner radius control
- Gradient mode with 3-colour thresholds (low/mid/high)

**Circular/Arc Graphs**
- 2 CPU arc graphs + 2 GPU arc graphs
- Customizable radius and thickness
- Start angle and sweep angle control
- Rotation control
- Fill colour, background colour, and border colour
- Gradient mode with 3-colour thresholds

### 🎨 Text Effects

**Shadow Effect**
- Shadow colour picker
- X/Y offset control
- Blur radius adjustment

**Outline Effect**
- Outline colour picker
- Outline width control

**Gradient Text**
- Two-colour gradient selection
- Direction options: Vertical, Horizontal, Diagonal
- Per-widget gradient toggle (use global theme or solid colour)

### 🛠️ Editing Tools

**Interactive Preview**
- Zoomable preview (100%, 150%, 200%)
- Real-time preview of all changes
- Drag-and-drop widget positioning

**Widget Palette**
- Collapsible drag-to-add widget palette
- Organized by category (Text, CPU, GPU, Memory, Graphs)
- Simply drag widgets onto the preview to add them

**Snap-to-Grid**
- Configurable grid size (5-50px)
- Visual grid overlay toggle
- Precise widget alignment

**Widget Selection & Manipulation**
- Click-to-select widgets
- Resize handles for adjusting widget size
- Rotation handle with sticky snap points (0°, 45°, 90°, etc.)
- Property popup on double-click for quick editing

**Display Rotation**
- Full display rotation support (0°, 90°, 180°, 270°)
- All widgets adjust automatically

### 🎭 Theme System

**Preset Themes**
- Load pre-configured theme presets
- Save your custom configurations as themes
- Quick theme switching

**Theme Components**
- Backgrounds organized by resolution
- Foreground overlays
- Complete configuration files

### ⚙️ Configuration

- YAML-based configuration files
- Resolution-specific configurations (320x240, 320x320, 480x480)
- Save and load custom configurations
- Reset to defaults option

---

## 🖥️ Supported Devices

| VID:PID   | Screen Resolution | Device |
|-----------|-------------------|--------|
| 0416:5302 | 320x240 | Frozen Warframe series |
| 0418:5304 | 480x480 | Various models |
| 87AD:70DB | 320x320, 480x480 | Various models |

---

## 📦 Installation

### Prerequisites

Ensure you have these dependencies installed:
- Python 3.8+
- python3-pip
- python3-venv
- libhidapi (libhidapi-dev on Debian/Ubuntu, hidapi on other distributions)

### Download & Install

1. **Download** the latest release:
   ```bash
   wget https://github.com/windin101/thermalright-lcd-control/releases/download/v1.4.5/thermalright-lcd-control-1.4.5.tar.gz -P /tmp/
   ```

2. **Extract** the archive:
   ```bash
   cd /tmp
   tar -xvf thermalright-lcd-control-1.4.5.tar.gz
   ```

3. **Install** the application:
   ```bash
   cd thermalright-lcd-control
   sudo bash install.sh
   ```

The application is now installed and the background service will start automatically.

---

## 🚀 Usage

### Launch the GUI

- **From Applications Menu**: Search for "Thermalright LCD Control"
- **From Terminal**: Run `thermalright-lcd-control-gui`

### Manage the Background Service

```bash
# Check service status
sudo systemctl status thermalright-lcd-control.service

# Restart service
sudo systemctl restart thermalright-lcd-control.service

# Stop service
sudo systemctl stop thermalright-lcd-control.service

# View logs
sudo journalctl -u thermalright-lcd-control.service -f
```

### Quick Start Guide

1. **Launch the GUI** and connect your device
2. **Choose a background** from the Media tab or select a solid colour
3. **Add widgets** by dragging from the Widget Palette onto the preview
4. **Position widgets** using drag-and-drop or coordinate inputs
5. **Customize appearance** using the property popups (double-click widgets)
6. **Apply text effects** from the Effects section
7. **Save your configuration** and it will automatically apply to your device

---

## 🔧 Troubleshooting

### Device Not Detected
- Ensure the device is connected via USB
- Check that you have the correct udev rules installed (handled by installer)
- Try running `lsusb` to verify the device is visible

### Display Not Updating
- Check service status: `sudo systemctl status thermalright-lcd-control.service`
- View service logs: `sudo journalctl -u thermalright-lcd-control.service -f`
- Try restarting the service

### Image Quality Issues
- Ensure your background image matches your display resolution
- Try different scaling modes (Fit, Fill, Stretch)
- Check that the image format is supported (PNG, JPG, GIF)

### Adding New Devices
See [HOWTO.md](doc/HOWTO.md) for detailed instructions on reverse engineering and adding support for new devices.

---

## 🗺️ Roadmap

### Planned Features

**Multi-Device Support**
- [ ] Simultaneous control of multiple LCD devices
- [ ] Independent configuration per device
- [ ] Device switching in GUI

**New Device Support**
- [ ] Thermalright Trofeo Vision support
- [ ] Additional Thermalright LCD cooler models
- [ ] Community-contributed device profiles

**Enhanced Features**
- [ ] Animation support for widgets
- [ ] Custom widget plugins
- [ ] Network metrics display
- [ ] Disk usage metrics
- [ ] Fan speed monitoring integration

**Quality of Life**
- [ ] Undo/Redo functionality
- [ ] Widget copy/paste
- [ ] Keyboard shortcuts
- [ ] Configuration import/export

---

## 📋 System Requirements

- **Operating System**: Ubuntu 20.04+ / Debian 11+ / Fedora 35+ / Other modern Linux distributions
- **Python**: 3.8 or higher
- **Desktop Environment**: Any modern Linux desktop (GNOME, KDE, XFCE, etc.)
- **Hardware**: Compatible Thermalright LCD device

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors & Contributors

**Original Author**: REJEB BEN REJEB - [benrejebrejeb@gmail.com](mailto:benrejebrejeb@gmail.com)

**Fork Maintainer**: windin101

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add my feature'`)
4. Push to your branch (`git push origin feature/my-feature`)
5. Create a Pull Request

### Areas We Need Help With
- Testing on different Thermalright LCD devices
- AMD and Intel GPU metric testing
- Documentation and translations
- New device reverse engineering

---

## 🙏 Acknowledgements

- Original reverse engineering work by REJEB BEN REJEB
- The Linux HID and USB community for driver support
- All contributors and testers
