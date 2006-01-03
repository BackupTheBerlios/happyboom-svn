"""
GZIP archive parser.

Author: Victor Stinner
"""

import datetime
from filter import OnDemandFilter, DeflateFilter
from chunk import FormatChunk, StringChunk, EnumChunk, BitsChunk, BitsStruct
from plugin import registerPlugin
from stream.gunzip import GunzipStream
from plugin import getPluginByStream
from error import error
from default import DefaultFilter
from text_handler import hexadecimal, humanFilesize, unixTimestamp
   
class GzipFile(OnDemandFilter):
    os_name = {
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

    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "gzip_file", "GZIP archive file", stream, parent, "<")

        # Gzip header
        self.read("id", "Identifier (31,139)", (FormatChunk, "uint8[2]"))
        assert self["id"] == (31, 139)
        self.read("compression", "Compression method", (FormatChunk, "uint8"), {"post": self.getCompressionMethod})
        bits = (
            (1, "text", "File content is probably ASCII text"),
            (1, "crc16", "Header CRC16"),
            (1, "extra", "Extra informations (variable size)"),
            (1, "filename", "Contains filename?"),
            (1, "comment", "Contains comment?"),
            (3, "unused", "Unused bits"))
        flags = self.doRead("flags", "Flags", (BitsChunk, BitsStruct(bits)))
        self.read("mtime", "Modification time", (FormatChunk, "uint32"), {"post": unixTimestamp})

        bits = (
            (1, "unused", "(unused)"),
            (1, "slowest", "Compressor used maximum compression (slowest)"),
            (1, "fastest", "Compressor used the fastest compression"),
            (5, "unused2", "(unused)"))
        extra_flags = self.doRead("extra_flags", "Extra flags", (BitsChunk, BitsStruct(bits)))

        self.read("os", "Operating system", (EnumChunk, "uint8", GzipFile.os_name))

        # Optionnal fields
        if flags["extra"] & 4 == 4:
            self.read("extra_length", "Extra length", (FormatChunk, "uint16"))
            self.read("extra", "Extra", (FormatChunk, "string[%u]"  % self["extra_length"]))
        if flags["filename"]:
            self.read("filename", "Filename", (StringChunk, "C"))
        if flags["comment"]:
            self.read("comment", "Comment", (StringChunk, "C"))
        if flags["crc16"]:
            self.read("hdr_crc16", "Header CRC16", (FormatChunk, "uint16"), post=hexadecimal)

        # Read content           
        oldpos = stream.tell()
        size = stream.getSize() - oldpos - 8
        try:
            gz_stream = GunzipStream(stream)
            if self.hasChunk("filename"):
                plugin = getPluginByStream(gz_stream, self["filename"])
            else:
                plugin = getPluginByStream(gz_stream, None)

            self.read("data", "Data", (DeflateFilter, gz_stream, size, plugin)) 
        except Exception, msg:
            error("Error while processing file in gzip: %s" % msg)
            stream.seek(oldpos)
            self.read("data", "Compressed data", (FormatChunk, "string[%u]" % size))

        # Footer
        self.read("crc32", "CRC32", (FormatChunk, "uint32"), {"post": hexadecimal})
        self.read("size", "Uncompressed size", (FormatChunk, "uint32"), {"post": humanFilesize})

    def getCompressionMethod(self, chunk):
        val = chunk.value
        if val < 8: return "reserved"
        if val == 8: return "deflate"
        return "Unknow (%s)" % val

registerPlugin(GzipFile, "application/x-gzip")
