from field import FieldSet, Integer, String, IntegerHex, Bit, Bits, ParserError
from generic.image import RGB
from bits import str2hex
from metadata import ImageMetaData

class PngMetaData(ImageMetaData):
    def __init__(self, png):
        header = png["/header/content"]
        color_type = header["color_type"]
        width, height = header["width"].value, header["height"].value
        bpp = header["bpp"].value
        if color_type["palette"].value:
            nb_colors = png["/palette/content"].nb_colors
        else:
            nb_colors = None
        if color_type["alpha"].value:
            format = "RGBA"
        else:
            format = "RGB"
#        if header["compression"].value != 0:
#            compression = "(compressed)"
#        else:
#            compression = "No"
        ImageMetaData.__init__(self, format, width, height, bpp, nb_colors=nb_colors)

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
        yield String(self, "type", "string[4]", "Type")

        type = self["type"].value
        if type in self.handler:
            size = self["size"]
#            oldpos = self._stream.tell()
#            sub = stream.createLimited(size=size)
            cls = self.handler[type]
            yield cls(self, "content", self.stream)
#            assert stream.tell() == (oldpos + size) 
        else:
            yield String(self, "content", "string[%u]" % self["size"].value, "Data")
        yield IntegerHex(self, "crc32", "uint32", "CRC32")

class PngFile(FieldSet):
    def createFields(self):
        yield String(self, "id", "string[8]", "PNG identifier") 
        if self["id"].value != "\x89PNG\r\n\x1A\n":
            raise ParserError("Png parser: file identifier looks wrong (%s instead of %s)" % \
                (str2hex(self["id"].value), str2hex("\x89PNG\r\n\x1A\n")))
        while True:
            field = Chunk(self, "chunks[]", self.stream)
            yield field
            if field.name == "end":
                break

