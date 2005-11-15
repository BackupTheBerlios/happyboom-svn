import zlib
from StringIO import StringIO
from stream import FileStream
from filter import Filter

class DeflateFilter(Filter):
    def __init__(self, stream, parent, start, size):
        # Read data
        self._parent_stream = stream
        self._parent_stream.seek(start)
        data = stream.getN(size)
        
        # Create a new stream
        stream = DeflateStream(data)
        self._compressed_size = size 
        self._decompressed_size = stream.getSize()

        # Create filter
        self._parent_stream.seek(start)
        Filter.__init__(self, "deflate", "Deflate", stream, parent)
        self._addr = self._parent_stream.tell()

        self.read("raw", "!{@end@}s", "")

    def getSize(self):
        return self._compressed_size

def DeflateStream(data):
    data = zlib.decompress(data)
    io = StringIO(data)
    return FileStream(io)
