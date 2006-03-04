from field import FieldSet, Integer, RawBytes, Bit, Bits, ParserError
from common import RGB
from bits import str2hex
from text_handler import hexadecimal

class HeaderFlags(FieldSet):
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
        yield HeaderFlags(self, "color_type", self.stream, "Color type")
        yield Integer(self, "compression", "uint8", "Compression method")
        yield Integer(self, "filter", "uint8", "Filter method")
        yield Integer(self, "interlace", "uint8", "Interlace method")

    def updateParent(self, chunk):
        chunk.description = "Header: %ux%u pixels and %u bits/pixel" \
            % (self["width"], self["height"], self["bpp"])

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

class Chunk(FieldSet):
    handler = {
#        "tIME": Time,
#        "pHYs": Physical,
        "IHDR": Header,
        "PLTE": Palette,
#        "gAMA": Gamma,
#        "tEXt": Text
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
            size = self["size"]
#            oldpos = self._stream.tell()
#            sub = stream.createLimited(size=size)
            cls = self.handler[type]
            yield cls(self, "content", self.stream)
#            assert stream.tell() == (oldpos + size) 
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

