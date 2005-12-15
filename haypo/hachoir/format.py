import re

_regex_format1 = re.compile("^[!<>]?(?:[0-9]+|\{[a-z@_]+\})?[BHLhscfd]$")
_regex_format2 = re.compile("^([!<>]?)((?:[0-9]+|\{[a-z@_]+\})?)([BHLhscfd])$")

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
