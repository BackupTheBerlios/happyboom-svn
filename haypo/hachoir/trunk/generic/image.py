from chunk import FormatChunk
from filter import OnDemandFilter

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
