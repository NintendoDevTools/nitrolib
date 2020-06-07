import sys

from nitrolib.emulator.device import NitroEmulator


def loadrom_emulator():
    """ Loads an NDS ROM """
    filename = sys.argv[1]
    if any(filename.endswith(c) for c in (".nds", ".srl", ".rom")):
        with open(filename, "rb") as fp:
            data = fp.read()
        # TODO: Check if rom is encrypted, error if not
        emulator = NitroEmulator()
        emulator.load_nds_rom(data, sys.argv[2] == "true")


def init_emulator(rom: bytes):
    """ For use in interactive mode """
    emulator = NitroEmulator()
    emulator.load_nds_rom(rom, True)
    return emulator
