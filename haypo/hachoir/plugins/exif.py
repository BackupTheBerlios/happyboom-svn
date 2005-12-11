"""
Exif filter.

Informations about Exif at:
- http://www.exif.org/
- http://libexif.sourceforge.net/

Author: Victor Stinner
"""

from filter import Filter
import struct

class ExifEntry(Filter):
    format = {
        1: (1, "B"),
        2: (1, "s"),
        3: (1, "H"),
        4: (1, "L"),
        5: (2, "L"),
        7: (1, "s"),
#        9: (1, "l"),
#        10: (2, "l")
        9: (1, "L"),
        10: (2, "L")
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
        Filter.__init__(self, "exif_entry", "Exif entry", stream, parent)
        self.endian = endian
        self.read("tag", endian+"H", "Tag", post=self.processTag)
        self.read("type", endian+"H", "Type", post=self.processType)
        self.read("count", endian+"L", "Count")

        # Create format
        format = ExifEntry.format.get(self["type"], (1, "B"))
        self.format = "%s%u%s" % (self.endian, format[0]*self["count"], format[1])

        # Get size
        self.size = struct.calcsize(self.format)

        # Get offset/value
        if 4 < self.size:
            self.read("offset", endian+"L", "Value offset")
        else:
            self.read("value", self.format, "Value")
            if self.size < 4:
                self.read("padding", "%us" % (4-self.size), "Padding")

    def updateParent(self, parent):
        parent.description = "Exif entry (%s)" % self.getTag() 

    def getTag(self):
        return ExifEntry.tag_name.get(self["tag"], "Unknown tag (0x%03X)" % self["tag"])

    def processType(self, chunk):
        return ExifEntry.type_name.get(chunk.value, "%u" % chunk.value) 

    def processTag(self, chunk):
        chunk.description = self.getTag()
        return "0x%04X" % chunk.value 

def sortExifEntry(a,b):
    return int( a["offset"] - b["offset"] )

class ExifIFD(Filter):
    def __init__(self, stream, parent, endian, offset_diff):
        Filter.__init__(self, "exif", "Exif IFD", stream, parent)
        self.endian = endian
        self.read("id", endian+"H", "IFD identifier")
        entries = []
        while True:
            next = stream.getFormat("!L", False)[0]
            if next in (0, 0xF0000000):
                break
            chunk = self.readChild("entry[]", ExifEntry, endian)
            entry = chunk.getFilter()
            if entry["tag"] == 0x8769:
                break
            if 4 < entry.size:
                entries.append(entry)
        self.read("next", endian+"L", "Next IFD offset")
#        self.read("x", "12s", "")
        entries.sort( sortExifEntry )
        for entry in entries:
            offset = entry["offset"]+offset_diff
            padding = offset - stream.tell()
            if 0 < padding:
                self.read("padding[]", "%us" % padding, "Padding (?)")
            assert offset == stream.tell()
            self.read("entry_value[]", entry.format, "Value of %s" % entry.getId())

    def updateParent(self, chunk):
        desc = "Exif IFD (id %s)" % self["id"]
        chunk.description = desc
        self.setDescription(desc)

class ExifFilter(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "exif", "Exif", stream, parent)

        # Headers
        self.read("header", "6s", "Header (Exif\\0\\0)")
        assert self["header"] == "Exif\0\0"
        self.read("byte_order", "2s", "Byte order")
        assert self["byte_order"] in ("II", "MM")
        if self["byte_order"] == "II":
           endian = "<"
        else:
           endian = ">"
        self.read("header2", endian+"H", "Header2 (42)")

        if False:
            # Part #0
            self.read("nb_entry", endian+"H", "Number of entries")
            self.read("offset", endian+"L", "Offset")
            nb_entry = self["nb_entry"]+1
            entries = []
            for i in range(0,nb_entry):
                chunk = self.readChild("entry[]", ExifEntry, endian)
                entry = chunk.getFilter()
                if entry["tag"] != 0x8769:
                    entries.append(entry)

            # TODO: What's this?
            self.read("next", endian+"L", "Next IFD offset")

            # Read data of part #0
            for entry in entries:
                if 4 < entry.size:
                    self.read("entry_value[]", entry.format, "Value of %s" % entry.getId())

            # Read IFD
            self.readChild("ifd", ExifIFD, endian)
        else:
            self.read("nb_entry", endian+"H", "Number of entries")
            self.read("whatsthis?", endian+"H", "What's this ??")
            while True:
                tag = stream.getN(2, False)
                if tag == "\xFF\xD8":
                    size = stream.getSize() - stream.tell()
                    sub = stream.createLimited(size=size)
                    from jpeg import JpegFile
                    self.readStreamChild("thumbnail", sub, JpegFile)
                    break
                if tag == "\xFF\xFF":
                    break
                self.readChild("ifd[]", ExifIFD, endian, 6)
        size = stream.getSize() - stream.tell()
        if size != 0:                
            self.read("end", "%us" % size, "End")
        assert self.getSize() == stream.getSize()
