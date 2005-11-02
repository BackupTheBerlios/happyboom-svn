"""
Ncftp bookmarks filter.

Status: Alpha 
Author: Victor Stinner
"""

import re
from datetime import datetime
from filter import Filter
from plugin import registerPlugin
from tools import convertDataToPrintableString

def displayModeItem(mode):
    if mode & 4 == 4: r="r"
    else: r="-"
    if mode & 2 == 2: w="w"
    else: w="-"
    if mode & 1 == 1: x="x"
    else: x="-"
    return "%c%c%c" % (r, w, x)

def displayMode(mode):
    owner = displayModeItem(mode >> 6 & 7)
    group = displayModeItem(mode >> 3 & 7)
    other = displayModeItem(mode & 7)
    print "Mode = %04o (%s%s%s)" % (mode, owner, group, other)
    
def displayFile(tar):
    print "name = \"%s\"" % (tar.name)
    displayMode(tar.mode)
    print "User = \"%s\" (id %s)" % (tar.uname, tar.uid)
    print "Group = \"%s\" (id %s)" % (tar.gname, tar.gid)
    print "Size = %s bytes" % (tar.size)
    print "Modification time = %s" % (tar.mtime)
    print "Magic = %s" % (tar.magic)
    print "Type = %s" % (tar.getType())
    
def displayTar(tar):
    for file in tar.files:
        file = file.getFilter()
        print "[ File %s ]" % file.name
        displayFile(file)

class TarFileEntry(Filter):
    def stripNul(self, chunk):
        return chunk.value.strip("\0")

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

    def stripNul(self, chunk):
        val = chunk.value.strip("\0")
        return convertDataToPrintableString(val)

    def getTime(self, chunk):
        value = self.octal2int(chunk.value) 
        return datetime.fromtimestamp(value)

    def __init__(self, stream, parent):
        Filter.__init__(self, "tar_file_entry","Tar file entry", stream, parent)
        self.read("name", "!100s", "Name", truncate=False, post=self.stripNul)
        self.name = self.name.strip("\0")
        self.read("mode", "!8s", "Mode", post=self.convertOctal)
        self.read("uid", "!8s", "User ID", post=self.convertOctal)
        self.read("gid", "!8s", "Group ID", post=self.convertOctal)
        self.read("size", "!12s", "Size", post=self.convertOctal)
        self.size = self.octal2int(self.size)
        self.read("mtime", "!12s", "Modification time", self.getTime)
        self.read("check_sum", "!8s", "Check sum")
        self.read("type", "!c", "Type")
        self.read("lname", "!100s", "Link name", post=self.stripNul, truncate=False)
        self.read("magic", "!8s", "Magic", post=self.stripNul)
        self.read("uname", "!32s", "User name", post=self.stripNul)
        self.read("gname", "!32s", "Group name", post=self.stripNul)
        self.read("devmajor", "!8s", "Dev major")
        self.read("devminor", "!8s", "Dev minor")
        self.read("header_padding", "!167s", "Padding (zero)")
        if self.type in ("\0", "0"):
            self.read("filedata", "!{size}s", "File data", truncate=True)
        if stream.tell() % 512 != 0:
            padding = 512 - stream.tell() % 512
            self.read("padding", "!%ss" % padding, "Padding (512 align)", truncate=True)

    def isEmpty(self):
        return self.name == ""

    def octal2int(self, str):
        str = str.strip("\0")
        if str=="": return 0
        assert re.match("^[0-7]+$", str)
        try:
            return int(str,8)
        except:
            return 0

    def getType(self):
        name = { \
            "\0": "Normal disk file (old format), Unix compatible",
            "0": "Normal disk file",
            "1": "Link to previously dumped file",
            "2": "Symbolic link",
            "3": "Character special file",
            "4": "Block special file",
            "5": "Directory",
            "6": "FIFO special file",
            "7": "Contiguous file"
        }
        if self.type not in name: return "Unknow type (%02X)" % ord(self.type)
        return name[self.type]

    def updateParent(self, chunk):
        if not self.isEmpty():
            text = "Tar File (%s: %s)" % (self.name, self.getType())
        else:
            text = "Tar File (terminator, empty header)"
        chunk.description = self.description = text

class TarFile(Filter):
    def __init__(self, stream):
        Filter.__init__(self, "tar_file", "TAR archive file", stream, None)

        self.readArray("files", TarFileEntry, "Tar Files", self.checkEndOfChunks)
        
#        padding = 4096 - stream.tell() % 4096
#        self.read("padding", "!%ss" % padding, "Padding (4096 align)")
#        assert stream.eof()

    def checkEndOfChunks(self, stream, array, file):
        if file != None:
            if file.isEmpty(): return True
        return stream.eof()
        
registerPlugin("^.*\.tar$", "Tar archive", TarFile, None)
