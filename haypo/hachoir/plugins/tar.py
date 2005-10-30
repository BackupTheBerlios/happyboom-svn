"""
Ncftp bookmarks filter.

Status: Alpha 
Author: Victor Stinner
"""

from datetime import datetime
from filter import Filter
from plugin import registerPlugin

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

class TarFile(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "tar_file","Tar file", stream, parent)
        self.read("name", "!100s", "Name", False)
        self.name = self.name.strip("\0")
        self.read("mode", "!8s", "Mode")
        self.mode = self.octal2int(self.mode)
        self.read("uid", "!8s", "User ID")
        self.uid = self.octal2int(self.uid)
        self.read("gid", "!8s", "Group ID")
        self.gid = self.octal2int(self.gid)
        self.read("size", "!12s", "Size")
        self.size = self.octal2int(self.size)
        self.read("mtime", "!12s", "Modification time")
        self.mtime = self.octal2int(self.mtime) 
        self.mtime = datetime.fromtimestamp(self.mtime)
        self.read("check_sum", "!8s", "Check sum")
        self.read("type", "!c", "Type")
        self.read("lname", "!100s", "Link name", False)
        self.read("magic", "!8s", "Magic")
        self.magic = self.magic.strip(" \0")
        self.read("uname", "!32s", "User name")
        self.uname = self.uname.strip("\0")
        self.read("gname", "!32s", "Group name")
        self.gname = self.gname.strip("\0")
        self.read("devmajor", "!8s", "Dev major")
        self.read("devminor", "!8s", "Dev minor")
        #self.read(None, "!167s", "Padding (zero)")
        self.read(None, "!167s", "Padding (zero)")
        if self.type in ("\0", "0"):
            self.read("filedata", "!{size}s", "File data")
        if stream.tell() % 512 != 0:
            padding = 512 - stream.tell() % 512
            self.read(None, "!%ss" % padding, "Padding (512 align)")

    def isEmpty(self):
        return self.name == ""

    def octal2int(self, str):
        str = str.strip("\0")
        try:
            return int(str.strip("\0"),8)
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

    def updateParent(self, parent, chunk):
        if not self.isEmpty():
            text = "Tar File (%s: %s)" % (self.name, self.getType())
        else:
            text = "Tar File (terminator, empty header)"
        chunk.description = self.description = text

class TarFilter(Filter):
    def __init__(self, stream):
        Filter.__init__(self, "tar_archive", "Tar archive", stream)

        self.readArray("files", TarFile, "Tar Files", self.checkEndOfChunks)
        
        padding = 4096 - stream.tell() % 4096
        self.read(None, "!%ss" % padding, "Padding (4096 align)")

        assert stream.eof()

    def checkEndOfChunks(self, stream, array, file):
        if file != None:
            if file.isEmpty(): return True
        return stream.eof()
        
registerPlugin("^.*\.tar$", "Tar archive", TarFilter, displayTar)
