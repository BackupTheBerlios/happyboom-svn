import zlib
from cStringIO import StringIO
from file import FileStream

def DeflateStream(data):
    data = zlib.decompress(data)
    io = StringIO(data)
    return FileStream(io)
