import re, struct

_regex_array =  re.compile("^([a-z]+[0-9]*)\[([0-9]+)\]$")
_format_size_cache = {}
_format_type = {
    "string": "s",
    "char": "c",
    "float": "f",
    "double": "d",
    "int8": "b",
    "uint8": "B",
    "int16": "h",
    "uint16": "H",
    "int32": "l",
    "uint32": "L"
}

def _convertNewFormat(format):
    old_format = format
    if format[0] in "!<>":
        endian = format[0]
        str_endian = format[0]
        format = format[1:]
    else:
        endian = None
        str_endian = ""
    m = _regex_array.match(format)
    if m != None:
        format = m.group(1)
        str_count = m.group(2)
        count = int(str_count)
    else:
        str_count = "" 
        count = 1
    if format not in _format_type:
        raise Exception("Format \"%s\" is invalid!" % old_format)
    type = _format_type[format]
    return (str_endian + str_count + type, endian, count, type)

def _getFormatCache(format):
    global _format_size_cache
    if format not in _format_size_cache:
        real_format, endian, count, type = _convertNewFormat(format)
        size = count * struct.calcsize(type)
        _format_size_cache[format] = (real_format, endian, count, type, size)
    return _format_size_cache[format]   

def formatIsString(format):
    cache = _getFormatCache(format)
    return cache[3] == "s"

def formatIsInteger(format):
    cache = _getFormatCache(format)
    return cache[3] in "bBhHlL"

def getFormatSize(format):
    cache = _getFormatCache(format)
    return cache[4]   

def getRealFormat(format):
    cache = _getFormatCache(format)
    return cache[0]   

def checkFormat(format):
    # TODO: Don't use try/except, but something better
    try:
        conv = _convertNewFormat(format)
        return True
    except:
        return False

def splitFormat(format):
    cache = _getFormatCache(format)
    return cache[1:4]   
