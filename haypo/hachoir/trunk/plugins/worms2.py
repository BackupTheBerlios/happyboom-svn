"""
Worms2 DIR file.
"""

from plugin import registerPlugin 
from filter import Filter
from plugin import registerPlugin
from tools import humanFilesize

class Worms2_Image(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "worms2_image", "Worms2 image", stream, parent)
        nb_color = 244/3
        self.read("palette", "%us" % (nb_color*3), "Palette (%u colors)" % nb_color)
        self.read("padding", "B", "Padding")
        self.read("width", "<H", "Width")
        self.read("height", "<H", "Height")
        size = self["width"] * self["height"]
        self.read("img_data", "%us" % size, "Data")
        size = stream.getSize() - stream.tell()
        self.read("end", "%us" % size, "Raw end")

class Worms2_Sprite(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "worms2_sprite", "Worms2 sprite", stream, parent)
        # TODO ...
        size = stream.getSize() - stream.tell()
        self.read("end", "%us" % size, "Raw end")

class Worms2_Font(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "worms2_sprite", "Worms2 sprite", stream, parent)
        self.read("palette", "%us" % (244+33), "Palette (?)")
        self.read("charset", "%us" % (32), "Charset")
        self.read("data", "%us" % (32+30+4+136), "Data")
        # TODO ...
        size = stream.getSize() - stream.tell()
        self.read("end", "%us" % size, "Raw end")

class Worms2_Resource(Filter):
    handler = {
        "IMG": Worms2_Image,
        "SPR": Worms2_Sprite,
        "FNT": Worms2_Font
    }
    def __init__(self, stream, parent):
        Filter.__init__(self, "worms2_res", "Worms2 resource", stream, parent)
        pos = stream.tell()
        self.tag = self.read("tag", "3s", "Type").value.strip("\0\n")
        self.valid = self.tag.strip("\0\n") != ""
        self.read("tag_end", "1s", "Type end")
        size = self.read("size", "<L", "Size").value
        if not self.valid:
            return
        self.readString("name", "C", "Name")
        size = pos + size + 1 - stream.tell()
        if self.tag in Worms2_Resource.handler:
            sub = stream.createSub(size=size)
            self.readStreamChild("data", sub, Worms2_Resource.handler[self.tag])
        else:
            self.read("data", "%us" % size, "Data")

    def updateParent(self, chunk):            
        size = humanFilesize(self["size"])
        tag = self.tag
        if tag != "":
            name = self["name"]
        else:
            tag = "(invalid)"
            name = "(invalid)"
        chunk.description = "Resource \"%s\" (type=%s, size=%s)" % (name, tag, size)

class Worms2_Dir_File(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "worms2_dir_file", "Worms2 directory (.dir) file", stream, parent)
        self.read("id", "3s", "Identifier (DIR)")
        self.read("raw", "%us" % (12-stream.tell()), "Raw data")
        while stream.tell() < 3432805:
            file = self.readChild("file[]", Worms2_Resource).getFilter()
            if not file.valid:
                break
         
registerPlugin(Worms2_Dir_File, "hachoir/worms2")
