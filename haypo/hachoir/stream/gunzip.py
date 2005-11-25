import gzip
from cStringIO import StringIO
from file import FileStream

def GunzipStream(data):
    io = StringIO(data)
    print io
    io = gzip.GzipFile(None, "r", None, io)
    data = io.read()
    io = StringIO(data)
    return FileStream(io)
