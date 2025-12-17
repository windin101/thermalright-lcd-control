# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb
import pathlib
import time
from abc import abstractmethod, ABC

import usb
from PIL import Image

from .config_loader import ConfigLoader
from .generator import DisplayGenerator
from ...common.logging_config import LoggerConfig


class DisplayDevice(ABC):
    _generator: DisplayGenerator = None
    dev = None
    report_id = bytes([0x00])

    def __init__(self, vid, pid, chunk_size, width, height, config_dir: str, *args, **kwargs):
        self.vid = vid
        self.pid = pid
        self.chunk_size = chunk_size
        self.height = height
        self.width = width
        self.header = self.get_header()
        self.config_file = f"{config_dir}/config_{width}{height}.yaml"
        self.last_modified = pathlib.Path(self.config_file).stat().st_mtime_ns
        self.logger = self.logger = LoggerConfig.setup_service_logger()
        self._build_generator()
        self.logger.debug(f"DisplayDevice initialized with header: {self.header}")

    def _build_generator(self) -> DisplayGenerator:
        config_loader = ConfigLoader()
        config = config_loader.load_config(self.config_file, self.width, self.height)
        return DisplayGenerator(config)

    def _get_generator(self) -> DisplayGenerator:
        if self._generator is None:
            self.logger.info(f"No generator found, reloading from {self.config_file}")
            self._generator = self._build_generator()
            return self._generator
        elif pathlib.Path(self.config_file).stat().st_mtime_ns > self.last_modified:
            self.logger.info(f"Config file updated: {self.config_file}")
            self.last_modified = pathlib.Path(self.config_file).stat().st_mtime_ns
            self._generator = self._build_generator()
            self.logger.info(f"Display device generator reloaded from {self.config_file}")
            return self._generator
        else:
            return self._generator

    def _encode_image(self, img: Image) -> bytearray:
        width, height = img.size
        out = bytearray()
        for x in range(width):
            for y in range(height-1, -1, -1):
                r, g, b = img.getpixel((x, y))
                val565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                hi = (val565 >> 8) & 0xFF
                lo = val565 & 0xFF
                out.extend((lo, hi))
        return out

    @abstractmethod
    def get_header(self, *args, **kwargs):
        pass

    def reset(self):
        # Find device (ex. Winbond 0416:5302)
        dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        if dev is None:
            raise ValueError("Display device not found")

        # Reset USB device
        dev.reset()
        self.logger.info("Display device reinitialised via USB reset")

    def _prepare_frame_packets(self, img_bytes: bytes):
        frame_packets = []
        for i in range(0, len(img_bytes), self.chunk_size):
            chunk = img_bytes[i:i + self.chunk_size]
            if len(chunk) < self.chunk_size:
                chunk += b"\x00" * (self.chunk_size - len(chunk))
            frame_packets.append(self.report_id + chunk)
        return frame_packets

    def run(self):
        self.logger.info("Display device running")
        while True:
            try:
                img, delay_time = self._get_generator().get_frame_with_duration()
                header = self.get_header()
                img_bytes = header + self._encode_image(img)
                frame_packets = self._prepare_frame_packets(img_bytes)
                for packet in frame_packets:
                    self.send_packet(packet)
                time.sleep(max(delay_time, 0.2))
            except Exception as e:
                self.logger.error(f"Error in display device run loop: {e}")
                time.sleep(1.0)  # Wait before retrying

    @abstractmethod
    def send_packet(self, packet: bytes):
        pass
