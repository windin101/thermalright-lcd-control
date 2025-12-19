# Thermalright LCD Control

A Linux application for controlling Thermalright LCD displays with an intuitive graphical interface.

![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)

## Overview

Thermalright LCD Control provides an easy-to-use interface for managing your Thermalright LCD display on Linux systems.

The application features both a desktop GUI and a background service for seamless device control.

I performed reverse engineering on the Thermalright Windows application to understand its internal mechanisms.

During my analysis, I identified four different USB VID:PID combinations handled by the Windows application, all sharing
the same interaction logic.

Since I have access only to the Frozen Warframe 420 BLACK ARGB, my testing was limited exclusively to this specific
device.

Also, this application implements reading metrics from Amd, Nvidia, and Intel GPU. My testing was limited to Nvidia GPU.

Feel free to contribute to this project and let me know if the application is working with other devices.

For backgrounds, i have included all media formats supported by the Windows application
and added the option to select a collection of images to cycle through on the display.

## Features

- 🖥️ **User-friendly GUI** - Modern interface for device configuration
- ⚙️ **Background service** - Automatic device management
- 🎨 **Theme support** - Customizable display themes and backgrounds
- 🎬 **Video backgrounds** - Support for animated video backgrounds with live preview
- 📋 **System integration** - Native Linux desktop integration

## Changelog

### [1.4.3] - 2025-12-20
- 🔧 **Graphics Update Fixes**: Enhanced Qt graphics rendering with forced repaints and event processing
- 🎛️ **Toggle Reliability**: Improved background and foreground image toggle functionality
- 📦 **Version Management**: Updated project version for release preparation

### [1.4.1] - 2025-12-19
- 🎬 **Video Thumbnails**: Preview area now shows actual video frames instead of dark placeholders
- 🔍 **Transparent Text**: Removed black boxes behind text widgets for better background blending
- 🎛️ **Background Toggle**: Added checkbox to show/hide background images with solid color fallback
- ✨ **Enhanced Preview**: Videos display first frame, text blends seamlessly with backgrounds

### [1.4.0] - 2025-12-18
- 📊 **Enhanced System Monitoring**: Real-time CPU, GPU, and RAM metrics display
- 🎨 **Dynamic GUI Layout**: Equal column layout with organized control sections
- 🔧 **Widget System Improvements**: Fixed creation errors and enhanced data display
- 📈 **Comprehensive Metrics**: Added CPU name, GPU name, frequency, memory, and RAM usage
- 📐 **Responsive Design**: Equal column distribution with minimum window sizing
- 🎯 **Improved User Experience**: Logical control organization (preview top, buttons middle, settings bottom)

### [1.3.0] - 2025-12-17
- ✨ **Theme Management**: Save and load reusable themes through the Themes tab
- 🎬 **Video Background Previews**: GUI now shows video thumbnails instead of black screens
- 🔄 **Save/Apply Button Redesign**: Save creates themes, Apply sends to device
- 🚫 **Preview Isolation**: Changes to preview no longer automatically update the device
- 🌍 **Cross-Environment Compatibility**: Application works on machines with different user home folders
- 📁 **Path Portability**: Dynamic path resolution for different installation environments
- 🔧 **Import System Modernization**: Converted to absolute imports for better portability
- 📝 **Enhanced Documentation**: Comprehensive changelog and fix documentation

See [CHANGELOG.md](doc/CHANGELOG.md) for detailed change history.

## Supported devices

| VID:PID      |
|--------------|
| 0416:5302    |
| 0418:5304    |
| 87AD:70DB    |

## Installation

### Download Packages

Download the appropriate package for your Linux distribution from
the [Releases](https://www.github.com/rejeb/thermalright-lcd-control/releases) page:

- **`.deb`** - For Ubuntu, Debian, and derivatives
- **`.rpm`** - For Fedora, RHEL, CentOS, openSUSE, and derivatives

### Debian/Ubuntu Installation

1. **Download** the `.deb` package:
   ```bash
   wget https://github.com/rejeb/thermalright-lcd-control/raw/refs/heads/master/releases/thermalright-lcd-control_1.2.0_all.deb -P /tmp/
   ```

2. **Install** the package:
   ```bash
   sudo apt install /tmp/thermalright-lcd-control_1.2.0_all.deb
   ```

3. **Fix dependencies** (if needed):
   ```bash
   sudo apt-get install -f
   ```

### Fedora/RHEL/CentOS Installation

1. **Download** the `.rpm` package:
   ```bash
   wget https://media.githubusercontent.com/media/rejeb/thermalright-lcd-control/refs/heads/master/releases/thermalright-lcd-control-1.2.0-1.noarch.rpm -P /tmp/
   ```

2. **Install** the package:
   ```bash
   # Fedora/CentOS 8+
   sudo dnf install /tmp/thermalright-lcd-control-*-1.noarch.rpm
   
   # RHEL/CentOS 7
   sudo yum install /tmp/thermalright-lcd-control-*-1.noarch.rpm
   ```

### openSUSE Installation

1. **Download** the `.rpm` package
   ```bash
   wget https://media.githubusercontent.com/media/rejeb/thermalright-lcd-control/refs/heads/master/releases/thermalright-lcd-control-1.2.0-1.noarch.rpm -P /tmp/
   ```

2. **Install** the package:
   ```bash
   sudo zypper install /tmp/thermalright-lcd-control-1.2.0-1.noarch.rpm
   ```

### Install using Tar.gz archive

1. **Check** for required dependencies:
   /!\ Make sure you have these required dependencies installed:
    - python3
    - python3-pip
    - python3-venv
    - libhidapi-* or hidapi depending on your distribution

2. **Download** the `.tar.gz` package:
   ```bash
   wget https://github.com/rejeb/thermalright-lcd-control/raw/refs/heads/master/releases/thermalright-lcd-control-1.2.0.tar.gz -P /tmp/
   ```
   
3. **Untar** the archive file:
   ```bash
   cd /tmp
   
   tar -xvf thermalright-lcd-control-1.2.0.tar.gz
   ```
    
4. **Install** application:
   ```bash
   cd /thermalright-lcd-control
   
   sudo ./install.sh
   ```

That's it! The application is now installed. You can see the default theme displayed on your Thermalright LCD device.

## Troubleshooting
If your device is 0416:5302 and nothing is displayed:
    - Check service status to see if it is running
    - Try restart service
    - Check service logs located in /var/log/thermalright-lcd-control.log


If your device is one of the other devices, contributions are welcome.
Here some tips to help you:
    - Check service status to see if it is running
    - Check service logs located in /var/log/thermalright-lcd-control.log
    - If the device is not working then this possibly mean that header value is not correct. 
See [Add new device](#add-new-device) section to fix header generation.
    - If the device is working but image is not good, this means that the image is not encoded correctly.
See [Add new device](#add-new-device) section to fix image encoding by overriding method _`_encode_image`.


## Usage

### Launch the Application

- **From Applications Menu**: Search for "Thermalright LCD Control" in your application launcher
- **From Terminal**: Run `thermalright-lcd-control`

### System Service

The background service starts automatically after installation. You can manage it using:

# Check service status

sudo systemctl status thermalright-lcd-control.service

# Restart service

sudo systemctl restart thermalright-lcd-control.service

# Stop service

sudo systemctl stop thermalright-lcd-control.service

## System Requirements

- **Operating System**: Ubuntu 20.04+ / Debian 11+ / Other modern Linux distributions
- **Python**: 3.8 or higher (automatically managed)
- **Desktop Environment**: Any modern Linux desktop (GNOME, KDE, XFCE, etc.)
- **Hardware**: Compatible Thermalright LCD device

## Add new device

In [HOWTO.md](doc/HOWTO.md) I detail all the steps I gone through to find out how myy device works and all steps to add a new device.

## Documentation

Comprehensive documentation is available in the [doc/](doc/) directory:

- **[Documentation Index](doc/README.md)** - Complete guide to all documentation files
- **[HOWTO.md](doc/HOWTO.md)** - Setup instructions and device reverse engineering
- **[CHANGELOG.md](doc/CHANGELOG.md)** - Detailed change history and version information
- **[VIDEO_BACKGROUND_PREVIEW_FIX.md](doc/VIDEO_BACKGROUND_PREVIEW_FIX.md)** - Video background implementation
- **[SAVE_APPLY_BUTTONS_UPDATE.md](doc/SAVE_APPLY_BUTTONS_UPDATE.md)** - Theme management system

See [doc/README.md](doc/README.md) for a complete index of all documentation files.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Author

**REJEB BEN REJEB** - [benrejebrejeb@gmail.com](mailto:benrejebrejeb@gmail.com)

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add my feature'`)
4. Push to your branch (`git push origin feature/my-feature`)
5. Create a Pull Request