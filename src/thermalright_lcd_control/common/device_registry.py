# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb
"""
Device Registry - Manages multi-device configuration persistence.

This module handles:
- Tracking configured devices by their unique ID (bus:address)
- Device-specific config file naming and storage
- Device metadata persistence (nicknames, last seen, etc.)
"""

import os
import yaml
from typing import Optional, Dict, List, TypedDict
from pathlib import Path


class DeviceRegistryEntry(TypedDict):
    """Type definition for a device registry entry"""
    device_id: str  # Unique ID: "bus:address"
    vid: int
    pid: int
    width: int
    height: int
    class_name: str
    nickname: Optional[str]  # User-friendly name for the device
    config_file: str  # Path to device-specific config file
    last_seen: Optional[str]  # ISO timestamp of last detection


class DeviceRegistry:
    """
    Manages device configuration registry for multi-device support.
    
    The registry persists device information and maps device IDs to their
    configuration files, allowing the system to remember devices and their
    settings across sessions.
    """
    
    def __init__(self, config_base_dir: str):
        """
        Initialize the device registry.
        
        Args:
            config_base_dir: Base directory for config files (e.g., ~/.config/thermalright-lcd-control)
        """
        self.config_base_dir = Path(config_base_dir)
        self.registry_file = self.config_base_dir / "device_registry.yaml"
        self._devices: Dict[str, DeviceRegistryEntry] = {}
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load the device registry from disk"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r") as f:
                    data = yaml.safe_load(f) or {}
                    self._devices = data.get("devices", {})
            except Exception:
                self._devices = {}
        else:
            self._devices = {}
    
    def _save_registry(self) -> None:
        """Save the device registry to disk"""
        self.config_base_dir.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, "w") as f:
            yaml.dump({"devices": self._devices}, f, default_flow_style=False)
    
    def register_device(
        self,
        device_id: str,
        vid: int,
        pid: int,
        width: int,
        height: int,
        class_name: str,
        nickname: Optional[str] = None
    ) -> DeviceRegistryEntry:
        """
        Register a new device or update an existing one.
        
        Args:
            device_id: Unique device identifier (bus:address format)
            vid: USB vendor ID
            pid: USB product ID
            width: Display width
            height: Display height
            class_name: Full class name for device driver
            nickname: Optional user-friendly name
            
        Returns:
            The created/updated registry entry
        """
        from datetime import datetime
        
        # Generate config filename based on device ID
        # Replace ":" with "_" for filesystem compatibility
        safe_device_id = device_id.replace(":", "_")
        config_file = f"config_{width}{height}_{safe_device_id}.yaml"
        
        entry = DeviceRegistryEntry(
            device_id=device_id,
            vid=vid,
            pid=pid,
            width=width,
            height=height,
            class_name=class_name,
            nickname=nickname or f"Display {len(self._devices) + 1}",
            config_file=config_file,
            last_seen=datetime.now().isoformat()
        )
        
        self._devices[device_id] = entry
        self._save_registry()
        
        return entry
    
    def get_device(self, device_id: str) -> Optional[DeviceRegistryEntry]:
        """
        Get a device registry entry by ID.
        
        Args:
            device_id: Unique device identifier
            
        Returns:
            Registry entry or None if not found
        """
        return self._devices.get(device_id)
    
    def get_all_devices(self) -> List[DeviceRegistryEntry]:
        """
        Get all registered devices.
        
        Returns:
            List of all device registry entries
        """
        return list(self._devices.values())
    
    def remove_device(self, device_id: str) -> bool:
        """
        Remove a device from the registry.
        
        Args:
            device_id: Unique device identifier
            
        Returns:
            True if device was removed, False if not found
        """
        if device_id in self._devices:
            del self._devices[device_id]
            self._save_registry()
            return True
        return False
    
    def update_nickname(self, device_id: str, nickname: str) -> bool:
        """
        Update the nickname for a device.
        
        Args:
            device_id: Unique device identifier
            nickname: New nickname
            
        Returns:
            True if updated, False if device not found
        """
        if device_id in self._devices:
            self._devices[device_id]["nickname"] = nickname
            self._save_registry()
            return True
        return False
    
    def update_last_seen(self, device_id: str) -> bool:
        """
        Update the last_seen timestamp for a device.
        
        Args:
            device_id: Unique device identifier
            
        Returns:
            True if updated, False if device not found
        """
        from datetime import datetime
        
        if device_id in self._devices:
            self._devices[device_id]["last_seen"] = datetime.now().isoformat()
            self._save_registry()
            return True
        return False
    
    def get_config_path(self, device_id: str) -> Optional[Path]:
        """
        Get the full config file path for a device.
        
        Args:
            device_id: Unique device identifier
            
        Returns:
            Full path to config file, or None if device not registered
        """
        entry = self.get_device(device_id)
        if entry:
            return self.config_base_dir / "config" / entry["config_file"]
        return None
    
    def get_default_config_path(self, width: int, height: int) -> Path:
        """
        Get the default config path for a resolution (no device-specific suffix).
        
        This is the fallback config used when no device-specific config exists.
        
        Args:
            width: Display width
            height: Display height
            
        Returns:
            Path to default config file
        """
        return self.config_base_dir / "config" / f"config_{width}{height}.yaml"
    
    def ensure_device_config(self, device_id: str) -> Optional[Path]:
        """
        Ensure a device-specific config file exists, creating from default if needed.
        
        Args:
            device_id: Unique device identifier
            
        Returns:
            Path to device config file, or None if device not registered
        """
        import shutil
        
        entry = self.get_device(device_id)
        if not entry:
            return None
        
        config_path = self.get_config_path(device_id)
        if config_path and not config_path.exists():
            # Copy from default config
            default_path = self.get_default_config_path(entry["width"], entry["height"])
            if default_path.exists():
                config_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(default_path, config_path)
        
        return config_path
