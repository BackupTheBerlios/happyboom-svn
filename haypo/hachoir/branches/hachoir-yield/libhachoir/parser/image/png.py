"""
PNG picture file parser.

Author: Victor Stinner
"""

from field import ( \
    FieldSet, ParserError,
    Integer, RawBytes, Bit, Bits, Enum)
from common import RGB
from bits import str2hex
from text_handler import hexadecimal
import datetime

class ColorType(FieldSet):
    def createFields(self):
        yield Bit(self, "palette", "Palette used?")
        yield Bit(self, "color", "Color used?")
        yield Bit(self, "alpha", "Alpha channel used?")
        yield Bits(self, "reserved", 5, "(reserved)")

class Header(FieldSet):
    def createFields(self):
        yield Integer(self, "width", "uint32", "Width (pixels)")
        yield Integer(self, "height", "uint32", "Height (pixels)")
        yield Integer(self, "bpp", "uint8", "Bits per pixel")
        yield ColorType(self, "color_type", self.stream, "Color type")
        yield Integer(self, "compression", "uint8", "Compression method")
        yield Integer(self, "filter", "uint8", "Filter method")
        yield Integer(self, "interlace", "uint8", "Interlace method")

    def _getDescription(self):
        if self._description == None:
            self._description = "Header: %ux%u pixels and %u bits/pixel" \
                % (self["width"].value, self["height"].value, self["bpp"].value)
        return self._description
    description = property(_getDescription, FieldSet._setDescription)

class Palette(FieldSet):
    def __init__(self, parent, name, stream, description=None):
        size = parent["size"].value
        if (size % 3) != 0:
            raise ParserError("Palette have invalid size (%s), should be 3*n." % size)
        self.nb_colors = size / 3
        if description == None:
            description = "Palette: %u colors" % self.nb_colors
        FieldSet.__init__(self, parent, name, stream, description)

    def createFields(self):
        for i in range(self.nb_colors):
            yield RGB(self, "color[]", self.stream)

class Gamma(FieldSet):
    static_size = 32

    def createFields(self):
        yield Integer(self, "gamma", "uint32", "Gamma (x10,000)", \
            text_handler=self.getGamma)

    def getGamma(self, chunk):
        return float(chunk.value) / 10000

class Text(FieldSet):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "text", "Text", stream, parent)
        kw = String(self, "keyword", "C", "Keyword")
        yield kw
        lg = self["../size"].value - kw.size/8
        yield String(self, "text", "string[%u]" % lg, "Text")

    def _getDescription(self):
        if self._description == None:
            self._description = 'Text: "%s"' % self["text"].display
        return self._description
    description = property(_getDescription, FieldSet._setDescription)

class Time(FieldSet):
    endian = "!"
    static_size = 7*8

    def createFields(self):
        yield Integer(self, "year", "uint16", "Year")
        yield Integer(self, "month", "uint8", "Month")
        yield Integer(self, "day", "uint8", "Day")
        yield Integer(self, "hour", "uint8", "Hour")
        yield Integer(self, "minute", "uint8", "Minute")
        yield Integer(self, "second", "uint8", "Second")

    def _getDescription(self):
        if self._description == None:
            time = datetime.datetime( \
                self["year"].value, self["month"].value, self["day"].value, \
                self["hour"].value, self["minute"].value, self["second"].value)
            self._description = "Time: %s" % time
        return self._description
    description = property(_getDescription, FieldSet._setDescription)

class Physical(FieldSet):
    unit_name = {
        0: "Unknow",
        1: "Meter"
    }

    def createFields(self):
        yield Integer(self, "pixel_per_unit_x", "uint32", "Pixel per unit, X axis")
        yield Integer(self, "pixel_per_unit_y", "uint32", "Pixel per unit, Y axis")
        yield Enum(self, "unit", "uint8", Physical.unit_name, "Unit type")

    def _getDescription(self):
        if self._description == None:
            x = self["pixel_per_unit_x"].value
            y = self["pixel_per_unit_y"].value
            self._description = "Physical: %ux%u pixels" % (x,y)
            if self["unit"].value == 1:
                self._description += " per meter"
        return self._description
    description = property(_getDescription, FieldSet._setDescription)

class Chunk(FieldSet):
    handler = {
        "tIME": Time,
        "pHYs": Physical,
        "IHDR": Header,
        "PLTE": Palette,
        "gAMA": Gamma,
        "tEXt": Text
    }
    name_by_type = {
        "tIME": ("time", "Time"),
        "pHYs": ("physical", "Physical"),
        "IHDR": ("header", "Header"),
        "PLTE": ("palette", "Palette"),
        "gAMA": ("gamma", "Gamma"),
        "IDAT": ("data[]", "Image data"),
        "IEND": ("end", "End"),
        "tEXt": ("text", "Text")
    }
    
    def __init__(self, parent, name, stream, description=None):
        FieldSet.__init__(self, parent, name, stream, description)
        self._size = (self["size"].value + 3*4) * 8

        type = self["type"].value
        if type in self.name_by_type:
            name = self.name_by_type[type]
            self._name = name[0]

    def createFields(self):
        yield Integer(self, "size", "uint32", "Size")
        yield RawBytes(self, "type", 4, "Type")

        type = self["type"].value
        if type in self.handler:
            cls = self.handler[type]
            yield cls(self, "content", self.stream)
            assert self["content"].size == self["size"].value*8
        else:
            yield RawBytes(self, "content", self["size"].value, "Data")
        yield Integer(self, "crc32", "uint32", "CRC32", text_handler=hexadecimal)

class PngFile(FieldSet):
    mime_types = ["image/png", "image/x-png"]

    def createFields(self):
        yield RawBytes(self, "id", 8, "PNG identifier") 
        if self["id"].value != "\x89PNG\r\n\x1A\n":
            raise ParserError("Png parser: file identifier looks wrong (%s instead of %s)" % \
                (str2hex(self["id"].value), str2hex("\x89PNG\r\n\x1A\n")))
        while True:
            field = Chunk(self, "chunks[]", self.stream)
            yield field
            if field.name == "end":
                break

