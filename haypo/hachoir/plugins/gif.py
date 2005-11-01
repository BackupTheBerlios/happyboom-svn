"""
GIF splitter.

Status: only loads header, and is buggy ...
Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin

def displayGif(gif):
    print "Format: %s" % (gif.header)
    print "Size: %ux%u" % (gif.screen.width, gif.screen.height)
    print "Colormap: %s" % (gif.color_map)
    i = 0
    for image in gif.images:
        image = image.getFilter()
        print "Image %u: %s" % (i, image)
        i = i + 1

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
        self.global_map = ((self.flags & 0x80) == 0x80)
        self.interlaced = ((self.flags & 0x40) == 0x40)
        self.bits_per_pixel = 1 + (self.flags & 0x07)
        if not self.global_map:
            self.readChild("local_map", GifColorMap, "Local color map")
        else:
            self.local_map = None
        # -- End of TODO

    def __str__(self):
        return "Gif image <position=(%u,%u), size=%ux%u, bits/pixel=%u>" % \
            (self.left, self.top,
             self.width, self.height,
             self.bits_per_pixel)
     
class GifColorMap(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "gif_colormap", "GIF color map", stream, parent)
        if issubclass(parent.__class__, GifImage):
            self._nb_colors = (1 << parent.bits_per_pixel)
        else:
            assert issubclass(parent.__class__, GifFile)
            screen = parent.getChunk("screen").getFilter()
            self._nb_colors = (1 << screen.bits_per_pixel)
        self.readArray("map", GifColor, "Color map", self.checkEndOfMap)

    def checkEndOfMap(self, stream, array, color):
        return len(array) == self._nb_colors 

    def __str__(self):
        return "Gif colormap <colors=%u>" % (len(self.map))
        
class GifExtensionChunk(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "gif_ext_data", "GIF extension data", stream, parent)
        self.read("size", "<B", "Size (in bytes)")
        self.read("content", "<{size}s", "Content")

class GifExtension(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "gif_ext", "GIF extension", stream, parent)
        self.read("func", "<B", "Function")
        self.readArray("chunks", GifExtensionChunk, "Extension chunks", self.checkEnd)

    def checkEnd(self, stream, array, chunk):
        if chunk == None: return False
        return chunk.size == 0 
        
class GifScreenDescriptor(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "gif_screen_desc", "GIF screen descriptor", stream, parent)
        self.read("width", "<H", "Width")
        self.read("height", "<H", "Height")

        # TODO: Fix this
        self.read("flags", "<B", "Flags")
        self.global_map = ((self.flags & 0x80) == 0x80) # ok
        self.color_res = 1 + ((self.flags >> 4) & 0x7) # ??
        self.bits_per_pixel = 1 + (self.flags & 0x7) # ok
        # -- End of TODO
        
        self.read("background", "<B", "Background color")
        self.read("notused", "<B", "Not used (zero)")
        
class GifFile(Filter):
    def __init__(self, stream):
        Filter.__init__(self, "gif_file", "GIF picture file", stream, None)
        # Header
        self.read("header", "6s", "File header")
        assert (self.header == "GIF87a") or (self.header == "GIF89a")
        
        self.readChild("screen", GifScreenDescriptor, "Screen descriptor")
        if self.screen.global_map:
            self.readChild("color_map", GifColorMap, "Color map")
        else:
            self.color_map = None
            
        self.images = []
        while True:
            code = self.read("separator[]", "c", "Separator code")
            code = code.getData()
            if code == "!":
                self.readChild("extensions[]", GifExtension, "Extension")
            elif code == ",":
                self.readChild("images[]", GifImage, "Image")
                # TODO: Write GifImage code :-)
                print "WARNING: GIF FILTER CAN NOT READ IMAGE CONTENT YET, SO ABORT READING!"
                return
            elif code == ";":
                # GIF Terminator
                return
            else:
                raise Exception("Wrong GIF image separator: ASCII %02X." % ord(code))

registerPlugin("^.*\.(gif|GIF)$", "GIF picture", GifFile, displayGif)
