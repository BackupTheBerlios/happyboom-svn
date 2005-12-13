"""
Master Boot Record.


"""

from filter import Filter
from plugin import registerPlugin

class PartitionEntry(Filter):
    system_name = {
        0x00: "Unused",
        0x05: "Extended",
        0x06: "FAT16",
        0x0E: "FAT16",
        0x0B: "FAT32",
        0x0C: "FAT32",
        0x82: "Linux swap",
        0x83: "Linux"
    }
    
    def __init__(self, stream, parent):
        Filter.__init__(self, "default", "Default filter", stream, parent)
        bootable = self.read("bootable", "B", "Bootable flag (true if equals to 0x80)").value
        assert bootable in (0x00, 0x80)
        self.read("start_head", "B", "Starting head number of the partition")
        self.read("start_sector", "B", "Starting sector number of the partition")
        self.read("start_low_cylinder", "B", "Lower 8 bits of starting cylinder number of the partition")
        self.read("system", "B", "System indicator", post=self.postSystem)
        self.read("end_head", "B", "Ending head number of the partition")
        self.read("end_sector", "B", "Ending sector number of the partition")
        self.read("end_low_cylinder", "B", "Lower 8 bits of ending cylinder number of the partition")
        self.read("sector_before", "<L", "Number of sectors before this partition")
        self.read("sector_after", "<L", "Number of sectors in this partition")
        assert self.getSize() == 16

    def updateParent(self, parent):
        desc = "Partition entry (%s)" % self.type
        parent.description = desc
        self.setDescription(desc)        

    def postSystem(self, chunk):
        type = chunk.value
        self.type = PartitionEntry.system_name.get(type, "Unknow (%02X)" % type)
        return self.type      

class MasterBootRecordFilter(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "default", "Default filter", stream, parent)
        assert 512<=stream.getSize()
        jmp = self.read("jmp", "!1B", "Long jump (x86 assembler: EA)").value
        assert jmp == 0xEB
        self.read("to", "<H", "(Jump to) address")
        size = 446 - stream.tell()
        self.read("data", "%us" % size, "Raw data")
        self.readChild("partition[]", PartitionEntry)
        self.readChild("partition[]", PartitionEntry)
        self.readChild("partition[]", PartitionEntry)
        self.readChild("partition[]", PartitionEntry)
        id = self.read("id", "<H", "Identifier (0xAA55)").value
        assert id == 0xAA55

registerPlugin(MasterBootRecordFilter, "hachoir/master-boot-record")
