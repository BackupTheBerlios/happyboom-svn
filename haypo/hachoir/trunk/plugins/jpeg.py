"""
JPEG picture parser.

Author: Victor Stinner
"""

from filter import OnDemandFilter
from plugin import registerPlugin
from chunk import FormatChunk
from exif import ExifFilter

class JpegChunkApp0(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "app0", "JPEG APP0", stream, parent, "!")
        self.read("jfif", "JFIF string", (FormatChunk, "string[5]"))
        self.read("ver_maj", "Major version", (FormatChunk, "uint8"))
        self.read("ver_min", "Minor version", (FormatChunk, "uint8"))
        self.read("units", "Units", (FormatChunk, "uint8"))
        if self["units"] == 0:
            self.read("aspect_x", "Aspect ratio (X)", (FormatChunk, "uint16"))
            self.read("aspect_y", "Aspect ratio (Y)", (FormatChunk, "uint16"))
        else:
            self.read("x_density", "X density", (FormatChunk, "uint16"))
            self.read("y_density", "Y density", (FormatChunk, "uint16"))
        self.read("thumb_w", "Thumbnail width", (FormatChunk, "uint8"))
        self.read("thumb_h", "Thumbnail height", (FormatChunk, "uint8"))
        thumb = self["thumb_w"] * self["thumb_h"]
        if thumb != 0:
            self.read("thumb_data", "Thumbnail data", (FormatChunk, "string[%u]" % size))

class JpegChunk(OnDemandFilter):
    type_name = {
        0xC0: "Start Of Frame 0 (SOF0)",
        0xC3: "Define Huffman Table (DHT)",
        0xD8: "Start of image (SOI)",
        0xD9: "End of image (EOI)",
        0xDA: "Start Of Scan (SOS)",
        0xDB: "Define Quantization Table (DQT)",
        0xDC: "Define number of Lines (DNL)",
        0xDD: "Define Restart Interval (DRI)",
        0xE1: "EXIF",
        0xE0: "APP0",
        0xFE: "Comment"
    }
    handler = {
        0xE0: JpegChunkApp0,
        0xE1: ExifFilter
    }

    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "chunk", "Chunk", stream, parent, "!")
        self.read("header", "Header", (FormatChunk, "uint8"))
        assert self["header"] == 0xFF
        self.read("type", "Type", (FormatChunk, "uint8"), {"post": self.postType})
        self.read("size", "Size", (FormatChunk, "uint16"))
        type = self["type"]
        size = self["size"] - 2
        if type in JpegChunk.handler:
            end = stream.tell() + size
            sub = stream.createSub(size=size)
            self.read("content", "Chunk content", (JpegChunk.handler[type],), {"stream": sub, "size": size})
            assert stream.tell() == end
        else:
            self.read("data", "Data", (FormatChunk, "string[%u]" % size))
            
    def updateParent(self, chunk):
        type = self.getChunk("type").display
        desc = "Chunk: %s" % type
        chunk.description = desc

    def postType(self, chunk):
        type = chunk.value
        return JpegChunk.type_name.get(type, "Unknow type (%02X)" % type)

class JpegFile(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "jpeg_file", "JPEG file", stream, parent)
        self.read("header", "Header \"start of image\" (0xFF xD8)", (FormatChunk, "string[2]"))
        assert self["header"] == "\xFF\xD8"
        while not stream.eof():
            chunk = self.doRead("chunk[]", "Chunk", (JpegChunk,))
            if chunk["type"] == 0xDA:
                break
        size = stream.getSize() - self.getSize()
        self.read("data", "JPEG data", (FormatChunk, "string[%u]" % size))
        
registerPlugin(JpegFile, "image/jpeg")
