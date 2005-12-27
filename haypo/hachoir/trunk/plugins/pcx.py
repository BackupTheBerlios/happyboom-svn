"""
PCX picture filter.
"""

from filter import OnDemandFilter, DeflateFilter
from plugin import registerPlugin
from chunk import FormatChunk, EnumChunk
from stream.file import FileStream
from cStringIO import StringIO
from generic.image import RGB, Palette

def StreamDeflateRLE(filter, stream, size):
    start = stream.tell()
    end = start + size - 1
    data = ""
    width = filter.width
    for y in range(0, filter.height):
        line = ""
        while len(line) < width:
            character = stream.getN(1)
            byte = ord(character)
            if byte & 192 == 192:
                repeat = byte & 63
                character = stream.getN(1)
                line = line + character * repeat                
            else:
                line = line + character
        assert len(line) == width
        data = data + line
    assert stream.tell() == end
    stream.seek(start)
    return FileStream(StringIO(data),None)

class PCX_Content(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "pcx_content", "PCX content", stream, parent)
        pcx = parent.getParent()
        bytes_per_line = pcx["bytes_per_line"]
        height = pcx["bytes_per_line"]
        for y in range(0, height):
            self.read("line[]", "Line", (FormatChunk, "string[%u]" % bytes_per_line))

class PCX_File(OnDemandFilter):
    compression_name = {
        1: "RLE"
    }
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "pcx_file", "PCX picture", stream, parent, "<")
        self.read("id", "PCX identifier (10)", (FormatChunk, "uint8"))
        assert self["id"] == 10
        self.read("version", "PCX version", (FormatChunk, "uint8"))
        self.read("compression", "Compression", (EnumChunk, "uint8", PCX_File.compression_name))
        self.bpp = self.doRead("bpp", "Bits / pixel", (FormatChunk, "uint8")).value
        # TODO: Support 4 and 24 bits/pxiel
        assert self.bpp == 8
        self.read("xmin", "Minimum X", (FormatChunk, "uint16"))
        self.read("ymin", "Minimum Y", (FormatChunk, "uint16"))
        self.width = self.doRead("width", "Width minus one", (FormatChunk, "uint16")).value + 1
        self.height = self.doRead("height", "Height minus one", (FormatChunk, "uint16")).value + 1
        self.read("horiz_dpi", "Horizontal DPI", (FormatChunk, "uint16"))
        self.read("vert_dpi", "Vertical DPI", (FormatChunk, "uint16"))
        self.read("palette_4bits", "Palette (4 bits)", (Palette, 16))
        self.read("reserved", "Reserved", (FormatChunk, "uint8"))
        self.read("nb_color_plan", "Number of color plans", (FormatChunk, "uint8"))
        self.read("bytes_per_line", "Bytes per line", (FormatChunk, "uint16"))
        self.read("color_mode", "Color mode", (FormatChunk, "uint16"))
        self.read("reserved2", "Reserved", (FormatChunk, "string[58]"))

        size = stream.getSize() - stream.tell()
        if self.bpp == 8:
            size = size - 256*3
        deflate = StreamDeflateRLE(self, stream, size)
        self.read("data", "Data", (DeflateFilter, deflate, size, PCX_Content))
        if self.bpp == 8:
            self.read("palette_8bits", "Palette (8 bit)", (Palette, 256)) 

registerPlugin(PCX_File, "image/x-pcx")
