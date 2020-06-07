IS-NITRO-Emulator
=================

Endpoints:

- 0x01 -> Bulk Out
- 0x82 -> Bulk In
- 0x83 -> Bulk In (Purpose unknown)

Protocol structure:

+---------+------+--------+-------------------+-------------------+-------------------+
| command | mode | region |      address      |       length      |      padding      |
+====+====+======+========+====+====+====+====+====+====+====+====+====+====+====+====+
| 00 | 00 |  00  |   00   | 00 | 00 | 00 | 00 | 00 | 00 | 00 | 00 | 00 | 00 | 00 | 00 |
+----+----+------+--------+----+----+----+----+----+----+----+----+----+----+----+----+

- Command -> Action to perform (See nitrolib.emulator.enums.CommandType)
- Mode -> Read (0x10) or Write (0x11)
- Region -> Memory region to affect (See nitrolib.emulator.enums.MemoryRegion)
- Address -> Memory address in the specified region to affect
- Length -> Length of the data to read/write
- Padding -> null bytes for padding
