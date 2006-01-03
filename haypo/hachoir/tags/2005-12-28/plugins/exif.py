"""
Exif filter.

Informations about Exif at:
- http://www.exif.org/
- http://libexif.sourceforge.net/

Author: Victor Stinner
"""

from filter import OnDemandFilter
from format import getFormatSize
from chunk import FormatChunk, EnumChunk
import struct

class ExifEntry(OnDemandFilter):
    format = {
        1: (1, "uint8"),
        2: (1, "string"),
        3: (1, "uint16"),
        4: (1, "uint32"),
        5: (2, "uint32"),
        7: (1, "string"),
        9: (1, "int32"),
        10: (2, "int32")
    }

    type_name = {    
        1: "BYTE (8 bits)",
        2: "ASCII (8 bits)",
        3: "SHORT (16 bits)",
        4: "LONG (32 bits)",
        5: "RATIONAL (two LONGs)",
        7: "UNDEFINED (8 bits)",
        9: "SLONG (32 bits)",
        10: "SRATIONTAL (two SLONGs)"
    }

    OFFSET_JPEG_SOI = 0x0201
    EXIF_IFD_POINTER = 0x8769

    tag_name = {    
        0x0100: "Image width",
        0x0101: "Image height",
        0x0102: "Number of bits per component",
        0x0103: "Compression scheme",
        0x0106: "Pixel composition",
        0x0112: "Orientation of image",
        0x0115: "Number of components",
        0x011C: "Image data arrangement",
        0x0212: "Subsampling ratio Y to C",
        0x0213: "Y and C positioning",
        0x011A: "Image resolution width direction",
        0x011B: "Image resolution in height direction",
        0x0128: "Unit of X and Y resolution",
        
        0x0111: "Image data location",
        0x0116: "Number of rows per strip",
        0x0117: "Bytes per compressed strip",
        0x0201: "Offset to JPEG SOI",
        0x0202: "Bytes of JPEG data",
        
        0x012D: "Transfer function",
        0x013E: "White point chromaticity",
        0x013F: "Chromaticities of primaries",
        0x0211: "Color space transformation matrix coefficients",
        0x0214: "Pair of blank and white reference values",
        
        0x0132: "File change date and time",
        0x010e: "Image title",
        0x010f: "Camera (Image input equipment) manufacturer",
        0x0110: "Camera (Input input equipment) model",
        0x0131: "Software",
        0x013B: "File change date and time",
        0x8298: "Copyright holder",
        0x8769: "Exif IFD Pointer",

        0x829A: "Exposure time",
        0x829D: "F number",
        0x8822: "Exposure program",
        0x8824: "Spectral sensitivity",
        0x8827: "ISO speed rating",
        0x8828: "Optoelectric conversion factor OECF",
        0x9201: "Shutter speed",
        0x9202: "Aperture",
        0x9203: "Brightness",
        0x9204: "Exposure bias",
        0x9205: "Maximum lens aperture",
        0x9206: "Subject distance",
        0x9207: "Metering mode",
        0x9208: "Light source",
        0x9209: "Flash",
        0x920A: "Lens focal length",
        0x9214: "Subject area",
        0xA20B: "Flash energy",
        0xA20C: "Spatial frequency response",
        0xA20E: "Focal plane X resolution",
        0xA20F: "Focal plane Y resolution",
        0xA210: "Focal plane resolution unit",
        0xA214: "Subject location",
        0xA215: "Exposure index",
        0xA217: "Sensing method",
        0xA300: "File source",
        0xA301: "Scene type",
        0xA302: "CFA pattern",
        0xA401: "Custom image processing",
        0xA402: "Exposure mode",
        0xA403: "White balance",
        0xA404: "Digital zoom ratio",
        0xA405: "Focal length in 35 mm film",
        0xA406: "Scene capture type",
        0xA407: "Gain control",
        0xA408: "Contrast",

        0x9000: "Exif version",
        0xA000: "Supported Flashpix version",
        0xA001: "Color space information",
        0x9101: "Meaning of each component",
        0x9102: "Image compression mode",
        0xA002: "Valid image width",
        0xA003: "Valid image height",
        0x927C: "Manufacturer notes",
        0x9286: "User comments",
        0xA004: "Related audio file",
        0x9003: "Date and time of original data generation",
        0x9004: "Date and time of digital data generation",
        0x9290: "DateTime subseconds",
        0x9291: "DateTimeOriginal subseconds",
        0x9292: "DateTimeDigitized subseconds",
        0xA420: "Unique image ID",
        0xA005: "Interoperability IFD Pointer"
    }

    def __init__(self, stream, parent, endian):
        OnDemandFilter.__init__(self, "exif_entry", "Exif entry", stream, parent, endian)
        self.read("tag", "Tag", (EnumChunk, "uint16", ExifEntry.tag_name))
        self.read("type", "Type", (EnumChunk, "uint16", ExifEntry.type_name))
        self.read("count", "Count", (FormatChunk, "uint32"))

        # Create format
        format = ExifEntry.format.get(self["type"], (1, "uint8"))
        self.format = "%s[%u]" % (format[1], format[0]*self["count"])

        # Get size
        self.size = getFormatSize(self.format)

        # Get offset/value
        if 4 < self.size:
            self.read("offset", "Value offset", (FormatChunk, "uint32"))
        else:
            self.read("value", "Value", (FormatChunk, self.format))
            if self.size < 4:
                self.read("padding", "Padding", (FormatChunk, "string[%u]" % (4-self.size)))

    def updateParent(self, parent):
        parent.description = "Exif entry: %s" % self.getChunk("tag").getDisplayData()

def sortExifEntry(a,b):
    return int( a["offset"] - b["offset"] )

class ExifIFD(OnDemandFilter):
    def __init__(self, stream, parent, endian, offset_diff):
        OnDemandFilter.__init__(self, "exif", "Exif IFD", stream, parent, endian)
        self.read("id", "IFD identifier", (FormatChunk, "uint16"))
        entries = []
        next_chunk_offset = None
        while True:
            # TODO: "!uint32" or self._endian+"uint32" ?
            next = stream.getFormat("!uint32", False)
            if next in (0, 0xF0000000):
                break
            entry = self.doRead("entry[]", "Entry", (ExifEntry, self._endian))
            if entry["tag"] in (ExifEntry.EXIF_IFD_POINTER, ExifEntry.OFFSET_JPEG_SOI):
                next_chunk_offset = entry["value"]+offset_diff
                if entry["tag"] == ExifEntry.OFFSET_JPEG_SOI:
                   parent.jpeg_soi = next_chunk_offset
                break
            if 4 < entry.size:
                entries.append(entry)
        self.read("next", "Next IFD offset", (FormatChunk, "uint32"))
        entries.sort( sortExifEntry )
        for entry in entries:
            offset = entry["offset"]+offset_diff
            padding = offset - stream.tell()
            if 0 < padding:
                self.read("padding[]", "Padding (?)", (FormatChunk, "string[%u]" % padding))
            assert offset == stream.tell()
            id = self.read("entry_value[]", "Value of %s" % entry.getId(), (FormatChunk, entry.format))
        if next_chunk_offset != None:
            padding = next_chunk_offset - stream.tell()
            if 0 < padding:
                self.read("padding[]", "Padding", (FormatChunk, "string[%u]" % padding))
        # TODO: When padding is needed !?                
#        size = self.getSize()
#        if (size % 4) != 0:
#            if parent.jpeg_soi != None and parent.jpeg_soi <= stream.tell():
#                return
#            padding = 4 - (size % 4)
#            self.read("padding[]", "Padding to be aligned to 4", (FormatChunk, "string[%u]" % padding))

    def updateParent(self, chunk):
        chunk.description = "Exif IFD (id %s)" % self["id"]

class ExifFilter(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "exif", "Exif", stream, parent, None)

        # Headers
        self.jpeg_soi = None
        self.read("header", "Header (Exif\\0\\0)", (FormatChunk, "string[6]"))
        assert self["header"] == "Exif\0\0"
        self.read("byte_order", "Byte order", (FormatChunk, "string[2]"))
        assert self["byte_order"] in ("II", "MM")
        if self["byte_order"] == "II":
           self._endian = "<"
        else:
           self._endian = ">"
        self.read("header2", "Header2 (42)", (FormatChunk, "uint16"))
        self.read("nb_entry", "Number of entries", (FormatChunk, "uint16"))
        self.read("whatsthis?", "What's this ??", (FormatChunk, "uint16"))
        while not stream.eof():
            tag = stream.getFormat("!uint16", False)
            if tag == 0xFFD8:
                size = stream.getSize() - stream.tell()
                sub = stream.createSub(size=size)
                from jpeg import JpegFile
                self.read("thumbnail", "JPEG thumbnail", (JpegFile,), {"stream": sub})
                break
            elif tag == 0xFFFF:
                break
            self.read("ifd[]", "IFD", (ExifIFD, self._endian, 6))
        self.addPadding()            
        assert self.getSize() == stream.getSize()
