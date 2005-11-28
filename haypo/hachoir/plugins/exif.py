"""
Exif filter.

Informations about Exif at:
- http://www.exif.org/
- http://libexif.sourceforge.net/

Author: Victor Stinner
"""

from filter import Filter

class ExifEntry(Filter):
    def __init__(self, stream, parent, endian):
        Filter.__init__(self, "exif_entry", "Exif entry", stream, parent)
        self.endian = endian
        self.read("tag", endian+"H", "Tag", post=self.processTag)
        self.read("whatsthis", "10s", "What's this?")

    def updateParent(self, parent):
        parent.description = "Exif entry (%s)" % self.getTag() 

    def getTag(self):
        know = {
            0x010e: "Image description",
            0x010f: "Camera constructor",
            0x0110: "Camera model",
            0x0131: "Software"
        }
        return know.get(self["tag"], "Unknown tag (0x%03X)" % self["tag"])

    def processTag(self, chunk):
        chunk.description = self.getTag()
        return "(0x%04X)" % chunk.value 

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

        # Part 0
        self.read("nb_entry", endian+"H", "Number of entries")
        self.read("offset", endian+"L", "Reserved")
        nb_entry = self["nb_entry"]
        for i in range(0,nb_entry):
            self.readChild("entry[]", ExifEntry, endian)

        # TODO: To be continued...
        self.read("end", "{@end@}s", "End")
