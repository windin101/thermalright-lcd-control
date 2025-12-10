
# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""
Module for detecting supported USB devices
"""
from pathlib import Path
from typing import Optional, Dict, Any, List

import usb.core
import yaml

from thermalright_lcd_control.common.logging_config import get_gui_logger
from thermalright_lcd_control.common.supported_devices import SUPPORTED_DEVICES


class USBDeviceDetector:
    """Detects supported USB devices defined in configuration"""

    def __init__(self, config_file: str = None):
        self.logger = get_gui_logger()
        self.config_file = config_file
        self.config = None
        self._load_config()

    def _load_config(self):
        """Load gui config from config file"""
        if not self.config_file:
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.config = config
        except (FileNotFoundError, yaml.YAMLError) as e:
            self.logger.error(f"Error loading configuration: {e}")

    def find_connected_device(self) -> Optional[Dict[str, Any]]:
        """
        Search for a supported device connected to the system (legacy single-device method)

        Returns:
            Dict containing the found device information (vid, pid, width, height)
            or None if no supported device is found
        """
        try:
            if self.config is None:
                self.logger.error("Configuration not loaded")
                return None
            
            # Get all connected USB devices
            device_config_file_path = Path(self.config['paths']['service_config'],"device_info.yaml")

            with open(device_config_file_path, 'r', encoding='utf-8') as f:
                device_config = yaml.safe_load(f)
            return device_config

        except (FileNotFoundError, yaml.YAMLError) as e:
            self.logger.error(f"Error loading device configuration file: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error detecting USB devices: {e}")
            return None

    def find_all_connected_devices(self) -> List[Dict[str, Any]]:
        """
        Search for ALL supported devices connected to the system
        
        Returns:
            List of dicts, each containing device information:
            - device_id: Unique identifier (bus:address)
            - vid: Vendor ID
            - pid: Product ID  
            - width: Display width
            - height: Display height
            - class_name: Device class for instantiation
            - display_name: Human-readable name for UI
            - bus: USB bus number
            - address: USB device address
        """
        connected_devices = []
        
        try:
            # Scan for each supported device type
            for vid, pid, device_variants in SUPPORTED_DEVICES:
                # Find all devices with this VID:PID
                devices = usb.core.find(idVendor=vid, idProduct=pid, find_all=True)
                
                if devices:
                    for usb_device in devices:
                        # Create unique device ID from bus and address
                        device_id = f"{usb_device.bus}:{usb_device.address}"
                        
                        # For devices with multiple variants (e.g., 320x320 vs 480x480),
                        # we'll use the first variant as default - user can change in GUI
                        # In future, we could try to auto-detect based on device response
                        for variant in device_variants:
                            device_info = {
                                'device_id': device_id,
                                'vid': vid,
                                'pid': pid,
                                'width': variant['width'],
                                'height': variant['height'],
                                'class_name': variant['class_name'],
                                'bus': usb_device.bus,
                                'address': usb_device.address,
                                'display_name': self._generate_display_name(
                                    vid, pid, variant['width'], variant['height'], 
                                    usb_device.bus, usb_device.address
                                )
                            }
                            connected_devices.append(device_info)
                            # Only add first variant per physical device
                            break
            
            self.logger.info(f"Found {len(connected_devices)} connected display device(s)")
            for dev in connected_devices:
                self.logger.debug(f"  - {dev['display_name']} ({dev['device_id']})")
                
        except Exception as e:
            self.logger.error(f"Error scanning for USB devices: {e}")
        
        return connected_devices

    def _generate_display_name(self, vid: int, pid: int, width: int, height: int, 
                                bus: int, address: int) -> str:
        """Generate a human-readable display name for a device"""
        # Map known VID:PID to friendly names
        device_names = {
            (0x0418, 0x5304): "Thermalright LCD",
            (0x0416, 0x5302): "Thermalright LCD", 
            (0x87AD, 0x70DB): "ChiZhu Tech LCD",
        }
        
        base_name = device_names.get((vid, pid), f"Display {vid:04X}:{pid:04X}")
        return f"{base_name} {width}x{height} (Bus {bus})"

    def get_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific device by its unique ID
        
        Args:
            device_id: Device ID in format "bus:address"
            
        Returns:
            Device info dict or None if not found
        """
        devices = self.find_all_connected_devices()
        for device in devices:
            if device['device_id'] == device_id:
                return device
        return None
