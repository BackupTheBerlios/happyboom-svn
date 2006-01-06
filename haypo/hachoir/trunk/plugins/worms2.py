"""
Worms2 DIR file parser.
Parser based on Laurent DEFERT SIMONNEAU work.

Author: Victor Stinner
"""

from plugin import registerPlugin 
from filter import OnDemandFilter
from plugin import registerPlugin
from chunk import FormatChunk, StringChunk, EnumChunk, BitsChunk, BitsStruct
from generic.image import Palette
from text_handler import humanFilesize
from tools import alignValue
import re

class ImageData(OnDemandFilter):
    def __init__(self, stream, parent, use_bank):
        OnDemandFilter.__init__(self, "image_data", "Image data (uncompressed)", stream, parent, "<")
        self.read("x", "X", (FormatChunk, "uint16"))
        self.read("y", "Y", (FormatChunk, "uint16"))
        self.read("width", "Width", (FormatChunk, "uint16"))
        self.read("height", "Height", (FormatChunk, "uint16"))
        self.use_bank = use_bank
        if use_bank:
            self.read("offset", "Offset", (FormatChunk, "uint32"))
        else:
            size = (self["width"]-self["x"]) * (self["height"]-self["y"])
            self.read("data", "Image content", (FormatChunk, "string[%u]" % size))

    def getStaticSize(stream, args):
        if args[0] == True:
            return 12 
        oldpos = stream.tell()
        x, y, w, h, = stream.getFormat("<uint16[4]")
        size = 2*4 + (w-x) * (h-y)
        stream.seek(oldpos)
        return size
    getStaticSize = staticmethod(getStaticSize)

    def updateParent(self, chunk):
        desc = "Image data: " 
        if self.use_bank:
            desc += "offset=%u " % self["offset"]
        chunk.description = desc+"%ux%u pixels at (%u,%u)" \
            % (self["width"], self["height"], self["x"], self["y"])

class Image(OnDemandFilter):
    def __init__(self, stream, parent, use_bank):
        OnDemandFilter.__init__(self, "image", "Image", stream, parent, "<")
        self.read("width", "Width", (FormatChunk, "uint16"))
        self.read("height", "Height", (FormatChunk, "uint16"))
        size = self["width"] * self["height"]
        if size <= stream.getRemainSize():
            self.compressed = False
            self.read("img_data", "Image data: %ux%u pixels in 8 bits/pixels" % (self["width"], self["height"]), (FormatChunk, "string[%u]" % size))
        else:
            self.compressed = True
        self.addPadding()

    def updateParent(self, chunk):            
        desc = "Image: %ux%u pixels" % (self["width"], self["height"])
        if self.compressed:
            desc += " (compressed)"
        chunk.description = desc 
class Step(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "sprite_item", "Sprite item", stream, parent, "<")
        self.read("zero1", "???", (FormatChunk, "string[6]"))
        assert self["zero1"] == "\0" * 6
        self.read("size", "Size in byte", (FormatChunk, "uint16"))
        self.read("zero2", "???", (FormatChunk, "uint16"))
        assert self["zero2"] == 0
        self.read("f1", "???", (FormatChunk, "uint8"))
        self.read("f2", "???", (FormatChunk, "uint8"))
        
    def updateParent(self, chunk):            
        chunk.description = "Step: size=%s f1=%s f2=%s" % \
            (self["size"],self["f1"],self["f2"])

class SpriteFrame(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "frame", "Sprite frame", stream, parent, "<")
        self.read("offset", "Offset in data", (FormatChunk, "uint16"))
        self.read("xxx", "Null or equals to 0, 1, 2, ... in Level.dir", (FormatChunk, "uint8"))
        self.read("step", "Step", (FormatChunk, "uint8"))
        self.read("x", "X", (FormatChunk, "uint16"))
        self.read("y", "Y", (FormatChunk, "uint16"))
        self.read("width", "Width", (FormatChunk, "uint16"))
        self.read("height", "Height", (FormatChunk, "uint16"))
        self.real_width = self["width"] - self["x"]
        self.real_height = self["height"] - self["y"]

    def updateParent(self, chunk):            
        chunk.description = "Frame: %ux%u bytes, %ux%u pixels at (%u,%u), offset=%s step=%s" % \
            (self.real_width, self.real_height, self["width"], self["height"], self["x"], self["y"], self["offset"], self["step"])

class Sprite(OnDemandFilter):
    def __init__(self, stream, parent, use_bank):
        OnDemandFilter.__init__(self, "sprite", "Sprite", stream, parent, "<")
        self.read("nb_step", "Number of steps", (FormatChunk, "uint16"))
        if 0 < self["nb_step"]:
            self.read("zero", "Zero?", (FormatChunk, "uint16"))
            for i in range(0, self["nb_step"]):
                self.read("step[]", "Step", (Step,))
        self.read("x", "X", (FormatChunk, "uint16"))
        self.read("y", "Y", (FormatChunk, "uint16"))
        self.read("width", "Width", (FormatChunk, "uint16"))
        self.read("height", "Height", (FormatChunk, "uint16"))
        self.read("count", "Frame count", (FormatChunk, "uint16"))
        frames = []
        for i in range(0, self["count"]):
            frame = self.doRead("frame[]", "Frame", (SpriteFrame,))
            frames.append(frame)
        if self["nb_step"] == 0:
            for frame in frames:
                size = frame.real_width * frame.real_height
                self.read("data[]", "Frame data: %ux%u pixels in 8 bits/pixel" % (frame.real_width, frame.real_height), (FormatChunk,"string[%u]" % size))
        elif False:            
            real_width = self["width"] - self["x"]
            real_height = self["height"] - self["y"]
            size = real_width * real_height
            if size <= (stream.getLastPos() - stream.tell()):
                self.read("image_data[]", "Data (%ux%u pixels)" % (real_width, real_height), (FormatChunk, "string[%u]" % size))
        self.addPadding()

    def updateParent(self, chunk):            
        desc = "Animation: %ux%u pixels, %u frame(s)" % (self["width"], self["height"], self["count"])
        if self["nb_step"] == 0:
            desc += " (uncompressed)"
        else:
            desc += ", %u step(s)" % (self["nb_step"])
        chunk.description = desc

class INF(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "inf", "INF resource", stream, parent, "<")
        for i in range(0, 6):
            self.read("line[]", "Line", (StringChunk, "WindowsLine"))
        self.read("name", "File name", (StringChunk, "WindowsLine"))
        self.read("line[]", "Line", (StringChunk, "WindowsLine"))
        while stream.getN(2, False) == "\r\n":
            self.read("empty_line[]", "(empty line)", (StringChunk, "WindowsLine"))
        self.read("separator", "Separator (26)", (FormatChunk, "uint8"))

    def updateParent(self, chunk):
        chunk.description = "INF: %s" % (self["name"])

class StringIndex(OnDemandFilter):
    def __init__(self, stream, parent, use_bank):
        OnDemandFilter.__init__(self, "str_idx", "String index", stream, parent, "<")
        self.count = 0
        while True:
            name = self.doRead("name[]", "Name", (StringChunk, "WindowsLine")).value
            if name == "!":
                break
            self.count += 1
        self.read("empty_line", "(empty line)", (StringChunk, "WindowsLine"))
        self.read("separator", "Separator (26)", (FormatChunk, "uint8"))

    def updateParent(self, chunk):
        chunk.description = "String index: %s strings" % (self.count)

class BankItem(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "bank_item", "Bank item", stream, parent, "<")
        self.x = self.doRead("x", "X", (FormatChunk, "uint16")).value
        self.y = self.doRead("y", "Y", (FormatChunk, "uint16")).value
        self.width = self.doRead("width", "Width", (FormatChunk, "uint16")).value
        self.height = self.doRead("height", "Height", (FormatChunk, "uint16")).value
        self.read("offset", "Offset?", (FormatChunk, "uint16"))
        self.read("xxx", "???", (FormatChunk, "uint16"))

    def getStaticSize(stream, args):
        return 12 
    getStaticSize = staticmethod(getStaticSize)

    def updateParent(self, chunk):
        desc = "Bank item: " 
        desc += "%ux%u pixels at (%u,%u)" % (self.width, self.height, self.x, self.y)
        desc += " offset=%s xxx=%s" % (self["offset"], self["xxx"])

        chunk.description = desc

class BankItem2(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "bank_item", "Bank item", stream, parent, "<")
        self.read("offset", "Offset?", (FormatChunk, "uint16"))
        self.read("step", "Step?", (FormatChunk, "uint16"))
        self.read("size", "Size?", (FormatChunk, "uint16"))
        self.read("zero", "Zero", (FormatChunk, "string[6]"))
        assert self["zero"] == "\0" * 6 

    def getStaticSize(stream, args):
        return 12 
    getStaticSize = staticmethod(getStaticSize)

    def updateParent(self, chunk):
        chunk.description = "Bank item2: size=%s offset=%s step=%s" % (self["size"], self["offset"], self["step"])

class BigBank(OnDemandFilter):
    def __init__(self, stream, parent, chunk_info, count):
        OnDemandFilter.__init__(self, "bigbank", "Big bank", stream, parent, "<")
        self.count = count
        for i in range(0, self.count):
            self.read("item[]", "Item", chunk_info)

    def getStaticSize(stream, args):
        size = args[0][0].getStaticSize(stream, [])
        count = args[1]
        assert size != None
        return count * size
    getStaticSize = staticmethod(getStaticSize)

    def updateParent(self, chunk):
        chunk.description = "Big Bank: %s items" % (self.count)

class Bank(OnDemandFilter):
    def __init__(self, stream, parent, use_bank):
        OnDemandFilter.__init__(self, "text_idx", "Text index", stream, parent, "<")
        nb_color = self.doRead("nb_color", "Number of colors", (FormatChunk, "uint16")).value
        self.read("palette", "Palette", (Palette, nb_color))
        self.read("xxx[]", "??", (FormatChunk, "uint16"))
       
        # Items (1)
        self.count = self.doRead("count", "Number of items (1)", (FormatChunk, "uint16")).value
        self.read("items1", "Items (1)", (BigBank, (BankItem,), self.count))
            
        # Items (2)
        self.read("zero1", "Zero?", (FormatChunk, "uint16"))
        assert self["zero1"] == 0
        self.count2 = self.doRead("count2", "Number of items (2)", (FormatChunk, "uint32")).value
        self.read("zero2", "Zero?", (FormatChunk, "uint32"))
        assert self["zero2"] == 0
        self.read("items2", "Items (2)", (BigBank, (BankItem,), self.count2))

        # Items (3)
        self.count3 = self["items2"]["item[%u]" % (self.count2-1)]["offset"]       
        self.read("items3", "Items (3)", (BigBank, (BankItem2,), self.count3))
       
        if False:
            # TODO: Finish the parser... 
            size = stream.getRemainSize() - 1
            self.read("data", "Images data", (FormatChunk, "string[%u]" % size))
            
            self.read("separator", "Separator (26)", (FormatChunk, "uint8"))
        else:
            self.addPadding()

    def updateParent(self, chunk):
        chunk.description = "Bank: %s items, %s items2, %s items3" % (self.count, self.count2, self.count3)

class Font(OnDemandFilter):
    def __init__(self, stream, parent, use_bank):
        OnDemandFilter.__init__(self, "font", "Font", stream, parent, "<")

        #--- Ugly header ---
        size = 33
        self.read("zero", "Zero", (FormatChunk, "string[%u]" % size))
        assert self["zero"] == "\0" * size
        size = 223
        self.read("header", "Header", (FormatChunk, "string[%u]" % size))
        self.read("size", "Font width and height", (FormatChunk, "uint16"))

        # Read images
        self.read("nb_char", "Number of characters", (FormatChunk, "uint16"))
        
        for i in range(0, self["nb_char"]):
            self.read("image[]", "Image", (ImageData, use_bank))

        # Get image size
        if use_bank:
            for i in range(0, self["nb_char"]):
                image = self["image[%u]" % i]
                size = image["width"] * image["height"]
                self.read("image_data[]", "Image data content", (FormatChunk, "string[%u]" % size))
        self.addPadding()

    def updateParent(self, chunk):
        chunk.description = "Font: %ux%u pixels, %u characters" \
            % (self["size"], self["size"], self["nb_char"])

class Resource(OnDemandFilter):
    tag_name = {
        "IMG": "Image",
        "SPR": "Sprite",
        "FNT": "Font",
        "DIR": "Directory",
        "BNK": "Bank"
    }

    handler = {
        "IMG": Image,
        "SPR": Sprite,
        "FNT": Font,
        "BNK": Bank
    }

    def __init__(self, stream, parent, has_name=True, use_bank=False, has_separator=False):
        OnDemandFilter.__init__(self, "worms2_res", "Worms2 resource", stream, parent, "<")
        guess = stream.getN(3, False)
        if guess not in Resource.tag_name:
            self.name = "Strange chunk!?"
            self.addPadding()
            return
        self.tag = self.doRead("tag", "Type", (EnumChunk, "string[3]", Resource.tag_name)).value
        self.read("tag_end", "Type end", (FormatChunk, "string[1]"))
        if self.tag != "DIR":
            self.read("size", "Size", (FormatChunk, "uint32"))

            # Read resource name
            if has_name:
                self.name = self.doRead("name", "Name", (StringChunk, "C")).value
            else:
                self.name = self.getChunk("tag").getDisplayData() 
            
            if self.tag != "BNK":
                # Read informations about colors
                self.read("bpp", "Bits / pixel", (FormatChunk, "uint8"))
                self.read("xxx", "???", (FormatChunk, "uint8"))
                nb_color = self.doRead("nb_color", "Number of colors", (FormatChunk, "uint16")).value

                self.read("palette", "Palette", (Palette, nb_color))
            else:
                has_separator = False
           
            size = self["size"] - self.getSize()
            if self.tag in Resource.handler:    
                # Data content handler
                self.handled = True
                #sub = stream.createSub(size=size)
                sub = stream.createLimited(size=size)
                self.read("data", "Data", (Resource.handler[self.tag], use_bank), {"stream": sub})
            else:
                self.handled = False
                self.read("data", "Data", (FormatChunk, "string[%u]" % size))

            # Separator
            if has_separator:
                if not use_bank or stream.getN(1) == "\x1A":
                    self.read("separator", "Separator (0x1A = 26)", (FormatChunk, "uint8"))
                #assert self["separator"] == 0x1A
        else:
            self.count = 0
            self.read("filesize", "File size", (FormatChunk, "uint32"), {"post": humanFilesize})
            self.name = "(directory)"
            has_name = True
            use_bank = False
            has_separator = True
            self.read("size", "Directory size", (FormatChunk, "uint32"))
            guess = stream.getN(3, False)
            if guess == "BNK":
                use_bank = True
                has_name = False
            fs = parent["fs"]
            for index in range(0, fs.count):
                file = fs["file[%u]" % index]
                self.seek(file["position"])
                name = file["name"]
                
                if name.endswith(".inf"):
                    self.read("res[]", "INF resource", (INF,))
                elif name.endswith("index.txt"):
                    self.read("res[]", "String index", (StringIndex, use_bank))
                else:
                    self.read("res[]", "Resource", (Resource, has_name, use_bank, has_separator))
                self.count += 1                        
            self.addPadding()

    def seek(self, pos):
        stream = self.getStream()
        assert stream.tell() <= pos and pos < stream.getSize()
        size = pos - stream.tell()
        if size != 0:
            self.read("padding[]", "Padding", (FormatChunk, "string[%u]" % size))

    def getStaticSize(stream, args):
        oldpos = stream.tell()
        tag = stream.getN(3, False)
        if tag != "DIR":
            stream.seek(4, 1)
            size = stream.getFormat("<uint32")
            if args[2] and (not args[1] or tag != "SPR"):
                size += 1
        else:
            stream.seek(8, 1)
            size = stream.getFormat("<uint32")
        stream.seek(oldpos)
        return size
    getStaticSize = staticmethod(getStaticSize)

    def updateParent(self, chunk):            
        if self["tag"] != "DIR":
            if self.handled:
                chunk.description = "[%s] %s" % (self.name, self["data"].getDescription())
            else:
                chunk.description = "[%s]" % (self.name)
        else:
            chunk.description = "Directory: %u resources" % self.count 

class File(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "fs", "File system", stream, parent, "<")
        self.read("position", "Position in file", (FormatChunk, "uint32"))
        self.read("size", "File size (in bytes)", (FormatChunk, "uint32"), {"post": humanFilesize})
        size = self.doRead("name", "Name", (StringChunk,"C")).size
        padding = 4 + alignValue(size, 4) - size
        max = stream.getLastPos() - stream.tell() + 1
        if max<padding:
            padding = max
        self.read("padding", "Padding", (FormatChunk,"string[%u]" % padding))
        
    def updateParent(self, chunk):
        size = self.getChunk("size").getDisplayData()
        chunk.description = "File: %s (%s), position=%s" \
            % (self["name"], size, self["position"])

class Numbers(OnDemandFilter):
    def __init__(self, stream, parent, count):
        OnDemandFilter.__init__(self, "fs", "File system", stream, parent, "<")
        self.count = count
        for i in range(0, self.count):
            self.read("value32[]", "?", (FormatChunk, "uint32"))
        
    def updateParent(self, chunk):
        chunk.description = "Numbers: %u integers (uint32)" % (self.count)

class FileSystem(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "fs", "File system", stream, parent, "<")
        self.count = 0 
        while not stream.eof():
            self.read("file[]", "File", (File,))
            self.count += 1
        
    def updateParent(self, chunk):
        chunk.description = "File system: %u files" % (self.count)

class Worms2_Dir_File(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "worms2_dir_file", "Worms2 directory (.dir) file", stream, parent, "<")
        stream.seek(8, 1)
        size = size = stream.getFormat("<uint32", False)
        stream.seek(-8, 1)
        sub = stream.createSub(size=size)
        self.read("resources", "Directory", (Resource, True, None, True), {"stream": sub})
        if True:
            count = 1026
            self.read("numbers", "Numbers?", (Numbers, count), {"size": count*4})
        
            size = stream.getRemainSize()
            self.read("fs", "File system", (FileSystem,), {"size": size})
         
registerPlugin(Resource, ["hachoir/worms2-font", "hachoir/worms2-image", "hachoir/worms2-sprite"])
registerPlugin(Worms2_Dir_File, "hachoir/worms2-directory")
