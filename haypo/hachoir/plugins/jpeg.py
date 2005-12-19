"""
Exported filter.

Description:
Default filter
"""

from filter import Filter, OnlyFormatChunksFilter
from plugin import registerPlugin
from exif import ExifFilter

class JpegChunkApp0(OnlyFormatChunksFilter):
    def __init__(self, stream, parent):
        OnlyFormatChunksFilter.__init__(self, "jpeg_chunk", "JPEG chunk App0", stream, parent)
        self.read("jfif", "5s", "JFIF string")
        self.read("ver_maj", "B", "Major version")
        self.read("ver_min", "B", "Minor version")
        self.read("units", "B", "Units (=0)")
        if self["units"] == 0:
            self.read("aspect_x", "!H", "Aspect ratio (X)")
            self.read("aspect_y", "!H", "Aspect ratio (Y)")
        else:
            self.read("x_density", "!H", "X density")
            self.read("y_density", "!H", "Y density")
        self.read("thumb_w", "B", "Thumbnail width")
        self.read("thumb_h", "B", "Thumbnail height")
        thumb = self["thumb_w"] * self["thumb_h"]
        if thumb != 0:
            self.read("thumb_data", "%us" % size, "Thumbnail data")

class JpegChunk(OnlyFormatChunksFilter):
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
        OnlyFormatChunksFilter.__init__(self, "jpeg_chunk", "JPEG chunk", stream, parent)
        self.read("header", "B", "Header")
        assert self["header"] == 0xFF
        self.read("type", "B", "Type", post=self.postType)
        self.read("size", "!H", "Size")
        type = self["type"]
        size = self["size"] - 2
        if type in JpegChunk.handler:
            end = stream.tell() + size
            sub = stream.createSub(size=size)
            self.readStreamChild("content", "Chunk content", sub, JpegChunk.handler[type])
            assert stream.tell() == end
        else:
            self.read("data", "!%us" % size, "Data")
            
    def updateParent(self, chunk):
        type = self.getChunk("type").display
        desc = "JPEG chunk \"%s\"" % type
        chunk.description = desc

    def postType(self, chunk):
        type = chunk.value
        return JpegChunk.type_name.get(type, "Unknow type (%02X)" % type)

class JpegFile(OnlyFormatChunksFilter):
    def __init__(self, stream, parent=None):
        OnlyFormatChunksFilter.__init__(self, "jpeg_file", "JPEG file", stream, parent)
        self.read("header", "2s", "Header \"start of image\" (0xFF xD8)")
        assert self["header"] == "\xFF\xD8"
        while not stream.eof():
            id = self.readChild("chunk[]", "Jpeg Chunk", JpegChunk)
            if self[id]["type"] == 0xDA:
                break
        size = stream.getSize() - self.getSize()
        self.read("data", "%us" % size, "JPEG data")
        
registerPlugin(JpegFile, "image/jpeg")
