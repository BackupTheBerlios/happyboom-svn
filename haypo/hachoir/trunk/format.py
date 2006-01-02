import re, struct
from cache import Cache

class FormatCache(Cache):
    # Uniq instance of the class
    _instance = None

    # Check if a format is an array or not
    # "string[4]" is an array, "char" isn't
    regex_array =  re.compile("^([a-z]+[0-9]*)\[([0-9]+)\]$")

    # Convert Hachoir syntax to struct module syntax
    format_type = {
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
    
    def __init__(self):
        assert FormatCache._instance == None
        Cache.__init__(self, "FormatCache")
        self._dict = {}

    def getCacheSize(self):
        return len(self._dict)

    def purgeCache(self):
        self._dict = {}

    def convertNewFormat(self, format):
        old_format = format
        if format[0] in "!<>":
            endian = format[0]
            str_endian = format[0]
            format = format[1:]
        else:
            endian = None
            str_endian = ""
        m = FormatCache.regex_array.match(format)
        if m != None:
            format = m.group(1)
            str_count = m.group(2)
            count = int(str_count)
        else:
            str_count = "" 
            count = 1
        if format not in FormatCache.format_type:
            raise Exception("Format \"%s\" is invalid!" % old_format)
        type = FormatCache.format_type[format]
        return (str_endian + str_count + type, endian, count, type)

    def __getitem__(self, format):
        if format not in self._dict:
            real_format, endian, count, type = self.convertNewFormat(format)
            size = count * struct.calcsize(type)
            self._dict[format] = (real_format, endian, count, type, size)
        return self._dict[format]   

    def getInstance():
        if FormatCache._instance == None:
            FormatCache._instance = FormatCache()
        return FormatCache._instance
    getInstance = staticmethod(getInstance)        

_format_size_cache = {}

def formatIsString(format):
    cache = FormatCache.getInstance()[format]
    return cache[3] == "s"

def formatIsInteger(format):
    cache = FormatCache.getInstance()[format]
    return cache[3] in "bBhHlL"

def getFormatEndian(format):
    cache = FormatCache.getInstance()[format]
    return cache[1]   

def getFormatSize(format):
    cache = FormatCache.getInstance()[format]
    return cache[4]   

def getRealFormat(format):
    cache = FormatCache.getInstance()[format]
    return cache[0]   

def checkFormat(format):
    # TODO: Don't use try/except, but something better
    try:
        cache = FormatCache.getInstance()
        conv = cache.convertNewFormat(format)
        return True
    except:
        return False

def splitFormat(format):
    cache = FormatCache.getInstance()[format]
    return cache[1:4]   

def formatIsArray(format):
    cache = FormatCache.getInstance()[format]
    return (1 < cache[2]) and (cache[3] != "s")
