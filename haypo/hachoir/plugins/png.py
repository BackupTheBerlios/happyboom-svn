"""
PNG splitter.

Status: split into chunks, can only resplit tIME chunk.
Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin

class PngHeader(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "png_header", "PNG header", stream, parent)
        self.read("width", "!L", "Width (pixels)")
        self.read("height", "!L", "Height (pixels)")
        self.read("bit_depth", "!B", "Bit depth")
        self.read("color_type", "!B", "Color type")
        self.read("compression_method", "!B", "Compression method")
        self.read("filter_method", "!B", "Filter method")
        self.read("interlace_method", "!B", "Interlace method")

    def __str__(self):
        return "PNG header <size=%ux%u, depth=%u bits/pixel>" % \
            (self["width"], self["height"],
             self["bit_depth"])

class PngPhysical(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "png_physical", "PNG physical", stream, parent)
        self.read("pixel_per_unit_x", "!L", "Pixel per unit, X axis")
        self.read("pixel_per_unit_y", "!L", "Pixel per unit, Y axis")
        self.read("unit_type", "!B", "Unit type")

    def __str__(self):
        if self["unit_type"] == 0:
            unit = "unknow"
        else:
            unit = "meter"
        return "PNG physical chunk <pixel per unit=(%u,%u), unit=%s>" % \
            (self["pixel_per_unit_x"], self["pixel_per_unit_y"], unit)

class PngGamma(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "png_gamma", "PNG gamma", stream, parent)
        self.read("gamma", "!L", "Gamma (x10,000)", post=self.getGamma)

    def getGamma(self, chunk):
        return float(chunk.value) / 10000

    def __str__(self):
        return "PNG gamma <gamma=%0.2f>" % (self["gamma"])

class PngText(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "png_text", "PNG text", stream, parent)
        chunk = self.readString("keyword", "C", "Keyword")
        lg = stream.getSize() - chunk.size
        self.read("text", "!%us" % lg, "Text")

    def __str__(self):
        return "PNG text <keyword=\"%s\", text=\"%s\">" % \
            (self["keyword"], self["text"])

class PngTime(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "png_time", "PNG time", stream, parent)
        self.read("year", "!H", "Year")
        self.read("month", "!B", "Month")
        self.read("day", "!B", "Day")
        self.read("hour", "!B", "Hour")
        self.read("minute", "!B", "Minute")
        self.read("second", "!B", "Second")

    def __str__(self):
        return "PNG time chunk <%04u-%02u-%02u %02u:%02u:%02u>" % \
            (self["year"], self["month"], self["day"],
             self["hour"], self["minute"], self["second"])
        
class PngChunk(Filter):
    handler = {
        "tIME": PngTime,
        "pHYs": PngPhysical,
        "IHDR": PngHeader,
        "gAMA": PngGamma,
        "tEXt": PngText
    }
    def __init__(self, stream, parent):
        Filter.__init__(self, "png_chunk", "PNG chunk", stream, parent)
        self.read("size", "!L", "Chunk size")
        self.read("type", "!4s", "Chunk type")
        type = self["type"]
        if type in PngChunk.handler:
            size = self["size"]
            oldpos = self._stream.tell()
            sub = stream.createSub(size=size)
            self.readStreamChild("chunk_data", sub, PngChunk.handler[type])
            assert stream.tell() == (oldpos + size) 
        else:
            self.read("data", "!{size}s", "Chunk data")
        self.read("crc32", "!L", "Chunk CRC32")

    def updateParent(self, chunk):
        self.description = "PNG chunk (type %s)" % self["type"]
        chunk.description = "PNG chunk (type %s)" % self["type"]

    def __str__(self):
        return "PngChunk <size=%u, type=%s>" % (self["size"], self["type"])

class PngFile(Filter):
    """
    Split a PNG file into chunks.
    """

    def __init__(self, stream, parent=None):
        Filter.__init__(self, "png_file", "PNG file", stream, parent)
        self.read("header", "!8s", "File header")
        assert self["header"] == "\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"
        while not stream.eof():
            self.readChild("chunks[]", PngChunk)

registerPlugin(PngFile, ["image/png", "image/x-png"])
