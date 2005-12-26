"""
AVI splitter.

Creation: 12 decembre 2005
Status: alpha
Author: Victor Stinner
"""

from filter import Filter
from tools import humanDuration

class ID3_String(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "id3_string", "ID3 string", stream, parent)
        self.read("zero", "B", "Zero")
        assert self["zero"] == 0
        size = stream.getSize()-1
        self.read("content", "%us" % size, "Content")

class ID3_Private(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "id3_priv", "ID3 private", stream, parent)
        size = stream.getSize()
        if stream.read(9, False) == "PeakValue":
            self.read("text", "%us" % 9, "Text")
            size = size - 9
            self.read("content", "%us" % size, "Content")
        else:
            self.read("content", "%us" % size, "Content")

class ID3_TrackLength(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "id3_tlen", "ID3 track length", stream, parent)
        self.read("zero", "B", "Zero")
        assert self["zero"] == 0
        size = stream.getSize()-1
        self.read("length", "%us" % size, "Length in ms", post=self.computeLength)

    def computeLength(self, chunk):
        try:
            ms = int(chunk.value)
            return humanDuration(ms)
        except:
            return chunk.value
        

class ID3_Chunk(Filter):
    name = {
        "COMM": "Comment",
        "PRIV": "Private",
        "TPE1": "Artist",
        "TCOP": "Copyright",
        "TALB": "Album",
        "TENC": "Encoder",
        "TYER": "Year",
        "TSSE": "Encoder settings",
        "TCOM": "Composer",
        "TRCK": "Track number",
        "PCNT": "Play counter",
        "TCON": "Content type",
        "TLEN": "Track length",
        "TIT2": "Track title"
    }
    handler = {
        "TYER": ID3_String,
        "TALB": ID3_String,
        "TCON": ID3_String,
        "TPE1": ID3_String,
        "TCOP": ID3_String,
        "TRCK": ID3_String,
        "TIT2": ID3_String,
        "TSSE": ID3_String,
        "PRIV": ID3_Private,
        "TLEN": ID3_TrackLength
    }
    def __init__(self, stream, parent):
        Filter.__init__(self, "id3_chunk", "ID3 Chunk", stream, parent)
        tag = self.read("tag", "!4s", "Tag").value
        self.read("size", ">L", "Size")
        self.read("flags", ">H", "Flags")
        size = self["size"]
        if tag in ID3_Chunk.handler:
            end = stream.tell() + size
            if size != 0:
                substream = stream.createLimited(size=size)
                self.readStreamChild("content", substream, ID3_Chunk.handler[tag])
            assert stream.tell() == end
        else:
            self.read("data", "%us" % size, "Raw data")

    def updateParent(self, chunk):
        type = self["tag"].strip("\0")
        if type != "":
            type = ID3_Chunk.name.get(type, "Unknow (\"%s\")" % type)
            desc = "ID3 Chunk: %s" % type
        else:
            desc = "(empty ID3 chunk)"
        chunk.description = desc
        self.setDescription(desc)

class ID3_Parser(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "id3", "ID3", stream, parent)
        header = self.read("header", "!3s", "Header (ID3)").value
        assert header == "ID3"
        ver_major = self.read("ver_major", "!1B", "Version (major)").value
        assert ver_major in (3,4)
        ver_minor = self.read("ver_minor", "!B", "Version (minor)").value
#        assert ver_minor == 0
        self.read("flags", "!B", "Flags")
        self.read("size", "!L", "Size")
        end = stream.tell() + self["size"]
        while stream.tell() < end:
            chunk = self.readChild("chunk[]", ID3_Chunk)
            if chunk.getFilter()["size"] == 0:
                break
        padding = end - stream.tell()
        if 0 < padding:
            self.read("padding", "%us" % padding, "Padding")
#        assert stream.tell() == end
