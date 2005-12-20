"""
RPM archive parser.

Author: Victor Stinner, 1st December 2005.
"""

from filter import Filter
from plugin import registerPlugin
from format import getFormatSize
from gzip import GzipFile

class RpmItem(Filter):
    format = {
        #  (use FormatChunk? else use StringChunk, chunk format, count)
        0: (True, "B", 1),
        1: (True, "c", 1),
        2: (True, "B", 1),
        3: (True, "H", 1),
        4: (True, "L", 1),
        5: (True, "L", 2),
        6: (False, "C", 1),
        7: (True, "s", 1),
        8: (True, "s", 1),
        9: (False, "C", 1)
    }
    type_name = {
        0: "NULL",
        1: "CHAR",
        2: "INT8",
        3: "INT16",
        4: "INT32",
        5: "INT64",
        6: "STRING",
        7: "BIN",
        8: "STRING_ARRAY",
        9: "STRING?"
    }
    tag_name = {
        1000: "File size",
        1001: "(Broken) MD5 signature",
        1002: "PGP 2.6.3 signature",
        1003: "(Broken) MD5 signature",
        1004: "MD5 signature",
        1005: "GnuPG signature",
        1006: "PGP5 signature",
        1007: "Uncompressed payload size (bytes)",
        256+8: "Broken SHA1 header digest",
        256+9: "Broken SHA1 header digest",
        256+13: "Broken SHA1 header digest",
        256+11: "DSA header signature",
        256+12: "RSA header signature"
    }
    
    def __init__(self, stream, parent):
        Filter.__init__(self, "rpm_item", "RPM item", stream, parent)
        self.read("tag", "!L", "Tag")
        self.read("type", "!L", "Type", post=self.postType)
        self.read("offset", "!L", "Offset")
        self.read("count", "!L", "Count")

    def postType(self, chunk):
        return self.getType(chunk.value)

    def updateParent(self, chunk):
        type = self.getType(self["type"])
        tag = self.getTagName()
        chunk.description = "RPM item: %s (%s)" % (tag, type)
        
    def getTagName(self):
        tag = self["tag"]
        return RpmItem.tag_name.get(tag, "Unknow tag (%s)" % tag)

    def doRead(self, filter):
        type = self["type"]
        desc = "Value of item %s, %s" % (self.getId(), self.getDescription())
        if type != 8:
            format = RpmItem.format[type]
            if format[0]:
                if 2 < self["count"] and format[1] != "s":
                    format = "!" + str(format[2] * self["count"] * getFormatSize(format[1])) + "s"
                else:
                    format = "!" + str(format[2] * self["count"]) + format[1]
                filter.read("data[]", format, desc)
            else:     
                format = format[1]
                filter.readString("data[]", format, desc)
        else:
            id = filter.getUniqChunkId("data[]")
            for i in range(0, self["count"]):
                filter.readString(id+"[]", "C", desc)
    
    def getType(self, type):
        return RpmItem.type_name.get(type, "Unknow type (%s)" % type)

class RpmHeaderItem(RpmItem):
    tag_name = {
        61: "Current image",
        62: "Signatures",
        63: "Immutable",
        64: "Regions",
        100: "I18N string locales",
        1000: "Name",
        1001: "Version",
        1002: "Release",
        1003: "Epoch",
        1004: "Summary",
        1005: "Description",
        1006: "Build time",
        1007: "Build host",
        1008: "Install time",
        1009: "Size",
        1010: "Distribution",
        1011: "Vendor",
        1012: "Gif",
        1013: "Xpm",
        1014: "Licence",
        1015: "Packager",
        1016: "Group",
        1017: "Changelog",
        1018: "Source",
        1019: "Patch",
        1020: "Url",
        1021: "OS",
        1022: "Arch",
        1023: "Prein",
        1024: "Postin",
        1025: "Preun",
        1026: "Postun",
        1027: "Old filenames",
        1028: "File sizes",
        1029: "File states",
        1030: "File modes",
        1031: "File uids",
        1032: "File gids",
        1033: "File rdevs",
        1034: "File mtimes",
        1035: "File MD5s",
        1036: "File link to's",
        1037: "File flags",
        1038: "Root",
        1039: "File username",
        1040: "File groupname",
        1043: "Icon",
        1044: "Source rpm",
        1045: "File verify flags",
        1046: "Archive size",
        1047: "Provide name",
        1048: "Require flags",
        1049: "Require name",
        1050: "Require version",
        1051: "No source",
        1052: "No patch",
        1053: "Conflict flags",
        1054: "Conflict name",
        1055: "Conflict version",
        1056: "Default prefix",
        1057: "Build root",
        1058: "Install prefix",
        1059: "Exclude arch",
        1060: "Exclude OS",
        1061: "Exclusive arch",
        1062: "Exclusive OS",
        1064: "RPM version",
        1065: "Trigger scripts",
        1066: "Trigger name",
        1067: "Trigger version",
        1068: "Trigger flags",
        1069: "Trigger index",
        1079: "Verify script",
        #TODO: Finish the list (id 1070..1162 using rpm library source code)
    }
        
    def getTagName(self):
        tag = self["tag"]
        return RpmHeaderItem.tag_name.get(tag, "Unknow tag (%s)" % tag)
            
def sortRpmItem(a,b):
    return int( a["offset"] - b["offset"] )

class Header(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "header", "Header", stream, parent)
        id = self.read("id", "4s", "Identifier").value
        assert id == "\x8E\xAD\xE8\x01"
        self.read("padding", "4s", "Padding")
        self.read("count", "!L", "Count")
        self.read("size", "!L", "Store size")
        items = []
        for i in range(0, self["count"]):
            item = self.readChild("item[]", RpmHeaderItem).getFilter()
            items.append(item)
        items.sort( sortRpmItem )

        start = stream.tell()
        end = stream.tell() + self["size"]
        for item in items:
            offset = item["offset"]
            diff = offset - (stream.tell() - start)
            if 0 < diff:
                self.read("padding[]", "%us" % diff, "Padding")

            print "Read %s" % item.getId()                
            item.doRead(self)
        size = end - stream.tell()
        if 0 < size:    
            self.read("padding[]", "%us" % size, "Padding")

class RpmSignature(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "rpm_sig", "RPM signature", stream, parent)
        self.read("id", "!3B", "Identifier")
        assert self["id"] == (142, 173, 232)
        self.read("version", "!B", "Signature version")
        self.read("reserved", "4s", "Reserved")
        self.read("count", "!L", "Count")
        self.read("size", "!L", "Size")
        items = []
        for i in range(0, self["count"]):
            item = self.readChild("item[]", RpmItem).getFilter()
            items.append(item)
        items.sort( sortRpmItem )

        start = stream.tell()
        end = stream.tell() + self["size"]
        for item in items:
            offset = item["offset"]
            diff = offset - (stream.tell() - start)
            if 0 < diff:
                self.read("padding[]", "%us" % diff, "Padding")
            item.doRead(self)
        size = end - stream.tell()
        if 0 < size:    
            self.read("padding[]", "%us" % size, "Padding")

class RpmFile(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "rpm_file", "RPM File", stream, parent)
        self.read("id", "!4B", "Identifier")
        assert self["id"] == (237, 171, 238, 219)
        self.read("major_ver", "!B", "Major version")
        self.read("minor_ver", "!B", "Minor version")
        self.read("type", "!H", "RPM type", post=self.postType)
        self.read("architecture", "!H", "Architecture")
        self.read("name", "!66s", "Archive name")
        self.read("osnum", "!H", "OS")
        self.read("signature_type", "!H", "Type of signature")
        self.read("reserved", "16s", "Reserved")
        self.readChild("signature", RpmSignature)
        self.readChild("header", Header)
        sub = stream.createSub()
        self.readStreamChild("gz_content", sub, GzipFile)

    def postType(self, chunk):
        if chunk.value == 0:
            return "Binary"
        elif chunk.value == 1:
            return "Source"
        else:
            return "Unknown (%s)" % chunk.value

registerPlugin(RpmFile, "application/x-rpm")
