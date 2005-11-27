"""
ELF filter.
Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin

class ELF_Header(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "default", "default", stream, parent)
        self.read("id", "4s", "Identifier")
        good_id = chr(127) + "ELF"
        assert self["id"] == good_id 
        self.read("class", "B", "Class")
        self.read("encoding", "B", "Encoding")
        self.read("file_version", "B", "File version")
        self.read("pad", "8s", "Pad")
        self.read("nident", "B", "Size of ident[]")
        self.read("type", "<H", "File fype", post=self.getType)
        self.read("machine", "<H", "Machine type", post=self.getMachine)
        self.read("version", "<L", "Version of ELF")
        self.read("entry", "<L", "Number of entries")
        self.read("phoff", "<L", "PH offset")
        self.read("shoff", "<L", "SH offset")
        self.read("flags", "<L", "Flags")
        self.read("ehsize", "<H", "EH size")
        self.read("phentsize", "<H", "PH entry size")
        self.read("phnum", "<H", "PH entry count")
        self.read("shentsize", "<H", "SH entry size")
        self.read("shnum", "<H", "SH entre count")
        self.read("shstrndx", "<H", "SH strtab index")

    def getType(self, chunk):
        type = chunk.value
        types = {
            0: "No file type",
            1: "Relocable file",
            2: "Executable file",
            3: "Shared object file",
            4: "Core file",
            0xFF00: "Processor-specific (0xFF00)",
            0xFFFF: "Processor-specific (0xFFFF)"
        }
        return types.get(type, "Unknow type (%u)" % type)

    def getMachine(self, chunk):
        type = chunk.value
        types = {
            0: "No machine",
            1: "AT&T WE 32100",
            2: "SPARC",
            3: "Intel 80386",
            4: "Motorolla 68000",
            5: "Motorolla 88000",
            7: "Intel 80860",
            8: "MIPS RS3000"
        }
        return types.get(type, "Unknow machine (%u)" % type)

class ELF_Filter(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "default", "default", stream, parent)
        self.readChild("header", ELF_Header)

registerPlugin(ELF_Filter, "application/x-executable")
