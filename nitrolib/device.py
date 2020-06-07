from abc import ABC
from struct import pack

from usb.core import Device


class DeviceNotFound(Exception):
    def __init__(self, device: NitroDevice):
        super().__init__(f"Unable to find device: {device.device_name}")


class NitroDevice(ABC):
    is_little_endian: bool
    device: Device

    def __init__(self, device_name: str):
        self.device_name = device_name

    def print_configurations(self):
        for cfg in self.device:
            print(cfg)
        print("-"*30)

    def encode(self, fmt: str, *args) -> bytes:
        return pack([">", "<"][self.is_little_endian] + fmt, *args)
