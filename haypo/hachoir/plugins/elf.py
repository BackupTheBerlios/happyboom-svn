"""
ELF filter.
Author: Victor Stinner
"""

from filter import Filter, DeflateFilter
from plugin import registerPlugin

def processAddr(chunk):
    return "%08X" % chunk.value

class ElfHeader(Filter):
    machine = {
        0: "No machine",
        1: "AT&T WE 32100",
        2: "SPARC",
        3: "Intel 80386",
        4: "Motorolla 68000",
        5: "Motorolla 88000",
        7: "Intel 80860",
        8: "MIPS RS3000"
    }

    def __init__(self, stream, parent):
        Filter.__init__(self, "elf_header", "ELF header", stream, parent)
        self.read("id", "4s", "Identifier")
        assert self["id"] == (chr(127) + "ELF")
        self.read("class", "B", "Class")
        self.read("encoding", "B", "Encoding")
        self.read("file_version", "B", "File version")
        self.read("pad", "8s", "Pad")
        self.read("nident", "B", "Size of ident[]")
        self.read("type", "<H", "File type", post=self.getType)
        self.read("machine", "<H", "Machine type", post=self.getMachine)
        self.read("version", "<L", "ELF format version")
        self.read("entry", "<L", "Number of entries")
        self.read("phoff", "<L", "Program header offset")
        self.read("shoff", "<L", "Section header offset")
        self.read("flags", "<L", "Flags")
        self.read("ehsize", "<H", "Elf header size (this header)")
        self.read("phentsize", "<H", "Program header entry size")
        self.read("phnum", "<H", "Program header entry count")
        self.read("shentsize", "<H", "Section header entry size")
        self.read("shnum", "<H", "Section header entre count")
        self.read("shstrndx", "<H", "Section header strtab index")

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
        return ElfHeader.machine.get(type, "Unknow machine (%u)" % type)

class SectionHeader32(Filter):
    types = {
        8: "BSS"
    }
    
    def __init__(self, stream, parent):
        Filter.__init__(self, "section_header", "Section header", stream, parent)
        self.read("name", "<L", "")
        self.read("type", "<L", "")
        self.read("flags", "<L", "")
        self.read("VMA", "<L", "Virtual memory address")#, post=processAddr)
        self.read("LMA", "<L", "Logical memory address (in file)")#, post=processAddr)
        self.read("size", "<L", "", post=processAddr)
        self.read("link", "<L", "")
        self.read("info", "<L", "")
        self.read("addralign", "<L", "")
        self.read("entsize", "<L", "")

    def getType(self):
        type = self["type"]
        return SectionHeader32.types.get(type, "unknow type=%u" % type)

    def getName(self):
        # TODO: Look in symbol name
        return self["name"]

    def updateParent(self, chunk):
        desc = "Section header (name: %s, type: %s)" % (self.getName(), self.getType())
        chunk.description = desc
        self.setDescription(desc)

class ProgramHeader32(Filter):
    type = {
        3: "Dynamic library"
    }
    
    def __init__(self, stream, parent):
        Filter.__init__(self, "prg_header", "Program header", stream, parent)
        self.read("type", "<H", "")
        self.read("flags", "<H", "")
        self.read("offset", "<L", "")
        self.read("vaddr", "<L", "", post=processAddr)
        self.read("paddr", "<L", "", post=processAddr)
        self.read("file_size", "<L", "")
        self.read("mem_size", "<L", "")
        self.read("align", "<L", "")
        self.read("padding", "<L", "(padding?)")

    def getType(self):
        type = self["type"]
        return ProgramHeader32.type.get(type, "unknow, %u" % type)

    def updateParent(self, chunk):
        desc = "Program Header (%s)" % self.getType() 
        self.setDescription(desc)
        chunk.description = desc 

def seek(filter, stream, offset):
    current = stream.tell()
    if current != offset:
        filter.read("padding[]", "%us" % (offset-current), "Padding")

def sortSection(a, b):
    return int(a["offset"] - b["offset"])

class Section(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "elf_section", "Elf section", stream, parent)
        self.read("raw", "{@end@}s", "Raw data")
        
class Sections(Filter):
    def __init__(self, stream, parent, sections):
        Filter.__init__(self, "elf_sections", "ELF sections", stream, parent)
        for section in sections:
            ofs = section["offset"]
            size = section["file_size"]
            sub = stream.createSub(ofs, size)
            #self.readChild("section[]", DeflateFilter, sub, size, Section) 
            chunk = self.readStreamChild("section[]", sub, Section) 
            chunk.description = "ELF section (in file: %s..%s)" % (ofs, ofs+size)

class ElfFile(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "elf_file", "ELF file", stream, parent)
        self.readChild("elf_header", ElfHeader)
        elf = self["elf_header"]
        sections = []
        for i in range(0, elf["phnum"]):
            section = self.readChild("prg_header[]", ProgramHeader32)
            sections.append(section.getFilter())

        i = 1
        for section in sections:
            print "Section %u: type %u, data in %u..%u " % (i, section["type"], section["offset"], section["offset"]+section["file_size"])
            i = i + 1
            
        if False:
            sections.sort( sortSection )
            for section in sections:
                if section["type"] != 6 and section["offset"] != 0:
                    print "  DO Section: %u..%u" % (section["offset"], section["offset"]+section["file_size"])
                    seek(self, stream, section["offset"])
                    print stream.tell(), section["offset"]
#                    assert stream.tell() == section["offset"]
                    self.read("section[]", "%us" % section["file_size"], "")
            seek(self, stream, elf["shoff"])
            assert stream.tell() == elf["shoff"]            
        else:
            size = elf["shoff"] - stream.tell()
            newstream = stream.clone()
            chunk = self.readChild("data", DeflateFilter, newstream, size, Sections, sections) 
            chunk.description = "Sections (use an evil hack to manage share same data on differents parts)"
            assert stream.tell() == elf["shoff"]
        for i in range(0, elf["shnum"]):
            chunk = self.readChild("section_header[]", SectionHeader32)
            assert chunk.size == 40

registerPlugin(ElfFile, "application/x-executable")
