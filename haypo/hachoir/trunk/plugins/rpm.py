"""
RPM archive parser.

Author: Victor Stinner, 1st December 2005.
"""

from filter import OnDemandFilter
from plugin import registerPlugin
from chunk import FormatChunk, EnumChunk, StringChunk
from format import getFormatSize
from gzip import GzipFile

class Item(OnDemandFilter):
    format = {
        #  (use FormatChunk? else use StringChunk, chunk format, count)
        0: (True, "uint8", 1),
        1: (True, "char", 1),
        2: (True, "uint8", 1),
        3: (True, "uint16", 1),
        4: (True, "uint32", 1),
        5: (True, "uint32", 2),
        6: (False, "C", 1),
        7: (True, "string", 1),
        8: (True, "strin", 1),
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
    
    def __init__(self, stream, parent, tag_name_dict=None):
        OnDemandFilter.__init__(self, "rpm_item", "RPM item", stream, parent, "!")
        if tag_name_dict == None:
            self.tag_name_dict = Item.tag_name
        else:
            self.tag_name_dict = tag_name_dict 
        self.read("tag", "Tag", (EnumChunk, "uint32", self.tag_name_dict))
        self.read("type", "Type", (EnumChunk, "uint32", Item.type_name))
        self.read("offset", "Offset", (FormatChunk, "uint32"))
        self.read("count", "Count", (FormatChunk, "uint32"))

    def updateParent(self, chunk):
        type = self.getChunk("type").getDisplayData()
        tag = self.getChunk("tag").getDisplayData()
        chunk.description = "Item: %s (%s)" % (tag, type)
        
    def doRead(self, filter):
        type = self["type"]
        if type != 8:
            desc = "Value of %s: %s" % (self.getId(), self.getDescription())
            format = Item.format[type]
            if format[0]:
                if 2 < self["count"] and format[1] != "string":
                    format = "string[%u]" % (format[2] * self["count"] * getFormatSize(format[1]))
                else:
                    format = "%s[%u]" % (format[1], format[2] * self["count"])
                filter.read("data[]", desc, (FormatChunk, format))
            else:     
                format = format[1]
                filter.read("data[]", desc, (StringChunk, format))
        else:
            id = filter.getUniqChunkId("data[]")
            for i in range(0, self["count"]):
                desc = "Value %u of %s: %s" % (i, self.getId(), self.getDescription())
                filter.read(id+"[]", desc, (StringChunk, "C"))

class ItemHeader(Item):
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

    def __init__(self, stream, parent):
        Item.__init__(self, stream, parent, ItemHeader.tag_name)
            
def sortRpmItem(a,b):
    return int( a["offset"] - b["offset"] )

class Header(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "header", "Header", stream, parent, "!")
        self.read("id", "Identifier", (FormatChunk, "string[4]"))
        assert self["id"] == "\x8E\xAD\xE8\x01"
        self.read("padding", "Padding", (FormatChunk, "string[4]"))
        self.read("count", "Count", (FormatChunk, "uint32"))
        self.read("size", "Store size", (FormatChunk, "uint32"))
        items = []
        for i in range(0, self["count"]):
            item = self.doRead("item[]", "Item", (ItemHeader,))
            items.append(item)
        items.sort( sortRpmItem )

        start = stream.tell()
        end = stream.tell() + self["size"]
        for item in items:
            offset = item["offset"]
            diff = offset - (stream.tell() - start)
            if 0 < diff:
                self.read("padding[]", "Padding", (FormatChunk, "string[%u]" % diff))

            print "Read %s" % item.getId()                
            item.doRead(self)
        size = end - stream.tell()
        if 0 < size:    
            self.read("padding[]", "Padding", (FormatChunk, "string[%u]" % size))

class Signature(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "rpm_sig", "Signature", stream, parent, "!")
        self.read("id", "Identifier", (FormatChunk, "uint8[3]"))
        assert self["id"] == (142, 173, 232)
        self.read("version", "Signature version", (FormatChunk, "uint8"))
        self.read("reserved", "Reserved", (FormatChunk, "string[4]"))
        self.read("count", "Count", (FormatChunk, "uint32"))
        self.read("size", "Size", (FormatChunk, "uint32"))
        items = []
        for i in range(0, self["count"]):
            item = self.doRead("item[]", "Item", (Item,))
            items.append(item)
        items.sort( sortRpmItem )

        start = stream.tell()
        end = stream.tell() + self["size"]
        for item in items:
            offset = item["offset"]
            diff = offset - (stream.tell() - start)
            if 0 < diff:
                self.read("padding[]", "Padding", (FormatChunk, "string[%u]" % diff))
            item.doRead(self)
        size = end - stream.tell()
        if 0 < size:    
            self.read("padding[]", "Padding", (FormatChunk, "string[%u]" % size))

class RpmFile(OnDemandFilter):
    rpm_type_name = {
        0: "Binary",
        1: "Source"
    }
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "rpm_file", "RPM File", stream, parent, "!")
        self.read("id", "Identifier", (FormatChunk, "uint8[4]"))
        assert self["id"] == (237, 171, 238, 219)
        self.read("major_ver", "Major version", (FormatChunk, "uint8"))
        self.read("minor_ver", "Minor version", (FormatChunk, "uint8"))
        self.read("type", "RPM type", (EnumChunk, "uint16", RpmFile.rpm_type_name))
        self.read("architecture", "Architecture", (FormatChunk, "uint16"))
        self.read("name", "Archive name", (FormatChunk, "string[66]"))
        self.read("osnum", "OS", (FormatChunk, "uint16"))
        self.read("signature_type", "Type of signature", (FormatChunk, "uint16"))
        self.read("reserved", "Reserved", (FormatChunk, "string[16]"))
        self.read("signature", "Signature", (Signature,))
        self.read("header", "Header", (Header,))
        sub = stream.createSub()
        self.read("gz_content", "Gziped content", (GzipFile,), {"stream": sub})

registerPlugin(RpmFile, "application/x-rpm")
