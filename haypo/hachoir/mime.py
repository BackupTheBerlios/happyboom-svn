#!/usr/bin/python
import os, stat

instance = None

def getInstance():
    global instance
    if instance == None:
        import magic
        instance = magic.open(magic.MAGIC_MIME)
        instance.load()
    return instance

def getFileMime(realname, filename=None):
    if filename == None:
        filename = realname
    mode = os.stat(filename)[stat.ST_MODE]
    assert not stat.S_ISDIR(mode) and not stat.S_ISLNK(mode)
    
    f = file(filename, "rb")
    buffer = f.read(4096)
    f.close()
    return getBufferMime(buffer, filename)

def getMimeByExt(ext):    
    if ext == '.gz':
        return 'application/x-gzip'
    return None        

def getBufferMime(buffer, filename):
    magic = getInstance()
    mime = magic.buffer(buffer)
    mime = mime.split(",")
    if mime[0] == 'application/octet-stream' and filename != None:
        ext = os.path.splitext(filename)[1]
        new_mime = getMimeByExt(ext)
        if new_mime != None:
            mime = (new_mime,)
    return mime            
