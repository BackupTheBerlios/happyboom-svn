"""
AVI splitter.

Creation: 12 decembre 2005
Status: alpha
Author: Victor Stinner
"""

from filter import Filter, OnDemandFilter
from plugin import registerPlugin
from tools import humanFilesize

class MovieChunk(OnDemandFilter):
    twocc_description = {
        "db": "Uncompressed video frame",
        "dc": "Compressed video frame",
        "wb": "Audio data",
        "pc": "Palette change"
    }

    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "movie_chunk", "Movie chunk", stream, parent)
        self.read("fourcc", "4s", "Stream chunk four character code")
        size = self.doRead("size", "<L", "Size").value
        if size == 0:
            self.type = "(empty)"
            return
        fourcc = self["fourcc"]
        twocc = fourcc[2:4]
        if twocc in MovieChunk.twocc_description:
            desc = MovieChunk.twocc_description[twocc]
        elif fourcc == "JUNK":
            desc = "Junk"
        else:
            desc = "Raw data"
        self.read("data", "%us" % size, desc)
        self.type = desc
        if size & 1:
            self.read("padding", "%us" % 1, "Padding")

    def updateParent(self, chunk):
        desc = "Movie chunk: %s" % self.type
        size = self["size"]
        if size != 0:
            desc = desc + " (%s)" % humanFilesize(size)
        chunk.description = desc 

class MovieStream(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "movie_str", "Movie stream", stream, parent)
        print " ********* PARSE STREAM ************"
        size = stream.getSize()
        end = stream.tell() + size

        self.chunk_count = 0
        start = stream.tell()
        while 8 <= end - stream.tell():
            # Little hack to read chunk size
            stream.seek(4, 1)
            chunk_size = stream.getFormat("<L", False)[0]
            stream.seek(-4, 1)
            chunk_size = 8 + chunk_size + chunk_size % 2
            # End of little hack :-)
            self.readSizedChild("chunk[]", "Movie chunk", chunk_size, MovieChunk)
            self.chunk_count += 1
            if self.chunk_count % 1000 == 0:
                print "Parse stream: %u %%" % ((stream.tell() - start) * 100 / size)
        size = end - stream.tell()
        if size > 0:
            self.read("end", "%us" % size, "Raw data")
        print " ********* END OF STREAM PARSING ************"

    def updateParent(self, chunk):
        chunk.description = "Movie stream: %u chunks" % self.chunk_count

class Header(Filter):
    def __init__(self, stream, parent, stream_type):
        Filter.__init__(self, "header", "Header", stream, parent)
        tag = self.read("tag", "4s", "Tag").value
        size = self.read("size", "<L", "Size").value
        self.type = "Unknow"
        if tag == "strh" and size >= 56:
            # Stream header
            self.type = "Stream header"
            hend = stream.tell() + size
            self.read("type_fourcc", "4s", "Stream type four character code")
            self.read("fourcc", "4s", "Stream four character code")
            self.read("flags", "<L", "Stream flags")
            self.read("priority", "<H", "Stream priority")
            self.read("langage", "2s", "Stream language")
            self.read("init_frames", "<L", "InitialFrames")
            self.read("scale", "<L", "Time scale")
            self.read("rate", "<L", "Divide by scale to give frame rate")
            self.read("start", "<L", "Stream start time (unit: rate/scale)")
            self.read("length", "<L", "Stream length (unit: rate/scale)")
            self.read("buf_size", "<L", "Suggested buffer size")
            self.read("quality", "<L", "Stream quality")
            self.read("sample_size", "<L", "Size of samples")
            self.read("left", "<H", "Destination rectangle (left)")
            self.read("top", "<H", "Destination rectangle (top)")
            self.read("right", "<H", "Destination rectangle (right)")
            self.read("bottom", "<H", "Destination rectangle (bottom)")
            diff = hend-stream.tell()
            if 0 < diff:
                self.read("h_extra", "%us" % diff, "Extra junk")
            assert stream.tell() == hend
        elif tag == "strf" and stream_type == "vids" and size == 40:
            # Video header
            self.type = "Video header"
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
        elif tag == "strf" and stream_type == "auds":
            # Audio (wav) header
            self.type = "Audio header"
            aend = stream.tell() + size
            self.read("a_id", "<H", "Audio format: Codec id")                    
            a_chan = self.read("a_channel", "<H", "Audio format: Channels").value
            self.read("a_sample_rate", "<L", "Audio format: Sample rate")                    
            self.read("a_bit_rate", "<L", "Audio format: Bit rate")
            self.read("a_block_align", "<H", "Audio format: Block align")
            if size >= 16:
                self.read("a_bits_per_sample", "<H", "Audio format: Bits per sample")
            if size >= 18:
                self.read("ext_size", "<H", "Audio format: Size of extra information")
            if a_chan > 2 and size >= 28:
                self.read("reserved", "<H", "Audio format: ")
                self.read("channel_mask", "<L", "Audio format: channels placement bitmask")
                self.read("subformat", "<L", "Audio format: Subformat id")
            diff = aend-stream.tell()
            if 0 < diff:
                self.read("a_extra", "%us" % diff, "Audio format: Extra")
            assert stream.tell() == aend
        elif tag == "strn":
            # Stream description
            self.read("desc", "%us" % size, "Stream description")
        else:
            if tag == "JUNK":
                self.type = "Junk"
            self.read("svalue[]", "%us" % size, "String value")

    def updateParent(self, chunk):
        chunk.description = "Header: %s" % self.type

class ChunkList(OnDemandFilter):
    handler = {
        "movi": MovieStream 
    }
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "avi_chunk", "AVI chunk", stream, parent)
        self.type = "Unknow"
        tag = self.doRead("tag", "4s", "Tag").value
        size = stream.getSize()-4
        end = stream.tell() + size
        if tag in ChunkList.handler:
            # Handler
            sub = stream.createSub(size=size)
            self.readSizedStreamChild("data", "Chunk data", size, sub, ChunkList.handler[tag])
        elif tag in ("hdrl", "INFO"):
            # (Headers) Chunks
            self.type = "List of chunks"
            while 8 < end - stream.tell():
                size = self.doReadChild("chunk[]", "Chunk", Chunk).size
                padding = size % 2
                if padding != 0:
                    self.read("padding[]", "%us" % padding, "Padding")
        elif tag == "strl":
            # Headers
            self.type = "Headers"
            stream_type = None
            while 8 <= end - stream.tell():
                header = self.doReadChild("header[]", "Header", Header, stream_type).getFilter()
                if header.hasChunk("type_fourcc"):
                    stream_type = header["type_fourcc"]
        else:
            # Raw data
            self.read("raw", "%us" % size, "Raw data")
        padding = end - stream.tell()
        if padding != 0:
            self.read("padding[]", "%us" % padding, "Padding")
        assert stream.tell() == end

    def updateParent(self, chunk):
        chunk.description = "Chunk list: %s" % self.type

class Chunk(OnDemandFilter):
    handler = {
        "LIST": ChunkList
    }

    tag_name = {
        "hdrl": "headers",
        "movi": "movie",
        "idx1": "index"
    }

    tag_description = {
        "hdrl": "Headers",
        "movi": "Movie stream",
        "idx1": "Stream index"
    }

    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "avi_chunk", "AVI chunk", stream, parent)
        tag = self.doRead("tag", "4s", "Tag").value
        size = self.doRead("size", "<L", "Size").value
        if tag in Chunk.handler:
            end = stream.tell() + size
            sub = stream.createSub(size=size)
            self.readSizedStreamChild("data", "Data", size, sub, Chunk.handler[tag])
            assert stream.tell() == end
        else:
            self.read("content", "%us" % size, "Raw data content")

    def updateParent(self, parent):
        tag = self["tag"]
        if tag == "LIST":
            tag = self["data"]["tag"]
            type = "LIST (%s)" % Chunk.tag_description.get(tag, tag)
        else:
            type = Chunk.tag_description.get(tag, tag)
        if tag in Chunk.tag_name:
            parent.id = Chunk.tag_name[tag]
        desc = "Chunk: %s" % type
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
            self.readChild("chunk[]", Chunk)

registerPlugin(AVI_File, "video/x-msvideo")
