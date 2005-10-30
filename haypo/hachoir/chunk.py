import struct
import re
import types
import string

class Chunk(object):
    def __init__(self, id, description, stream, addr, size, parent):
        self.id = id
        self.description = description
        self._size = size
        self._addr = addr
        self._parent = parent

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
    def _getSize(self):
        return self._size
    addr = property(_getAddr)        
    size = property(_getSize)        
    
class ArrayChunk(Chunk):
    def __init__(self, id, description, stream, array, parent):
        Chunk.__init__(self, id, description, stream, stream.tell(), 0, parent)
        self._array = array

    def _getSize(self):
        size = 0
        for item in self._array:
            size = size + item.size
        return size
    size = property(_getSize)        
    
    def getData(self, max_size=None):
        return self._array

    def __getitem__(self, index):
        return self._array[index]
        
class FilterChunk(Chunk):
    def __init__(self, id, description, stream, filter):
        Chunk.__init__(self, id, description, stream, filter.getAddr(), filter.getSize(), filter)
        self._filter = filter
        
    def getDisplayData(self):
        return "(...)" 
        
    def getData(self, max_size=None):
        return self._filter

    def getFilter(self):
        return self._filter

class FormatChunk(Chunk):
    def __init__(self, id, description, stream, addr, format, parent):
        Chunk.__init__(self, id, description, stream, addr, 0, parent)
        self.__stream = stream
        self.__addr = addr
        self.__format = format
        self.value = None

    def _getSize(self):
        return struct.calcsize(self._getRealFormat())
    size = property(_getSize)        

    def _getRealFormat(self):
        return re.sub(r'\{([^}]+)\}', self.__replaceFieldFormat, self.__format)

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

    def __replaceFieldFormat(self, match):
#        return str(getattr(self, match.group(1)))
        return str(getattr(self._parent, match.group(1)))
   
    def getData(self, max_size=None):
        data, truncated = self.getRawData(max_size)
        if not truncated:
            format = self._getRealFormat()
            data = struct.unpack(format, data)
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
                    know = { \
                        "\n": "\\n",
                        "\r": "\\r",
                        "\t": "\\t",
                        "\0": "\\0"}
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
