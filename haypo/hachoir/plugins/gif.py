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
    for image in gif.images:
        print image

class GifColor(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("red", "<B", "Red")
        self.read("green", "<B", "Green")
        self.read("blue", "<B", "Blue")

class GifImage(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
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
            self.local_map = GifColorMap(stream, 1 << self.bits_per_pixel, self)
        else:
            self.local_map = None
        # -- End of TODO

    def __str__(self):
        return "Gif image <position=(%u,%u), size=%ux%u, bits/pixel=%u>" % \
            (self.left, self.top,
             self.width, self.height,
             self.bits_per_pixel)
     
class GifColorMap(Filter):
    def __init__(self, stream, nb_colors, parent):
        Filter.__init__(self, stream, parent)
        self.map = []
        self.openChild()
        for i in range(0, nb_colors):
            self.newChild("Color")
            self.map.append( GifColor(stream, self) )
        self.closeChild("Colors")

    def __str__(self):
        return "Gif colormap <colors=%u>" % (len(self.map))
        
class GifExtensionChunk(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("size", "<B", "Size (in bytes)")
        self.read("content", "<[size]s", "Content")

class GifExtension(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("func", "<B", "Function")
        self.chunks = []
        self.openChild()
        while True:
            self.newChild("Extension chunk")
            chunk = GifExtensionChunk(stream, self)
            self.chunks.append( chunk )
            if chunk.size == 0: break 
        self.closeChild("Extension chunk")
        
class GifScreenDescriptor(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, stream, parent)
        self.read("width", "<H", "Width")
        self.read("height", "<H", "Height")

        # TODO: Fix this
        self.read("flags", "<B", "Flags")
        self.global_map = ((self.flags & 0x80) == 0x80) # ok
        self.color_res = 1 + ((self.flags >> 4) & 0x7) # ??
        self.bits_per_pixel = 1 + (self.flags & 0x7) # ok
        # -- End of TODO
        
        self.background = stream.get8()
        zero = stream.get8()
        
class GifFilter(Filter):
    def __init__(self, stream):
        Filter.__init__(self, stream)
        # Header
        self.read("header", "6s", "File header")
        assert (self.header == "GIF87a") or (self.header == "GIF89a")
        self.newChild("Screen descriptor")
        self.screen = GifScreenDescriptor(stream, self)
        if self.screen.global_map:
            self.newChild("Color map")
            self.color_map = GifColorMap(stream, 1 << self.screen.bits_per_pixel, self)
        else:
            self.color_map = None
        self.images = []
        self.extensions = []
        while True:
            self.read("code", "c", "Separator code")
            if self.code == "!":
                self.openChild()
                self.newChild("New extension")
                self.extensions.append( GifExtension(stream, self) )
                self.closeChild("Extension")
            elif self.code == ",":
                self.openChild()
                self.newChild("New image")
                self.images.append( GifImage(stream, self) )
                self.closeChild("Image")
                return
            elif self.code == ";":
                # GIF Terminator
                return
            else:
                raise Exception("Wrong GIF image separator: ASCII %02X." % ord(self.code))

registerPlugin("^.*\.(gif|GIF)$", "GIF picture", GifFilter, displayGif)
