"""
AVI splitter.

Creation: 12 decembre 2005
Status: alpha
Author: Victor Stinner
"""

from filter import OnDemandFilter
from plugin import registerPlugin
from tools import humanFilesize
from chunk import FormatChunk

class MovieChunk(OnDemandFilter):
    twocc_description = {
        "db": "Uncompressed video frame",
        "dc": "Compressed video frame",
        "wb": "Audio data",
        "pc": "Palette change"
    }

    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "movie_chunk", "Movie chunk", stream, parent, "<")
        self.read("fourcc", "Stream chunk four character code", (FormatChunk, "string[4]"))
        size = self.doRead("size", "Size", (FormatChunk, "uint32")).value
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
        self.read("data", desc, (FormatChunk, "string[%u]" % size))
        self.type = desc
        if size & 1:
            self.read("padding", "Padding", (FormatChunk, "uint8"))

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
            # Little hack to read chunk size
            stream.seek(4, 1)
            chunk_size = stream.getFormat("<uint32", False)
            stream.seek(-4, 1)
            chunk_size = 8 + chunk_size + chunk_size % 2
            # End of little hack :-)
            self.read("chunk[]", "Movie chunk", (MovieChunk,), {"size": chunk_size})
            self.chunk_count += 1
            if self.chunk_count % 1000 == 0:
                print "Parse stream: %u %%" % ((stream.tell() - start) * 100 / size)
        size = end - stream.tell()
        if size > 0:
            self.read("end", "Raw data", (FormatChunk, "string[%u]" % size))
        print " ********* END OF STREAM PARSING ************"

    def updateParent(self, chunk):
        chunk.description = "Movie stream: %u chunks" % self.chunk_count

class Header(OnDemandFilter):
    def __init__(self, stream, parent, stream_type):
        OnDemandFilter.__init__(self, "header", "Header", stream, parent, "<")
        tag = self.doRead("tag", "Tag", (FormatChunk, "string[4]")).value
        size = self.doRead("size", "Size", (FormatChunk, "uint32")).value
        self.type = "Unknow"
        if tag == "strh" and size >= 56:
            # Stream header
            self.type = "Stream header"
            hend = stream.tell() + size
            self.read("type_fourcc", "Stream type four character code", (FormatChunk, "string[4]"))
            self.read("fourcc", "Stream four character code", (FormatChunk, "string[4]"))
            self.read("flags", "Stream flags", (FormatChunk, "uint32"))
            self.read("priority", "Stream priority", (FormatChunk, "uint16"))
            self.read("langage", "Stream language", (FormatChunk, "string[2]"))
            self.read("init_frames", "InitialFrames", (FormatChunk, "uint32"))
            self.read("scale", "Time scale", (FormatChunk, "uint32"))
            self.read("rate", "Divide by scale to give frame rate", (FormatChunk, "uint32"))
            self.read("start", "Stream start time (unit: rate/scale)", (FormatChunk, "uint32"))
            self.read("length", "Stream length (unit: rate/scale)", (FormatChunk, "uint32"))
            self.read("buf_size", "Suggested buffer size", (FormatChunk, "uint32"))
            self.read("quality", "Stream quality", (FormatChunk, "uint32"))
            self.read("sample_size", "Size of samples", (FormatChunk, "uint32"))
            self.read("left", "Destination rectangle (left)", (FormatChunk, "uint16"))
            self.read("top", "Destination rectangle (top)", (FormatChunk, "uint16"))
            self.read("right", "Destination rectangle (right)", (FormatChunk, "uint16"))
            self.read("bottom", "Destination rectangle (bottom)", (FormatChunk, "uint16"))
            diff = hend-stream.tell()
            if 0 < diff:
                self.read("h_extra", "Extra junk", (FormatChunk, "string[%u]" % diff))
            assert stream.tell() == hend
        elif tag == "strf" and stream_type == "vids" and size == 40:
            # Video header
            self.type = "Video header"
            self.read("v_size", "Video format: Size", (FormatChunk, "uint32"))                    
            self.read("v_width", "Video format: Width", (FormatChunk, "uint32"))                    
            self.read("v_height", "Video format: Height", (FormatChunk, "uint32"))                    
            self.read("v_panes", "Video format: Panes", (FormatChunk, "uint16"))
            self.read("v_depth", "Video format: Depth", (FormatChunk, "uint16"))                    
            self.read("v_tag1", "Video format: Tag1", (FormatChunk, "uint32"))                    
            self.read("v_img_size", "Video format: Image size", (FormatChunk, "uint32"))                    
            self.read("v_xpels_meter", "Video format: XPelsPerMeter", (FormatChunk, "uint32"))
            self.read("v_ypels_meter", "Video format: YPelsPerMeter", (FormatChunk, "uint32"))
            self.read("v_clr_used", "Video format: ClrUsed", (FormatChunk, "uint32"))
            self.read("v_clr_importand", "Video format: ClrImportant", (FormatChunk, "uint32"))
        elif tag == "strf" and stream_type == "auds":
            # Audio (wav) header
            self.type = "Audio header"
            aend = stream.tell() + size
            self.read("a_id", "Audio format: Codec id", (FormatChunk, "uint16"))
            a_chan = self.doRead("a_channel", "Audio format: Channels", (FormatChunk, "uint16")).value
            self.read("a_sample_rate", "Audio format: Sample rate", (FormatChunk, "uint32"))                    
            self.read("a_bit_rate", "Audio format: Bit rate", (FormatChunk, "uint32"))
            self.read("a_block_align", "Audio format: Block align", (FormatChunk, "uint16"))
            if size >= 16:
                self.read("a_bits_per_sample", "Audio format: Bits per sample", (FormatChunk, "uint16"))
            if size >= 18:
                self.read("ext_size", "Audio format: Size of extra information", (FormatChunk, "uint16"))
            if a_chan > 2 and size >= 28:
                self.read("reserved", "Audio format: ", (FormatChunk, "uint16"))
                self.read("channel_mask", "Audio format: channels placement bitmask", (FormatChunk, "uint32"))
                self.read("subformat", "Audio format: Subformat id", (FormatChunk, "uint32"))
            diff = aend-stream.tell()
            if 0 < diff:
                self.read("a_extra", "Audio format: Extra", (FormatChunk, "string[%u]" % diff))
            assert stream.tell() == aend
        elif tag == "strn":
            # Stream description
            self.read("desc", "Stream description", (FormatChunk, "string[%u]" % size))
        else:
            if tag == "JUNK":
                self.type = "Junk"
            self.read("junk", "Junk", (FormatChunk, "string[%u]" % size))

    def updateParent(self, chunk):
        chunk.description = "Header: %s" % self.type

class ChunkList(OnDemandFilter):
    handler = {
        "movi": MovieStream 
    }
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "avi_chunk", "AVI chunk", stream, parent)
        self.type = "Unknow"
        tag = self.doRead("tag", "Tag", (FormatChunk, "string[4]")).value
        size = stream.getSize()-4
        end = stream.tell() + size
        if tag in ChunkList.handler:
            # Handler
            sub = stream.createSub(size=size)
            self.read("data", "Chunk data", (ChunkList.handler[tag],), {"size": size, "stream": sub})
        elif tag in ("hdrl", "INFO"):
            # (Headers) Chunks
            self.type = "List of chunks"
            while 8 < end - stream.tell():
                size = self.doRead("chunk[]", "Chunk", (Chunk,)).getSize()
                if size % 2 != 0:
                    self.read("padding[]", "Padding", (FormatChunk, "uint8"))
        elif tag == "strl":
            # Headers
            self.type = "Headers"
            stream_type = None
            while 8 <= end - stream.tell():
                header = self.doRead("header[]", "Header", (Header, stream_type))
                if header.hasChunk("type_fourcc"):
                    stream_type = header["type_fourcc"]
        else:
            # Raw data
            self.read("raw", "Raw data", (FormatChunk, "string[%u]" % size))
        padding = end - stream.tell()
        if padding != 0:
            self.read("padding[]", "Padding", (FormatChunk, "string[%u]" % padding))
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
        OnDemandFilter.__init__(self, "chunk", "Chunk", stream, parent, "<")
        tag = self.doRead("tag", "Tag", (FormatChunk, "string[4]")).value
        size = self.doRead("size", "Size", (FormatChunk, "uint32")).value
        if tag in Chunk.handler:
            end = stream.tell() + size
            sub = stream.createSub(size=size)
            self.read("data", "Data", (Chunk.handler[tag],), {"size": size, "stream": sub})
            assert stream.tell() == end
        else:
            self.read("content", "Raw data content", (FormatChunk, "string[%u]" % size))

    def updateParent(self, parent):
        tag = self["tag"].strip("\0")
        if tag == "LIST":
            tag = self["data"]["tag"]
            type = "LIST (%s)" % Chunk.tag_description.get(tag, tag)
        else:
            type = Chunk.tag_description.get(tag, "\"%s\"" % tag)
        if tag in Chunk.tag_name:
            parent.id = Chunk.tag_name[tag]
        desc = "Chunk: %s" % type
        self.setDescription(desc)
        parent.description = desc

class AVI_File(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "avi_file", "AVI file", stream, parent, "<")
        self.read("header", "AVI header (RIFF)", (FormatChunk, "string[4]"))
        assert self["header"] == "RIFF"
        self.read("filesize", "File size", (FormatChunk, "uint32"))
        self.read("avi", "\"AVI \" string", (FormatChunk, "string[4]"))
        assert self["avi"] == "AVI "
        while not stream.eof():
            self.read("chunk[]", "Chunk", (Chunk,))

registerPlugin(AVI_File, "video/x-msvideo")
