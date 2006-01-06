from chunk import FormatChunk
from filter import OnDemandFilter

# TODO: Merge RGB and RGBA classes? (same for Palette and PaletteRGBA)

class RGB(OnDemandFilter):
    name = {
        0x000000: "Black",
        0xFFFFFF: "White"
    }
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "rgb_color", "RGB color", stream, parent, "!")
        self.read("red", "Red", (FormatChunk, "uint8"))
        self.read("green", "Green", (FormatChunk, "uint8"))
        self.read("blue", "Blue", (FormatChunk, "uint8"))

    def getStaticSize(stream, args):
        return 3 
    getStaticSize = staticmethod(getStaticSize)

    def updateParent(self, chunk):
        value = (self["red"] << 16) + (self["green"] << 8) + self["blue"]
        if value in RGB.name:
            chunk.description = "RGB color: "+RGB.name[value]
        else:
            chunk.description = "RGB color: #%02X%02X%02X" % (self["red"], self["green"], self["blue"])

class Palette(OnDemandFilter):
    def __init__(self, stream, parent, count):
        OnDemandFilter.__init__(self, "palette", "Palette of %u RGB colors" % count, stream, parent)
        for i in range(0, count):
            self.read("color[]", "Color", (RGB,))
            
class RGBA(OnDemandFilter):
    name = {
        0x000000: "Black",
        0xFFFFFF: "White"
    }
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "rgb_color", "RGB color", stream, parent, "!")
        self.read("red", "Red", (FormatChunk, "uint8"))
        self.read("green", "Green", (FormatChunk, "uint8"))
        self.read("blue", "Blue", (FormatChunk, "uint8"))
        self.read("alpha", "Blue", (FormatChunk, "uint8"))

    def getStaticSize(stream, args):
        return 4
    getStaticSize = staticmethod(getStaticSize)

    def updateParent(self, chunk):
        value = (self["red"] << 16) + (self["green"] << 8) + self["blue"]
        desc = "RGBA color: "
        if value in RGB.name:
            desc += RGB.name[value]
        else:
            desc += "#%02X%02X%02X" % (self["red"], self["green"], self["blue"])
        chunk.description = desc+", opacity=%u%%" % (self["alpha"]*100/256)

class PaletteRGBA(OnDemandFilter):
    def __init__(self, stream, parent, count):
        OnDemandFilter.__init__(self, "palette", "Palette of %u RGBA colors" % count, stream, parent)
        for i in range(0, count):
            self.read("color[]", "Color", (RGBA,))