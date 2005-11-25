from stream.file import FileStream
from cStringIO import StringIO

def StringStream(data):
    file = StringIO(data)
    return FileStream(file)
