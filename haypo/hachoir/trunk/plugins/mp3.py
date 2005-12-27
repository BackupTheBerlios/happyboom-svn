"""
AVI splitter.

Creation: 12 decembre 2005
Status: alpha
Author: Victor Stinner
"""

from filter import OnDemandFilter
from plugin import registerPlugin
from chunk import FormatChunk, BitsChunk, BitsStruct
from id3 import ID3_Parser

class MP3_File(OnDemandFilter):
    version = {
        0: "2.5",
        2: "2",
        3: "1"
    }
    layer = {
        0: "(reserved)",
        1: "III",
        2: "II",
        3: "I"
    }
    bit_rate = {
        # MPEG1
        1: {
            # MPEG1, layer I
            3: {
                1: 32,
                2: 64,
                3: 96,
                4: 128,
                5: 160,
                6: 192,
                7: 224,
                8: 256,
                9: 288,
                10: 320,
                11: 352,
                12: 384,
                13: 416,
                14: 448
            },

            # MPEG1, layer II
            2: {
                1: 32,
                2: 48,
                3: 56,
                4: 64,
                5: 80,
                6: 96,
                7: 112,
                8: 128,
                9: 160,
                10: 192,
                11: 224,
                12: 256,
                13: 320,
                14: 384
            },

            # MPEG1, layer III
            1: {
                1: 32,
                2: 40,
                3: 48,
                4: 56,
                5: 64,
                6: 80,
                7: 96,
                8: 112,
                9: 128,
                10: 160,
                11: 192,
                12: 224,
                13: 256,
                14: 320
            }
        },
        
        # MPEG2 / MPEG2.5
        2: {
            # MPEG2 / MPEG2.5, layer I
            3: {
                1: 32,
                2: 64,
                3: 96,
                4: 128,
                5: 160,
                6: 192,
                7: 224,
                8: 256,
                9: 288,
                10: 320,
                11: 352,
                12: 384,
                13: 416,
                14: 448},

            # MPEG2 / MPEG2.5, layer II
            2: {
                1: 32,
                2: 48,
                3: 56,
                4: 64,
                5: 80,
                6: 96,
                7: 112,
                8: 128,
                9: 160,
                10: 192,
                11: 224,
                12: 256,
                13: 320,
                14: 384},

            # MPEG2 / MPEG2.5, layer III
            1: {
                1: 8, # 8
                2: 16, # 16
                3: 24, # 24
                4: 32, # 32
                5: 64, # 40
                6: 80, # 48
                7: 56, # 56
                8: 64, # 64
                9: 128, # 80
                10: 160, # 96
                11: 112, # 112
                12: 128, # 128
                13: 256, # 144 
                14: 320} # 160
        }
    }
    sampling_rate = {
        # MPEG1
        3: {
            0: 44100,
            1: 48000,
            2: 32000},
        # MPEG2
        2: {
            0: 22050,
            1: 24000,
            2: 16000},
        # MPEG2.5
        1: {
            0: 11025,
            1: 12000,
            2: 8000}
    }
    emphasis = {
        0: "none",
        1: "50/15 ms",
        3: "CCIT J.17"
    }
    channel_mode = {
        0: "Stereo",
        1: "Joint stereo",
        2: "Dual channel",
        3: "Single channel"
    }

    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "mp3", "MP3 file", stream, parent, "!")
        if stream.getN(3, False)=="ID3":
            self.read("id3", "ID3 header", (ID3_Parser,))

        bits = (
            (11, "sync", "Synchronize bits (set to 1)"),
            (2, "version", "MPEG audio version"), # MP3_File.version
            (2, "layer", "MPEG audio layer"), # MP3_File.layer[self.layer]
            (1, "protection", "Protected?"))
        self.header = self.doRead("header", "Header", (BitsChunk, BitsStruct(bits)))
        assert self.header["sync"] == 2047

        if False:
            bits = (
                (1, "xxx", "???"),
                (1, "padding", "Stream chunk use padding?"),
                (2, "sampling_rate", "Sampling rate"),
                (4, "bit_rate", "Bit rate"))
        else:
            bits = (
                (4, "bit_rate", "Bit rate"),
                (2, "sampling_rate", "Sampling rate"),
                (1, "padding", "Stream chunk use padding?"),
                (1, "xxx", "???"))
        self.rates = self.doRead("rates", "Rates and padding", (BitsChunk, BitsStruct(bits)))

        bits = (
            (2, "emphasis", "Emphasis"), # MP3_File.emphasis[emphasis]
            (1, "original", "Is original?"),
            (1, "copyright", "Is copyrighted?"),
            (2, "mode_ext", "Mode extension"),
            (2, "channel_mode", "Channel mode")) # MP3_File.channel_mode[channel_mode]
        self.various = self.doRead("various", "Channel mode, mode extension, copyright, original", (BitsChunk, BitsStruct(bits)))

        version = self.header["version"]
        layer = self.header["layer"]
        self.sampling_rate = MP3_File.sampling_rate[version][self.rates["sampling_rate"]]

        # Get bit rates
        if version == 3:
            rates = MP3_File.bit_rate[1] # MPEG1
        else:
            rates = MP3_File.bit_rate[2] # MPEG2 / MPEG2.5
        self.bit_rate = rates[layer][self.rates["bit_rate"]]

        frame_size = (144 * self.sampling_rate) / self.bit_rate + self.rates["padding"]
        print "Frame size=%s" % frame_size
        print "MPEG: %u bps, %s Hz" % (self.bit_rate, self.sampling_rate)

#       TODO: :-)
#        size = ??? 
#        self.read("content", "Content", (FormatChunk, "string[%u]" % size))
        
        size = stream.getSize() - stream.tell()
        self.read("end", "End", (FormatChunk, "string[%u]" % size))
        
registerPlugin(MP3_File, "audio/mpeg")
