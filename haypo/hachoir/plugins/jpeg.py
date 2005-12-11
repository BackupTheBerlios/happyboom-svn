"""
Exported filter.

Description:
Default filter
"""

from filter import Filter
from plugin import registerPlugin
from exif import ExifFilter

class JpegChunkApp0(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "jpeg_chunk", "JPEG chunk App0", stream, parent)
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

class JpegChunk(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "jpeg_chunk", "JPEG chunk", stream, parent)
        chunk = self.read("header", "B", "Header")
        assert self["header"] == 0xFF
        chunk = self.read("type", "B", "Type", post=self.getChunkType)
        known = {
            0xE0: JpegChunkApp0,
            0xE1: ExifFilter
        }
        chunk_type = self["type"]
        self.read("size", "!H", "Size")
        size = self["size"] - 2
        if chunk_type in known:
            end = stream.tell() + size
            sub = stream.createSub(size=size)
            self.readStreamChild("app0", sub, known[chunk_type])
            assert stream.tell() == end
        else:
            self.read("data", "!%us" % size, "Data")

    def getChunkType(self, chunk):
        types = {
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
        type = chunk.value
        if type in types:
            type = types[type]
        else:
            type = "Unknow type (%02X)" % type
        self.setDescription("JPEG chunk \"%s\"" % type)
        return type

class JpegFile(Filter):
    def checkEndOfChunks(self, stream, array, chunk):
        if chunk != None and chunk["type"] == 0xDA: return True
        return stream.eof()

    def __init__(self, stream, parent=None):
        Filter.__init__(self, "jpeg_file", "JPEG file", stream, parent)
        self.read("header", "!2B", "Header \"start of image\" (0xFF, 0xD8)")
        assert self["header"] == (0xFF, 0xD8)
        self.readArray("chunk", JpegChunk, "Chunks", self.checkEndOfChunks)
        self.read("data", "!{@end@}s", "JPEG data")
        
registerPlugin(JpegFile, "image/jpeg")
