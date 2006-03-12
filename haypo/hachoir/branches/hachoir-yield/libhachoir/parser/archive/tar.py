"""
Tar archive parser.

Author: Victor Stinner
"""

from field import FieldSet, Integer, Enum, RawBytes, String
from error import error
from tools import humanFilesize
import re, datetime

from bits import str2hex

class FileEntry(FieldSet):
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

    def createFields(self):
        yield String(self, "name", "string[100]", "Name", strip="\0")
        yield String(self, "mode", "string[8]", "Mode", text_handler=self.convertOctal)
        yield String(self, "uid", "string[8]", "User ID", text_handler=self.convertOctal)
        yield String(self, "gid", "string[8]", "Group ID", text_handler=self.convertOctal)
        yield String(self, "size", "string[12]", "Size", text_handler=self.convertOctal)
        yield String(self, "mtime", "string[12]", "Modification time", text_handler=self.getTime)
        yield String(self, "check_sum", "string[8]", "Check sum", text_handler=self.convertOctal)
        yield Enum(self, "type", "uint8", FileEntry.type_name, "Type")
        yield String(self, "lname", "string[100]", "Link name", strip=" \0")
        yield String(self, "magic", "string[8]", "Magic", strip=" \0")
        yield String(self, "uname", "string[32]", "User name", strip=" \0") 
        yield String(self, "gname", "string[32]", "Group name", strip=" \0") 
        yield String(self, "devmajor", "string[8]", "Dev major", strip=" \0")
        yield String(self, "devminor", "string[8]", "Dev minor", strip=" \0")
        yield RawBytes(self, "padding", 167, "Padding (zero)")

        self.filesize = self.octal2int(self["size"].value)
        if self["type"].value in (0, ord("0")) and self.filesize != 0:
            #substream = stream.createSub(stream.tell(), self.size)
            #plugin = guessPlugin(substream, self["name"].value)
            #self.read("content", "Compressed file content", (DeflateFilter, substream, self.size, plugin), {"stream": substream, "size": self.size})
            yield RawBytes(self, "content", self.filesize, "File content")

        padding = 512 - (self.newFieldAskAddress()/8) % 512
        if padding != 512:
            yield RawBytes(self, "padding_end", padding, "Padding (512 align)")

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
        return str(datetime.datetime.fromtimestamp(value))

    def isEmpty(self):
        return self["name"].value == ""

    def octal2int(self, text):
        text = text.strip(" \0")
        if text == "":
            return 0
        assert re.match("^[0-7]+$", text)
        try:
            return int(text, 8)
        except:
            return 0

    def _getDescription(self):
        if self._description == None:
            self._description = "Tar File "
            if not self.isEmpty():
                self._description += "(%s: %s, %s)" \
                    % (self.filename, self["type"].display, humanFilesize(self.filesize))
            else:
                self._description += "(terminator, empty header)"
        return self._description
    description = property(_getDescription, FieldSet._setDescription)
    
    def updateParent(self, chunk):
        chunk.description = text
        self.setDescription(text)

class TarFile(FieldSet):
    mime_types = ["application/x-gtar", "application/x-tar"]
    
    def createFields(self):
        while self._total_field_size < self.stream.size:
            file = FileEntry(self, "file[]", self.stream, "File")
            yield file
            if file.isEmpty():
                break
            print file["name"].value
        padding = self.stream.size - self._total_field_size
        if padding != 0:
            assert (padding % 8) == 0
            yield RawBytes(self, "padding", padding, "Padding")

