"""
Worms2 DIR file parser.
Parser based on Laurent DEFERT SIMONNEAU work.

Author: Victor Stinner
"""

from plugin import registerPlugin 
from filter import OnDemandFilter
from plugin import registerPlugin
from tools import humanFilesize
from chunk import FormatChunk, StringChunk, EnumChunk

class Worms2_Image(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "worms2_image", "Worms2 image", stream, parent, "<")
        nb_color = 244/3
        self.read("palette", "Palette (%u colors)" % nb_color, (FormatChunk, "string[%u]" % (nb_color*3)))
        self.read("padding", "Padding", (FormatChunk, "uint8"))
        self.read("width", "Width", (FormatChunk, "uint16"))
        self.read("height", "Height", (FormatChunk, "uint16"))
        size = self["width"] * self["height"]
        self.read("img_data", "Data", (FormatChunk, "string[%u]" % size))
        size = stream.getSize() - stream.tell()
        self.read("end", "Raw end", (FormatChunk, "string[%u]" % size))

class Worms2_Sprite(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "worms2_sprite", "Worms2 sprite", stream, parent)
        # TODO ...
        size = stream.getSize() - stream.tell()
        self.read("end", "Raw end", (FormatChunk, "string[%u]" % size))

class Worms2_Font(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "worms2_sprite", "Worms2 sprite", stream, parent)
        self.read("palette", "Palette (?)", (FormatChunk, "string[%u]" % (244+33)))
        self.read("charset", "Charset", (FormatChunk, "string[%u]" % (32)))
        self.read("data", "Data", (FormatChunk, "string[%u]" % (32+30+4+136)))
        # TODO ...
        size = stream.getSize() - stream.tell()
        self.read("end", "Raw end", (FormatChunk, "string[%u]" % size))

class Resource(OnDemandFilter):
    name = {
        "IMG": "Image",
        "SPR": "Sprite",
        "FNT": "Font",
        "DIR": "Directory"
    }

    handler = {
        "IMG": Worms2_Image,
        "SPR": Worms2_Sprite,
        "FNT": Worms2_Font
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
        size = humanFilesize(self["size"])
        tag = self.getChunk("tag").getDisplayData()
        chunk.description = tag+": %s (size=%s)" % (self.name, size)

class Worms2_Dir_File(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "worms2_dir_file", "Worms2 directory (.dir) file", stream, parent, "<")
        self.read("resources", "Directory of resources", (Resource,))
         
registerPlugin(Worms2_Dir_File, "hachoir/worms2")
