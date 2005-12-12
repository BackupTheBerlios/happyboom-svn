"""
AVI splitter.

Creation: 12 decembre 2005
Status: alpha
Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin

class AVI_ChunkList(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "avi_chunk", "AVI chunk", stream, parent)
        tag = self.read("tag", "4s", "Tag").value
        size = stream.getSize()-4
        end = stream.tell() + size
        if tag in ("hdrl", "INFO"):
            while 8 <= end - stream.tell():
                chunk = self.readChild("chunk[]", AVI_Chunk)            
            size = end - stream.tell()
            if size != 0:
                self.read("padding", "%us" % size, "Padding")
        elif tag == "strl":
            while not stream.eof():
                self.read("stag[]", "4s", "String tag")
                size = self.read("ssize[]", "<L", "String size").value
                self.read("svalue[]", "%us" % size, "String value")
        else:
            self.read("raw", "%us" % size, "Raw data")
        assert stream.tell() == end

class AVI_ChunkString(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "avi_chunk", "AVI chunk", stream, parent)

class AVI_Chunk(Filter):
    handler = {
        "LIST": AVI_ChunkList
    }
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "avi_chunk", "AVI chunk", stream, parent)
        tag = self.read("tag", "4s", "Tag").value
        size = self.read("size", "<L", "Size").value
        if tag in AVI_Chunk.handler:
            end = stream.tell() + size
            sub = stream.createSub(size=size)
            self.readStreamChild("data", sub, AVI_Chunk.handler[tag])
            assert stream.tell() == end
        else:
            self.read("raw", "%us" % size, "Raw data")

    def updateParent(self, parent):
        type = self["tag"]
        if type == "LIST":
            tag2 = self["data"]["tag"]
            type = type + " (%s)" % tag2      
        desc = "Chunk %s" % type
        self.setDescription(desc)
        parent.description = desc

class AVI_File(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "avi_file", "AVI file", stream, parent)
        self.read("header", "4s", "AVI header (RIFF)")
        assert self["header"] == "RIFF"
        self.read("filesize", "<L", "File size")
        self.read("avi", "4s", "\"AVI \" string")
        assert self["avi"] == "AVI "
        while not stream.eof():
            self.readChild("chunk[]", AVI_Chunk)

registerPlugin(AVI_File, "video/x-msvideo")
