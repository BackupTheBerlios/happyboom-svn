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

def _getBufferMime(buffer):    
    if ord(buffer[0])==31 and ord(buffer[1])==139:
        return "application/x-gzip"
    return None        

def getBufferMime(buffer, filename):
    magic = getInstance()
    mimes = magic.buffer(buffer)
    mimes = mimes.split(", ")
    import string
    mimes = map(string.split, mimes, ';')
    if mimes[0][0] == 'application/octet-stream' and filename != None:
        ext = os.path.splitext(filename)[1]
        new_mime = _getBufferMime(buffer)
        if new_mime == None:
            new_mime = getMimeByExt(ext)
        if new_mime != None:
            mimes = ((new_mime,),)
    return mimes
