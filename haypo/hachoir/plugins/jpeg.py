"""
Exported filter.

Description:
Default filter
"""

from filter import Filter
from plugin import registerPlugin

class JpegChunkApp0(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "jpeg_chunk", "JPEG chunk App0", stream, parent)
        self.read("jfif", "!5s", "JFIF string")
        self.read("ver_maj", "!B", "Major version")
        self.read("ver_min", "!B", "Minor version")
        self.read("units", "!1B", "Units (=0)")
        self.read("x_density", "!H", "X density")
        self.read("y_density", "!H", "Y density")
        self.read("thumb_w", "!B", "Thumbnail width")
        self.read("thumb_h", "!1B", "Thumbnail height")
        thumb = self.thumb_w * self.thumb_h
        if thumb != 0:
            self.read("thumb_data", "!%us" % size, "Thumbnail data", truncate=True)

class JpegChunk(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "jpeg_chunk", "JPEG chunk", stream, parent)
        self.read("header", "!2B", "Header", post=self.getChunkType)
        assert self.header[0] == (0xFF)
        self.read("size", "!H", "Size")
        if self.header[1] == 0xE0:
            chunk = self.readChild("app0", JpegChunkApp0)
            assert chunk.size == (self.size - 2)
        else:
            self.read("data", "!%us" % (self.size - 2), "Data")

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
            0xE0: "APP0",
            0xFE: "Comment"
        }
        type = chunk.value[1]
        if type in types:
            type = types[type]
        else:
            type = "Unknow type (%02X)" % type
        self.setDescription("JPEG chunk \"%s\"" % type)
        return type

class JpegFile(Filter):
    def checkEndOfChunks(self, stream, array, chunk):
        if chunk != None and chunk.header[1] == 0xDA: return True
        return stream.eof()

    def __init__(self, stream):
        Filter.__init__(self, "jpeg_file", "JPEG file", stream, None)
        self.read("header", "!2B", "Header \"start of image\" (0xFF, 0xD8)")
        assert self.header == (0xFF, 0xD8)
        self.readArray("chunk", JpegChunk, "Chunks", self.checkEndOfChunks)
        self.read("data", "!{@end@}s", "JPEG data")
        
registerPlugin("^.*\.(jpg|jpeg|JPG|JPEG)$", "JPEG picture", JpegFile, None)
