# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""
Device Selector Widget - Dropdown for selecting between multiple connected displays
"""

from typing import Optional, List, Dict, Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLabel, QPushButton
)

from thermalright_lcd_control.gui.utils.usb_detector import USBDeviceDetector
from thermalright_lcd_control.common.logging_config import get_gui_logger


class DeviceSelector(QWidget):
    """
    Widget for selecting between multiple connected LCD displays.
    
    Emits device_changed signal when user selects a different device.
    """
    
    # Signal emitted when a different device is selected
    # Carries the device info dict
    device_changed = Signal(dict)
    
    def __init__(self, 
                 detector: USBDeviceDetector,
                 current_device: Optional[Dict[str, Any]] = None,
                 parent: Optional[QWidget] = None):
        """
        Initialize the device selector.
        
        Args:
            detector: USBDeviceDetector instance for scanning devices
            current_device: Currently selected device (if any)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.logger = get_gui_logger()
        self.detector = detector
        self.current_device = current_device
        self._devices: List[Dict[str, Any]] = []
        
        self._setup_ui()
        self.refresh_devices()
    
    def _setup_ui(self):
        """Set up the UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Label
        label = QLabel("Display:")
        layout.addWidget(label)
        
        # Device dropdown
        self.combo = QComboBox()
        self.combo.setMinimumWidth(200)
        self.combo.currentIndexChanged.connect(self._on_device_selected)
        layout.addWidget(self.combo, 1)
        
        # Refresh button
        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setToolTip("Refresh device list")
        self.refresh_btn.setMaximumWidth(30)
        self.refresh_btn.clicked.connect(self.refresh_devices)
        layout.addWidget(self.refresh_btn)
    
    def refresh_devices(self):
        """Scan for connected devices and update the dropdown"""
        self.logger.debug("Scanning for connected devices...")
        
        # Store current selection to try to restore it
        current_id = None
        if self.current_device:
            current_id = self.current_device.get('device_id')
        
        # Block signals while updating
        self.combo.blockSignals(True)
        self.combo.clear()
        
        # Scan for devices
        self._devices = self.detector.find_all_connected_devices()
        
        if not self._devices:
            self.combo.addItem("No devices found")
            self.combo.setEnabled(False)
            self.current_device = None
        else:
            self.combo.setEnabled(True)
            selected_index = 0
            
            for i, device in enumerate(self._devices):
                display_name = device.get('display_name', f"Device {i+1}")
                self.combo.addItem(display_name, device)
                
                # Try to restore previous selection
                if current_id and device.get('device_id') == current_id:
                    selected_index = i
            
            self.combo.setCurrentIndex(selected_index)
            self.current_device = self._devices[selected_index]
        
        self.combo.blockSignals(False)
        
        self.logger.info(f"Found {len(self._devices)} device(s)")
    
    def _on_device_selected(self, index: int):
        """Handle device selection change"""
        if index < 0 or index >= len(self._devices):
            return
        
        new_device = self._devices[index]
        
        # Only emit if actually changed
        if self.current_device:
            current_id = self.current_device.get('device_id')
            new_id = new_device.get('device_id')
            if current_id == new_id:
                return
        
        self.logger.info(f"Device selected: {new_device.get('display_name')}")
        self.current_device = new_device
        self.device_changed.emit(new_device)
    
    def get_current_device(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected device"""
        return self.current_device
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Get all connected devices"""
        return self._devices.copy()
    
    def select_device_by_id(self, device_id: str) -> bool:
        """
        Select a device by its unique ID.
        
        Args:
            device_id: Device ID in "bus:address" format
            
        Returns:
            True if device was found and selected, False otherwise
        """
        for i, device in enumerate(self._devices):
            if device.get('device_id') == device_id:
                self.combo.setCurrentIndex(i)
                return True
        return False
    
    def has_multiple_devices(self) -> bool:
        """Check if multiple devices are connected"""
        return len(self._devices) > 1
