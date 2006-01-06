"""
PNG picture parser.

Author: Victor Stinner
"""

import datetime
from filter import OnDemandFilter
from chunk import FormatChunk, StringChunk, EnumChunk, BitsStruct, BitsChunk
from plugin import registerPlugin
from text_handler import hexadecimal
from generic.image import RGB

class Palette(OnDemandFilter):
    def __init__(self, stream, parent):
        size = stream.getSize()
        assert (size % 3) == 0
        count = size / 3
        OnDemandFilter.__init__(self, "palette", "Palette: %u colors" % count, stream, parent, "!")
        for i in range(0, count):
            self.read("color[]", "Color", (RGB,))

class Header(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "header", "Header", stream, parent, "!")
        self.read("width", "Width (pixels)", (FormatChunk, "uint32"))
        self.read("height", "Height (pixels)", (FormatChunk, "uint32"))
        self.read("bpp", "Bits per pixel", (FormatChunk, "uint8"))
        bits = (
            (1, "palette", "Palette used?"),
            (1, "color", "Color used?"),
            (1, "alpha", "Alpha channel used?"),
            (5, "reserved", "(reserved)"))
        self.read("color_type", "Color type", (BitsChunk, BitsStruct(bits)))
        self.read("compression", "Compression method", (FormatChunk, "uint8"))
        self.read("filter", "Filter method", (FormatChunk, "uint8"))
        self.read("interlace", "Interlace method", (FormatChunk, "uint8"))

    def updateParent(self, chunk):
        chunk.description = "Header: %ux%u pixels and %u bits/pixel" \
            % (self["width"], self["height"], self["bpp"])

class Physical(OnDemandFilter):
    unit_name = {
        0: "Unknow",
        1: "Meter"
    }
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "physical", "Physical", stream, parent, "!")
        self.read("pixel_per_unit_x", "Pixel per unit, X axis", (FormatChunk, "uint32"))
        self.read("pixel_per_unit_y", "Pixel per unit, Y axis", (FormatChunk, "uint32"))
        self.read("unit", "Unit type", (EnumChunk, "uint8", Physical.unit_name))

    def updateParent(self, chunk):
        x = self["pixel_per_unit_x"]
        y = self["pixel_per_unit_y"]
        desc = "Physical: %ux%u pixels" % (x,y)
        if self["unit"] == 1:
            desc += " per meter"
        chunk.description = desc 

class Gamma(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "gamma", "Gamma", stream, parent, "!")
        self.read("gamma", "Gamma (x10,000)", (FormatChunk, "uint32"), {"post": self.getGamma})

    def getGamma(self, chunk):
        return float(chunk.value) / 10000

class Text(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "text", "Text", stream, parent)
        chunk = self.doRead("keyword", "Keyword", (StringChunk, "C"))
        lg = stream.getSize() - chunk.size
        self.read("text", "Text", (FormatChunk, "string[%u]" % lg))

    def updateParent(self, chunk):
        text = self.getChunk("text").getValue(40)
        chunk.description = "Text: \"%s\"" % text        

class Time(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "time", "Time", stream, parent, "!")
        self.read("year", "Year", (FormatChunk, "uint16"))
        self.read("month", "Month", (FormatChunk, "uint8"))
        self.read("day", "Day", (FormatChunk, "uint8"))
        self.read("hour", "Hour", (FormatChunk, "uint8"))
        self.read("minute", "Minute", (FormatChunk, "uint8"))
        self.read("second", "Second", (FormatChunk, "uint8"))

    def updateParent(self, chunk):
        time = datetime.datetime(self["year"], self["month"], self["day"], self["hour"], self["minute"], self["second"])
        chunk.description = "Time: %s" % time

class Chunk(OnDemandFilter):
    handler = {
        "tIME": Time,
        "pHYs": Physical,
        "IHDR": Header,
        "PLTE": Palette,
        "gAMA": Gamma,
        "tEXt": Text
    }
    name = {
        "tIME": ("time", "Time"),
        "pHYs": ("physical", "Physical"),
        "IHDR": ("header", "Header"),
        "PLTE": ("palette", "Palette"),
        "gAMA": ("gamma", "Gamma"),
        "IDAT": ("data[]", "Image data"),
        "IEND": ("end", "End"),
        "tEXt": ("text", "Text")
    }
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "chunk", "Chunk", stream, parent, "!")
        self.read("size", "Size", (FormatChunk, "uint32"))
        self.read("type", "Type", (FormatChunk, "string[4]"))
        type = self["type"]
        if type in Chunk.handler:
            size = self["size"]
            oldpos = self._stream.tell()
            sub = stream.createLimited(size=size)
            handler = Chunk.handler[type]
            self.data = self.doRead("data", "Data", (handler,), {"stream": sub, "size": size})
            assert stream.tell() == (oldpos + size) 
        else:
            self.read("data", "Data", (FormatChunk, "string[%u]" % self["size"]))
            self.data = None
        self.read("crc32", "CRC32", (FormatChunk, "uint32"), {"post": hexadecimal})

    def updateParent(self, chunk):
        type = self["type"]
        if type in Chunk.name:
            name = Chunk.name[type]
            id = self.getParent().getUniqChunkId(name[0])
            self.setId(id)
            type = name[1] 
        else:
            type = "Unknow (%s)" % type
        if self.data:            
            desc = self.data.getDescription()
        else:
            desc = "Chunk %s" % type
            type = self["type"]
            if type == "IEND":
                desc += ": end of file"
            elif type == "IDAT":
                desc += ": image data"
        chunk.description = desc

class PngFile(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "png", "PNG picture", stream, parent, "!")
        self.read("id", "PNG identifier", [FormatChunk, "string[8]"])
        assert self["id"] == "\x89PNG\r\n\x1A\n"
        while not stream.eof():
            size = 4*3 + stream.getFormat("!uint32", False)
            self.read("chunks[]", "Chunk", (Chunk,), {"size": size})

registerPlugin(PngFile, ["image/png", "image/x-png"])