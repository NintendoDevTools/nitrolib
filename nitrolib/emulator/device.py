from binascii import hexlify

from pkg_resources import resource_stream

from usb.core import find
from usb.util import find_descriptor, claim_interface

from nitrolib.util import partition
from nitrolib.device import NitroDevice, DeviceNotFound
from nitrolib.emulator.enums import WriteCommandType, MemoryRegion, ReadCommandType


class NitroEmulator(NitroDevice):
    is_little_endian = True

    def __init__(self):
        super().__init__("IS-NITRO-Emulator")
        self.device = find(idVendor=0x0F6e, idProduct=0x0404)

        if self.device is None:
            raise DeviceNotFound(self)

        if self.debug:
            self.print_configurations()

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

        self.isid = resource_stream(__name__, "../resources/isid.bin").read()
        self.debugger_code = resource_stream(__name__, "../resources/debugger_code.bin").read()

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

    def read(self, command: ReadCommandType, region: MemoryRegion, address: int, length: int) -> bytes:
        packed = self.encode("HBBIII",
                             command.value,
                             0x11,  # Read
                             region.value,  # TODO: Determine based on CommandType
                             address,
                             length,
                             0)  # Padding?
        self._usb_write(packed)
        data = self._usb_read(length)
        if self.debug:
            print(f"Read {hex(command.value)} {hex(region.value)}\nAt {hex(address)} Size {hex(length)}")
            print(hexlify(data[:0x100]).decode())
            print("-" * 10)
        return data

    def write(self, command: WriteCommandType, region: MemoryRegion, address: int, data: bytes):
        packed = self.encode("HBBIII",
                             command.value,
                             0x10,  # Write
                             region.value,
                             address,
                             len(data),
                             0)  # Padding?
        self._usb_write(packed)
        self._usb_write(data)
        if self.debug:
            print(f"Write {hex(command.value)} {hex(region.value)}\nAt {hex(address)} Size {hex(len(data))}")
            print(hexlify(data[:0x100]).decode())
            print("-"*10)

    # Public methods

    def full_reset(self):
        self.write(WriteCommandType.FULL_RESET, MemoryRegion.CONTROL, 0, b'\x81\xF2')

    def processor_stop(self):
        self.write(WriteCommandType.CURRENT_PROCESSOR, MemoryRegion.CONTROL, 0, b'\x81\x00\x01\x00')

    def processor_start(self):
        self.write(WriteCommandType.CURRENT_PROCESSOR, MemoryRegion.CONTROL, 0, b'\x81\x00\x00\x00')

    def select_arm9(self):
        self.write(WriteCommandType.SELECT_PROCESSOR, MemoryRegion.CONTROL, 0, b'\x8b\x00\x00\x00')

    def select_arm7(self):
        self.write(WriteCommandType.SELECT_PROCESSOR, MemoryRegion.CONTROL, 0, b'\x8b\x00\x01\x00')

    def _slot1_toggle(self, on: bool):
        self.write(WriteCommandType.UNKNOWN_AD, MemoryRegion.CONTROL, 0,
                   b'\xAD\x00\x00\x00'
                   b'\x0A\x00\x00\x00' +
                   self.encode('I', int(on)) +
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00')

    def slot1_on(self):
        self._slot1_toggle(True)

    def slot1_off(self):
        self._slot1_toggle(False)

    def slot2_on(self):
        self.write(WriteCommandType.UNKNOWN_AD, MemoryRegion.CONTROL, 0,
                   b'\xAD\x00\x00\x00'
                   b'\x02\x00\x00\x00'
                   b'\x01\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00')
        self.write(WriteCommandType.UNKNOWN_AD, MemoryRegion.CONTROL, 0,
                   b'\xAD\x00\x00\x00'
                   b'\x04\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00')

    def slot2_off(self):
        self.write(WriteCommandType.UNKNOWN_AD, MemoryRegion.CONTROL, 0,
                   b'\xAD\x00\x00\x00'
                   b'\x02\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00'
                   b'\x00\x00\x00\x00')

    def write_slot1(self, address, data):
        self.write(WriteCommandType.WRITE_MAIN_MEMORY, MemoryRegion.NDS, address, data)

    def read_slot1(self, address, length):
        self.read(ReadCommandType.READ_MAIN_MEMORY, MemoryRegion.NDS, address, length)

    def write_slot2(self, address, data):
        self.write(WriteCommandType.WRITE_MAIN_MEMORY, MemoryRegion.GBA, address, data)

    def read_slot2(self, address, length):
        self.read(ReadCommandType.READ_MAIN_MEMORY, MemoryRegion.GBA, address, length)

    def read_nec(self, address, unit, count):
        header = self.encode("BBHI",
                             0x25,
                             unit,
                             count,
                             address)
        self.write(WriteCommandType.READ_NEC_CONTROL, MemoryRegion.CONTROL, 0, header)
        return self.read(ReadCommandType.READ_NEC, MemoryRegion.CONTROL, 0, 8)

    def write_nec(self, address, unit, count, data):
        header = self.encode("BBHI",
                             0x26,
                             unit,
                             count,
                             address)
        self.write(WriteCommandType.WRITE_NEC, MemoryRegion.CONTROL, 0, header + data)

    def _write_video_register(self, register, data):
        self.write_nec(0x8000030, 2, 1, self.encode('BB', register, 0))
        self.write_nec(0x8000034, 2, 1, self.encode('BB', data & 0xFF, 0))
        self.write_nec(0x8000036, 2, 1, self.encode('BB', data >> 8, 0))

    def trigger_fiq(self):
        self.write(WriteCommandType.FIQ, MemoryRegion.CONTROL, 0, b'\xaa\x00\x01\x00')
        self.write(WriteCommandType.FIQ, MemoryRegion.CONTROL, 0, b'\xaa\x00\x00\x00')

    def load_nds_rom(self, rom: bytes, to_firmware: bool = False, enable_gba: bool = False, debug_rom: bytes = None):
        debug_rom = debug_rom or self.debugger_code
        self.full_reset()
        self.processor_stop()
        self.slot1_off()
        self.slot2_off()

        # Gericom/ISNitroController uses RESET_STATE for this, but that doesn't seem to do much on my end.
        # Maybe related to being a Lite model?

        # Something with the slots based on what I can find?

        # Write rom chunked
        rom_chunk_size = 1 << 16  # 65536 bytes at a time
        for i, rom_chunk in enumerate(partition(rom, rom_chunk_size)):
            print(hex(i * rom_chunk_size), "/", hex(len(rom)))
            self.write_slot1(i * rom_chunk_size, rom_chunk)

        # TODO: Look into whether this is needed
        # self.write(MemoryRegion.EMULATION_MEMORY, InteractionType.NDS, 0, rom[:0x160])

        self.write_slot1(0x0FF80000, debug_rom)
        self.write(WriteCommandType.WRITE_MAIN_MEMORY, MemoryRegion.GBA, 0, self.isid)

        if not to_firmware:
            self.write_slot1(
                0x160,
                self.encode("IIII",
                            0x8FF80000,         # Debug rom offset
                            len(debug_rom),     # Debug rom size
                            0x02700000,         # ARM9 Entry
                            0x02700004))        # ARM7 Entry

        if enable_gba:
            self.slot2_on()
        self.slot1_on()
        self.processor_start()

    def load_gba_rom(self):
        self.full_reset()
        self.slot2_off()
        self.processor_stop()
        self.slot2_on()
        self.processor_start()

    def enable_video(self):
        pass
