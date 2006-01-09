#!/usr/bin/env python

"""
MIME type detection using libmagic library.

See also:
- ftp://ftp.astron.com/pub/file/ (libmagic)
- http://www.demonseed.net/~jp/code/magic.py (100% Python)
- http://svn.gna.org/viewcvs/castor/trunk/lib/mime.php?view=markup (PHP)
- files in /usr/share/misc/file/* (on Unix/BSD systems)
"""

import os, sys, stat, string, re
from error import warning

instance = None

_mime_by_ext = {
    '.gz':  'application/x-gzip',
    '.ico': 'image/x-ico'
}

class GuessMime:
    def __init__(self):
        self.use_fallback = False
        self.func = None
        try:
            path = os.path.dirname(__file__)
            sys.path.append(path)
            import magic
            self.func = magic.open(magic.MAGIC_MIME)
            self.func.load()
        except ImportError:
            warning("Warning: The library libmagic for Python is unavailable. Using internal fallback engine.")
            self.use_fallback = True
        if self.use_fallback:
            from  fallback.magic import whatis
            self.func = whatis

    def guess(self, buffer):
        if not self.use_fallback:
            return self.func.buffer(buffer)
        else:
            mime = self.func(buffer)
            return mime

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
    global _mime_by_ext
    return _mime_by_ext.get(ext, None)

def getStreamMime(stream, filename):
    oldpos = stream.tell()
    stream.seek(0)
    size = stream.getSize()
    if 4096<size:
        size = 4096
    data = stream.getN(size)
    stream.seek(oldpos)
    return getBufferMime(data, filename)

def getAnotherBufferMime(buffer):    
    if buffer[:2] == "\x4d\x4d" and buffer[6:12]=="\x02\0\x0A\0\0\0":
        return "image/x-3ds"

    if 2<=len(buffer) and ord(buffer[0])==31 and ord(buffer[1])==139:
        return "application/x-gzip"

    # Text
    if buffer[0:4] == "%PDF":
        return "application/pdf"

    # Pictures
    if buffer[0:14] == "gimp xcf file\0":
        return "image/x-xcf"

    if buffer[0:2] == "\0\0" \
    and buffer[2:4] in ("\x01\0", "\x02\0") \
    and buffer[9] == "\0":
        return "image/x-ico"

    if buffer[0] == "\x0A" \
    and buffer[1] in "\x00\x02\x03\x04\x05" \
    and buffer[64] == "\0":
        return "image/x-pcx"

    # File system        
    if 4096<=len(buffer) \
    and buffer[1080:1082]=="\x53\xEF" \
    and buffer[1116:1120]=="\x04\x00\x00\x00":
        return "hachoir/fs-ext2"
        
    if 512<=len(buffer) \
    and buffer[0] in "\xEB\xFA" \
    and buffer[510:512] == "\x55\xAA" \
    and buffer[446] in "\x00\x80" \
    and buffer[446+16*1] in "\x00\x80" \
    and buffer[446+16*2] in "\x00\x80" \
    and buffer[446+16*3] in "\x00\x80":
        return "hachoir/master-boot-record"
    
    # Worms2 files
    if buffer[0:4] == "IMG\x1A":
        return "hachoir/worms2-image"
    if buffer[0:4] == "SPR\x1A":
        return "hachoir/worms2-sprite"
    if buffer[0:4] == "FNT\x1A":
        return "hachoir/worms2-font"
    if buffer[0:4] == "DIR\x1A":
        return "hachoir/worms2-directory"
    return None        

def splitMimes(mimes):
    """
    Split MIME types into a list.
    Examples:
    - "text/plain; encoding=latin-1" => [["text/plain", {"encoding": latin-1"}]
    - "text/plain, text/xml" => [["text/plain"],["text/xml"]]
    - "text/plain; charset=ISO-8859-1; format=flowed"
      => [['text/plain', {'charset': 'ISO-8859-1', 'format': 'flowed'}]]
    - "application/x-archive application/x-debian-package"
    """

    regex = re.compile("[^/]+/[^; ]+(?:;[^;]+)*")
    mimes = regex.findall(mimes)    
    
    list = []
    for mime in mimes:
        mime = mime.strip(" ,")
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
    global instance
    if instance == None:
        instance = GuessMime()
    mimes = instance.guess(buffer)
    mimes = splitMimes(mimes)
    if len(mimes) == 0 or mimes[0][0] in ('application/octet-stream', 'image/tiff'):
        new_mime = getAnotherBufferMime(buffer)
        if new_mime == None and filename != None:
            ext = os.path.splitext(filename)[1]
            new_mime = getMimeByExt(ext)
        if new_mime != None:
            mimes = ((new_mime,),)
    return mimes
