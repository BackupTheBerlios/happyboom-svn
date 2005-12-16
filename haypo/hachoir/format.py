import re, struct

_regex_format1 = re.compile("^[!<>]?(?:[0-9]+|\{[a-z@_]+\})?[BHLbhscfd]$")
_regex_format2 = re.compile("^([!<>]?)((?:[0-9]+|\{[a-z@_]+\})?)([BHLbhscfd])$")
_format_size_cache = {}

def getFormatSize(format):
    global _format_size_cache
    if format not in _format_size_cache:
        assert checkFormat(format)
        endian, count, type = splitFormat(format)
        if count != "":
            count = int(count)
        else:
            count = 1
        _format_size_cache[format] = count * struct.calcsize(type)
    return _format_size_cache[format]   

def checkFormat(format):
    m = _regex_format1.match(format)
    return m != None

def splitFormat(format):
    m = _regex_format2.match(format)
    if m == None: return None
    endian = m.group(1)
    if endian=="": endian="!"
    size = m.group(2)
    type = m.group(3)
    return (endian, size, type,)
