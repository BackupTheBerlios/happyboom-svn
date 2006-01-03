"""
Ncftp bookmarks filter.

Status: Alpha 
Author: Victor Stinner
"""

import re
from datetime import datetime
from filter import OnDemandFilter, DeflateFilter
from tools import convertDataToPrintableString
from plugin import registerPlugin
from chunk import FormatChunk, EnumChunk
from default import DefaultFilter
from plugin import guessPlugin 
from error import error
from tools import getBacktrace, humanFilesize

class FileEntry(OnDemandFilter):
    type_name = {
        0: "Normal disk file (old format)",
        # 48 is "0", 49 is "1", ...
        48: "Normal disk file",
        49: "Link to previously dumped file",
        50: "Symbolic link",
        51: "Character special file",
        52: "Block special file",
        53: "Directory",
        54: "FIFO special file",
        55: "Contiguous file"
    }

    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "file", "File entry", stream, parent)
        self.read("name", "Name", (FormatChunk, "string[100]"), {"post": self.printable})
        self.read("mode", "Mode", (FormatChunk, "string[8]"), {"post": self.convertOctal})
        self.read("uid", "User ID", (FormatChunk, "string[8]"), {"post": self.convertOctal})
        self.read("gid", "Group ID", (FormatChunk, "string[8]"), {"post": self.convertOctal})
        self.read("size", "Size", (FormatChunk, "string[12]"), {"post": self.convertOctal})
        self.read("mtime", "Modification time", (FormatChunk, "string[12]"), {"post": self.getTime})
        self.read("check_sum", "Check sum", (FormatChunk, "string[8]"), {"post": self.convertOctal})
        self.read("type", "Type", (EnumChunk, "uint8", FileEntry.type_name))
        self.read("lname", "Link name", (FormatChunk, "string[100]"), {"post": self.printable})
        self.read("magic", "Magic", (FormatChunk, "string[8]"), {"post": self.printable})
        self.read("uname", "User name", (FormatChunk, "string[32]"), {"post": self.printable})
        self.read("gname", "Group name", (FormatChunk, "string[32]"), {"post": self.printable})
        self.read("devmajor", "Dev major", (FormatChunk, "string[8]"), {"post": self.printable})
        self.read("devminor", "Dev minor", (FormatChunk, "string[8]"), {"post": self.printable})
        self.read("padding", "Padding (zero)", (FormatChunk, "string[167]"))

        self.name = self["name"].strip("\0")
        self.size = self.octal2int(self["size"])
        if self["type"] in (0, ord("0")) and self.size != 0:
            substream = stream.createSub(stream.tell(), self.size)
            plugin = guessPlugin(substream, self.name)
            self.read("content", "Compressed file content", (DeflateFilter, substream, self.size, plugin), {"stream": substream, "size": self.size})

        padding = 512 - stream.tell() % 512
        if padding != 512:
            self.read("padding_end", "Padding (512 align)", (FormatChunk, "string[%u]" % padding))

    def printable(self, chunk):
        value = chunk.value.strip(" \0")
        return convertDataToPrintableString(value)

    def getMode(self, chunk):
        mode = self.octal2int(chunk.value)
        owner = self._getModeItem(mode >> 6 & 7)
        group = self._getModeItem(mode >> 3 & 7)
        other = self._getModeItem(mode & 7)
        return "%04o (%s%s%s)" % (mode, owner, group, other)

    def _getModeItem(mode):
        if mode & 4 == 4: r="r"
        else: r="-"
        if mode & 2 == 2: w="w"
        else: w="-"
        if mode & 1 == 1: x="x"
        else: x="-"
        return "%c%c%c" % (r, w, x) 

    def convertOctal(self, chunk):
        return self.octal2int(chunk.value)

    def getTime(self, chunk):
        value = self.octal2int(chunk.value) 
        return str(datetime.fromtimestamp(value))

    def isEmpty(self):
        return self.name == ""

    def octal2int(self, str):
        str = str.strip(" \0")
        if str=="": return 0
        assert re.match("^[0-7]+$", str)
        try:
            return int(str,8)
        except:
            return 0

    def updateParent(self, chunk):
        if not self.isEmpty():
            text = "Tar File (%s: %s, %s)" \
                % (self.name, self.getChunk("type").display, humanFilesize(self.size))
        else:
            text = "Tar File (terminator, empty header)"
        chunk.description = text
        self.setDescription(text)

class TarFile(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "tar_file", "TAR archive file", stream, parent)
        while not stream.eof():
            file = self.doRead("file[]", "File", (FileEntry,))
            if file.isEmpty():
                break
        padding = stream.getSize() - stream.tell()
        self.read("padding", "Padding", (FormatChunk, "string[%u]" % padding))

registerPlugin(TarFile, ["application/x-gtar", "application/x-tar"])
