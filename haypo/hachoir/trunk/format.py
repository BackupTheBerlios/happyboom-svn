import re, struct

_regex_format1 = re.compile("^[!<>]?(?:[0-9]+|\{[a-z@_]+\})?[BHLbhscfd]$")
_regex_format2 = re.compile("^([!<>]?)((?:[0-9]+|\{[a-z@_]+\})?)([BHLbhscfd])$")
_format_size_cache = {}

def _getFormatCache(format):
    global _format_size_cache
    if format not in _format_size_cache:
        assert checkFormat(format)
        endian, count, type = _doSplitFormat(format)
        size = count * struct.calcsize(type)
        _format_size_cache[format] = (endian, count, type, size)
    return _format_size_cache[format]   

def getFormatSize(format):
    cache = _getFormatCache(format)
    return cache[3]   

def checkFormat(format):
    m = _regex_format1.match(format)
    return m != None

def splitFormat(format):
    cache = _getFormatCache(format)
    return cache[:3]   

def _doSplitFormat(format):
    m = _regex_format2.match(format)
    assert m != None
    endian = m.group(1)
    count = m.group(2)
    type = m.group(3)
    if endian == "":
        endian = "!"
    if count != "":
        count = long(count)
    else:
        count = 1
    return (endian, count, type,)
