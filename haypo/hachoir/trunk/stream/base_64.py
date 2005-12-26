from base64 import decodestring
from cStringIO import StringIO
from file import FileStream

def Base64Stream(lines):
    data = ""
    for line in lines:
        data = data + line.strip()
    data = "".join(data)
    data = decodestring(data)
    io = StringIO(data)
    io = FileStream(io, None)
    io.seek(0)
    return io
