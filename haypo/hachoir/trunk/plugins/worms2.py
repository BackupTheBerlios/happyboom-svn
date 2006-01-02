"""
Worms2 DIR file parser.
Parser based on Laurent DEFERT SIMONNEAU work.

Author: Victor Stinner
"""

from plugin import registerPlugin 
from filter import OnDemandFilter
from plugin import registerPlugin
from tools import humanFilesize
from chunk import FormatChunk, StringChunk, EnumChunk, BitsChunk, BitsStruct
from generic.image import Palette

# Only for debug purpose
from text_handler import binary

class ImageData(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "image_data", "Image data (uncompressed)", stream, parent, "<")
        self.x = self.doRead("x", "Offset X", (FormatChunk, "uint16")).value
        self.y = self.doRead("y", "Offset Y", (FormatChunk, "uint16")).value
        self.width = self.doRead("width", "Width", (FormatChunk, "uint16")).value
        self.height = self.doRead("height", "Height", (FormatChunk, "uint16")).value
        size = (self.width-self.x) * (self.height-self.y)
        self.read("data", "Image content", (FormatChunk, "string[%u]" % size))

    def getStaticSize(stream, args):
        oldpos = stream.tell()
        x, y = stream.getFormat("<uint16"), stream.getFormat("<uint16")
        w, h = stream.getFormat("<uint16"), stream.getFormat("<uint16")
        size = 2*4 + (w-x) * (h-y)
        stream.seek(oldpos)
        return size
    getStaticSize = staticmethod(getStaticSize)

    def updateParent(self, chunk):
        chunk.description = "Image data: %ux%u pixels at (%u,%u)" \
            % (self.width, self.height, self.x, self.y)

class Image(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "image", "Image", stream, parent, "<")
        self.read("padding", "Padding", (FormatChunk, "uint8"))
        self.read("width", "Width", (FormatChunk, "uint16"))
        self.read("height", "Height", (FormatChunk, "uint16"))
        size = self["width"] * self["height"]
        self.read("img_data", "Data", (FormatChunk, "string[%u]" % size))
        self.addPadding()

    def updateParent(self, chunk):            
        chunk.description = "Image: %ux%u pixels" % \
            (self["width"], self["height"])

class MysteriousHeader(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "sprite_item", "Sprite item", stream, parent, "<")
        self.read("a", "???", (FormatChunk, "uint16"))
        self.read("b", "???", (FormatChunk, "uint16"))
        self.read("c", "???", (FormatChunk, "uint16"))
        self.read("d", "???", (FormatChunk, "uint16"))
        self.read("e", "???", (FormatChunk, "uint16"))
        self.read("f", "???", (FormatChunk, "uint16"))
        
    def updateParent(self, chunk):            
        chunk.description = "Mysterious: d=%s f=%s a=%s b=%s c=%s e=%s" % \
            (self["d"],self["f"],self["a"],self["b"],self["c"],self["e"])

class SpriteFrame(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "frame", "Sprite frame", stream, parent, "<")
        self.read("a", "???", (FormatChunk, "uint8"))
        self.read("b", "???", (FormatChunk, "uint16"))
        self.read("c", "???", (FormatChunk, "uint8"))
        self.read("x", "Offset X", (FormatChunk, "uint16"))
        self.read("y", "Offset Y", (FormatChunk, "uint16"))
        self.read("width", "Width", (FormatChunk, "uint16"))
        self.read("height", "Height", (FormatChunk, "uint16"))

    def updateParent(self, chunk):            
        chunk.description = "Frame: %ux%u pixels at (%u,%u)" % \
            (self["width"], self["height"], self["x"], self["y"])

class Sprite(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "sprite", "Sprite", stream, parent, "<")
        name = parent.name
        self.read("header116", "Header 116", (FormatChunk, "uint8"))
        assert self["header116"] == 116 

        if False:
            self.read("n", "Type?", (FormatChunk, "uint8"))
            self.read("zero[]", "???", (FormatChunk, "string[9]"))
            self.read("flags_a", "???", (FormatChunk, "uint16"), {"post": binary})
            self.read("zero[]", "???", (FormatChunk, "uint16"))
            flags_b = self.doRead("flags_b", "???", (FormatChunk, "uint16"), {"post": binary}).value
            for i in range(0, self["n"]-1):
                self.read("mysterious[]", "Mysterious header", (MysteriousHeader,))
        else:
            self.read("n", "Type?", (FormatChunk, "uint16"))
            self.read("zero", "Zero?", (FormatChunk, "uint16"))
            for i in range(0, self["n"]):
                self.read("mysterious[]", "Mysterious header", (MysteriousHeader,))
            
        self.read("x", "Offset X", (FormatChunk, "uint16"))
        self.read("y", "Offset Y", (FormatChunk, "uint16"))
        self.read("width", "Width", (FormatChunk, "uint16"))
        self.read("height", "Height", (FormatChunk, "uint16"))
        self.read("count", "Frame count", (FormatChunk, "uint16"))
        for i in range(0, self["count"]):
            self.read("item[]", "Frame", (SpriteFrame,))
        if False:            
            real_width = self["width"] - self["x"]
            real_height = self["height"] - self["y"]
            size = real_width * real_height
            if size <= (stream.getLastPos() - stream.tell()):
                self.read("image_data[]", "Data (%ux%u pixels)" % (real_width, real_height), (FormatChunk, "string[%u]" % size))
        self.addPadding()

    def updateParent(self, chunk):            
        chunk.description = "Animation: %ux%u pixels, %u mysterious, %u frame(s)" % \
            (self["width"], self["height"], self["n"], self["count"])

class Font(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "font", "Font", stream, parent, "<")

        self.read("header116", "Header 116", (FormatChunk, "uint8"))

        #--- Ugly header ---
        size = 33
        self.read("zero[]", "???", (FormatChunk, "string[%u]" % size))
        size = 256 - stream.tell()
        self.read("xxx", "???", (FormatChunk, "string[%u]" % size))
        self.read("nb_char8bit", "???", (FormatChunk, "uint8"))
        self.read("align", "Next factor of four to height?", (FormatChunk, "uint16"))

        # Read images
        self.read("nb_char", "Number of characters", (FormatChunk, "uint16"))
        for i in range(0, self["nb_char"]):
            self.read("image[]", "Image", (ImageData,))

        # Get image size
        image = self["image[0]"]
        self.width = image.width
        self.height = image.height
        self.addPadding()

    def updateParent(self, chunk):
        chunk.description = "Font: %ux%u pixels, %u characters" \
            % (self.width, self.height, self["nb_char"])

class Resource(OnDemandFilter):
    name = {
        "IMG": "Image",
        "SPR": "Sprite",
        "FNT": "Font",
        "DIR": "Directory"
    }

    handler = {
        "IMG": Image,
        "SPR": Sprite,
        "FNT": Font
    }

    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "worms2_res", "Worms2 resource", stream, parent, "<")
        pos = stream.tell()
        self.tag = self.doRead("tag", "Type", (EnumChunk, "string[3]", Resource.name)).value
        self.read("tag_end", "Type end", (FormatChunk, "string[1]"))
        size = self.doRead("size", "Size", (FormatChunk, "uint32")).value
        if self.tag != "DIR":
            self.name = self.doRead("name", "Name", (StringChunk, "C")).value
            
            size = pos + size + 1 - stream.tell()
            if self.tag in Resource.handler:
                self.read("palette", "Palette", (Palette, 81))
                size = size-81*3
                #sub = stream.createLimited(size=size)
                sub = stream.createSub(size=size)
                self.read("data", "Data", (Resource.handler[self.tag],), {"stream": sub})
            else:
                self.read("data", "Data", (FormatChunk, "string[%u]" % size))
        else:
            self.name = "(directory)"
            end = self.doRead("last_pos", "Last position", (FormatChunk, "uint32")).value
            while stream.tell() < end:
                self.read("res[]", "Resource", (Resource,))

    def getStaticSize(stream, args):
        oldpos = stream.tell()
        if stream.getFormat("string[3]", False) != "DIR":
            stream.seek(4, 1)
            size = 1 + stream.getFormat("<uint32")
        else:
            stream.seek(8, 1)
            size = stream.getFormat("<uint32")
        stream.seek(oldpos)
        return size
    getStaticSize = staticmethod(getStaticSize)

    def updateParent(self, chunk):            
        if self["tag"] != "DIR":
            chunk.description = "[%s] %s" % (self.name, self["data"].getDescription())
        else:
            tag = self.getChunk("tag").getDisplayData()
            size = humanFilesize(self["size"])
            chunk.description = tag+": %s (size=%s)" % (self.name, size)

class Worms2_Dir_File(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "worms2_dir_file", "Worms2 directory (.dir) file", stream, parent, "<")
        self.read("resources", "Directory of resources", (Resource,))
         
registerPlugin(Worms2_Dir_File, "hachoir/worms2")
