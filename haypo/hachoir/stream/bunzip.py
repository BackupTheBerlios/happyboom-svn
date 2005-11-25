import bz2 
from cStringIO import StringIO
from file import FileStream
import os

def BunzipStream(stream):
    if True: #not isinstance(stream, FileStream):
        filename = None
        realname = os.tmpnam()
        file = open(realname, 'w')
        oldpos = stream.tell()
        stream.seek(0)
        file.write(stream.getN(stream.getSize()))
        stream.seek(oldpos)
        file.close()
    else:
        print "Ok."
        filename = stream.filename
        realname = filename
       
    # TODO: Is it the best value !?
    buffersize = 4096 
    io = bz2.BZ2File(realname, "r", buffersize)

    if filename==None:
        os.unlink(realname)

    # Check data size
    io.seek(0,2)
    guess_size = io.tell()
    io.seek(0)

    io.seek(-1,2)
    real_size = io.tell() + 1
    io.seek(0)
   
    # Workaroud Python bug :-(
    if real_size != guess_size:
        io = StringIO(io.read())

    return FileStream(io, filename)
