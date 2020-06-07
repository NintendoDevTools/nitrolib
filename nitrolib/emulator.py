from pkg_resources import resource_stream

from usb.core import find
from usb.util import find_descriptor, claim_interface

from nitrolib.util import partition
from nitrolib.device import NitroDevice, DeviceNotFound
from nitrolib.enums import MemoryRegion, InteractionType


class NitroEmulator(NitroDevice):
    is_little_endian = True

    def __init__(self):
        super().__init__("IS-NITRO-Emulator")
        self.device = find(idVendor=0x0F6e, idProduct=0x0404)

        if self.device is None:
            raise DeviceNotFound(self)

        self.device.set_configuration()
        # self.device.reset()  # Prevent weird timeouts when used twice

        config = self.device.get_active_configuration()
        interface = config[(0, 0)]

        # Claim interface
        if self.device.is_kernel_driver_active(interface.iInterface):
            self.device.detach_kernel_driver(interface.iInterface)
            claim_interface(self.device, interface.iInterface)

        self.endpoint_out = find_descriptor(interface, bEndpointAddress=0x01)  # Bulk Out
        self.endpoint_in = find_descriptor(interface, bEndpointAddress=0x82)  # Bulk in
        # self.endpoint_debug = find_descriptor(interface, bEndpointAddress=0x83)  # Bulk in 2?

        assert self.endpoint_out is not None
        assert self.endpoint_in is not None

        self.isid = resource_stream(__name__, "resources/isid.bin").read()
        self.debugger_code = resource_stream(__name__, "resources/debugger_code.bin").read()

        """
        self.do_th = True
        def read_debug():
            while self.do_th:
                try:
                    data = bytes(self.endpoint_debug.read(self.endpoint_debug.wMaxPacketSize))
                    print(data)
                except USBError:
                    pass  # ignore

        self.th = Thread(target=read_debug)
        self.th.start()
        """

    # Device utils

    def _usb_write(self, data: bytes):
        max_size = self.endpoint_out.wMaxPacketSize
        packets = partition(data, max_size)
        for packet in packets:
            written = self.endpoint_out.write(packet)
            assert written == len(packet)

    def _usb_read(self, size: int) -> bytes:
        data = b''
        while len(data) < size:
            data += bytes(self.endpoint_in.read(size - len(data)))
        return data

    def read(self, region: MemoryRegion, interact: InteractionType, address: int, length: int) -> bytes:
        packed = self.encode("HBBIII",
                             region.value,
                             0x11,  # Read
                             interact.value,  # TODO: Determine based on CommandType
                             address,
                             length,
                             0)  # Padding?
        self._usb_write(packed)
        return self._usb_read(length)

    def write(self, region: MemoryRegion, interact: InteractionType, address: int, data: bytes):
        packed = self.encode("HBBIII",
                             region.value,
                             0x10,  # Write
                             interact.value,
                             address,
                             len(data),
                             0)  # Padding?
        self._usb_write(packed)
        self._usb_write(data)

    # Public methods

    def full_reset(self):
        self.write(MemoryRegion.FULL_RESET, InteractionType.CONTROL, 0, b'\x81\xF2')

    def processor_stop(self):
        self.write(MemoryRegion.CURRENT_PROCESSOR, InteractionType.CONTROL, 0, b'\x81\x00\x01\x00')

    def processor_start(self):
        self.write(MemoryRegion.CURRENT_PROCESSOR, InteractionType.CONTROL, 0, b'\x81\x00\x00\x00')

    def select_arm9(self):
        self.write(MemoryRegion.CURRENT_PROCESSOR, InteractionType.CONTROL, 0, b'\x8b\x00\x00\x00')

    def select_arm7(self):
        self.write(MemoryRegion.CURRENT_PROCESSOR, InteractionType.CONTROL, 0, b'\x8b\x00\x01\x00')

    def slot1_on(self):
        self.write(MemoryRegion.UNKNOWN_AD, InteractionType.CONTROL, 0,
                   b'\xAD\x00\x00\x00'
                   b'\x0A\x00\x00\x00'
                   b'\x01\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00')

    def slot1_off(self):
        self.write(MemoryRegion.UNKNOWN_AD, InteractionType.CONTROL, 0,
                   b'\xAD\x00\x00\x00'
                   b'\x0A\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00')

    def load_rom(self, rom: bytes, to_firmware: bool = False):
        self.full_reset()
        self.slot1_off()

        # Gericom/ISNitroController uses RESET_STATE for this, but that doesn't seem to do much on my end.
        # Maybe related to being a Lite model?
        self.processor_stop()

        # Something with the slots based on what I can find?
        self.write(MemoryRegion.UNKNOWN_AD, InteractionType.CONTROL, 0,
                   b'\xAD\x00\x00\x00'
                   b'\x09\x00\x00\x00'
                   b'\xAD\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00')

        # Write rom chunked
        rom_chunk_size = 1 << 16  # 65536 bytes at a time
        for i, rom_chunk in enumerate(partition(rom, rom_chunk_size)):
            print(hex(i * rom_chunk_size), "/", hex(len(rom)))
            self.write(MemoryRegion.EMULATION_MEMORY, InteractionType.NDS, i * rom_chunk_size, rom_chunk)

        # TODO: Look into whether this is needed
        self.write(MemoryRegion.EMULATION_MEMORY, InteractionType.NDS, 0, rom[:0x160])

        self.write(MemoryRegion.EMULATION_MEMORY, InteractionType.NDS, 0x0FF80000, self.debugger_code)
        self.write(MemoryRegion.EMULATION_MEMORY, InteractionType.GBA, 0, self.isid)

        if not to_firmware:
            self.write(MemoryRegion.EMULATION_MEMORY, InteractionType.NDS, 0x160,
                       self.encode("IIII",
                                   0x8FF80000,                  # Debug rom offset
                                   len(self.debugger_code),     # Debug rom size
                                   0x02700000,                  # Debug rom - ram address to load into
                                   0x02700004))                 # Unknown?

        self.slot1_on()
        self.processor_start()

        # Screens turn off and on, then hangs on white screen here with a loud "click" sound.
        # SYSTEM1 and POWER lights are turned on.
        # If booting to firmware, buttons are not pressable
