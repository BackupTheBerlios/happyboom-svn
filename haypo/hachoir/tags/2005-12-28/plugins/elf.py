"""
ELF (Unix/BSD executable file format) parser.

Author: Victor Stinner
"""

from filter import OnDemandFilter, DeflateFilter
from chunk import FormatChunk, EnumChunk
from plugin import registerPlugin
from text_handler import hexadecimal

class ElfHeader(OnDemandFilter):
    machine_name = {
        0: "No machine",
        1: "AT&T WE 32100",
        2: "SPARC",
        3: "Intel 80386",
        4: "Motorolla 68000",
        5: "Motorolla 88000",
        7: "Intel 80860",
        8: "MIPS RS3000"
    }
    type_name = {
        0: "No file type",
        1: "Relocable file",
        2: "Executable file",
        3: "Shared object file",
        4: "Core file",
        0xFF00: "Processor-specific (0xFF00)",
        0xFFFF: "Processor-specific (0xFFFF)"
    }

    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "elf_header", "ELF header", stream, parent, "<")
        self.read("id", "Identifier", (FormatChunk, "string[4]"))
        assert self["id"] == "\x7FELF"
        self.read("class", "Class", (FormatChunk, "uint8"))
        self.read("encoding", "Encoding", (FormatChunk, "uint8"))
        self.read("file_version", "File version", (FormatChunk, "uint8"))
        self.read("pad", "Pad", (FormatChunk, "string[8]"))
        self.read("nb_ident", "Size of ident[]", (FormatChunk, "uint8"))
        self.read("type", "File type", (EnumChunk, "uint16", ElfHeader.type_name))
        self.read("machine", "Machine type", (EnumChunk, "uint16", ElfHeader.machine_name))
        self.read("version", "ELF format version", (FormatChunk, "uint32"))
        self.read("entry", "Number of entries", (FormatChunk, "uint32"))
        self.read("phoff", "Program header offset", (FormatChunk, "uint32"))
        self.read("shoff", "Section header offset", (FormatChunk, "uint32"))
        self.read("flags", "Flags", (FormatChunk, "uint32"))
        self.read("ehsize", "Elf header size (this header)", (FormatChunk, "uint16"))
        self.read("phentsize", "Program header entry size", (FormatChunk, "uint16"))
        self.read("phnum", "Program header entry count", (FormatChunk, "uint16"))
        self.read("shentsize", "Section header entry size", (FormatChunk, "uint16"))
        self.read("shnum", "Section header entre count", (FormatChunk, "uint16"))
        self.read("shstrndx", "Section header strtab index", (FormatChunk, "uint16"))

class SectionHeader32(OnDemandFilter):
    type_name = {
        8: "BSS"
    }
    
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "section_header", "Section header", stream, parent, "<")
        self.read("name", "Name", (FormatChunk, "uint32"))
        self.read("type", "Type", (EnumChunk, "uint32", SectionHeader32.type_name))
        self.read("flags", "Flags", (FormatChunk, "uint32"))
        self.read("VMA", "Virtual memory address", (FormatChunk, "uint32"), {"post": hexadecimal})
        self.read("LMA", "Logical memory address (in file)", (FormatChunk, "uint32"), {"post": hexadecimal})
        self.read("size", "Size", (FormatChunk, "uint32"), {"post": hexadecimal})
        self.read("link", "Link", (FormatChunk, "uint32"))
        self.read("info", "Information", (FormatChunk, "uint32"))
        self.read("addr_align", "Address alignment", (FormatChunk, "uint32"))
        self.read("entry_size", "Entry size", (FormatChunk, "uint32"))

    def updateParent(self, chunk):
        name = self["name"]
        type = self.getChunk("type").getDisplayData()
        desc = "Section header (name: %s, type: %s)" % (name, type)
        chunk.description = desc

class ProgramHeader32(OnDemandFilter):
    type_name = {
        3: "Dynamic library"
    }
    
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "prg_header", "Program header", stream, parent, "<")
        self.read("type", "Type", (EnumChunk, "uint16", ProgramHeader32.type_name))
        self.read("flags", "Flags", (FormatChunk, "uint16"))
        self.read("offset", "Offset", (FormatChunk, "uint32"))
        self.read("vaddr", "V. address", (FormatChunk, "uint32"), {"post": hexadecimal})
        self.read("paddr", "P. address", (FormatChunk, "uint32"), {"post": hexadecimal})
        self.read("file_size", "File size", (FormatChunk, "uint32"))
        self.read("mem_size", "Memory size", (FormatChunk, "uint32"))
        self.read("align", "Alignement", (FormatChunk, "uint32"))
        self.read("padding", "(padding?)", (FormatChunk, "uint32"))

    def updateParent(self, chunk):
        type = self.getChunk("type").getDisplayData() 
        chunk.description = "Program Header (%s)" % type

def seek(filter, stream, offset):
    current = stream.tell()
    if current != offset:
        filter.read("padding[]", "Padding", (FormatChunk, "string[%u]" % (offset-current)))

def sortSection(a, b):
    return int(a["offset"] - b["offset"])

class Section(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "elf_section", "Elf section", stream, parent, "<")
        # TODO ...
        self.read("raw", "Raw data", (FormatChunk, "string[%u]" % stream.getSize()))
        
class Sections(OnDemandFilter):
    def __init__(self, stream, parent, sections):
        OnDemandFilter.__init__(self, "elf_sections", "ELF sections", stream, parent, "<")
        for section in sections:
            ofs = section["offset"]
            size = section["file_size"]
            if size != 0:
                sub = stream.createSub(ofs, size)
                #self.read("section[]", "Section", (DeflateFilter, sub, size, Section))
                chunk = self.doRead("section[]", "Section", (Section,), {"stream": sub}) 
            else:
                chunk = self.doRead("section[]", "Section", (FormatChunk, "string[0]"))
            chunk.description = "ELF section (in file: %s..%s)" % (ofs, ofs+size)

class ElfFile(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "elf_file", "ELF file", stream, parent, "<")
        elf = self.doRead("header", "Header", (ElfHeader,))
        sections = []
        for i in range(0, elf["phnum"]):
            section = self.doRead("prg_header[]", "Program header", (ProgramHeader32,))
            sections.append(section)

#        i = 1
#        for section in sections:
#            print "Section %u: type %u, data in %u..%u " % (i, section["type"], section["offset"], section["offset"]+section["file_size"])
#            i = i + 1
            
        size = elf["shoff"] - stream.tell()
        chunk = self.doRead("data", "Data", (DeflateFilter, stream, size, Sections, sections))
        chunk.description = "Sections (use an evil hack to manage share same data on differents parts)"
        assert stream.tell() == elf["shoff"]

        for i in range(0, elf["shnum"]):
            chunk = self.doRead("section_header[]", "Section header", (SectionHeader32,))
            assert chunk.getSize() == 40

registerPlugin(ElfFile, ["application/x-executable", "application/x-object", "application/x-sharedlib"])
