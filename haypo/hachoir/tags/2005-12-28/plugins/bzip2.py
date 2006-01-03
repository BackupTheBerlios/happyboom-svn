"""
BZIP2 archive file
"""

from plugin import guessPlugin
from filter import OnDemandFilter, DeflateFilter
from plugin import registerPlugin
from chunk import FormatChunk
from stream.bunzip import BunzipStream
from text_handler import hexadecimal

class Bzip2_File(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "bz2_file", "Bzip2 archive file", stream, parent, "<")
        self.read("id", "Identifier (BZh)", (FormatChunk, "string[3]"))
        assert self["id"] == "BZh"
        self.read("blocksize", "Block size", (FormatChunk, "char"))
        assert "1" <= self["blocksize"] and self["blocksize"] <= "9"
        # Size of memory needed to decompress (on classic mode, not "small" mode)
        size = (ord(self["blocksize"]) - ord("0")) * 100
        self.getChunk("blocksize").description = "Block size (will need %u KB of memory)" % size
        self.read("blockheader", "Block header", (FormatChunk, "uint8"))
        assert self["blockheader"] in (0x17, 0x31)
        if self["blockheader"] == 0x17:
            self.read("id2", "Identifier2 (re8P)", (FormatChunk, "string[4]"))
            self.read("id3", "Identifier3 (0x90)", (FormatChunk, "uint8"))
        else:
            # blockheader = 0x31 ("1")
            self.read("id2", "Identifier 2 (AY&SY)", (FormatChunk, "string[5]"))
            assert self["id2"] == "AY&SY"
        self.read("crc", "CRC32", (FormatChunk, "uint32"), {"post": hexadecimal})
        dataio = BunzipStream(stream)
        plugin = guessPlugin(dataio, None)
        size = stream.getSize()-stream.tell()
        self.read("content", "Compressed data content", (DeflateFilter, dataio, size, plugin))

registerPlugin(Bzip2_File, "application/x-bzip2")
