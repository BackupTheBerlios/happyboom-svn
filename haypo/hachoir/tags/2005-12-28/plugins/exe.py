"""
EXE filter.

Status: read ms-dos and pe headers
Todo: support resources ... and disassembler ? :-)
Author: Victor Stinner
"""

from filter import OnDemandFilter
from plugin import registerPlugin
from chunk import FormatChunk, EnumChunk, BitsStruct, BitsChunk
from text_handler import unixTimestamp
from tools import humanFilesize

class PE_ResourceData(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "pe_rsrc_data", "PE resource data", stream, parent, "<")
        self.read("offset", "Offset", (FormatChunk, "uint32"))
        self.read("size", "Size", (FormatChunk, "uint32"))
        self.read("page_code", "Page code (language)", (FormatChunk, "uint32"))
        self.read("language", "Page code (language)", (FormatChunk, "<l"))
        self.read("reserved", "Reserverd", (FormatChunk, "!L"))

class PE_ResourceEntry(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "pe_rsrc_entry", "PE resource entry", stream, parent, "<")
        self.read("id", "ID or name", (FormatChunk, "uint32"))
        self.read("offset", "Offset", (FormatChunk, "uint32"))
        
class PE_ResourceDirectory(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "pe_rsrc_dir", "PE resource directory", stream, parent, "<")
        self.offset_res_section = stream.tell()
        self.read("option", "Options", (FormatChunk, "uint32"))
        self.read("creation_date", "Creation date", (FormatChunk, "uint32"), {"post": unixTimestamp})
        self.read("maj_ver", "Major version", (FormatChunk, "uint16"))
        self.read("named_entries", "Named entries", (FormatChunk, "uint16"))
        self.read("indexed_entries", "Indexed entries", (FormatChunk, "uint16"))

        self.read("xxx", "???", (FormatChunk, "string[%u]" % 0x10))

        n = (self["named_entries"] + self["indexed_entries"])
        for i in range(0,n):
            self.read("item[]", "PE resource entry", (PE_ResourceEntry,))

class PE_Section(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "pe_section", "PE section", stream, parent, "<")
        self.read("name", "Name", (FormatChunk, "string[8]"))
        # TODO: use chunk post proces
        self.name = self["name"].strip(" \0")
        self.read("rva", "RVA", (FormatChunk, "uint32"))
        self.read("size", "Size", (FormatChunk, "uint32"))
        self.read("file_size", "File size", (FormatChunk, "uint32"))
        self.read("file_offset", "File offset", (FormatChunk, "uint32"))
        self.read("reloc_ptr", "Relocation pointer", (FormatChunk, "uint32"))
        self.read("lines_ptr", "File line numbers pointer", (FormatChunk, "uint32"))
        self.read("nb_reloc", "Number of relocations", (FormatChunk, "uint16"))
        self.read("nb_lines", "Number of file line", (FormatChunk, "uint16"))
        self.read("options", "Options", (FormatChunk, "uint32"))

    def updateParent(self, chunk):
        name = self["name"].strip("\0")
        chunk.description = "Section: \"%s\" (size=%s)" % (name, humanFilesize(self["size"]))

class PE_Directory(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "pe_dir", "PE directory", stream, parent, "<")
        self.read("size", "Size", (FormatChunk, "uint32"))
        self.read("rva", "RVA", (FormatChunk, "uint32"))

    def updateParent(self, chunk):
        if self["rva"] != 0:
            chunk.description = "Directory: size=%s" % humanFilesize(self["size"])
        else:
            chunk.description = "Directory: (unused)"

class PE_OptionnalHeader(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "pe_opt_hdr", "PE optionnal header", stream, parent, "<")
        self.read("header", "Header", (FormatChunk, "uint16"))
        assert self["header"] == 0x010B
        self.read("linker_maj_ver", "Linker major version", (FormatChunk, "uint8"))
        self.read("linker_min_ver", "Linker minor version", (FormatChunk, "uint8"))
        self.read("code_size", "Code size (bytes)", (FormatChunk, "uint32"))
        self.read("data_size", "Data size (bytes)", (FormatChunk, "uint32"))
        self.read("heap_size", "Heap size (bytes)", (FormatChunk, "uint32"))
        self.read("entry_point_rva", "Entry point offset (RVA)", (FormatChunk, "uint32"))
        self.read("code_rva", "Code offset (RVA)", (FormatChunk, "uint32"))
        self.read("data_rva", "Data offset (RVA)", (FormatChunk, "uint32"))
        self.read("base_image_rva", "Base image offset (RVA)", (FormatChunk, "uint32"))
        self.read("memory_alignment", "Memory alignment", (FormatChunk, "uint32"))
        self.read("file_alignment", "File alignment", (FormatChunk, "uint32"))
        self.read("os_maj_ver", "OS major version", (FormatChunk, "uint16"))
        self.read("os_min_ver", "OS minor version", (FormatChunk, "uint16"))
        self.read("prog_maj_ver", "Program major version", (FormatChunk, "uint16"))
        self.read("prog_min_ver", "Program minor version", (FormatChunk, "uint16"))
        self.read("api_maj_ver", "API major version?!", (FormatChunk, "uint16"))
        self.read("api_min_ver", "API minor version?!", (FormatChunk, "uint16"))
        self.read("windows_ver", "Windows version?!", (FormatChunk, "uint32"))
        self.read("image_size", "Image size", (FormatChunk, "uint32"))
        self.read("headers_size", "Headers size", (FormatChunk, "uint32"))
        self.read("checksum", "Checkum", (FormatChunk, "uint32"))
        self.read("neeed_api", "Needed API?!", (FormatChunk, "uint16"))
        self.read("dll_options", "DLL options (only for DLL)", (FormatChunk, "uint16"))
        self.read("reserved_stack_size", "Reserved stack size", (FormatChunk, "uint32"))
        self.read("common_stack_size", "Common stack size", (FormatChunk, "uint32"))
        self.read("reserved_heap_size", "Reserved heap size", (FormatChunk, "uint32"))
        self.read("common_heap_size", "Common heap size", (FormatChunk, "uint32"))
        self.read("loader_options", "Loader options", (FormatChunk, "uint32"))
        self.read("nb_directories", "Number of directories (16)", (FormatChunk, "uint32"))
        assert self["nb_directories"] == 16
        for i in range(0, self["nb_directories"]):
            self.read("directorie[]", "PE directory", (PE_Directory,))

class PE_Header(OnDemandFilter):
    cpu_type_name = {
        0x00: "Unknow (any type)",
        0x184: "Alpha AXP",
        0x1c0: "ARM",
        0x284: "Alpha AXP 64 bits",
        0x14c: "Intel 386",
        0x200: "Intel IA64",
        0x268: "Motorolla 68000",
        0x266: "MIPS",
        0x366: "MIPS with FPU",
        0x466: "MIPS16 with FPU",
        0x1f0: "PowerPC little endian",
        0x162: "R3000",
        0x166: "MIPS little endian (R4000)",
        0x168: "R10000",
        0x1a2: "Hitachi SH3",
        0x1a6: "Hitachi SH4",
        0x1c2: "Thumb (?)"
    }
    
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "pe_header", "PE header", stream, parent, "<")
        self.read("header", "File header", (FormatChunk, "string[4]"))
        assert self["header"] == "PE\0\0"
        self.read("cpu_type", "CPU type", (EnumChunk, "uint16", PE_Header.cpu_type_name))
        self.read("nb_sections", "Number of sections", (FormatChunk, "uint16"))
        self.read("creation_date", "Creation date", (FormatChunk, "uint32"), {"post": unixTimestamp})
        self.read("ptr_to_symbols", "Pointer to symbol table", (FormatChunk, "uint32"))
        self.read("nb_symbols", "Number of symbols", (FormatChunk, "uint32"))
        self.read("opt_header_size", "Optionnal header size", (FormatChunk, "uint16"))

        bits = (
            (1, "reloc_stripped", "If true, don't contain base relocations."),
            (1, "exec_image", "Exectuable image?"),
            (1, "line_nb_stripped", "COFF line numbers stripped?"),
            (1, "local_sym_stripped", "COFF symbol table entries stripped?"),
            (1, "aggr_ws", "Aggressively trim working set"),
            (1, "large_addr", "Application can handle addresses greater than 2 GB"),
            (1, "reserved", "(reserved)"),
            (1, "reverse_lo", "Little endian: LSB precedes MSB in memory"),
            (1, "32bit", "Machine based on 32-bit-word architecture"),
            (1, "debug_stripped", "Debugging information removed?"),
            (1, "swap", "If image is on removable media, copy and run from swap file"),
            (1, "reserved2", "(reserved)"),
            (1, "system", "It's a system file"),
            (1, "dll", "It's a dynamic-link library (DLL)"),
            (1, "up", "File should be run only on a UP machine"),
            (1, "reverse_hi", "Big endian: MSB precedes LSB in memory"),
        )
        self.read("options", "Options", (BitsChunk, BitsStruct(bits)))
        #self.read("options", "Options", (FormatChunk, "uint16"))

    def getCpuType(self):
        cpu_name = {
            0x014C: "Intel 80386 or greater",
            0x014D: "Intel 80486 or greater",
            0x014E: "Intel Pentium or greader", 
            0x0160: "R3000 (MIPS), big endian",
            0x0162: "R3000 (MIPS), little endian",
            0x0166: "R4000 (MIPS), little endian",
            0x0168: "R10000 (MIPS), little endian",
            0x0184: "DEC Alpha AXP",
            0x01F0: "IBM Power PC, little endian"}
        return cpu_name.get(self["cpu_type"], "unknow")

class MS_Dos(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "msdos_header", "MS-Dos executable header", stream, parent, ">")
        self.read("header", "File header", (FormatChunk, "string[2]"))
        assert self["header"] == "MZ"
        self.read("filesize_mod_512", "Filesize mod 512", (FormatChunk, "uint16"))
        self.read("filesize_div_512", "Filesize div 512", (FormatChunk, "uint16"))
        self.filesize = self["filesize_div_512"] * 512 + self["filesize_mod_512"]
        self.read("reloc_entries", "Number of relocation entries", (FormatChunk, "uint16"))
        self.read("code_offset", "Offset to the code in the file (div 16)", (FormatChunk, "<uint16"))
        self.code_offset = self["code_offset"] * 16
        self.read("needed_memory", "Memory needed to run (div 16)", (FormatChunk, "uint16"))
        self.needed_memory = self["needed_memory"] * 16
        self.read("max_memory", "Maximum memory needed to run (div 16)", (FormatChunk, "uint16"))
        self.max_memory = self["max_memory"] * 16
        self.read("init_ss_sp", "Initial value of SP:SS registers.", (FormatChunk, "uint32"))
        self.read("checksum", "Checksum", (FormatChunk, "uint16"))
        self.read("init_cs_ip", "Initial value of CS:IP registers.", (FormatChunk, "uint32"))
        self.read("reloc_offset", "Offset in file to relocation table.", (FormatChunk, "<uint16"))
        self.read("overlay_number", "Overlay number", (FormatChunk, "uint16"))
        self.read("reserved", "Reserverd", (FormatChunk, "string[8]"))
        self.read("oem_id", "OEM id", (FormatChunk, "uint16"))
        self.read("oem_info", "OEM info", (FormatChunk, "uint16"))
        self.read("reserved2", "Reserved", (FormatChunk, "string[20]"))
        self.read("pe_offset", "Offset to PE header", (FormatChunk, "<uint32"))

class ExeFile(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "exe_file", "EXE file", stream, parent, "<")

        msdos = self.doRead("msdos_header", "MS-Dos header", (MS_Dos,))

        if msdos["reloc_offset"] == 0x40:
            # Read PE header
            size = msdos["pe_offset"] - stream.tell()
            self.read("msdos_code", "Padding", (FormatChunk, "string[%u]" % size))
            self.pe = self.doRead("pe", "PE header", (PE_Header,))
           
            # Read PE optionnal header
            self.read("pe_opt", "PE optionnal header", (PE_OptionnalHeader,))

            # Read sections
            sections = []
            for i in range(0, self["pe"]["nb_sections"]):
                section = self.doRead("pe_section[]", "PE section", (PE_Section,))
                sections.append(section)

            # TODO: Finish the code ... 
#            for section in sections:
#                if section.name == ".rsrc":
#                    offset_res_section = section["file_offset"]
#                    size = offset_res_section - stream.tell()
#                    self.read("padding[]", "Padding", (FormatChunk, "string[%u]" % size))
#                    self.read("pe_resources", "PE resources", (PE_ResourceDirectory,))
        else:
            self.pe = None

registerPlugin(ExeFile, ["application/x-dosexec", "application/x-ms-dos-executable"])
