# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""
Entry point for Thermalright LCD Control GUI
"""

import argparse
import os
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from thermalright_lcd_control.gui.main_window import MediaPreviewUI
from thermalright_lcd_control.gui.utils.usb_detector import USBDeviceDetector
from thermalright_lcd_control.gui.styles import setup_application_palette
from thermalright_lcd_control.common.supported_devices import SUPPORTED_DEVICES

def show_error_and_exit(message: str):
    """Display error message and exit application"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("Error - No device found")
    msg_box.setText("No supported device found.")
    msg_box.setInformativeText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec()

    sys.exit(1)


def main(config_file=None):
    """Main function to start the GUI application

    Args:
        config_file (str, optional): Path to the GUI configuration file
    """
    app = QApplication(sys.argv)
    
    # Use system platform theme if available, or detect KDE/GNOME
    # Note: pip-installed PySide6 only has Fusion/Windows styles,
    # but we can still use the system color scheme
    platform_theme = os.environ.get('QT_QPA_PLATFORMTHEME', '')
    current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
    
    # Check if running under a known desktop environment
    has_desktop_theme = (
        platform_theme or  # Explicit platform theme set
        current_desktop in ['kde', 'gnome', 'xfce', 'cinnamon', 'mate', 'lxqt', 'budgie', 'deepin']
    )
    
    if not has_desktop_theme:
        # Only force Fusion + custom palette for minimal WMs without theming
        app.setStyle("Fusion")
        setup_application_palette(app)
    # else: Let Qt use system defaults (colors will come from desktop theme)
    
    app.setApplicationName("thermalright-lcd-control")
    app.setApplicationDisplayName("Thermalright LCD Control")
    app.setDesktopFileName("thermalright-lcd-control.desktop")

    # Use default config file if none provided
    if config_file is None:
        config_file = "gui_config.yaml"

    # Check for supported device presence
    detector = USBDeviceDetector(config_file)
    connected_device = detector.find_connected_device()

    if connected_device is None:
        error_message = (
            "No supported Thermalright LCD device detected.\n\n"
            "Supported devices:\n"
        )

        # Add supported devices list to message
        for vid,pid, devices in SUPPORTED_DEVICES:
            for device in devices:
                width = device.get('width', 'N/A')
                height = device.get('height', 'N/A')
                error_message += f"• VID: {hex(vid)}, PID: {hex(pid)} ({width}x{height})\n"

        error_message += (
            "\nPlease ensure a supported device is connected "
            "and recognized by the system."
        )

        show_error_and_exit(error_message)

    window = MediaPreviewUI(config_file, connected_device)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Thermalright LCD Control GUI")
    parser.add_argument('--config',
                        required=True,
                        help="Path to GUI configuration file (gui_config.yaml)")

    args = parser.parse_args()
    main(args.config)