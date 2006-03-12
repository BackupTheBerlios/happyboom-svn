"""
Microsoft Bitmap picture parser.
- file extension: ".bmp"

Author: Victor Stinner
Creation: 16 december 2005
"""

from field import FieldSet, Integer, RawBytes, ParserError, Enum

class BmpFile(FieldSet):
    mime_types = ["image/x-ms-bmp", "image/x-bmp"]
    endian = "<"

    compression_name = {
        0: "Uncopressed",
        1: "RLE"
    }        
    
    def createFields(self):
        yield RawBytes(self, "header", 2, "Header (\"BM\")")
        if self["header"].value != "BM": 
            raise ParserError(
                "BMP picture parser error: indentifier is uncorrect")
        yield Integer(self, "file_size", "uint32", "File size (bytes)")
        yield Integer(self, "notused", "uint32", "Reseved")
        yield Integer(self, "data_start", "uint32", "Data start position")
        yield Integer(self, "header_size", "uint32", "Header size")
        if self["header_size"].value not in (12, 40):
            raise ParserError(
                "BMP picture parser error: header size is uncorrect " \
                "(%s instead of 12 or 40)" % \
                self["header_size"].value)
        yield Integer(self, "width", "uint32", "Width (pixels)")
        yield Integer(self, "height", "uint32", "Height (pixels)")
        yield Integer(self, "nb_plan", "uint16", "Number of plan (=1)")
        yield Integer(self, "bpp", "uint16", "Bits per pixel")
        if self["header_size"].value == 40:
            yield Enum(self, "compression", "uint32", BmpFile.compression_name, "Compression method")
            yield Integer(self, "image_size", "uint32", "Image size (bytes)")
            yield Integer(self, "horizontal_dpi", "uint32", "Horizontal DPI")
            yield Integer(self, "vertical_dpi", "uint32", "Vertical DPI")
            yield Integer(self, "used_colors", "uint32", "Number of color used")
            yield Integer(self, "important_color", "uint32", "Number of import colors")
#        self.addPadding("data", "Image raw data")

