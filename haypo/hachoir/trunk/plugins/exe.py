"""
EXE filter.

Status: read ms-dos and pe headers
Todo: support resources ... and disassembler ? :-)
Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin

class PE_ResourceData(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "pe_rsrc_data", "PE resource data", stream, parent)
        self.read("offset", "<L", "Offset")
        self.read("size", "<L", "Size")
        self.read("page_code", "<L", "Page code (language)")
        self.read("language", "<l", "Page code (language)")
#        self.language = -self["language"]
        self.read("reserved", "!L", "Reserverd")

        oldpos = stream.tell()
        
        #stream.seek(XXX + self.offset - self.offset_res_section)
        stream.seek(self["offset"])
        stream.seek(oldpos)

class PE_ResourceEntry(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "pe_rsrc_entry", "PE resource entry", stream, parent)
        self.read("id", "<L", "ID or name")
        self.read("offset", "<L", "Offset")
        
class PE_ResourceDirectory(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "pe_rsrc_dir", "PE resource directory", stream, parent)
        self.offset_res_section = stream.tell()
        self.read("option", "<L", "Options")
        self.read("creation_date", "<L", "Creation date")
        self.read("maj_ver", "<H", "Major version")
        self.read("named_entries", "<H", "Named entries")
        self.read("indexed_entries", "<H", "Indexed entries")

        stream.seek( stream.tell() + 0x10)
        self.readArray("item", PE_ResourceEntry, "PE resource entry", self.checkEndOfRes)
    
    def checkEndOfRes(self, stream, array, dir):
        return len(array) == (self["named_entries"] + self["indexed_entries"])

class PE_Section(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "pe_section", "PE section", stream, parent)
        self.read("name", "8s", "Name")
        # TODO: use chunk post proces
        self.name = self["name"].strip(" \0")
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
        Filter.__init__(self, "pe_dir", "PE directory", stream, parent)
        self.read("size", "<L", "Size")
        self.read("rva", "<L", "RVA")

class PE_OptionnalHeader(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "pe_opt_hdr", "PE optionnal header", stream, parent)
        self.read("header", "<H", "Header")
        assert self["header"] == 0x010B
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
        assert self["nb_directories"] == 16
        self.readArray("directories", PE_Directory, "PE directories", self.checkEndOfDir)

    def checkEndOfDir(self, stream, array, dir):
        return len(array) == self.nb_directories

class PE_Filter(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "pe_header", "PE header", stream, parent)
        self.read("header", "4s", "File header")
        assert self["header"] == "PE\0\0"
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
        return cpu_name.get(self["cpu_type"], "unknow")

class MS_Dos(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "msdos_header", "MS-Dos executable header", stream, parent)
        self.read("header", "2s", "File header")
        assert self["header"] == "MZ"
        self.read("filesize_mod_512", ">H", "Filesize mod 512")
        self.read("filesize_div_512", ">H", "Filesize div 512")
        self.filesize = self["filesize_div_512"] * 512 + self["filesize_mod_512"]
        self.read("reloc_entries", ">H", "Number of relocation entries")
        self.read("code_offset", "<H", "Offset to the code in the file (div 16)")
        self.code_offset = self["code_offset"] * 16
        self.read("needed_memory", ">H", "Memory needed to run (div 16)")
        self.needed_memory = self["needed_memory"] * 16
        self.read("max_memory", ">H", "Maximum memory needed to run (div 16)")
        self.max_memory = self["max_memory"] * 16
        self.read("init_ss_sp", ">L", "Initial value of SP:SS registers.")
        self.read("checksum", ">H", "Checksum")
        self.read("init_cs_ip", ">L", "Initial value of CS:IP registers.")
        self.read("reloc_offset", "<H", "Offset in file to relocation table.")
        self.read("overlay_number", ">H", "Overlay number")
        self.read("reserved", ">4H", "Reserverd")
        self.read("oem_id", ">H", "OEM id")
        self.read("oem_info", ">H", "OEM info")
        self.read("reserved2", "!10H", "Reserved")
        self.read("pe_offset", "<L", "Offset to PE header")

class ExeFile(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "exe_file", "EXE file", stream, parent)

        self.readChild("ms_dos", MS_Dos)

        if self["ms_dos"]["reloc_offset"] == 0x40:
            stream.seek(self["ms_dos"]["pe_offset"], 0)

            self.readChild("pe", PE_Filter)
            self.pe = self["pe"]
            self.readChild("pe_opt", PE_OptionnalHeader)
            self.readArray("pe_sections", PE_Section, "PE sections", self.checkEndOfSections)

            # TODO: Fix this ...
            
            offset_res_section = None
            for section in self["pe_sections"]:
                section = section.getFilter()
                if section.name == ".rsrc":
                    offset_res_section = section.file_offset
                    self.getStream().seek( offset_res_section )
                    break
            if offset_res_section != None:
                #for i in range(1): #range(self.pe.nb_sections):
                self.readChild("pe_resources", PE_ResourceDirectory)
        else:
            self.pe = None

    def checkEndOfSections(self, stream, array, section):
        return len(array) == self["pe"]["nb_sections"]

registerPlugin(ExeFile, "application/x-dosexec")
