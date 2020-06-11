import sys
from argparse import ArgumentParser

from nitrolib.emulator.device import NitroEmulator


def main():
    parser = ArgumentParser()
    parser.add_argument("--device", '-d')
    command = parser.add_mutually_exclusive_group()
    command.add_argument("--loadrom", action="store_true")
    parser.add_argument("--rom", "-r", default=None)
    parser.add_argument("--debug-binary", "-b", default=None)
    args = parser.parse_args()
    if args.device == "emulator":
        if args.loadrom:
            assert args.rom is not None
            loadrom_emulator(args.rom, args.debug_binary)
    else:
        parser.print_help()


def loadrom_emulator(rom, debug):
    """ Loads an NDS ROM """

    with open(rom, "rb") as fp:
        rom_bin = fp.read()

    if debug is None:
        debug_bin = None
    else:
        with open(debug, "rb") as fp:
            debug_bin = fp.read()

    emulator = NitroEmulator()
    emulator.load_nds_rom(rom_bin, False, debug_rom=debug_bin)


def init_emulator(rom: bytes):
    """ For use in interactive mode """
    emulator = NitroEmulator()
    emulator.load_nds_rom(rom, True)
    return emulator


if __name__ == "__main__":
    main()
