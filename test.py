# Note: Must be run as sudo/administrator because the ISNE is a protected device
from nitrolib import NitroEmulator

if __name__ == "__main__":
    emu = NitroEmulator()
    with open("test.nds", "rb") as fp:
        rom = fp.read()
    emu.load_nds_rom(rom)
