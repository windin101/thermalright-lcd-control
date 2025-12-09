# Thermalright LCD Control

A Linux application for controlling Thermalright LCD displays with an intuitive graphical interface.

![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)
![version](https://img.shields.io/badge/version-1.3.1-green.svg)

# Overview

This fork extends the original Thermalright LCD Control project with enhanced GUI features, text effects, and improved usability. The goal is to provide a polished, user-friendly experience for customizing your Thermalright LCD display on Linux. This will be expanded to adding support for aditional Thermalright products

# Origional Project Overview

Thermalright LCD Control provides an easy-to-use interface for managing your Thermalright LCD display on Linux systems.

The application features both a desktop GUI and a background service for seamless device control.

I performed reverse engineering on the Thermalright Windows application to understand its internal mechanisms.

During my analysis, I identified four different USB VID:PID combinations handled by the Windows application, all sharing the same interaction logic.

Since I have access only to the Frozen Warframe 420 BLACK ARGB, my testing was limited exclusively to this specific device.

Also, this application implements reading metrics from Amd, Nvidia, and Intel GPU. My testing was limited to Nvidia GPU.

Feel free to contribute to this project and let me know if the application is working with other devices.

For backgrounds, i have included all media formats supported by the Windows application and added the option to select a collection of images to cycle through on the display.

Features
🖥️ User-friendly GUI - Modern interface for device configuration
⚙️ Background service - Automatic device management
🎨 Theme support - Customizable display themes and backgrounds
📋 System integration - Native Linux desktop integration
Supported devices
VID:PID	SCREEN RESOLUTION
0416:5302	320x240
0418:5304	480x480
87AD:70DB	320x320,480x480
Installation
Download Packages
Download the appropriate package for your Linux distribution from the Releases page:

.targ.gz - For any distribution
Installation
Check for required dependencies: /!\ Make sure you have these required dependencies installed:

python3
python3-pip
python3-venv
libhidapi-* or hidapi depending on your distribution
Download the .tar.gz package:

wget https://github.com/windin101/thermalright-lcd-control/releases/download/1.3.1/thermalright-lcd-control-1.3.1.tar.gz -P /tmp/
Untar the archive file:

cd /tmp

tar -xvf thermalright-lcd-control-1.3.1.tar.gz
Install application:

cd /thermalright-lcd-control

sudo bash install.sh
That's it! The application is now installed. You can see the default theme displayed on your Thermalright LCD device.

Troubleshooting
If your device is 0416:5302 and nothing is displayed:

Check service status to see if it is running
Try restart service
Check service logs located in /var/log/thermalright-lcd-control.log
If your device is one of the other devices, contributions are welcome. Here some tips to help you:

Check service status to see if it is running
Check service logs located in /var/log/thermalright-lcd-control.log
If the device is not working then this possibly mean that header value is not correct. See Add new device section to fix header generation.
If the device is working but image is not good, this means that the image is not encoded correctly. See Add new device section to fix image encoding by overriding method __encode_image.
Usage
Launch the Application
From Applications Menu: Search for "Thermalright LCD Control" in your application launcher
From Terminal: Run thermalright-lcd-control
System Service
The background service starts automatically after installation. You can manage it using:

Check service status
sudo systemctl status thermalright-lcd-control.service

Restart service
sudo systemctl restart thermalright-lcd-control.service

Stop service
sudo systemctl stop thermalright-lcd-control.service

System Requirements
Operating System: Ubuntu 20.04+ / Debian 11+ / Other modern Linux distributions
Python: 3.8 or higher (automatically managed)
Desktop Environment: Any modern Linux desktop (GNOME, KDE, XFCE, etc.)
Hardware: Compatible Thermalright LCD device
Add new device
In HOWTO.md I detail all the steps I gone through to find out how myy device works and all steps to add a new device.

License
This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

Author
REJEB BEN REJEB - benrejebrejeb@gmail.com

🤝 Contributing
Contributions are welcome! To contribute:

Fork the project
Create a feature branch (git checkout -b feature/my-feature)
Commit your changes (git commit -am 'Add my feature')
Push to your branch (git push origin feature/my-feature)
Create a Pull Request