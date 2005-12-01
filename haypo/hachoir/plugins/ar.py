"""
GNU ar archive : archive file (.a) and Debian (.deb) archive.
"""

from filter import Filter, DeflateFilter
from plugin import registerPlugin, guessPlugin
from error import error
   
class ArchiveFileEntry(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "file_entry", "File entry", stream, parent)
        self.readString("header", "UnixLine", "Header")
        info = self["header"].split()
        assert len(info) == 7
        self.filename = info[0]
        self.size = int(info[5])
        dataio = stream.createSub(stream.tell(), self.size)
        plugin = guessPlugin(dataio, self.filename)
        self.readChild("data", DeflateFilter, dataio, self.size, plugin)

    def updateParent(self, chunk):
        desc = "File entry (%s)" % self.filename
        chunk.description = desc
        self.setDescription(desc)
        
class ArchiveFile(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "ar_file", "GNU ar file", stream, parent)
        self.readString("id", "UnixLine", "ar archive identifier")
        while not stream.eof():
            while True:
                data = stream.read(1, False)
                if data == "\n":
                    self.readString("empty_line[]", "UnixLine", "Empty line")
                else:
                    break
            self.readChild("file[]", ArchiveFileEntry)
        
registerPlugin(ArchiveFile, ["application/x-debian-package", "application/x-archive"])
