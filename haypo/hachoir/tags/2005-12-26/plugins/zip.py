"""
Zip splitter.

Status: can read most important headers
Author: Victor Stinner
"""

import sys
from filter import Filter
from plugin import registerPlugin
from error import error
from text_handler import humanFilesize, hexadecimal

class ZipCentralDirectory(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "zip_central_dir", "ZIP central directory", stream, parent)
        self.read("version_made_by", "<H", "Version made by")
        self.read("version_needed", "<H", "Version neede")
        self.read("flags", "<H", "General purpose flag")
        self.read("compression_method", "<H", "Compression method")
        self.read("last_mod_file_time", "<H", "Last moditication file time")
        self.read("last_mod_file_date", "<H", "Last moditication file date")
        self.read("crc32", "<L", "CRC-32")
        self.read("compressed_size", "<L", "Compressed size")
        self.read("uncompressed_size", "<L", "Uncompressed size")
        self.read("filename_length", "<H", "Filename length")
        self.read("extra_length", "<H", "Extra fields length")
        self.read("file_comment_length", "<H", "File comment length")
        self.read("disk_number_start", "<H", "Disk number start")
        self.read("internal_attr", "<H", "Internal file attributes")
        self.read("external_attr", "<L", "External file attributes")
        self.read("offset_header", "<L", "Relative offset of local header")
        self.read("filename", "%us" % self["filename_length"], "Filename")
        self.read("extra", "%us" % self["extra_length"], "Extra fields")
        self.read("file_comment", "%us" % self["file_comment_length"], "File comment")

    def updateParent(self, chunk):
        desc = "Central directory: %s" % self["filename"]
        chunk.description = desc
        self.setDescription(desc)

class ZipEndCentralDirectory(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "zip_end_dir", "ZIP end central directory", stream, parent)
        self.read("number_disk", "<H", "Number of this disk")
        self.read("number_disk2", "<H", "Number of this disk2")
        self.read("total_number_disk", "<H", "Total number of entries")
        self.read("total_number_disk2", "<H", "Total number of entries2")
        self.read("size", "<L", "Size of the central directory")
        self.read("offset", "<L", "Offset of start of central directory")
        self.readString("comment", "Pascal16", "ZIP comment")

#class ZipZip64(Filter):
#    def __init__(self, stream, parent):
#        Filter.__init__(self, "zip_zip64, "ZIP ZIP64", stream, parent)
#        self.read("size", "<Q", "Directory size")
#        self.read("version_made_by", "<H", "Version made by")
#        self.read("version_needed", "<H", "Version neede")
#        self.read("disk_index", "<L", "Disk index")
#        self.read("disk_index2", "<L", "Disk index2")
#        self.read("disk_number", "<Q", "Disk number")
#        self.read("disk_number2", "<Q", "Disk number2")
#        self.read("size2", "<Q", "Directory size2")
#        self.read("offset", "<Q", "Offset")
        
class ZipFileEntry(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "zip_file_entry", "ZIP file entry", stream, parent)
        self.read("version", "<H", "Version")
        self.read("flags", "<H", "Flags")
        self.read("compression_method", "<H", "Compression method")
        self.read("last_mod_time", "<H", "Last modification time")
        self.read("last_mod_date", "<H", "Last modification date")
        self.read("crc32", "<L", "Checksum (CRC32)")
        self.read("compressed_size", "<L", "Compressed size (bytes)", post=humanFilesize)
        self.read("uncompressed_size", "<L", "Uncompressed size (bytes)", post=humanFilesize)
        self.read("filename_length", "<H", "Filename length")
        self.read("extra_length", "<H", "Extra length")
        self.read("filename", "%us" % self["filename_length"], "Filename")
        self.read("extra", "%us" % self["extra_length"], "Extra")
        self.read("compressed_data", "%us" % self["compressed_size"], "Compressed data")
        if (self["flags"] & 4) == 4:
            self.read("file_crc32", "<L", "Checksum (CRC32)")
            self.read("file_compressed_size", "<L", "Compressed size (bytes)")
            self.read("file_uncompressed_size", "<L", "Uncompressed size (bytes)")

    def updateParent(self, chunk):
        size = self.getChunk("compressed_size").display
        desc = "File entry: %s (%s)" % (self["filename"], size)
        chunk.description = desc
        self.setDescription(desc)
        
class ZipFile(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "zip_file", "ZIP archive file", stream, parent)
        # File data
        self.signature = None
        self.central_directory = []
        self.files = []
        while not stream.eof():
            header = self.read("header[]", "<L", "Header", post=hexadecimal).value
            if header == 0x04034B50:
                self.readChild("files[]", ZipFileEntry)
            elif header == 0x02014b50:
                self.readChild("central_directory[]", ZipCentralDirectory)
            elif header == 0x06054b50:
                self.readChild("end_central_directory", ZipEndCentralDirectory)
            elif header == 0x05054b50:
                self.readString("signature", "Pascal16", "Signature")
            else:
                error("Error, unknow ZIP header (0x%08X)." % header)
                size = stream.getSize() - stream.tell()
                self.read("raw", "%us" % size, "Raw")
        
registerPlugin(ZipFile, "application/x-zip")