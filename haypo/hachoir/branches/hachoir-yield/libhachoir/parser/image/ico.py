"""
ICO picture file format parser.

Author: Victor Stinner
"""

from libhachoir.field import FieldSet, ParserError, Integer, Enum, RawBytes
from libhachoir.parser.image.common import PaletteRGBA

class BitmapInfoHeader(FieldSet):
    """ Win32 BITMAPINFOHEADER structure from GDI """

    static_size = 40*8

    compression_name = {
        0: "Uncompressed (RGB)",
        1: "RLE (8 bits)",
        2: "RLE (4 bits)",
        3: "Bitfields",
        4: "JPEG",
        5: "PNG"
    }
    endian = "<"
    
    def createFields(self):
        yield Integer(self, "hdr_size", "uint32", "Header size (in bytes) (=40)")
        if self["hdr_size"].value != 40:
            yield ParserError( \
                "Bitmap information header looks uncorrect "
                "(header size is %s instead of 40)" \
                % self["hdr_size"].value)
        yield Integer(self, "width", "uint32", "Width")
        yield Integer(self, "height", "uint32", "Height")
        yield Integer(self, "nb_planes", "uint16", "Color planes")
        assert self["nb_planes"].value == 1
        yield Integer(self, "bpp", "uint16", "Bits/pixel")
        yield Enum(self, "compression", "uint32", BitmapInfoHeader.compression_name, "Compression")
        yield Integer(self, "size", "uint32", "Image size (in bytes)")
        yield Integer(self, "xres", "uint32", "X pixels per meter")
        yield Integer(self, "yres", "uint32", "Y pixels per meter")
        yield Integer(self, "color_used", "uint32", "Number of used colors")
        yield Integer(self, "color_important", "uint32", "Number of important colors")

    def _getDescription(self):
        if self._description == None:
            self.description = "Bitmap info header: %ux%u pixels, %u bits/pixel" % \
                (self["width"].value, self["height"].value,
                 self["bpp"].value)
        return self._description
    description = property(_getDescription, FieldSet._setDescription)

class IconHeader(FieldSet):
    endian = "<"

    def createFields(self):
        yield Integer(self, "width", "uint8", "Width")
        yield Integer(self, "height", "uint8", "Height")
        yield Integer(self, "nb_color", "uint8", "Number of colors")
        yield Integer(self, "reserved", "uint8", "(reserved)")
        yield Integer(self, "planes", "uint16", "Color planes (=1)")
        if self["planes"].value != 1:
            raise ParserError( \
                "Stream doesn't looks like an icon header "
                "(wrong plan count)!")
        yield Integer(self, "bpp", "uint16", "Bits per pixel")
        yield Integer(self, "size", "uint32", "Content size in bytes")
        yield Integer(self, "offset", "uint32", "Data offset")

    def _getDescription(self):
        if self._description == None:
            self._description = "Icon: %ux%u pixels, %u bits/pixel" \
                % (self["width"].value, self["height"].value, self["bpp"].value)
        return self._description
    description = property(_getDescription, FieldSet._setDescription)

class IconData(FieldSet):
    def __init__(self, parent, name, header, description="Icon data"):
        FieldSet.__init__(self, parent, name, parent.stream, description=description)
        self.header = header

    def createFields(self):
        yield BitmapInfoHeader(self, "header", self.stream)
        
        # Read palette if needed
        nb_color = self.header["nb_color"].value
        if self.header["bpp"].value == 8:
            nb_color = 256
        if nb_color != 0:            
            yield PaletteRGBA(self, "palette", nb_color)

        # Read pixels
        size = self.header["size"].value - self.newFieldAskAddress()/8
        yield RawBytes(self, "pixels", size, "Image pixels")

class IcoFile(FieldSet):
    mime_types = "image/x-ico"
    type_name = {
        1: "Icon",
        2: "Mouse cursor"
    }
    endian = "<"

    def createFields(self):
        yield Integer(self, "id", "uint16", "Identifier (0x0000)")
        if self["id"].value != 0:
            raise ParserError(
                "Stream doesn't look like an windows icon file "
                "(wrong file identifier)")
        yield Enum(self, "type", "uint16", IcoFile.type_name, "Resource type")
        yield Integer(self, "nb_items", "uint16", "Number of items")
        items = []
        for i in range(0, self["nb_items"].value):
            item = IconHeader(self, "icon_header[]", self.stream, "Icon header %u" % i)
            yield item
            items.append(item)
        for header in items:
            assert header["offset"].value*8 == self.newFieldAskAddress()
            yield IconData(self, "icon_data[]", header)

