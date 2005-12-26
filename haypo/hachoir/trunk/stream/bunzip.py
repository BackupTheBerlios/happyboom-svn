import bz2 
from cStringIO import StringIO
from file import FileStream
import os

def BunzipStream(stream):
    size = stream.getSize()
    filename = stream.filename

    # TODO: If you reach this limit that mean that a new
    # code have to be written :-) (using BZ2File or BZ2Decompressor)
    assert size < 10000000
    oldpos = stream.tell()
    stream.seek(0)
    content = stream.getN(size)
    stream.seek(oldpos)
    
    content = bz2.decompress(content)
    io = StringIO(content)
    return FileStream(io, filename)

#def DONTUSETHISBunzipStream(stream):
#    # DON'T USE THIS FUNCTION
#    # because it uses security buggy function: os.tmpnam()
#
#    if True: #not isinstance(stream, FileStream):
#        filename = None
#        realname = os.tmpnam()
#        file = open(realname, 'w')
#        oldpos = stream.tell()
#        stream.seek(0)
#        file.write(stream.getN(stream.getSize()))
#        stream.seek(oldpos)
#        file.close()
#    else:
#        print "Ok."
#        filename = stream.filename
#        realname = filename
#       
#    # TODO: Is it the best value !?
#    buffersize = 4096 
#    io = bz2.BZ2File(realname, "r", buffersize)
#
#    if filename==None:
#        os.unlink(realname)
#
#    # Check data size (buggy with Python <= 2.4.2 and maybe other)
#    io.seek(0,2)
#    guess_size = io.tell()
#    io.seek(0)
#
#    # Check data size
#    io.seek(-1,2)
#    real_size = io.tell() + 1
#    io.seek(0)
#   
#    # Workaroud Python bug :-(
#    if real_size != guess_size:
#        io = StringIO(io.read())
#
#    return FileStream(io, filename)
