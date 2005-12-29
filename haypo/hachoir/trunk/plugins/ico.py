"""
ICO picture file format parser.

Author: Victor Stinner
"""

from filter import OnDemandFilter
from plugin import registerPlugin
from chunk import FormatChunk, EnumChunk
from generic.image import PaletteRGBA
from generic.win32 import BitmapInfoHeader

class IconData(OnDemandFilter):
    def __init__(self, stream, parent, header):
        OnDemandFilter.__init__(self, "icon_data", "Icon data", stream, parent, "<")
        start = stream.tell()
        self.read("header", "Header", (BitmapInfoHeader,))
        
        # Read palette if needed
        nb_color = header["nb_color"]
        if header["bpp"] == 8:
            nb_color = 256
        if nb_color != 0:            
            self.read("palette", "Palette", (PaletteRGBA, nb_color))

        # Read pixels
        size = header["width"] * header["height"] * header["bpp"] / 8
        self.read("pixels", "Image pixels", (FormatChunk, "string[%u]" % size))

        padding = stream.getLastPos() - stream.tell() + 1
        if 0 < padding:
            self.read("padding", "(padding)", (FormatChunk, "string[%u]" % padding))

class IconHeader(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "icon", "Icon header", stream, parent, "<")
        self.read("width", "Width", (FormatChunk, "uint8"))
        self.read("height", "Height", (FormatChunk, "uint8"))
        self.read("nb_color", "Number of colors", (FormatChunk, "uint8"))
        self.read("reserved", "(reserved)", (FormatChunk, "uint8"))
        self.read("planes", "Color planes (=1)", (FormatChunk, "uint16"))
        assert self["planes"] == 1
        self.read("bpp", "Bits per pixel", (FormatChunk, "uint16"))
        self.read("size", "Content size in bytes", (FormatChunk, "uint32"))
        self.read("offset", "Data offset", (FormatChunk, "uint32"))

    def updateParent(self, chunk):
        chunk.description = "Icon: %ux%u pixels, %u bits/pixel" \
            % (self["width"], self["height"], self["bpp"])

class IcoFile(OnDemandFilter):
    type_name = {
        1: "Icon",
        2: "Mouse cursor"
    }
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "ico_file", "ICO picture file", stream, parent, "<")
        self.read("id", "Identifier (\"\\0\\0\")", (FormatChunk, "string[2]"))
        assert self["id"] == "\0\0"
        self.read("type", "Resource type", (EnumChunk, "uint16", IcoFile.type_name))
        self.read("nb_items", "Number of items", (FormatChunk, "uint16"))
        items = []
        for i in range(0, self["nb_items"]):
            item = self.doRead("icon_header[]", "Icon header %u" % i, (IconHeader,))
            items.append(item)
        for header in items:
            assert header["offset"] == stream.tell()
            sub = stream.createLimited(size=header["size"])
            self.read("icon_data[]", "Icon data", (IconData, header), {"stream": sub})

registerPlugin(IcoFile, "image/x-ico")
