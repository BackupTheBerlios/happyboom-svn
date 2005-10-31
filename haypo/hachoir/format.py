import re

def checkFormat(format):
    m = re.compile("^[!<>]?(?:[0-9]+|\{[a-z@_]+\})?[BHLs]$").match(format)
    return m != None

def splitFormat(format):
    m = re.compile("^([!<>]?)((?:[0-9]+|\{[a-z@_]+\})?)([BHLs])$").match(format)
    if m == None: return None
    endian = m.group(1)
    if endian=="": endian="!"
    size = m.group(2)
    type = m.group(3)
    return (endian, size, type,)
