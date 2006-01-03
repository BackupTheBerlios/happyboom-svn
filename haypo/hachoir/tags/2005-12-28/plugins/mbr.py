"""
Master Boot Record.


"""

from filter import OnDemandFilter
from plugin import registerPlugin
from chunk import EnumChunk, FormatChunk
from tools import humanFilesize

class PartitionEntry(OnDemandFilter):
    system_name = {
        0x00: "Unused",
        0x05: "Extended",
        0x06: "FAT16",
        0x0B: "FAT32",
        0x0C: "FAT32 (LBA)",
        0x0E: "FAT16 (LBA)",
        0x82: "Linux swap",
        0x83: "Linux (ext2/ext3)"
    }
    
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "default", "Default filter", stream, parent, "<")
        self.read("bootable", "Bootable flag (true if equals to 0x80)", (FormatChunk, "uint8"))
        assert self["bootable"] in (0x00, 0x80)
        self.read("start_head", "Starting head number of the partition", (FormatChunk, "uint8"))
        self.read("start_sector", "Starting sector number of the partition", (FormatChunk, "uint8"))
        self.read("start_low_cylinder", "Lower 8 bits of starting cylinder number of the partition", (FormatChunk, "uint8"))
        self.read("system", "System indicator", (EnumChunk, "uint8", PartitionEntry.system_name))
        self.read("end_head", "Ending head number of the partition", (FormatChunk, "uint8"))
        self.read("end_sector", "Ending sector number of the partition", (FormatChunk, "uint8"))
        self.read("end_low_cylinder", "Lower 8 bits of ending cylinder number of the partition", (FormatChunk, "uint8"))
        self.read("LBA", "LBA (number of sectors before this partition)", (FormatChunk, "uint32"))
        self.read("size", "Size (block count)", (FormatChunk, "uint32"))

    def updateParent(self, chunk):
        desc = "Partition entry: "
        system = self.getChunk("system")
        if system.value != 0:
            type = self.getChunk("system").getDisplayData()
            block_size = self.getParent().block_size
            size = self["size"] * block_size
            desc += "%s, %s" % (type, humanFilesize(size))
        else:
            desc += "(unused)"
        chunk.description = desc

class MasterBootRecord(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "default", "Default filter", stream, parent, "<")
        # TODO: Get right block size!
        self.block_size = 512
        assert 512<=stream.getSize()
        self.read("jmp", "Jump instruction", (FormatChunk, "uint8"))
        assert self["jmp"] in (0xEB, 0xFA)
        size = 446 - stream.tell()
        self.read("data", "Raw data", (FormatChunk, "string[%u]" % size))
        for i in range(0,4):
            self.read("partition[]", "Partition entry", (PartitionEntry,))
        self.read("id", "Identifier (0xAA55)", (FormatChunk, "uint16"))
        assert self["id"] == 0xAA55

registerPlugin(MasterBootRecord, "hachoir/master-boot-record")
