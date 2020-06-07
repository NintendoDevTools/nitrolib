from enum import Enum


class CommandType(Enum):
    EMULATION_MEMORY = 0x00
    FULL_RESET = 0x81
    RESET_STATE = 0x83
    CURRENT_PROCESSOR = 0x8A
    SELECT_PROCESSOR = 0x8B
    UNKNOWN_AD = 0xAD
    UNKNOWN_AE = 0xAE


class MemoryRegion(Enum):
    CONTROL = 0
    NDS = 1  # ?
    GBA = 2  # ?
