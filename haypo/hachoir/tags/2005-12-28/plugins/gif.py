"""
GIF picture parser.

Author: Victor Stinner
"""

from filter import OnDemandFilter
from plugin import registerPlugin
from chunk import FormatChunk, EnumChunk, BitsChunk, BitsStruct
from error import warning
from generic.image import Palette

class Image(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "gif_image", "Image", stream, parent, "<")
        self.read("left", "Left", (FormatChunk, "uint16"))
        self.read("top", "Top", (FormatChunk, "uint16"))
        self.read("width", "Width", (FormatChunk, "uint16"))
        self.read("height", "Height", (FormatChunk, "uint16"))

        bits = (
            (1, "local_color", "Local color table"),
            (1, "interlace", "Interlaced?"),
            (1, "sort", "Sort"),
            (2, "reserved", "Reserved"),
            (3, "size_local", "Size of local color"))
        self.flags = self.doRead("flags", "Flags", (BitsChunk, BitsStruct(bits)))

        return
        if not self.flags["local_color"]:
            self.read("local_map", "Local color map", (Palette, 1 << self.flags["size_local"]))
            self.local_map = self["local_map"]
        else:
            self.local_map = None

    def updateParent(self, chunk):
        chunk.description = "Image: %ux%u pixels at (%u,%u)" \
            % (self["width"], self["height"], self["left"], self["top"])

class ExtensionChunk(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "gif_ext_data", "GIF extension data", stream, parent)
        self.read("size", "Size (in bytes)", (FormatChunk, "uint8"))
        self.read("content", "Content", (FormatChunk, "string[%u]" % self["size"]))

class Extension(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "gif_ext", "GIF extension", stream, parent)
        self.read("func", "Function", (FormatChunk, "uint8"))
        while True:
            chunk = self.doRead("chunk[]", "Chunk", (ExtensionChunk,))
            if chunk["size"] == 0:
                break
        
class ScreenDescriptor(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "gif_screen_desc", "GIF screen descriptor", stream, parent, "<")
        self.read("width", "Width", (FormatChunk, "uint16"))
        self.read("height", "Height", (FormatChunk, "uint16"))

        bits = (
            (1, "global_map", "Has global map?"),
            (3, "bpp", "Bits per pixel minus one"),
            (3, "color_res", "Color resolution minus one"),
            (1, "xxx", "???"))
        self.flags = self.doRead("flags", "Flags", (BitsChunk, BitsStruct(bits)))
        self.bits_per_pixel = 1 + self.flags["bpp"]


#        self.read("flags", "Flags", (FormatChunk, "uint8"), {"post": self.processFlags})
        
        self.read("background", "Background color", (FormatChunk, "uint8"))
        self.read("notused", "Not used (zero)", (FormatChunk, "uint8"))

    def updateParent(self, chunk):
        chunk.description = "Screen descriptor: %ux%u, %u colors" \
            % (self["width"], self["height"], 1 << self.bits_per_pixel)

class GifFile(OnDemandFilter):
    separator_name = {
        "!": "Extension",
        ",": "Image",
        ";": "Terminator"
    }
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "gif_file", "GIF picture file", stream, parent)
        # Header
        self.read("header", "File header", (FormatChunk, "string[6]"))
        assert self["header"] in ("GIF87a", "GIF89a")
        
        screen = self.doRead("screen", "Screen descriptor", (ScreenDescriptor,))
        if screen.flags["global_map"]:
            self.read("color_map", "Color map", (Palette, 1 << screen.bits_per_pixel))
            self.color_map = self["color_map"]
        else:
            self.color_map = None
            
        self.images = []
        while True:
            code = self.doRead("separator[]", "Separator code", (EnumChunk, "char", GifFile.separator_name)).value
            if code == "!":
                self.read("extensions[]", "Extension", (Extension,))
            elif code == ",":
                self.read("image[]", "Image", (Image,))
                # TODO: Write Huffman parser code :-)
                return
            elif code == ";":
                # GIF Terminator
                return
            else:
                raise Exception("Wrong GIF image separator: ASCII %02X." % ord(code))
                

registerPlugin(GifFile, "image/gif")
