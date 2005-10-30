import struct
import re
import types
import string

class Chunk(object):
    def __init__(self, id, description, stream, addr, size):
        self.id = id
        self.description = description
        self.size = size
        self._addr = addr

    def __str__(self):
        return "Chunk(%s) <addr=%s, size=%s, id=%s, description=%s>" % \
            (self.__class__, self._addr, self.size, self.id, self.description)
        
    def getRawData(self, max_size=None):
        return None
        
    def getData(self, max_size=None):
        return None

    def getDisplayData(self):
        return self.getData()

    def _getAddr(self): return self._addr
    addr = property(_getAddr)        
    
class ArrayChunk(Chunk):
    def __init__(self, id, description, stream, addr, size, array):
        Chunk.__init__(self, id, description, stream, addr, size)
        self._array = array
    
    def getData(self, max_size=None):
        return self._array

    def __getitem__(self, index):
        return self._array[index]
        
class FilterChunk(Chunk):
    def __init__(self, id, description, stream, addr, size, filter):
        Chunk.__init__(self, id, description, stream, addr, size)
        self._filter = filter
        
    def getDisplayData(self):
        return "(...)" 
        
    def getData(self, max_size=None):
        return self._filter

    def getFilter(self):
        return self._filter

class FormatChunk(Chunk):
    def __init__(self, id, description, stream, addr, format):
        size = struct.calcsize(format)
        Chunk.__init__(self, id, description, stream, addr, size)
        self.__stream = stream
        self.__addr = addr
        self.__format = format
        self.value = None

    def getFormat(self): return self.__format

    def isArray(self):
        if self.isString(): return False
        return re.compile("^.?[0-9]+.*$").match(self.__format) != None
        
    def isString(self):
        return self.__format[-1] == "s"

    def getRawData(self, max_size=None):
        """ max_size can be None """
        self.__stream.seek(self.addr)
        if (max_size == None or self.size<max_size) or not self.isString():
            data = self.__stream.getN(self.size)
            return data, False
        else:
            data = self.__stream.getN(max_size)
            return data+"(...)", True
   
    def getData(self, max_size=None):
        data, truncated = self.getRawData(max_size)
        if not truncated:
            data = struct.unpack(self.__format, data)
            if not self.isArray():
                data = data[0]
        return data

    def getDisplayData(self):
#        if self.id == None: return "-"

        data = self.getData(20)
        if type(data)==types.StringType:
            display = ""
            for c in data:
                if ord(c)<32:
                    know = {"\n": "\\n", "\r": "\\r", "\0": "\\0"}
                    if c in know:
                        display = display + know[c]
                    else:
                        display = display + "\\x%02X" % ord(c)
                elif c in string.printable:
                    display = display + c
                else:
                    display = display + "."
            return "\"%s\"" % display
        return data 
