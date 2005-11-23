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

def getFileMime(filename):
    mode = os.stat(filename)[stat.ST_MODE]
    if stat.S_ISDIR(mode):
        return "Directory"
    if stat.S_ISLNK(mode):
        return "Link"
    
    f = file(filename, "rb")
    buffer = f.read(4096)
    f.close()
    return getBufferMime(buffer)

def getBufferMime(buffer):
    magic = getInstance()
    type = magic.buffer(buffer)
    return type.split(",")
