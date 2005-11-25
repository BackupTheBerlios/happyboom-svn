from stream.file import FileStream
from StringIO import StringIO

def StringStream(data):
    file = StringIO(data)
    return FileStream(file)
