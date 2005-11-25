"""
BZIP2 archive file
"""

from filter import Filter
from plugin import registerPlugin

class Bzip2_File(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "bz2_file", "Bzip2 archive file", stream, parent)
        self.read("id", "3s", "Identifier (BZh)")
        assert self.id == "BZh"
        self.read("blocksize", "c", "Block size")
        assert "1" <= self.blocksize and self.blocksize <= "9"
        # Size of memory needed to decompress (on classic mode, not "small" mode)
        size = (ord(self.blocksize) - ord("0")) * 400
        self.getChunk("blocksize").description = "Block size (will need %u KB of memory)" % size
        self.read("blockheader", "B", "Block header")
        assert self.blockheader in (0x17, 0x31)
        if self.blockheader == 0x17:
            self.readA()
        else: # blockheader = 0x31 ("1")
            self.readB()

    def readB(self):
        self.read("id2", "5s", "Identifier 2 (AY&SY)")
        assert self.id2 == "AY&SY"
        self.read("crc", "<L", "CRC32")
        
    def readA(self):
        self.read("id2", "4s", "Identifier2 (re8P)")
        self.read("id3", "B", "Identifier3 (0x90)")
        self.read("crc", "<L", "CRC32")
         
registerPlugin(Bzip2_File, "application/x-bzip2")
