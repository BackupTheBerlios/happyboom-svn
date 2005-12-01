"""
RPM archive parser.

Author: Victor Stinner, 1st December 2005.
"""

from filter import Filter
from plugin import registerPlugin

class RpmItem(Filter):
    type_name = {
        0: "NULL",
        1: "CHAR",
        2: "INT8",
        3: "INT16",
        4: "INT32",
        5: "INT64",
        6: "STRING",
        7: "BIN",
        8: "STRING_ARRAY"
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
        chunk.description = "RPM item (%s)" % type

    def getType(self, type):
        return RpmItem.type_name.get(type, "Unknow type (%s)" % type)

class RpmSignature(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "rpm_sig", "RPM signature", stream, parent)
        self.read("id", "!3B", "Identifier")
        assert self["id"] == (142, 173, 232)
        self.read("version", "!B", "Signature version")
        self.read("reserved", "4s", "Reserved")
        self.read("count", "!L", "Count")
        self.read("size", "!L", "Size")
        for i in range(0, self["count"]):
            self.readChild("item[]", RpmItem)

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
        self.readChild("sig", RpmSignature)

    def postType(self, chunk):
        if chunk.value == 0:
            return "Binary"
        elif chunk.value == 1:
            return "Source"
        else:
            return "Unknown (%s)" % chunk.value

registerPlugin(RpmFile, "application/x-rpm")
