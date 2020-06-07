from enum import Enum


class ReadCommandType(Enum):
    READ_MAIN_MEMORY = 0x00
    READ_NEC = 0x1A


class WriteCommandType(Enum):
    WRITE_MAIN_MEMORY = 0x00
    READ_NEC_CONTROL = 0x25
    WRITE_NEC = 0x26
    FULL_RESET = 0x81
    RESET_STATE = 0x83
    CURRENT_PROCESSOR = 0x8A
    SELECT_PROCESSOR = 0x8B
    FIQ = 0xAA
    UNKNOWN_AD = 0xAD
    UNKNOWN_AE = 0xAE


class MemoryRegion(Enum):
    CONTROL = 0
    NDS = 1  # ?
    GBA = 2  # ?
