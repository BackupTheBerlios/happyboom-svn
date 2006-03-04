"""
PCX picture filter.
"""

from field import FieldSet, Integer, String
from common import Palette

class PcxFile(FieldSet):
    endian = "<"
    mime_types = "image/x-pcx"
    compression_name = { 1: "RLE" }

    def createFields(self):
        yield Integer(self, "id", "uint8", "PCX identifier (10)")
        if self["id"].value != 10:
            raise ParserError("PCX parser: wrong identifier (%u instead of 10)" \
                % self["id"].value)
        yield Integer(self, "version", "uint8", "PCX version")
        yield Integer(self, "compression", "uint8", "Compression") # (EnumChunk, , PCX_File.compression_name)
        yield Integer(self, "bpp", "uint8", "Bits / pixel")
        yield Integer(self, "xmin", "uint16", "Minimum X")
        yield Integer(self, "ymin", "uint16", "Minimum Y")
        yield Integer(self, "xmax", "uint16", "Width minus one") # value + 1
        yield Integer(self, "ymax", "uint16", "Height minus one") # value + 1
        yield Integer(self, "horiz_dpi", "uint16", "Horizontal DPI")
        yield Integer(self, "vert_dpi", "uint16", "Vertical DPI")
        yield Palette(self, "palette_4bits", 16, "Palette (4 bits)")
        yield Integer(self, "reserved", "uint8", "Reserved")
        yield Integer(self, "nb_color_plan", "uint8", "Number of color plans")
        yield Integer(self, "bytes_per_line", "uint16", "Bytes per line")
        yield Integer(self, "color_mode", "uint16", "Color mode")
        yield String(self, "reserved2", "string[58]", "Reserved")

        size = self.stream.getSize() - self.stream.tell()
        has_palette = (self["bpp"].value == 8)
        if has_palette:
            size -= 256*3*8            
        yield String(self, "data", "string[%u]" % size, "Image data")

        if has_palette:
            yield Palette(self, "palette_8bits", 256, "Palette (8 bit)")

