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
        7: (1, "B"),
        9: (1, "l"),
        10: (2, "l")
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
        0x8298: "Copyright holder"

    }

    def __init__(self, stream, parent, endian):
        Filter.__init__(self, "exif_entry", "Exif entry", stream, parent)
        self.endian = endian
        self.read("tag", endian+"H", "Tag", post=self.processTag)
        self.read("type", endian+"H", "Type", post=self.processType)
        self.read("count", endian+"L", "Count")

        # Create format
        assert self["type"] in ExifEntry.format
        format = ExifEntry.format[ self["type"] ]
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

        # Part #0
        self.read("nb_entry", endian+"H", "Number of entries")
        self.read("offset", endian+"L", "Reserved")
        nb_entry = self["nb_entry"]
        entries = []
        for i in range(0,nb_entry):
            chunk = self.readChild("entry[]", ExifEntry, endian)
            entries.append(chunk.getFilter())

        # TODO: What's this?
        self.read("whatisthat", "16s", "What's this?")

        # Read data of part #0
        for entry in entries:
            if 4 < entry.size:
                self.read("entry_value[]", entry.format, "Value of %s" % entry.getId())

        # TODO: To be continued...
        self.read("end", "{@end@}s", "End")
