"""
PNG splitter.

Status: split into chunks, can only resplit tIME chunk.
Author: Victor Stinner
"""

from stream import StringStream, LimitedFileStream
from filter import Filter
from plugin import registerPlugin

def displayPng(png):
    for chunk in png.chunks:
        if issubclass(chunk.data.__class__, Filter):
            print chunk.data
        else:
            print "(unknow chunk type \"%s\")" % chunk.type

class PngHeader(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("width", "!L", "Width (pixels)")
        self.read("height", "!L", "Height (pixels)")
        self.read("bit_depth", "!B", "Bit depth")
        self.read("color_type", "!B", "Color type")
        self.read("compression_method", "!B", "Compression method")
        self.read("filter_method", "!B", "Filter method")
        self.read("interlace_method", "!B", "Interlace method")

    def __str__(self):
        return "PNG header <size=%ux%u, depth=%u bits/pixel>" % \
            (self.width, self.height,
             self.bit_depth)

class PngPhysical(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("pixel_per_unit_x", "!L", "Pixel per unit, X axis")
        self.read("pixel_per_unit_y", "!L", "Pixel per unit, Y axis")
        self.read("unit_type", "!B", "Unit type")

    def __str__(self):
        if self.unit_type=="0":
            unit = "unknow"
        else:
            unit = "meter"
        return "PNG physical chunk <pixel per unit=(%u,%u), unit=%s>" % \
            (self.pixel_per_unit_x, self.pixel_per_unit_y, unit)

class PngGamma(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("gamma", "!L", "Gamma (divided by 10,000)")
        self.gamma = float(self.gamma)
        self.gamma = self.gamma / 10000

    def __str__(self):
        return "PNG gamma <gamma=%0.2f>" % (self.gamma)

class PngText(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        old = self.stream.tell()
        pos = self.stream.search("\0", 14)
        if pos == -1:
            raise Exception("Fails to find end of text")
        self.read("keyword", "!%us" % (pos-old), "Keyword")
        self.read("separator", "!B", "Null byte used to separe strings")
        lg = self.stream.getLastPos()-self.stream.tell()
        self.read("text", "!%us" % lg, "Text")

    def __str__(self):
        return "PNG text <keyword=\"%s\", text=\"%s\">" % \
            (self.keyword, self.text)

class PngTime(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("year", "!H", "Year")
        self.read("month", "!B", "Month")
        self.read("day", "!B", "Day")
        self.read("hour", "!B", "Hour")
        self.read("minute", "!B", "Minute")
        self.read("second", "!B", "Second")

    def __str__(self):
        return "PNG time chunk <%04u-%02u-%02u %02u:%02u:%02u>" % \
            (self.year, self.month, self.day,
             self.hour, self.minute, self.second)

class PngFilter(Filter):
    """
    Split a PNG file into chunks.
    """

    def __init__(self, stream):
        Filter.__init__(self, stream)
        self.read("header", "8s", "File header")
        assert self.header == "\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"
        self.chunks = []
        self.openChild()
        while not self.stream.eof():
            self.newChild("New chunk")
            chunk = PngChunk(stream, parent=self)
            self.chunks.append( chunk )

        self.closeChild("Chunks")
        
class PngChunk(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, stream, parent)
        self.read("size", "!L", "Chunk size")
        self.read("type", "!4s", "Chunk type")
        self.chunk_splitter = {
            "tIME": PngTime,
            "pHYs": PngPhysical,
            "IHDR": PngHeader,
            "gAMA": PngGamma,
            "tEXt": PngText
        }
        if self.type in self.chunk_splitter:
            self.openChild()
            self.newChild("Chunk data (type %s)" % self.type)
            func = self.chunk_splitter[self.type]
            new_stream = LimitedFileStream( self.stream.filename, self.stream.tell(), self.size )
            self.data = func(new_stream, self)            
            self.stream.seek(self.stream.tell() + self.size)
            self.closeChild("Chunk data (type %s)" % self.type)
        else:
            self.read("data", "![size]s", "Chunk data")
        self.read("crc32", "!L", "Chunk CRC32")

    def __str__(self):
        return "PngChunk <size=%u, type=%s>" % (self.size, self.type)

registerPlugin("^.*\.(PNG|png)$", "PNG picture", PngFilter, displayPng)
