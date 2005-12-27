"""
Gimp image parser (XCF file, ".xcf" extension).

You can find informations about XCF file in Gimp source code. URL to read
CVS online:
  http://cvs.gnome.org/viewcvs/gimp/app/xcf/

Author: Victor Stinner
"""

from filter import OnDemandFilter
from chunk import FormatChunk, StringChunk, EnumChunk
from plugin import registerPlugin

class XcfCompression(OnDemandFilter):
    name = {
        0: "None",
        1: "RLE",
        2: "Zlib",
        3: "Fractal"
    }

    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "compression", "Compression", stream, parent)
        self.read("compression", "Compression method", (EnumChunk, "uint8", XcfCompression.name))

class XcfResolution(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "resolution", "Resolution", stream, parent, "!")
        self.read("xres", "X resolution", (FormatChunk, "float"))
        self.read("yres", "Y resolution", (FormatChunk, "float"))

class XcfTattoo(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "tattoo", "Tattoo", stream, parent, "!")
        self.read("tattoo", "Tattoo", (FormatChunk, "uint32"))

class XcfUnit(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "unit", "Unit", stream, parent, "!")
        self.read("unit", "Unit", (FormatChunk, "uint32"))

class XcfParasiteEntry(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "xcf_para", "XCF parasite", stream, parent, "!")
        self.read("name", "Name", (StringChunk, "Pascal32"), {"strip": "\0", "charset": "utf-8"})
        self.read("flags", "Flags", (FormatChunk, "uint32"))
        self.read("size", "Size", (FormatChunk, "uint32"))
        if 0 < self["size"]:
            self.read("data", "Data", (FormatChunk, "string[%u]" % self["size"]))

class XcfLevel(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "xcf_level", "XCF level", stream, parent, "!")
        self.read("width", "Width", (FormatChunk, "uint32"))
        self.read("height", "Height", (FormatChunk, "uint32"))
        self.read("offset", "Offset", (FormatChunk, "uint32"))
        offset = self["offset"]
        if offset == 0:
            return
        data_offsets = []
        while stream.tell() < offset:
            chunk = self.doRead("data_offset[]", "Data offset", (FormatChunk, "uint32"))
            if chunk.value == 0:
                break
            data_offsets.append(chunk)
        assert stream.tell() == offset
        previous = offset
        for chunk in data_offsets:
            data_offset = chunk.value
            size = data_offset - previous
            self.read("data[]", "Data content of %s" % chunk.id, (FormatChunk, "string[%u]" % size))
            previous = data_offset

class XcfHierarchie(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "xcf_hier", "XCF hierarchie", stream, parent, "!")
        self.read("width", "Width", (FormatChunk, "uint32"))
        self.read("height", "Height", (FormatChunk, "uint32"))
        self.read("bpp", "Bits/pixel", (FormatChunk, "uint32"))
            
        offsets = []
        while True:
            chunk = self.doRead("offset[]", "Level offset", (FormatChunk, "uint32"))
            if chunk.value == 0:
                break
            offsets.append(chunk.value)
        for offset in offsets:
            seek(self, stream, offset)
            self.read("level[]", "Level", (XcfLevel,))
#        self.read("channel[]", "Channel", (XcfChannel,))

class XcfChannel(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "xcf_channel", "XCF channel", stream, parent, "!")
        self.read("width", "Channel width", (FormatChunk, "uint32"))
        self.read("height", "Channel height", (FormatChunk, "uint32"))
        self.read("name", "Channel name", (StringChunk, "Pascal32"), {"strip": "\0", "charset": "utf-8"})
        readProperties(self, stream)
        self.read("hierarchie_ofs", "Hierarchie offset", (FormatChunk, "uint32"))
        self.read("hierarchie", "Hierarchie", (XcfHierarchie,))

    def updateParent(self, chunk):
        desc = "Channel \"%s\"" % self["name"]
        chunk.description = desc
        self.setDescription(desc)

class XcfLayer(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "xcf_layer", "XCF layer", stream, parent, "!")
        self.read("width", "Layer width", (FormatChunk, "uint32"))
        self.read("height", "Layer height", (FormatChunk, "uint32"))
        self.read("type", "Layer type", (FormatChunk, "uint32"))
        self.read("name", "Layer name", (StringChunk, "Pascal32"), {"strip": "\0", "charset": "utf-8"})
        readProperties(self, stream)
        # TODO: Hack for Gimp 1.2 files
        self.read("hierarchie_ofs", "Hierarchie offset", (FormatChunk, "uint32"))
        self.read("mask_ofs", "Layer mask offset", (FormatChunk, "uint32"))
        seek(self, stream, self["hierarchie_ofs"])
        self.read("hierarchie", "Hierarchie", (XcfHierarchie,))
        # TODO: Read layer mask if needed: self["mask_ofs"] != 0

    def updateParent(self, chunk):
        desc = "Layer \"%s\"" % self["name"]
        chunk.description = desc
        self.setDescription(desc)

class XcfParasites(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "parasites", "Parasites", stream, parent)
        while not stream.eof():
            self.read("parasite[]", "Parasite", (XcfParasiteEntry,))

class XcfProperty(OnDemandFilter):
    type_name = {
        0: "End",
        1: "Colormap",
        2: "Active layer",
        3: "Active channel",
        4: "Selection",
        5: "Floating selection",
        6: "Opacity",
        7: "Mode",
        8: "Visible",
        9: "Linked",
        10: "Lock alpha",
        11: "Apply mask",
        12: "Edit mask",
        13: "Show mask",
        14: "Show masked",
        15: "Offsets",
        16: "Color",
        17: "Compression",
        18: "Guides",
        19: "Resolution",
        20: "Tattoo",
        21: "Parasites",
        22: "Unit",
        23: "Paths",
        24: "User unit",
        25: "Vectors",
        26: "Text layer flags"
    }
    handler = {
        17: XcfCompression,
        19: XcfResolution,
        20: XcfTattoo,
        21: XcfParasites,
        22: XcfUnit
    }

    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "xcf_prop", "XCF property", stream, parent, "!")
        self.read("type", "Property type", (EnumChunk, "uint32", XcfProperty.type_name))
        self.read("size", "Property size", (FormatChunk, "uint32"))
        type = self["type"]
        if type in XcfProperty.handler:
            end = stream.tell() + self["size"]
            substream = stream.createSub(size=self["size"])
            self.read("data", "Data", (XcfProperty.handler[type],), {"stream": substream})
            assert stream.tell() == end
        elif 0 < self["size"]:
            self.read("data", "Data", (FormatChunk, "string[%u]" % self["size"]))

    def updateParent(self, parent):
        parent.description = "Property: %s" % self.getChunk("type").getDisplayData()

def readProperties(filter, stream):        
    while True:
        property = filter.doRead("property[]", "Property", (XcfProperty,))
        if property["type"] == 0:
            break

def seek(filter, stream, offset):
    current = stream.tell()
    if current != offset:
        filter.read("padding[]", "Padding", (FormatChunk, "string[%u]" % (offset-current)))

class XcfFile(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "xcf", "XCF file", stream, parent, "!")
        self.read("header", "Header", (StringChunk, "C"))
        assert self["header"] == "gimp xcf file"
        self.read("width", "Image width", (FormatChunk, "uint32"))
        self.read("height", "Image height", (FormatChunk, "uint32"))
        self.read("type", "Image type", (FormatChunk, "uint32"))
        readProperties(self, stream)

        layer_offsets = []
        while True:
            chunk = self.doRead("layer_offset[]", "Layer offset", (FormatChunk, "uint32"))
            if chunk.value == 0:
                break
            layer_offsets.append(chunk.value)
        channel_offsets = []
        while True:
            chunk = self.doRead("channel_offset[]", "Channel offset", (FormatChunk, "uint32"))
            if chunk.value == 0:
                break
            channel_offsets.append(chunk.value)
        for offset in layer_offsets:
            seek(self, stream, offset)
            self.read("layer[]", "Layer", (XcfLayer,))
        for offset in channel_offsets:
            seek(self, stream, offset)
            self.read("channel[]", "Channel", (XcfChannel,))

registerPlugin(XcfFile, "image/x-xcf")
