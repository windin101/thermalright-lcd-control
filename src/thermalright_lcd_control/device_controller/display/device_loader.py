import importlib
from typing import Optional, List, TypedDict

import usb.core
import yaml

from thermalright_lcd_control.device_controller.display.display_device import DisplayDevice


def _get_supported_devices():
    """Lazy import to avoid circular dependency"""
    from thermalright_lcd_control.common.supported_devices import SUPPORTED_DEVICES
    return SUPPORTED_DEVICES


class LoadedDevice(TypedDict):
    """Type definition for a loaded device with its metadata"""
    device_id: str  # Unique ID: "bus:address"
    device: DisplayDevice
    vid: int
    pid: int
    bus: int
    address: int
    width: int
    height: int
    class_name: str


class DeviceLoader:
    def __init__(self, config_dir: str):
        self.config_dir = config_dir

    def load_device(self) -> Optional[DisplayDevice]:
        """Load a single device from device_info.yaml (backward compatible)"""
        with open(f"{self.config_dir}/device_info.yaml", "r") as config_file:
            yaml_config = yaml.load(config_file, Loader=yaml.FullLoader)
        class_name_str = yaml_config["class_name"]
        vid = yaml_config["vid"]
        pid = yaml_config["pid"]
        device = usb.core.find(idVendor=vid, idProduct=pid)
        if device is not None:
            class_name = self.load_class(class_name_str)
            return class_name(self.config_dir)
        return None

    def load_device_by_id(self, device_id: str) -> Optional[LoadedDevice]:
        """
        Load a specific device by its unique ID (bus:address format).
        
        Args:
            device_id: Unique device identifier in "bus:address" format
            
        Returns:
            LoadedDevice dict with device instance and metadata, or None if not found
        """
        try:
            bus, address = map(int, device_id.split(":"))
        except ValueError:
            return None
        
        # Find the USB device by bus and address
        usb_device = usb.core.find(bus=bus, address=address)
        if usb_device is None:
            return None
        
        # Lazy import to avoid circular dependency
        supported_devices = _get_supported_devices()
        
        # Find matching supported device info
        for vid, pid, variants in supported_devices:
            if usb_device.idVendor == vid and usb_device.idProduct == pid:
                # Use first variant as default
                variant = variants[0]
                class_name = self.load_class(variant["class_name"])
                display_device = class_name(self.config_dir)
                
                return LoadedDevice(
                    device_id=device_id,
                    device=display_device,
                    vid=vid,
                    pid=pid,
                    bus=bus,
                    address=address,
                    width=variant["width"],
                    height=variant["height"],
                    class_name=variant["class_name"]
                )
        
        return None

    def load_all_devices(self) -> List[LoadedDevice]:
        """
        Load all connected supported devices.
        
        Returns:
            List of LoadedDevice dicts, each containing a device instance and metadata
        """
        loaded_devices = []
        
        # Lazy import to avoid circular dependency
        supported_devices = _get_supported_devices()
        
        for vid, pid, variants in supported_devices:
            # Find all USB devices matching this VID/PID
            devices = usb.core.find(
                find_all=True,
                idVendor=vid,
                idProduct=pid
            )
            
            for usb_device in devices:
                device_id = f"{usb_device.bus}:{usb_device.address}"
                
                try:
                    # Use first variant as default
                    variant = variants[0]
                    class_name = self.load_class(variant["class_name"])
                    display_device = class_name(self.config_dir)
                    
                    loaded_devices.append(LoadedDevice(
                        device_id=device_id,
                        device=display_device,
                        vid=vid,
                        pid=pid,
                        bus=usb_device.bus,
                        address=usb_device.address,
                        width=variant["width"],
                        height=variant["height"],
                        class_name=variant["class_name"]
                    ))
                except Exception:
                    # Skip devices that fail to load
                    continue
        
        return loaded_devices

    @staticmethod
    def load_class(full_class_name: str):
        try:
            module_name, class_name = full_class_name.rsplit(".", 1)
        except ValueError:
            raise ValueError(f"Invalid name : {full_class_name} (must contain dot)")

        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as e:
            raise ImportError(f"Impossible d’importer le module '{module_name}'") from e

        try:
            cls = getattr(module, class_name)
        except AttributeError as e:
            raise ImportError(f"Classe '{class_name}' introuvable dans '{module_name}'") from e

        return cls
