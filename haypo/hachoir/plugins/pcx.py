"""
PCX picture filter.
"""

from filter import Filter, DeflateFilter
from plugin import registerPlugin
from stream.file import FileStream
from cStringIO import StringIO

class RGB(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "rgb_color", "RGB color (8 bits/component)", stream, parent)
        self.read("red", "B", "Red")
        self.read("green", "B", "Green")
        self.read("blue", "B", "Blue")

class Palette(Filter):
    def __init__(self, stream, parent, count):
        Filter.__init__(self, "rgb_color", "RGB color (8 bits/component)", stream, parent)
        for i in range(0, count):
            self.readChild("color[]", RGB)

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

class PCX_Content(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "pcx_content", "PCX content", stream, parent)
        pcx = parent.getParent()
        bytes_per_line = pcx["bytes_per_line"]
        height = pcx["bytes_per_line"]
        for y in range(0, height):
            self.read("line[]", "%us" % bytes_per_line, "Line")

class PCX_File(Filter):
    compression_name = {
        1: "RLE"
    }
    def __init__(self, stream, parent):
        Filter.__init__(self, "pcx_file", "PCX picture", stream, parent)
        id = self.read("id", "B", "PCX identifier (10)").value
        assert id == 10
        self.read("version", "B", "PCX version")
        self.read("compression", "B", "Compression", post=self.postCompression)
        self.bpp = self.read("bpp", "B", "Bits / pixel").value
        # TODO: Support 4 and 24 bits/pxiel
        assert self.bpp == 8
        self.read("xmin", "<H", "Minimum X")
        self.read("ymin", "<H", "Minimum Y")
        self.width = self.read("width", "<H", "Width minus one").value+1
        self.height = self.read("height", "<H", "Height minus one").value+1
        self.read("horiz_dpi", "<H", "Horizontal DPI")
        self.read("vert_dpi", "<H", "Vertical DPI")
        self.readChild("palette_4bits", Palette, 16)
        self.read("reserved", "B", "Reserved")
        self.read("nb_color_plan", "B", "Number of color plans")
        self.read("bytes_per_line", "<H", "Bytes per line")
        self.read("color_mode", "<H", "Color mode")
        self.read("reserved2", "58s", "Reserved")

        size = stream.getSize() - stream.tell()
        if self.bpp == 8:
            size = size - 256*3
        deflate = StreamDeflateRLE(self, stream, size)
        self.readChild("data", DeflateFilter, deflate, size, PCX_Content)
        if self.bpp == 8:
            self.readChild("palette_8bits", Palette, 256)

    def postCompression(self, chunk):
        mode = chunk.value
        return PCX_File.compression_name.get(mode, "Unknow (%s)" % mode)

registerPlugin(PCX_File, "image/x-pcx")
