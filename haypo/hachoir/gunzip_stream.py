import gzip
from StringIO import StringIO
from stream import FileStream

def GunzipStream(data):
    io = StringIO(data)
    io = gzip.GzipFile(None, "r", None, io)
    data = io.read()
    io = StringIO(data)
    return FileStream(io)
