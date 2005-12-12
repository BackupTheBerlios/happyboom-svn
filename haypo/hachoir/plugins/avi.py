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
        elif tag == "strl":
            while 8 <= end - stream.tell():
                stag = self.read("stag[]", "4s", "String tag").value
                size = self.read("ssize[]", "<L", "String size").value
                if stag == "strf" and size == 40:
                    # Video header
                    self.read("v_size", "<L", "Video format: Size")                    
                    self.read("v_width", "<L", "Video format: Width")                    
                    self.read("v_height", "<L", "Video format: Height")                    
                    self.read("v_panes", "<H", "Video format: Panes")                    
                    self.read("v_depth", "<H", "Video format: Depth")                    
                    self.read("v_tag1", "<L", "Video format: Tag1")                    
                    self.read("v_img_size", "<L", "Video format: Image size")                    
                    self.read("v_xpels_meter", "<L", "Video format: XPelsPerMeter")
                    self.read("v_ypels_meter", "<L", "Video format: YPelsPerMeter")
                    self.read("v_clr_used", "<L", "Video format: ClrUsed")
                    self.read("v_clr_importand", "<L", "Video format: ClrImportant")
                elif stag == "strf" and size == 30:
                    # Audio (wav) header
                    aend = stream.tell() + size
                    self.read("a_id", "<H", "Audio format: ID")                    
                    self.read("a_channel", "<H", "Audio format: Channels")                    
                    self.read("a_sample_rate", "<L", "Audio format: Sample rate")                    
                    self.read("a_bit_rate", "<L", "Audio format: Bit rate")
                    self.read("a_block_align", "<H", "Audio format: Block align")
                    # if size == 14: bits_per_sample = 8
                    self.read("a_bits_per_sample", "<H", "Audio format: Bits per sample")
                    self.read("a_codec_id", "<H", "Audio format: Codec id")
                    diff = aend-stream.tell()
                    if 0 < diff:
                        self.read("a_extra", "%us" % diff, "Audio format: Extra")
                    assert stream.tell() == aend
                else:
                    self.read("svalue[]", "%us" % size, "String value")
        else:
            self.read("raw", "%us" % size, "Raw data")
        padding = end - stream.tell()
        if padding != 0:
            self.read("padding", "%us" % padding, "Padding")
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
