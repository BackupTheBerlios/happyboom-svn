"""
Zip splitter.

Status: can read most important headers
Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin
import sys

def splitZip(stream):
    return ZipFilter(stream)

def displayZip(zip):    
    print "[ Zip archive ]"
    for file in zip.files:
        sys.stdout.write ("* File %s (size=%0.1f KB" %
            (file.filename, file.uncompressed_size / 1024))
        if file.uncompressed_size != 0:
            sys.stdout.write (" - %0.1f%%" % \
                (100 - file.compressed_size * 100 / file.uncompressed_size))
        sys.stdout.write (")\n")
    print "[ End of the zip archive ]"

class ZipCentralDirectory(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
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
        self.read("filename", "<[filename_length]s", "Filename")
        self.read("extra", "<[extra_length]s", "Extra fields")
        self.read("file_comment", "<[file_comment_length]s", "File comment")

class ZipEndCentralDirectory(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("number_disk", "<H", "Number of this disk")
        self.read("number_disk2", "<H", "Number of this disk2")
        self.read("total_number_disk", "<H", "Total number of entries")
        self.read("total_number_disk2", "<H", "Total number of entries2")
        self.read("size", "<L", "Size of the central directory")
        self.read("offset", "<L", "Offset of start of central directory")
        self.read("comment_length", "<H", "ZIP comment length")
        self.read("comment", "<[comment_length]s", "ZIP comment")

#class ZipZip64(Filter):
#    def __init__(self, stream, parent):
#        Filter.__init__(self, stream, parent)
#        self.read("size", "<Q", "Directory size")
#        self.read("version_made_by", "<H", "Version made by")
#        self.read("version_needed", "<H", "Version neede")
#        self.read("disk_index", "<L", "Disk index")
#        self.read("disk_index2", "<L", "Disk index2")
#        self.read("disk_number", "<Q", "Disk number")
#        self.read("disk_number2", "<Q", "Disk number2")
#        self.read("size2", "<Q", "Directory size2")
#        self.read("offset", "<Q", "Offset")
        
class ZipFile(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("version", "<H", "Version")
        self.read("flags", "<H", "Flags")
        self.read("compression_method", "<H", "Compression method")
        self.read("last_mod_time", "<H", "Last modification time")
        self.read("last_mod_date", "<H", "Last modification date")
        self.read("crc32", "<L", "Checksum (CRC32)")
        self.read("compressed_size", "<L", "Compressed size (bytes)")
        self.read("uncompressed_size", "<L", "Uncompressed size (bytes)")
        self.read("filename_length", "<H", "Filename length")
        self.read("extra_length", "<H", "Extra length")
        self.read("filename", "<[filename_length]s", "Filename")
        self.read("extra", "<[extra_length]s", "Extra")
        self.read("compressed_data", "<[compressed_size]s", "Compressed data")
        if (self.flags & 4) == 4:
            self.read("file_crc32", "<L", "Checksum (CRC32)")
            self.read("file_compressed_size", "<L", "Compressed size (bytes)")
            self.read("file_uncompressed_size", "<L", "Uncompressed size (bytes)")
        
class ZipFilter(Filter):
    def __init__(self, stream):
        Filter.__init__(self, stream)
        # File data
        self.signature = None
        self.central_directory = []
        self.end_central_directory = None
        self.files = []
        while not stream.eof():
            self.read("header", "<L", "Header")
            if self.header == 0x04034B50:
                self.newChild("File entry")
                self.openChild()
                self.files.append( ZipFile(stream, self) )
                self.closeChild("File entry")
            elif self.header == 0x02014b50:
                self.newChild("Central directory")
                self.openChild()
                self.central_directory.append( ZipCentralDirectory(stream,self) )
                self.closeChild("Central directory")
            elif self.header == 0x06054b50:
                self.newChild("End of central directory")
                self.openChild()
                self.end_central_directory = ZipEndCentralDirectory(stream,self)
                self.closeChild("End of central directory")
            elif self.header == 0x05054b50:
                self.read("signature_length", "!H", "Signature length")
                self.read("signature", "![signature_length]s", "Signature")
            else:
                raise Exception("Error, unknow ZIP header (0x%08X)." % self.header)
        
registerPlugin("^.*\.(zip|ZIP)$", "ZIP (compressed archive)", splitZip, displayZip)
