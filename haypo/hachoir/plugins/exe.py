"""
EXE filter.

Status: alpha 
Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin

def displayPE(pe):
    print "[ PE HEADER ]"
    print "Architecture: %s" % pe.getCpuType()
            
def displayPE_Section(section):
    print "-> Section %- 8s: size=%u, rva=%08X" % \
        (section.name, section.size, section.rva)

def displayPE_Resource(res):
    print "Resource: id=%u" % \
        (res.id)
        
def displayPE_ResourceDirectory(res):
    print "Resources: nb_entries = %u + %s" % \
        (res.named_entries, res.indexed_entries)
    for item in res.items:
        displayPE_Resource(item)

def displayExe(exe):
    print "[ MS-DOS HEADER ]"
    print "Init. SS:SP: %04X:%04X" % \
        (exe.init_ss_sp & 0xFFFF,
         exe.init_ss_sp >> 16 & 0xFFFF)
    if exe.pe:
#        displayPE(exe.pe)
        for section in exe.pe_sections:
            displayPE_Section(section)
        for res in exe.pe_resources:
            displayPE_ResourceDirectory(res)
            
class PE_ResourceData(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("offset", "<L", "Offset")
        self.read("size", "<L", "Size")
        self.read("page_code", "<L", "Page code (language)")
        self.read("language", "<l", "Page code (language)")
        self.language = -self.language
        self.read(None, "!L", "Reserverd")

        oldpos = stream.tell()
        
        #stream.seek(XXX + self.offset - self.offset_res_section)
        stream.seek(self.offset)
        stream.seek(oldpos)

class PE_ResourceEntry(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("id", "<L", "ID or name")
        self.read("offset", "<L", "Offset")
        
class PE_ResourceDirectory(Filter):
    def __init__(self, stream, parent, offset_res_section):
        Filter.__init__(self, stream, parent)
        self.offset_res_section = offset_res_section
        self.read("option", "<L", "Options")
        self.read("creation_date", "<L", "Creation date")
        self.read("maj_ver", "<H", "Major version")
        self.read("named_entries", "<H", "Named entries")
        self.read("indexed_entries", "<H", "Indexed entries")
        nb_entries = self.named_entries + self.indexed_entries
        self.openChild()

        stream.seek( stream.tell() + 0x10)
        self.items = []
        for i in range(nb_entries):
            self.newChild("Resource")
            self.items.append( PE_ResourceEntry(stream,self) )
        self.closeChild("Resources")

class PE_Section(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("name", "8s", "Name")
        self.name = self.name.strip("\0")
        self.read("rva", "<L", "RVA")
        self.read("size", "<L", "Size")
        self.read("file_size", "<L", "File size")
        self.read("file_offset", "<L", "File offset")
        self.read("reloc_ptr", "<L", "Relocation pointer")
        self.read("lines_ptr", "<L", "File line numbers pointer")
        self.read("nb_reloc", "<H", "Number of relocations")
        self.read("nb_lines", "<H", "Number of file line")
        self.read("options", "<L", "Options")

class PE_Directory(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("size", "<L", "Size")
        self.read("rva", "<L", "RVA")

class PE_OptionnalHeader(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("header", "<H", "Header")
        assert self.header == 0x010B
        self.read("linker_maj_ver", "B", "Linker major version")
        self.read("linker_min_ver", "B", "Linker minor version")
        self.read("code_size", "<L", "Code size (bytes)")
        self.read("data_size", "<L", "Data size (bytes)")
        self.read("heap_size", "<L", "Heap size (bytes)")
        self.read("entry_point_rva", "<L", "Entry point offset (RVA)")
        self.read("code_rva", "<L", "Code offset (RVA)")
        self.read("data_rva", "<L", "Data offset (RVA)")
        self.read("base_image_rva", "<L", "Base image offset (RVA)")
        self.read("memory_alignment", "<L", "Memory alignment")
        self.read("file_alignment", "<L", "File alignment")
        self.read("os_maj_ver", "<H", "OS major version")
        self.read("os_min_ver", "<H", "OS minor version")
        self.read("prog_maj_ver", "<H", "Program major version")
        self.read("prog_min_ver", "<H", "Program minor version")
        self.read("api_maj_ver", "<H", "API major version?!")
        self.read("api_min_ver", "<H", "API minor version?!")
        self.read("windows_ver", "<L", "Windows version?!")
        self.read("image_size", "<L", "Image size")
        self.read("headers_size", "<L", "Headers size")
        self.read("checksum", "<L", "Checkum")
        self.read("neeed_api", "<H", "Needed API?!")
        self.read("dll_options", "<H", "DLL options (only for DLL)")
        self.read("reserved_stack_size", "<L", "Reserved stack size")
        self.read("common_stack_size", "<L", "Common stack size")
        self.read("reserved_heap_size", "<L", "Reserved heap size")
        self.read("common_heap_size", "<L", "Common heap size")
        self.read("loader_options", "<L", "Loader options")
        self.read("nb_directories", "<L", "Number of directories (16)")
        assert self.nb_directories == 16
        self.directories = []
        self.openChild()
        for i in range(self.nb_directories):
            self.newChild("PE directory")            
            self.directories.append( PE_Directory(stream, self) )
        self.closeChild("PE directories")            

class PE_Filter(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("header", "4s", "File header")
        assert self.header == "PE\0\0"
        self.read("cpu_type", "<H", "CPU type")
        self.read("nb_sections", "<H", "Number of sections")
        self.read("creation_date", "<L", "Creation date")
        self.read("ptr_to_symbols", "<L", "Pointer to symbol table")
        self.read("nb_symbols", "<L", "Number of symbols")
        self.read("opt_header_size", "<H", "Optionnal header size")
        self.read("options", "<H", "Options")

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
        return cpu_name.get(self.cpu_type, "unknow")

class ExeFilter(Filter):
    def __init__(self, stream):
        Filter.__init__(self, stream)
        self.read("header", "2s", "File header")
        assert self.header == "MZ"
        self.read("filesize_mod_512", ">H", "Filesize mod 512")
        self.read("filesize_div_512", ">H", "Filesize div 512")
        self.filesize = self.filesize_div_512 * 512 + self.filesize_mod_512
        self.read("reloc_entries", ">H", "Number of relocation entries")
        self.read("code_offset", "<H", "Offset to the code in the file (div 16)")
        self.code_offset = self.code_offset * 16
        self.read("needed_memory", ">H", "Memory needed to run (div 16)")
        self.needed_memory = self.needed_memory * 16
        self.read("max_memory", ">H", "Maximum memory needed to run (div 16)")
        self.max_memory = self.max_memory * 16
        self.read("init_ss_sp", ">L", "Initial value of SP:SS registers.")
        self.read("checksum", ">H", "Checksum")
        self.read("init_cs_ip", ">L", "Initial value of CS:IP registers.")
        self.read("reloc_offset", "<H", "Offset in file to relocation table.")
        self.read("overlay_number", ">H", "Overlay number")
        self.read(None, ">4H", "Reserverd")
        self.read("oem_id", ">H", "OEM id")
        self.read("oem_info", ">H", "OEM info")
        self.read(None, "!10H", "Reserved")
        self.read("pe_offset", "<L", "Offset to PE header")

        if self.reloc_offset == 0x40:
            self.openChild()
            self.newChild("PE header")
            self.stream.seek(self.pe_offset)
            self.pe = PE_Filter(stream, self)
            self.closeChild("PE header")

            self.openChild()
            self.newChild("PE optionnal header")            
            self.pe_optionnal_header = PE_OptionnalHeader(stream, self)
            self.closeChild("PE optionnal header")            

            self.openChild()
            self.pe_sections = []
            for i in range(self.pe.nb_sections):
                self.newChild("PE section")            
                self.pe_sections.append( PE_Section(stream, self) )
            self.closeChild("PE sections")     

            # Look for resource section
            self.pe_resources = []
            offset_res_section = None
            for section in self.pe_sections:
                if section.name == ".rsrc":
                    offset_res_section = section.file_offset
                    self.stream.seek( offset_res_section )
                    break
            if offset_res_section != None:
                self.openChild()
                for i in range(1): #range(self.pe.nb_sections):
                    self.newChild("PE resource header")            
                    self.pe_resources.append( PE_ResourceDirectory(stream, self, offset_res_section) )
                self.closeChild("PE resources header")            
        else:
            self.pe = None

registerPlugin("^.*\.(exe|EXE)$", "MS-Dos / Windows filter", ExeFilter, displayExe)
