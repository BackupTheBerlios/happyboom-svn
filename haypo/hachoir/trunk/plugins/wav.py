"""
WAV audio file parser

Author: Victor Stinner
"""

from filter import OnDemandFilter
from plugin import registerPlugin
from chunk import FormatChunk, EnumChunk

class WAV_Fact(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "fact", "Stream length (\"fact\" chunk)", stream, parent, "<")
        self.read("nb_samples", "Number of samples in audio stream", (FormatChunk, "int32"))

class WAV_Format(OnDemandFilter):
    codec_name = {
        1: "Uncompressed"
    }
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "format", "Audio format", stream, parent, "<")
        self.read("codec", "Audio codec", (EnumChunk, "int16", WAV_Format.codec_name))
        self.read("channels", "Channels", (FormatChunk, "uint16"))
        self.read("sample_per_sec", "Samples per second", (FormatChunk, "uint32"))
        self.read("byte_per_sec", "Average bytes per second", (FormatChunk, "uint32"))
        self.read("block_align", "Block align", (FormatChunk, "uint16"))
        self.read("bits_per_sample", "Bits per sample", (FormatChunk, "uint16"))

    def updateParent(self, chunk):
        if self["channels"] == 2:
            channels = "stereo"
        else:
            channels = "mono"
        chunk.description = "Audio format: %u kHz, %s" \
            % (self["sample_per_sec"], channels)

class Chunk(OnDemandFilter):
    handler = {
        "fmt ": WAV_Format,
        'fact': WAV_Fact
    }

    tag_name = {
        "fmt ": "format",
        "data": "audio_data"
    }

    tag_description = {
        "fmt": "Audio format",
        "data": "Audio stream data"
    }

    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "chunk", "Chunk", stream, parent, "<")
        tag = self.doRead("tag", "Tag", (FormatChunk, "string[4]")).value
        size = self.doRead("size", "Size", (FormatChunk, "uint32")).value
        if tag in Chunk.handler:
            end = stream.tell() + size
            sub = stream.createSub(size=size)
            self.read("content", "Data content", (Chunk.handler[tag],), {"size": size, "stream": sub})
            assert stream.tell() == end
        else:
            self.read("content", "Raw data content", (FormatChunk, "string[%u]" % size))

    def updateParent(self, chunk):
        tag = self["tag"].strip("\0")
        type = Chunk.tag_description.get(tag, "\"%s\"" % tag)
        if tag in Chunk.tag_name:
            chunk.id = Chunk.tag_name[tag]
        chunk.description = "Chunk: %s" % type

class WavFile(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "wav_file", "WAV audio file", stream, parent, "<")
        self.read("header", "RIFF header (\"RIFF\")", (FormatChunk, "string[4]"))
        assert self["header"] == "RIFF"
        self.read("filesize", "File size", (FormatChunk, "uint32"))
        self.read("wave", "\"WAVE\" string", (FormatChunk, "string[4]"))
        assert self["wave"] == "WAVE"
        self.format = None
        while not stream.eof():
            id = self.read("chunk[]", "Chunk", (Chunk,))
            if id == "format":
                self.format = self["format"]

registerPlugin(WavFile, "audio/x-wav")
