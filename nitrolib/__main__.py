import sys

from nitrolib.emulator import NitroEmulator


def loadrom_emulator():
    filename = sys.argv[1]
    if any(filename.endswith(c) for c in (".nds", ".srl", ".rom")):
        with open(filename, "rb") as fp:
            data = fp.read()
        # TODO: Check if rom is encrypted
        emulator = NitroEmulator()
        emulator.load_rom(data, sys.argv[2] == "true")
