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
from tools import str2hex, str2bin

class ImageData(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "image_data", "Image data (uncompressed)", stream, parent, "<")
        self.x = self.doRead("x", "Offset X", (FormatChunk, "uint16")).value
        self.y = self.doRead("y", "Offset Y", (FormatChunk, "uint16")).value
        self.width = self.doRead("width", "Width", (FormatChunk, "uint16")).value
        self.height = self.doRead("height", "Height", (FormatChunk, "uint16")).value
        size = (self.width-self.x) * (self.height-self.y)
        self.read("data", "Font content", (FormatChunk, "string[%u]" % size))

    def updateParent(self, chunk):
        chunk.description = "Image data: %ux%u pixels at (%u,%u)" \
            % (self.width, self.height, self.x, self.y)

class Image(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "image", "Image", stream, parent, "<")
        self.read("palette", "Palette", (Palette, 81))
        self.read("padding", "Padding", (FormatChunk, "uint8"))
        self.read("width", "Width", (FormatChunk, "uint16"))
        self.read("height", "Height", (FormatChunk, "uint16"))
        size = self["width"] * self["height"]
        self.read("img_data", "Data", (FormatChunk, "string[%u]" % size))
        size = stream.getLastPos() - stream.tell()
        self.read("end", "Raw end", (FormatChunk, "string[%u]" % size))

    def updateParent(self, chunk):            
        chunk.description = "Image: %ux%u pixels" % \
            (self["width"], self["height"])

class Sprite(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "sprite", "Sprite", stream, parent, "<")
        name = parent.name
        self.read("palette", "Palette", (Palette, 81))
        if True:
            self.read("header116", "Header 116", (FormatChunk, "uint8"))
            assert self["header116"] == 116 
            self.read("a", "???", (FormatChunk, "uint8"))
            self.read("zero", "Zeros", (FormatChunk, "string[9]"))
            assert self["zero"] == ("\0" * 9)
            if False:
                bits = (
                    (1, "info1", ""),
                    (1, "various1", ""),
                    (1, "info2", ""),
                    (3, "various2", ""),
                    (3, "zero", ""),
                    (3, "various3", ""),
                    (1, "info3", ""),
                    (1, "one", ""),
                    (2, "various4", "")
                )
                flags = self.doRead("flags", "Flags", (BitsChunk, BitsStruct(bits)))
                assert flags["zero"] == 0
                assert flags["one"] == True
            else:
                self.read("flags", "???", (FormatChunk, "uint16"), {"post": binary})
            self.read("zero2", "Zero2", (FormatChunk, "uint16"))
            assert self["zero2"] == 0
            import re
            if re.match("^Tv", name) != None:
                size = 2
            elif re.match("^Holy", name) != None:
                size = 26
            elif re.match("^Banana", name) != None:
                size = 29-15+2
            elif re.match("^Homing", name) != None:
                size = 29-15+3+8-1+2
            elif re.match("^Marker", name) != None:
                size = 29+2-15 
            else:
                size = 29-15
            self.read("end_of_header", "End of mysterious header", (FormatChunk, "string[%u]" % size))
            self.x = self.doRead("offset_x[]", "Offset X", (FormatChunk, "uint16")).value
            self.y = self.doRead("offset_y[]", "Offset Y", (FormatChunk, "uint16")).value
            self.width = self.doRead("width[]", "Width", (FormatChunk, "uint16")).value
            self.height = self.doRead("height[]", "Height", (FormatChunk, "uint16")).value

            #print "Sprite % 20s: x=%s, header=% 2s, header=%s | %s" \
            #    % (name, x, size, str2bin(self["end_of_header"][:2]), str2hex(self["end_of_header"]))
            #print "Sprite % 20s: a=%s, header=% 2s, header=%s" \
            #    % (name, self["a"], size, str2hex(self["end_of_header"]))

#            print "Sprite % 20s, a=%s, header=% 2s, flags=%s (%s), size=%ux%u at (%u,%u)" \
#                % (name, self["a"], size, str2bin(self.getChunk("flags").getRaw()), self["flags"], width, height, x, y)

        else:                
            self.read("data", "Data", (FormatChunk, "string[40]"))
            print "Sprite % 20s: %s" \
                % (name, str2hex(self["data"]))
            
        size = stream.getLastPos() - stream.tell()
        self.read("end", "Raw end", (FormatChunk, "string[%u]" % size))

    def updateParent(self, chunk):            
        chunk.description = "Sprite: %ux%u pixels" % \
            (self.width, self.height)

class Font(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "font", "Font", stream, parent, "<")
        self.read("palette", "Palette", (Palette, 81))
        self.read("header", "Header !?", (FormatChunk, "string[%u]" % 0x105))

#        while not stream.eof():
        self.nb_characters = 0
        while 2*4 < (stream.getLastPos() - stream.tell()):
            id = self.read("image[]", "Image", (ImageData,))
            if self.nb_characters == 0:
                image = self[id]
                self.width = image.width
                self.height = image.height
            self.nb_characters += 1
        size = stream.getLastPos() - stream.tell()
        self.read("end", "Raw end", (FormatChunk, "string[%u]" % size))

    def updateParent(self, chunk):
        chunk.description = "Font: %ux%u pixels, %u characters" \
            % (self.width, self.height, self.nb_characters)

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
                sub = stream.createLimited(size=size)
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
