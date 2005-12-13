"""
AVI splitter.

Creation: 12 decembre 2005
Status: alpha
Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin
from id3 import ID3_Parser

class MP3_File(Filter):
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
        Filter.__init__(self, "mp3", "MP3 file", stream, parent)
        if stream.getN(3, False)=="ID3":
            self.readChild("id3", ID3_Parser)
        self.read("header", "!H", "Header", post=self.postHeader)
        self.read("rate", "B", "Rates and padding", post=self.postRate)
        self.read("various", "B", "Channel mode, mode extension, copyright, original", post=self.postVarious)

        print (self.sampling_rate, self.bit_rate, self.padding)
        frame_size = (144 * self.sampling_rate) / self.bit_rate + self.padding
        print "Frame size=%s" % frame_size
        
    def postVarious(self, chunk):
        # Get channel mode
        channel_mode = chunk.value >> 6 & 3
        text = MP3_File.channel_mode[channel_mode]

#        mode_extension = chunk.value >> 4 & 3

        # Get copyright bit
        copyright = chunk.value >> 3 & 1
        if copyright == 1:
            text = text + ", copyrighted"

        # Get original bit
        original = chunk.value >> 2 & 1
        if original == 1:
            text = text + ", is original"
        else:
            text = text + ", copied"

        # Get emphasis
        emphasis = chunk.value & 3
        assert emphasis in MP3_File.emphasis
        emphasis = MP3_File.emphasis[emphasis]
        if emphasis != "none":
            text = text + ", emphasis=%s" % emphasis
        return text 

    def postHeader(self, chunk):
        header = chunk.value
        sync = header >> 5
        assert sync == 2047
        self.version = header >> 3 & 3
        assert self.version in MP3_File.version
        self.layer = header >> 1 & 3
        protection = header & 1
        text = "MPEG%s, layer %s" % (\
            MP3_File.version[self.version],
            MP3_File.layer[self.layer])
        if protection==1:
            text = "%s, protected" % text
        return text

    def postRate(self, chunk):
        # Get bit rates
        bit_rate = chunk.value >> 4
        if self.version == 3: # MPEG1
            rates = MP3_File.bit_rate[1] # MPEG1
        else:
            rates = MP3_File.bit_rate[2] # MPEG2 / MPEG2.5
        assert self.layer in rates
        rates = rates[self.layer]
        assert bit_rate in rates
        self.bit_rate = rates[bit_rate]
        
        # Get sampling rate
        sampling_rate = chunk.value >> 2 & 3
        rates = MP3_File.sampling_rate[self.version]
        assert sampling_rate in rates
        self.sampling_rate = rates[sampling_rate]
        text = "%u bps, %s Hz" % (self.bit_rate, self.sampling_rate)
        
        # Get Padding
        self.padding = chunk.value >> 1 & 1
        if self.padding==1:
            text = text + ", padded"
        return text

registerPlugin(MP3_File, "audio/mpeg")
