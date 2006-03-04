"""
MIME type detection using libmagic library.

See also:
- ftp://ftp.astron.com/pub/file/ (libmagic)
- http://www.demonseed.net/~jp/code/magic.py (100% Python)
- http://svn.gna.org/viewcvs/castor/trunk/lib/mime.php?view=markup (PHP)
- files in /usr/share/misc/file/* (on Unix/BSD systems)
"""

import os, sys, stat, re
from error import warning

_mime_by_ext = {
    '.gz':  'application/x-gzip',
    '.ico': 'image/x-ico'
}

# Regular expression used to split a list of MIME types
_mime_splitter_regex = re.compile("[^/]+/[^; ]+(?:;[^;]+)*")

def getGuessFunc():
    """
    Find a function to guess MIME type of a buffer. Try to load libmagic
    (python module "magic"), or use internal fallback.
    @return: Function used to guess MIME type
    @rtype: C{func}
    """
    try:
        path = os.path.dirname(__file__)
        sys.path.append(path)
        import magic
        func = magic.open(magic.MAGIC_MIME)
        func.load()
        return func.buffer
    except ImportError:
        warning("Warning: The library libmagic for Python is unavailable. "
        "Using internal fallback engine.")
        from fallback.magic import whatis
        return whatis

guessMime = getGuessFunc()

def getFileMime(realname, filename=None):
    """ Guess MIME type of a file.

    @parameter realname: Physical filename (used to open the file)
    @type host: C{str}
    @parameter filename: Filename used to detect MIME type using its extension
    @type host: C{str}
    @return: MIME type, or None if fails
    @rtype: C{str}
    """
    if filename == None:
        filename = realname
    mode = os.stat(filename)[stat.ST_MODE]
    assert not stat.S_ISDIR(mode) and not stat.S_ISLNK(mode)
    
    content = file(filename, "rb").read(4096)
    return getBufferMime(content, filename)

def getMimeByExt(ext):    
    """ Guess MIME type of a file using its extension

    @parameter ext: Filename extension (eg. ".zip")
    @type: C{str}
    @return: MIME type, or None if fails
    @rtype: C{str}
    """
    return _mime_by_ext.get(ext, None)

def getStreamMime(stream, filename):
    """ Guess MIME type of a stream using first 4 KB

    @parameter stream: Stream containing data
    @type: C{Stream}
    @parameter filename: Filename of the stream source, can be None
    @type: C{str}
    @return: MIME type, or None if fails
    @rtype: C{str}
    """

    oldpos = stream.tell()
    stream.seek(0)
    size = stream.getSize()
    if 4096 < size:
        size = 4096
    data = stream.getN(size)
    stream.seek(oldpos)
    return getBufferMime(data, filename)

def getAnotherBufferMime(content):    
    """ Another method (L{guessMime}) to guess MIME type. This
    function is used for uncommon MIME types like Gimp picture
    (image/x-xcf).

    @parameter content: First 4 KB of file/stream content.
    @type: C{str}
    @return: MIME type, or None if fails
    @rtype: C{str}
    """

    if content[:2] == "\x4d\x4d" and content[6:12] == "\x02\0\x0A\0\0\0":
        return "image/x-3ds"

    if 2 <= len(content) and ord(content[0]) == 31 and ord(content[1]) == 139:
        return "application/x-gzip"

    # Text
    if content[0:4] == "%PDF":
        return "application/pdf"

    # Pictures
    if content[0:14] == "gimp xcf file\0":
        return "image/x-xcf"

    if content[0:2] == "\0\0" \
    and content[2:4] in ("\x01\0", "\x02\0") \
    and content[9] == "\0":
        return "image/x-ico"

    if content[0] == "\x0A" \
    and content[1] in "\x00\x02\x03\x04\x05" \
    and content[64] == "\0":
        return "image/x-pcx"

    # File system        
    if 4096 <= len(content) \
    and content[1080:1082] == "\x53\xEF" \
    and content[1116:1120] == "\x04\x00\x00\x00":
        return "hachoir/fs-ext2"
        
    if 512 <= len(content) \
    and content[0] in "\xEB\xFA" \
    and content[510:512] == "\x55\xAA" \
    and content[446] in "\x00\x80" \
    and content[446+16*1] in "\x00\x80" \
    and content[446+16*2] in "\x00\x80" \
    and content[446+16*3] in "\x00\x80":
        return "hachoir/master-boot-record"
    
    # Worms2 files
    if content[0:4] == "IMG\x1A":
        return "hachoir/worms2-image"
    if content[0:4] == "SPR\x1A":
        return "hachoir/worms2-sprite"
    if content[0:4] == "FNT\x1A":
        return "hachoir/worms2-font"
    if content[0:4] == "DIR\x1A":
        return "hachoir/worms2-directory"
    return None        

def splitMimes(mimes):
    """ Split flat MIME type string into a list in which each entry has
    the following format: ["type", {"key1": value1, "key2": value2, ...}]

    Examples:
    - "text/plain; encoding=latin-1" => [["text/plain", {"encoding": latin-1"}]
    - "text/plain, text/xml" => [["text/plain", {}],["text/xml", {}]]
    - "text/plain; charset=ISO-8859-1; format=flowed"
      => [['text/plain', {'charset': 'ISO-8859-1', 'format': 'flowed'}]]

    @parameter mimes: Flat MIME type string
    @type: C{str}
    @return: MIME type in a list
    @rtype: C{list}
    """

    mimes = _mime_splitter_regex.findall(mimes)    
    
    mime_list = []
    for mime in mimes:
        parts = mime.strip(" ,").split(";")
        mime = parts[0]
        parts = [ item.strip() for item in parts[1:] ]
        values = {}
        for part in parts:
            if part != "":
                split_part = part.split("=", 1)             
                values[ split_part[0] ] = split_part[1]
        mime_list.append([mime, values])
    return mime_list

def getBufferMime(content, filename):
    """ Main function used to guess the MIME types. It calls L{guessMime},
    and then L{getAnotherBufferMime} if needed.

    @parameter content: First 4 KB of file/stream content.
    @type: C{str}
    @parameter filename: Filename of the file/stream, can be None.
    @type: C{str}
    @return: MIME type list (same format than L{splitMimes} result)
    @rtype: C{str}
    """

    mimes = guessMime(content)
    mimes = splitMimes(mimes)
    if len(mimes) == 0 \
    or mimes[0][0] in ('application/octet-stream', 'image/tiff'):
        new_mime = getAnotherBufferMime(content)
        if new_mime == None and filename != None:
            ext = os.path.splitext(filename)[1]
            new_mime = getMimeByExt(ext)
        if new_mime != None:
            mimes = ((new_mime, {}),)
    return mimes
