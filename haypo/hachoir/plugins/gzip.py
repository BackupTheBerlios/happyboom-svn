"""
Exported filter.

Description:
GZIP archive file
"""

import datetime
from filter import Filter
from plugin import registerPlugin
from stream.gunzip import GunzipStream
from plugin import getPluginByStream
from error import error
from default import DefaultFilter
   
class GunzipFilter(Filter):
    def __init__(self, stream, parent, start, size, filter_class):
        # Read data
        self._parent_stream = stream
        self._parent_stream.seek(0)
        data = stream.getN(self._parent_stream.getSize())
        
        # Create a new stream
        stream = GunzipStream(data)
        self._compressed_size = size 
        self._decompressed_size = stream.getSize()

        # Create filter
        self._parent_stream.seek(start)
        Filter.__init__(self, "deflate", "Deflate", stream, parent)
        self._addr = self._parent_stream.tell()

        self.readChild("data", filter_class)

    def getSize(self):
        return self._compressed_size

class GzipFile(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "gzip_file", "GZIP archive file", stream, parent)
        self.read("id", "!2B", "Identifier (31,139)")
        assert self.id == (31, 139)
        self.read("comp_method", "!B", "Compression method", post=self.getCompressionMethod)
        self.read("flags", "!B", "Flags", post=self.getFlags)
        self.read("mtime", "<1L", "Modification time", post=self.getMTime)
        self.read("extra", "!B", "Extra flags")
        self.read("os", "!B", "OS", post=self.getOS)

        if self.extra & 4 == 4:
            self.read("extra_length", "<2H", "Extra length")
            self.read("extra", "!{extra_length}s", "Extra")
        if self.flags & 8 == 8:
            self.readString("filename", "C", "Filename")
        if self.flags & 16 == 16:
            self.readString("comment", "C", "Comment")
        if self.flags & 2 == 2:
            self.readString("crc16", "!H", "CRC16")

        oldpos = stream.tell()
        size = stream.getSize() - oldpos - 8
        try:
            # TODO: Fix this fucking GunzipStream (use something better)
            stream.seek(0)
            data = stream.getN(stream.getSize())
            stream = GunzipStream(data)
            stream.seek(oldpos)
            plugin = getPluginByStream(stream, self.filename)
            # END OF TODO

            self.readChild("data", GunzipFilter, oldpos, size, plugin) 
        except Exception, msg:
            error("Error while processing file in gzip: %s" % msg)
            stream.seek(oldpos)
            self.read("data", "!%us" % size, "Compressed data", truncate=True)
        
        self.read("crc32", "<L", "CRC32")
        self.read("size", "<L", "Uncompressed size")

    def getFlags(self, chunk):
        val = chunk.value
        flags = []
        if val & 1 == 1: flags.append("text")
        if val & 2 == 2: flags.append("crc16")
        if val & 4 == 4: flags.append("extra")
        if val & 8 == 8: flags.append("filename")
        if val & 16 == 16: flags.append("comment")
        return "|".join(flags)
        
    def getCompressionMethod(self, chunk):
        val = chunk.value
        if val < 8: return "reserved"
        if val == 8: return "deflate"
        return "Unknow (%s)" % val

    def getMTime(self, chunk):
        dt = datetime.datetime.fromtimestamp(chunk.value)
        return str(dt)

    def getOS(self, chunk):
        os = { \
            0: "FAT filesystem",
            1: "Amiga",
            2: "VMS (or OpenVMS)",
            3: "Unix",
            4: "VM/CMS",
            5: "Atari TOS",
            6: "HPFS filesystem (OS/2, NT)",
            7: "Macintosh",
            8: "Z-System",
            9: "CP/M",
            10: "TOPS-20",
            11: "NTFS filesystem (NT)",
            12: "QDOS",
            13: "Acorn RISCOS"}            
        val = chunk.value
        return os.get(val, "Unknow (%s)" % val)
        
registerPlugin(GzipFile, "application/x-gzip")
