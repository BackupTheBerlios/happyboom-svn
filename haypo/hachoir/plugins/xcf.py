"""
Exif filter.

Informations about Exif at:
- http://www.exif.org/
- http://libexif.sourceforge.net/

Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin

def readCompression(filter, stream):
    name = {
        0: "None",
        1: "RLE",
        2: "Zlib",
        3: "Fractal"
    }
    chunk = filter.read("compression", "B", "")
    type = name.get(chunk.value, "Unknow (%s)" % chunk.value)
    chunk.description = "Compress type (%s)" % type

def readResolution(filter, stream):
    filter.read("xres", "f", "X resolution")
    filter.read("yres", "f", "Y resolution")

def readTattoo(filter, stream):
    filter.read("tattoo", "!L", "Tattoo")

def readUnit(filter, stream):
    filter.read("unit", "!L", "Unit")

def readString(filter, stream, name, description):
    chunk = filter.read(name+"_size", "!L", description+" length")
    filter.read(name, "%us" % chunk.value, description)

class XcfParasite(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "xcf_para", "XCF parasite", stream, parent)
        readString(self, stream, "name", "Name")
        self.read("flags", "!L", "Flags")
        self.read("size", "!L", "Size")
        if 0 < self["size"]:
            self.read("data", "%us" % self["size"], "Data")

class XcfLevel(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "xcf_level", "XCF level", stream, parent)
        self.read("width", "!L", "Width")
        self.read("height", "!L", "Height")
        self.read("offset", "!L", "Offset")
        offset = self["offset"]
        if offset == 0:
            return
        data_offsets = []
        while stream.tell() < offset:
            chunk = self.read("data_offset[]", "!L", "Data offset")
            if chunk.value == 0:
                break
            data_offsets.append(chunk.value)
        assert stream.tell() == offset
        previous = offset
        for data_offset in data_offsets:
            size = data_offset - previous
            self.read("data[]", "%us" % size, "Data")
            previous = data_offset

class XcfHierarchie(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "xcf_hier", "XCF hierarchie", stream, parent)
        self.read("width", "!L", "Width")
        self.read("height", "!L", "Height")
        self.read("bpp", "!L", "Bits/pixel")
            
        offsets = []
        while True:
            chunk = self.read("offset[]", "!L", "Level offset")
            if chunk.value == 0:
                break
            offsets.append(chunk.value)
        for offset in offsets:
            seek(self, stream, offset)
            self.readChild("level[]", XcfLevel)
#        self.readChild("channel[]", XcfChannel)

class XcfChannel(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "xcf_channel", "XCF channel", stream, parent)
        self.read("width", "!L", "Channel width")
        self.read("height", "!L", "Channel height")
        readString(self, stream, "name", "Channel name")
        readProperties(self, stream)
        return
        self.read("hierarchie_ofs", "!L", "Hierarchie offset")
        self.readChild("hierarchie", XcfHierarchie)

class XcfLayer(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "xcf_layer", "XCF layer", stream, parent)
        self.read("width", "!L", "Layer width")
        self.read("height", "!L", "Layer height")
        self.read("type", "!L", "Layer type")
        readString(self, stream, "name", "Layer name")
        readProperties(self, stream)
        # TODO: Hack for Gimp 1.2 files
        self.read("hierarchie_ofs", "!L", "Hierarchie offset")
        self.read("mask_ofs", "!L", "Layer mask offset")
        seek(self, stream, self["hierarchie_ofs"])
        self.readChild("hierarchie", XcfHierarchie)
        # TODO: Read layer mask if needed: self["mask_ofs"] != 0

def readParasites(filter, stream):
    while not stream.eof():
        filter.readChild("parasite[]", XcfParasite)

class XcfProperty(Filter):
    known_types = {
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
        17: readCompression,
        19: readResolution,
        20: readTattoo,
        21: readParasites,
        22: readUnit
    }

    def __init__(self, stream, parent):
        Filter.__init__(self, "xcf_prop", "XCF property", stream, parent)
        chunk = self.read("type", "!L", "")
        chunk.description = "Property type (%s)" % self.getType()
        self.read("size", "!L", "Property size")
        type = self["type"]
        if type in XcfProperty.handler:
            end = stream.tell() + self["size"]
            substream = stream.createSub(size=self["size"])
            XcfProperty.handler[type] (self, substream)
            assert stream.tell() == end
        elif 0 < self["size"]:
            self.read("data", "%us" % self["size"], "Data")

    def updateParent(self, parent):
        parent.description = "XCF property (%s)" % self.getType()

    def getType(self):
        return XcfProperty.known_types.get(self["type"], "Unknow type (%u)" % self["type"])

def readProperties(filter, stream):        
    while True:
        chunk = filter.readChild("property[]", XcfProperty)
        type = chunk.getFilter()["type"]
        if type == 0:
            break

def seek(filter, stream, offset):
    current = stream.tell()
    if current != offset:
        filter.read("padding[]", "%us" % (offset-current), "Padding")

class XcfFile(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "xcf", "XCF file", stream, parent)
        self.readString("header", "C", "Header")
        assert self["header"] == "gimp xcf file"
        self.read("width", "!L", "Image width")
        self.read("height", "!L", "Image height")
        self.read("type", "!L", "Image type")
        readProperties(self, stream)

        offsets = []
        while True:
            chunk = self.read("layer_offset[]", "!L", "Layer offset")
            if chunk.value == 0:
                break
            offsets.append(chunk.value)
        for offset in offsets:
            seek(self, stream, offset)
            self.readChild("layer[]", XcfLayer)

registerPlugin(XcfFile, "image/x-xcf")
