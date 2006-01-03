"""
Microsoft Bitmap picture parser.
- file extension: ".bmp"

Author: Victor Stinner
Creation: 16 december 2005
"""

from filter import OnDemandFilter
from chunk import FormatChunk
from plugin import registerPlugin

class BitmapFile(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "bmp_file", "Bitmap picture file (BMP)", stream, parent, "<")
        self.read("header", "Header (\"BM\")", (FormatChunk, "string[2]"))
        self.read("file_size", "File size (bytes)", (FormatChunk, "uint32"))
        self.read("notused", "Reseved", (FormatChunk, "uint32"))
        self.read("data_start", "Data start position", (FormatChunk, "uint32"))
        header_size = self.doRead("header_size", "Header size", (FormatChunk, "uint32")).value
        assert self["header_size"] in (12, 40)
        self.read("width", "Width (pixels)", (FormatChunk, "uint32"))
        self.read("height", "Height (pixels)", (FormatChunk, "uint32"))
        self.read("nb_plan", "Number of plan (=1)", (FormatChunk, "uint16"))
        self.read("bits_pixel", "Bits per pixel", (FormatChunk, "uint16"))
        if header_size == 40:
            self.read("compression", "Compression method", (FormatChunk, "uint32"))
            self.read("image_size", "Image size (bytes)", (FormatChunk, "uint32"))
            self.read("horizontal_dpi", "Horizontal DPI", (FormatChunk, "uint32"))
            self.read("vertical_dpi", "Vertical DPI", (FormatChunk, "uint32"))
            self.read("used_colors", "Number of color used", (FormatChunk, "uint32"))
            self.read("important_color", "Number of import colors", (FormatChunk, "uint32"))
        size = stream.getSize() - stream.tell()            
        self.read("data", "Image raw data", (FormatChunk, "string[%u]" % size))

registerPlugin(BitmapFile, "image/x-ms-bmp")
