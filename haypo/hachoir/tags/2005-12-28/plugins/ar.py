"""
GNU ar archive : archive file (.a) and Debian (.deb) archive.
"""

from filter import OnDemandFilter, DeflateFilter
from chunk import StringChunk
from plugin import registerPlugin, guessPlugin
from error import error
   
class ArchiveFileEntry(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "file_entry", "File entry", stream, parent)
        self.read("header", "Header", (StringChunk,  "UnixLine"))
        info = self["header"].split()
        assert len(info) == 7
        self.filename = info[0]
        self.size = int(info[5])
        dataio = stream.createSub(stream.tell(), self.size)
        plugin = guessPlugin(dataio, self.filename)
        self.read("content", "File data content", (DeflateFilter, dataio, self.size, plugin))

    def updateParent(self, chunk):
        desc = "File entry (%s)" % self.filename
        chunk.description = desc
        self.setDescription(desc)
        
class ArchiveFile(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "ar_file", "Unix archive file", stream, parent)
        self.read("id", "Unix archive identifier (\"<!arch>\")", (StringChunk, "UnixLine"))
        while not stream.eof():
            while True:
                data = stream.read(1, False)
                if data == "\n":
                    self.read("empty_line[]", "Empty line", (StringChunk, "UnixLine"))
                else:
                    break
            self.read("file[]", "File", (ArchiveFileEntry,))
        
registerPlugin(ArchiveFile, ["application/x-debian-package", "application/x-archive"])
