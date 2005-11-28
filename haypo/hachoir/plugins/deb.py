"""
Debian (.deb) archive file
"""

from filter import Filter, DeflateFilter
from plugin import registerPlugin, guessPlugin
   
class DebianFileEntry(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "file_entry", "File entry", stream, parent)
        self.readString("header", "UnixLine", "Header")
#        info = re.split(" +", self.header)
        info = self["header"].split()
        filename = info[0]
        size = int(info[5])
        dataio = stream.createSub(stream.tell(), size)
        plugin = guessPlugin(dataio, filename)
#        self.readStreamChild("data", dataio, plugin)
#        self.read("data", "%us" % size, "Data")
        self.readChild("data", DeflateFilter, dataio, size, plugin)
        
class DebianFile(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "deb_file", "Debian archive file", stream, parent)
        self.readString("id", "UnixLine", "Debian archive identifier")
        self.readString("header", "UnixLine", "Header")
        self.readString("version", "UnixLine", "Version")
        self.readArray("file", DebianFileEntry, "Files", self.checkEnd)

    def checkEnd(self, stream, array, last):
#        if len(array)==1: return True
        return stream.eof()
        
registerPlugin(DebianFile, "application/x-debian-package")
