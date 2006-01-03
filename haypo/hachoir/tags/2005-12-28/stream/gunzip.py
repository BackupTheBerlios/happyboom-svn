import gzip
from cStringIO import StringIO
from file import FileStream

def GunzipStream(stream):
    oldpos = stream.tell()
    stream.seek(0)
    data = stream.getN(stream.getSize())
    stream.seek(oldpos)
    
    io = StringIO(data)
    io = gzip.GzipFile(None, "r", None, io)
    data = io.read()
    io = StringIO(data)
    return FileStream(io)
