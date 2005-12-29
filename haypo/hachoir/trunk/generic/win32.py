"""
Windows (Win32) structures parsers.
"""

from filter import OnDemandFilter
from chunk import FormatChunk, EnumChunk

class BitmapInfoHeader(OnDemandFilter):
    """ Win32 BITMAPINFOHEADER structure from GDI """

    compression_name = {
        0: "Uncompressed (RGB)",
        1: "RLE (8 bits)",
        2: "RLE (4 bits)",
        3: "Bitfields",
        4: "JPEG",
        5: "PNG"
    }
    
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "icon_header3", "Icon header3", stream, parent, "<")
        self.read("hdr_size", "Header size (in bytes) (=40)", (FormatChunk, "uint32"))
        assert self["hdr_size"] == 40
        self.read("width", "Width", (FormatChunk, "uint32"))
        self.read("height", "Height", (FormatChunk, "uint32"))
        self.read("planes", "Color planes", (FormatChunk, "uint16"))
        assert self["planes"] == 1
        self.read("bpp", "Bits/pixel", (FormatChunk, "uint16"))
        self.read("compression", "Compression", (EnumChunk, "uint32", BitmapInfoHeader.compression_name))
        self.read("size", "Image size (in bytes)", (FormatChunk, "uint32"))
        self.read("xres", "X pixels per meter", (FormatChunk, "uint32"))
        self.read("yres", "Y pixels per meter", (FormatChunk, "uint32"))
        self.read("color_used", "Number of used colors", (FormatChunk, "uint32"))
        self.read("color_important", "Number of important colors", (FormatChunk, "uint32"))

    def getStaticSize(stream, args):
        return 40 
    getStaticSize = staticmethod(getStaticSize)

    def updateParent(self, chunk):
        chunk.description = "Bitmap info header: %ux%u pixels, %u bits/pixel" \
            % (self["width"], self["height"], self["bpp"])
