"""
ID3 parser

Author: Victor Stinner
"""

from filter import OnDemandFilter
from tools import humanDuration
from chunk import FormatChunk, EnumChunk

class ID3_String(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "id3_string", "ID3 string", stream, parent)
        self.read("zero", "Zero", (FormatChunk, "uint8"))
        assert self["zero"] == 0
        size = stream.getSize()-1
        self.read("content", "Content", (FormatChunk, "string[%u]" % size))

class ID3_Private(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "id3_priv", "ID3 private", stream, parent)
        size = stream.getSize()
        if stream.read(9, False) == "PeakValue":
            self.read("text", "Text", (FormatChunk, "string[%u]" % 9))
            size = size - 9
        self.read("content", "Content", (FormatChunk, "string[%u]" % size))

class ID3_TrackLength(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "id3_tlen", "ID3 track length", stream, parent)
        self.read("zero", "Zero", (FormatChunk, "uint8"))
        assert self["zero"] == 0
        size = stream.getSize()-1
        self.read("length", "Length in ms", (FormatChunk, "string[%u]" % size), {"post": self.computeLength})

    def computeLength(self, chunk):
        try:
            ms = int(chunk.value)
            return humanDuration(ms)
        except:
            return chunk.value

class ID3_Chunk(OnDemandFilter):
    tag_name = {
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
        OnDemandFilter.__init__(self, "id3_chunk", "ID3 Chunk", stream, parent, ">")
        tag = self.doRead("tag", "Tag", (EnumChunk, "string[4]", ID3_Chunk.tag_name)).value
        self.read("size", "Size", (FormatChunk, "uint32"))
        self.read("flags", "Flags", (FormatChunk, "uint16"))
        size = self["size"]
        if tag in ID3_Chunk.handler:
            end = stream.tell() + size
            if size != 0:
                substream = stream.createLimited(size=size)
                self.read("content", "Content", (ID3_Chunk.handler[tag],), {"stream": substream})
            assert stream.tell() == end
        else:
            self.read("content", "Raw data content", (FormatChunk, "string[%u]" % size))

    def updateParent(self, chunk):
        type = self["tag"].strip("\0")
        if type != "":
            type = ID3_Chunk.tag_name.get(type, "Unknow (\"%s\")" % type)
            desc = "ID3 Chunk: %s" % type
        else:
            desc = "(empty ID3 chunk)"
        chunk.description = desc
        self.setDescription(desc)

class ID3_Parser(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "id3", "ID3", stream, parent, "!")
        self.read("header", "Header (ID3)", (FormatChunk, "string[3]"))
        assert self["header"] == "ID3"
        self.read("ver_major", "Version (major)", (FormatChunk, "uint8"))
        assert self["ver_major"] in (3,4)
        self.read("ver_minor", "Version (minor)", (FormatChunk, "uint8"))
        assert self["ver_minor"] == 0
        self.read("flags", "Flags", (FormatChunk, "uint8"))
        self.read("size", "Size", (FormatChunk, "uint32"))
        end = self["size"]
        while stream.tell() < end:
            chunk = self.doRead("chunk[]", "Chunk", (ID3_Chunk,))
            if chunk["size"] == 0:
                break

        # Search first byte of the MPEG file                
        size = stream.searchLength("\xFF", False)
        if size == -1:
            # ... or read until the end
            size = end - stream.tell()
        if 0 < size:
            self.read("padding", "Padding", (FormatChunk, "string[%u]" % size))
