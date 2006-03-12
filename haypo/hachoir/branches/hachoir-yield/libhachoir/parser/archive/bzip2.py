"""
BZIP2 archive file

Author: Victor Stinner
"""

from field import (FieldSet, ParserError, RawBytes, String, Character, Integer)
from text_handler import hexadecimal

class Bzip2_File(FieldSet):
    mime_types = "application/x-bzip2"
    endian = "<"

    def createFields(self):
        yield String(self, "id", "string[3]", "Identifier (BZh)")
        assert self["id"].value == "BZh"
        yield Character(self, "blocksize", "Block size")
        if not("1" <= self["blocksize"].value <= "9"):
            raise ParserError(
                "Stream doesn't look like bzip2 archive (wrong blocksize)!")

        # Size of memory needed to decompress (on classic mode, not "small" mode)
        size = (ord(self["blocksize"].value) - ord("0")) * 100
        self["blocksize"].description = "Block size (will need %u KB of memory)" % size
        
        yield Integer(self, "blockheader", "uint8", "Block header")
        if self["blockheader"].value == 0x17:
            yield String(self, "id2", "string[4]", "Identifier2 (re8P)")
            yield Integer(self, "id3", "uint8", "Identifier3 (0x90)")
        elif self["blockheader"].value == 0x31:
            yield String(self, "id2", "string[5]", "Identifier 2 (AY&SY)")
            assert self["id2"].value == "AY&SY"
        else:
            raise ParserError(
                "Stream doesn't look like bzip2 archive (wrong blockheader)!")
        yield Integer(self, "crc32", "uint32", "CRC32", text_handler=hexadecimal)

        size = self.stream.size - self.newFieldAskAddress()
        assert (size % 8) == 0
        yield RawBytes(self, "content", size/8, "Compressed data content")

