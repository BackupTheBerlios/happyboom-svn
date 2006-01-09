"""
RAR archive parser.

Informations source:
---
UniquE RAR File Library (under their license or GNU GPL license)
The free file lib for the demoscene
multi-OS version (Win32, Linux and SunOS)

RAR decompression code:
 (C) Eugene Roshal
Modifications to a FileLib:
 (C) 2000-2002 Christian Scheurer aka. UniquE/Vantage (cs@unrarlib.org)
Linux port:
 (C) 2000-2002 Johannes Winkelmann (jw@tks6.net)
---

Author: Victor Stinner
Creation: 9 january 2006 
"""

from filter import OnDemandFilter
from chunk import FormatChunk, StringChunk, BitsStruct, BitsChunk
from plugin import registerPlugin
from text_handler import hexadecimal, unixTimestamp, humanFilesize

class MainHeader(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "head", "Header", stream, parent, "<")
        self.read("crc", "CRC (16 bits)", (FormatChunk, "uint16"), {"post": hexadecimal})
        self.read("type", "Type", (FormatChunk, "uint8"), {"post": hexadecimal})

        bits = (
            (1, "xxx", "???"),
            (1, "comment", "Has comment"),
            (1, "lock", "Lock (?)"),
            (1, "solid", "Solid archive (?)"),
            (1, "pack_comment", "Pack comment"),
            (1, "av", "av (audio/video?)"),
            (1, "protect", "Protect"),
            (9, "raw", "Raw bits"),
        )
        self.read("flags", "Flags", (BitsChunk, BitsStruct(bits)))
        #self.read("flags", "Flags", (FormatChunk, "uint16"))
        self.read("size", "Size", (FormatChunk, "uint16"))
        self.read("reserved", "(reserved)", (FormatChunk, "uint16"))
        self.read("reserved2", "(reserved)", (FormatChunk, "uint32"))

class FileHeader(OnDemandFilter):
    window_size = {
        0: "64 bits",
        1: "128 bits",
        2: "256 bits",
        3: "512 bits",
        4: "1024 bits"
    }
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "head", "Header", stream, parent, "<")
        self.read("crc", "CRC (16 bits)", (FormatChunk, "uint16"), {"post": hexadecimal})
        self.read("type", "Type", (FormatChunk, "uint8"), {"post": hexadecimal})
        
        bits = (
            (1, "split_before", "Split before"),
            (1, "split_after", "Split after"),
            (1, "password", "Passowrd"),
            (1, "comment", "Has comment?"),
            (1, "solid", "Solid"),
#            (3, "window_size", "Window size"),
            (11, "raw", "Bits"),
        )
        self.read("flags", "Flags", (BitsChunk, BitsStruct(bits)))
        
        self.read("hdr_size", "Header size", (FormatChunk, "uint16"))
        self.read("pack_size", "Pack size", (FormatChunk, "uint32"), {"post": humanFilesize})
        self.read("unpack_size", "Unpack size", (FormatChunk, "uint32"), {"post": humanFilesize})
        self.read("os", "Host OS", (FormatChunk, "uint8"))
        self.read("crc32", "File CRC32", (FormatChunk, "uint32"), {"post": hexadecimal})
        self.read("time", "File timestamp", (FormatChunk, "uint32"), {"post": unixTimestamp})
        self.read("unp_ver", "Unpacker version(?)", (FormatChunk, "uint8"))
        self.read("method", "Compression method", (FormatChunk, "uint8"))
        self.read("name_len", "Name size", (FormatChunk, "uint16"))
        self.read("file_attr", "File attributes", (FormatChunk, "uint32"))
        self.read("name", "File name", (StringChunk, "Fixed"), {"size": self["name_len"]})

    def updateParent(self, chunk):
        chunk.description = "File: %s" % (self["name"])

class RAR_File(OnDemandFilter):
    handler = {
        0x73: ("main_head", "Main header", (MainHeader,)),
        0x74: ("file_head", "File header", (FileHeader,))
    }
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "rar_file", "RAR archive file", stream, parent, "<")

        # Read header:
        # - "Rar!\x1A\x07\x00" is RAR v2.0 header
        # - "UniquE!" is Unique RAR header (generated with UniquE RAR library?)
        # - "\x52\x45\x7e\x5e" ("RE~^") is old header (not supported)
        self.read("id", "RAR identifier", (FormatChunk, "string[7]"))
        assert self["id"] in ("Rar!\x1A\x07\x00", "UniquE!")

        # Read blocks
        while not stream.eof():
            # Read type
            stream.seek(2, 1)
            type = stream.getFormat("uint8", False)
            stream.seek(-2, 1)
            if type not in RAR_File.handler:
                print "RAR: unknow type=%02X" % type
                break
            handler = RAR_File.handler[type]
            self.read(*handler)
        self.addPadding()

registerPlugin(RAR_File, "application/x-rar")
