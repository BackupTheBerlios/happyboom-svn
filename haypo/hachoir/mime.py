#!/usr/bin/python

"""
MIME type detection using libmagic library.

See also:
- ftp://ftp.astron.com/pub/file/ (libmagic)
- http://www.demonseed.net/~jp/code/magic.py (100% Python)
- http://svn.gna.org/viewcvs/castor/trunk/lib/mime.php?view=markup (PHP)
"""

import os, stat, string

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
    if buffer[:4] == "%PDF":
        return "application/pdf"
    if buffer[:14] == "gimp xcf file\0":
        return "image/x-xcf"
    return None        

def splitMimes(mimes):
    """
    Split MIME types into a list.
    Examples:
    - "text/plain; encoding=latin-1" => [["text/plain", {"encoding": latin-1"}]
    - "text/plain, text/xml" => [["text/plain"],["text/xml"]]
    - "text/plain; charset=ISO-8859-1; format=flowed"
      => [['text/plain', {'charset': 'ISO-8859-1', 'format': 'flowed'}]]
    """
    
    list = []
    for mime in map(string.strip, mimes.split(",")):
        parts = mime.split(";")
        mime = parts[0]
        parts = map(string.strip, parts[1:])
        values = {}
        for part in parts:
            if part != "":
                split_part = part.split("=", 1)             
                values[ split_part[0] ] = split_part[1]
        list.append([mime,values])
    return list

def getBufferMime(buffer, filename):
    magic = getInstance()
    mimes = magic.buffer(buffer)
    mimes = splitMimes(mimes)
    if mimes[0][0] == 'application/octet-stream' and filename != None:
        ext = os.path.splitext(filename)[1]
        new_mime = _getBufferMime(buffer)
        if new_mime == None:
            new_mime = getMimeByExt(ext)
        if new_mime != None:
            mimes = ((new_mime,),)
    return mimes
