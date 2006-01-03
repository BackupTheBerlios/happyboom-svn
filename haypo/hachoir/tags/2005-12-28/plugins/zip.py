"""
Zip splitter.

Status: can read most important headers
Author: Victor Stinner
"""

import sys
from filter import OnDemandFilter
from plugin import registerPlugin
from chunk import FormatChunk, StringChunk, BitsChunk, BitsStruct, EnumChunk
from error import error
from text_handler import humanFilesize, hexadecimal, msdosDatetime

# TODO: Merge ZipCentralDirectory and FileEntry (looks very similar)

class ZipCentralDirectory(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "zip_central_dir", "ZIP central directory", stream, parent, "<")
        self.read("version_made_by", "Version made by", (FormatChunk, "uint16"))
        self.read("version_needed", "Version needed", (FormatChunk, "uint16"))
        self.read("flags", "General purpose flag", (FormatChunk, "uint16"))
        self.read("compression", "Compression method", (EnumChunk, "uint16", FileEntry.compression_name))
        self.read("last_mod", "Last moditication file time", (FormatChunk, "uint32"), {"post": msdosDatetime})
        self.read("crc32", "CRC-32", (FormatChunk, "uint32"), {"post": hexadecimal})
        self.read("compressed_size", "Compressed size", (FormatChunk, "uint32"))
        self.read("uncompressed_size", "Uncompressed size", (FormatChunk, "uint32"))
        self.read("filename_length", "Filename length", (FormatChunk, "uint16"))
        self.read("extra_length", "Extra fields length", (FormatChunk, "uint16"))
        self.read("comment_length", "File comment length", (FormatChunk, "uint16"))
        self.read("disk_number_start", "Disk number start", (FormatChunk, "uint16"))
        self.read("internal_attr", "Internal file attributes", (FormatChunk, "uint16"))
        self.read("external_attr", "External file attributes", (FormatChunk, "uint32"))
        self.read("offset_header", "Relative offset of local header", (FormatChunk, "uint32"))
        self.read("filename", "Filename", (FormatChunk, "string[%u]" % self["filename_length"]))
        self.read("extra", "Extra fields", (FormatChunk, "string[%u]" % self["extra_length"]))
        self.read("comment", "Comment", (FormatChunk, "string[%u]" % self["comment_length"]))

    def updateParent(self, chunk):
        desc = "Central directory: %s" % self["filename"]
        chunk.description = desc
        self.setDescription(desc)

class ZipEndCentralDirectory(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "zip_end_dir", "ZIP end central directory", stream, parent, "<")
        self.read("number_disk", "Number of this disk", (FormatChunk, "uint16"))
        self.read("number_disk2", "Number of this disk2", (FormatChunk, "uint16"))
        self.read("total_number_disk", "Total number of entries", (FormatChunk, "uint16"))
        self.read("total_number_disk2", "Total number of entries2", (FormatChunk, "uint16"))
        self.read("size", "Size of the central directory", (FormatChunk, "uint32"))
        self.read("offset", "Offset of start of central directory", (FormatChunk, "uint32"))
        self.read("comment", "ZIP comment", (StringChunk, "Pascal16"))
       
class FileEntry(OnDemandFilter):
    compression_name = {
        0: "no compression",
        1: "Shrunk",
        2: "Reduced (factor 1)",
        3: "Reduced (factor 2)",
        4: "Reduced (factor 3)",
        5: "Reduced (factor 4)",
        6: "Imploded",
        7: "Tokenizing",
        8: "Deflate",
        9: "Deflate64",
        10: "PKWARE Imploding"
    }
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "zip_file_entry", "ZIP file entry", stream, parent, "<")
        self.read("version", "Version", (FormatChunk, "uint16"))
        bits = (
            (1, "encryption", "File is encrypted?"),
            (1, "8k_sliding", "Use 8K sliding dictionnary (instead of 4K)"),
            (1, "3shannon", "Use a 3 Shannon-Fano tree (instead of 2 Shannon-Fano)"),
            (1, "use_data_desc", "Use data descriptor?"),
            (1, "reserved", "Reserved"),
            (1, "patched", "File is compressed with patched data?"),
            (6, "unused", "Unused bits"),
            (4, "pkware", "Reserved by PKWARE"))
        flags = self.doRead("flags", "Flags", (BitsChunk, BitsStruct(bits)))
        self.read("compression", "Compression method", (EnumChunk, "uint16", FileEntry.compression_name))
        self.read("last_mod", "Last modification time", (FormatChunk, "uint32"), {"post": msdosDatetime})
        self.read("crc32", "Checksum (CRC32)", (FormatChunk, "uint32"), {"post": hexadecimal})
        self.read("compressed_size", "Compressed size (bytes)", (FormatChunk, "uint32"), {"post": humanFilesize})
        self.read("uncompressed_size", "Uncompressed size (bytes)", (FormatChunk, "uint32"), {"post": humanFilesize})
        self.read("filename_length", "Filename length", (FormatChunk, "uint16"))
        self.read("extra_length", "Extra length", (FormatChunk, "uint16"))
        self.read("filename", "Filename", (FormatChunk, "string[%u]" % self["filename_length"]))
        self.read("extra", "Extra", (FormatChunk, "string[%u]" % self["extra_length"]))
        self.read("compressed_data", "Compressed data", (FormatChunk, "string[%u]" % self["compressed_size"]))
        if flags["use_data_desc"]:
            self.read("file_crc32", "Checksum (CRC32)", (FormatChunk, "uint32"), {"post": hexadecimal})
            self.read("file_compressed_size", "Compressed size (bytes)", (FormatChunk, "uint32"), {"post": humanFilesize})
            self.read("file_uncompressed_size", "Uncompressed size (bytes)", (FormatChunk, "uint32"), {"post": humanFilesize})

    def updateParent(self, chunk):
        size = self.getChunk("compressed_size").display
        desc = "File entry: %s (%s)" % (self["filename"], size)
        chunk.description = desc
        self.setDescription(desc)
        
class ZipFile(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "zip_file", "ZIP archive file", stream, parent, "<")
        # File data
        self.signature = None
        self.central_directory = []
        self.files = []
        while not stream.eof():
            header = self.doRead("header[]", "Header", (FormatChunk, "uint32"), {"post": hexadecimal}).value
            if header == 0x04034B50:
                self.read("file[]", "File", (FileEntry,))
            elif header == 0x02014b50:
                self.read("central_directory[]", "Central directory", (ZipCentralDirectory,))
            elif header == 0x06054b50:
                self.read("end_central_directory", "End of central directory", (ZipEndCentralDirectory,))
            elif header == 0x05054b50:
                self.read("signature", "Signature", (StringChunk, "Pascal16"))
            else:
                error("Error, unknow ZIP header (0x%08X)." % header)
                size = stream.getSize() - stream.tell()
                self.read("raw", "Raw", (FormatChunk, "string[%u]" % size))
        
registerPlugin(ZipFile, "application/x-zip")
