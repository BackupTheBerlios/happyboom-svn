"""
GIF splitter.

Status: loads header, don't load image data (stop filter), and is buggy ...
Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin
from error import warning

class GifColor(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "gif_color", "GIF color (RGB)", stream, parent)
        self.read("red", "<B", "Red")
        self.read("green", "<B", "Green")
        self.read("blue", "<B", "Blue")

class GifImage(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "gif_image", "GIF image data", stream, parent)
        self.read("left", "<H", "Left")
        self.read("top", "<H", "Top")
        self.read("width", "<H", "Width")
        self.read("height", "<H", "Height")

        # TODO: Fix this ...
        self.read("flags", "<H", "Flags")
        self.global_map = ((self["flags"] & 0x80) == 0x80)
        self.interlaced = ((self["flags"] & 0x40) == 0x40)
        self.bits_per_pixel = 1 + (self["flags"] & 0x07)
        if not self.global_map:
            self.readChild("local_map", GifColorMap)
            self.local_map = self["local_map"]
        else:
            self.local_map = None
        # -- End of TODO

class GifColorMap(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "gif_colormap", "GIF color map", stream, parent)
        if issubclass(parent.__class__, GifImage):
            self._nb_colors = (1 << parent.bits_per_pixel)
        else:
            assert issubclass(parent.__class__, GifFile)
            screen = parent.getChunk("screen").getFilter()
            self._nb_colors = (1 << screen.bits_per_pixel)
        n = 0
        while n<self._nb_colors:
            self.readChild("color[]", GifColor)
            n = n + 1

    def checkEndOfMap(self, stream, array, color):
        return len(array) == self._nb_colors 

class GifExtensionChunk(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "gif_ext_data", "GIF extension data", stream, parent)
        self.read("size", "<B", "Size (in bytes)")
        self.read("content", "<{size}s", "Content")

class GifExtension(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "gif_ext", "GIF extension", stream, parent)
        self.read("func", "<B", "Function")
        while True:
            chunk = self.readChild("chunk[]", GifExtensionChunk)
            if chunk.getFilter()["size"] == 0:
                break
        
class GifScreenDescriptor(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "gif_screen_desc", "GIF screen descriptor", stream, parent)
        self.read("width", "<H", "Width")
        self.read("height", "<H", "Height")

        # TODO: Fix this
        self.read("flags", "<B", "Flags", post=self.processFlags)
        # -- End of TODO
        
        self.read("background", "<B", "Background color")
        self.read("notused", "<B", "Not used (zero)")

    def processFlags(self, chunk):
        flags = chunk.value
        self.global_map = ((flags & 0x80) == 0x80) # ok
        self.color_res = 1 + ((flags >> 4) & 0x7) # ??
        self.bits_per_pixel = 1 + (flags & 0x7) # ok
        if self.global_map:
            text = "global map, "
        else:
            text = ""
        return text + "color res=%u, bits/pixel=%u" % (self.color_res, self.bits_per_pixel)
        
class GifFile(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "gif_file", "GIF picture file", stream, parent)
        # Header
        self.read("header", "6s", "File header")
        assert (self["header"] == "GIF87a") or (self["header"] == "GIF89a")
        
        self.readChild("screen", GifScreenDescriptor)
        if self["screen"].global_map:
            self.readChild("color_map", GifColorMap)
            self.color_map = self["color_map"]
        else:
            self.color_map = None
            
        self.images = []
        while True:
            code = self.read("separator[]", "c", "Separator code")
            code = code.getValue()
            if code == "!":
                self.readChild("extensions[]", GifExtension)
            elif code == ",":
                self.readChild("images[]", GifImage)
                # TODO: Write GifImage code :-)
                self.readImage(stream)
                warning("GIF FILTER CAN NOT READ IMAGE CONTENT YET, SO ABORT READING!")
                return
            elif code == ";":
                # GIF Terminator
                return
            else:
                raise Exception("Wrong GIF image separator: ASCII %02X." % ord(code))

    def readImage(self, stream):              
        size = stream.getSize() - stream.tell()
        self.read("data", "%us" % size, "Image data")

registerPlugin(GifFile, "image/gif")
