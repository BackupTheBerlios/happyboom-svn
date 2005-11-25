import struct
import re
import types
from format import checkFormat, splitFormat
from error import warning, error
from tools import convertDataToPrintableString

class Chunk(object):
    def __init__(self, id, description, stream, addr, size, parent):
        self.__id = id
        self.description = description
        self._size = size
        self._addr = addr
        self._parent = parent
        self._stream = stream
        self.post_process = None
        self.display = None

    def postProcess(self):        
        if self.post_process != None:
            self.display = self.post_process(self)

    def getFormat(self):
        return self.__class__

    def update(self):
        self.display = None
        self.postProcess()

    def __str__(self):
        return "Chunk(%s) <addr=%s, size=%s, id=%s, description=%s>" % \
            (self.__class__, self._addr, self.size, self.id, self.description)
        
    def getStream(self):
        return self._stream

    def getStringValue(self):
        value = self.getDisplayData()
        if type(value) == types.TupleType:
            return "(%s)" % ", ".join( map(str,value) )
        else:
            return "%s" % value

    def getValue(self, max_size=None):
        return None

    def getDisplayData(self):
        if self.display != None:
            return self.display
        else:
            return self.getValue()

    def setParent(self, parent):
        self._parent = parent
    def getParent(self): return self._parent
    def _setAddr(self, addr): self._addr = addr
    def _getAddr(self): return self._addr
    def _getSize(self): return self._size
    def __getId(self): return self.__id
    def __setId(self, id):
        if self.__id == id: return
        self._parent.updateChunkId(self, id)
        self.__id = id
    addr = property(_getAddr, _setAddr)        
    size = property(_getSize)        
    id = property(__getId, __setId)
    value = property(getValue)
    
class FilterChunk(Chunk):
    def __init__(self, id, filter, parent):
        Chunk.__init__(self, id, filter.getDescription(), filter.getStream(), filter.getAddr(), filter.getSize(), parent)
        self._filter = filter
        self._filter.filter_chunk = self
    
    def getFormat(self):
        return self._filter.getId()

    def update(self):
        new = self._filter.clone()
        if new != None:
            self.setFilter(new)
        Chunk.update(self)

    def setFilter(self, filter):
        self._filter = filter
        self._filter.updateParent(self)
    
    def _setAddr(self, addr):
        self._addr = addr
        self._filter.setAddr(addr)
    addr = property(Chunk._getAddr, _setAddr)        
        
    def _getSize(self):
        return self._filter.getSize()
    size = property(_getSize)        
        
    def getDisplayData(self):
        return "(...)" 
        
    def getValue(self, max_size=None):
        return self._filter
    value = property(getValue)

    def getFilter(self):
        return self._filter

class StringChunk(Chunk):
    def __init__(self, id, description, stream, str_type, parent):
        assert str_type in ("C", "UnixLine", "WindowsLine", "MacLine", "AutoLine")
        Chunk.__init__(self, id, description, stream, stream.tell(), 0, parent)
        self._str_type = str_type
        self._read()

    def getFormat(self):
        names = {
            "C": "c-string",
            "MacLine": "mac line",
            "UnixLine": "unix line",
            "AutoLine": "line",
            "WindowsLine": "windows line"
        }
        assert self._str_type in names
        return names[self._str_type]

    def _read(self):
        self._stream.seek(self.addr)
        if self._str_type == "UnixLine":
            end = "\n"
        elif self._str_type == "WindowsLine":
            end = "\r\n"
        elif self._str_type == "MacLine":
            end = "\r"
        elif self._str_type == "AutoLine":
            end = "\r"
        else: 
            # Type: C string
            end = "\0"
        self._size = self._stream.searchLength(end, True)
        assert self._size != -1
        if self._str_type == "AutoLine":
            self._stream.seek(self.addr+self._size)
            try:
                next = self._stream.getN(1)
                if next == '\n':
                    self._size = self._size + 1
                    end = end+"\n"
            except Exception, err:
                warning("Warning while getting end of line of \"auto line\": %s" % err)
        self._stream.seek(self.addr)
        self.str = self._stream.getN(self._size - len(end))

    def update(self):
        Chunk.update(self)
        self._read()

    def getValue(self, max_size=None):
        return self.str
    value = property(getValue)

    def getDisplayData(self):
        if self.display != None:
            return self.display
        else:
            return convertDataToPrintableString(self.str)
        
class FormatChunkCache:
    def __init__(self, chunk):
        self._value = {}
        self._addr = None
        self._format = None
        self._size = None
        self._chunk = chunk
        
    def _isArray(self, format):
        if self._chunk.isString(): return False
        endian, size, type = splitFormat(format)
        return (size != "1" and size != "")

    def _getRawData(self, max_size=None):
        stream = self._chunk.getStream()
        stream.seek(self._addr)
        if (max_size == None or self._size<max_size) or not self._chunk.isString():
            data = stream.getN(self._size)
            return data, False
        else:
            data = stream.getN(max_size)
            return data+"(...)", True

    def update(self):
        real_format = self._chunk.getRealFormat(self._chunk.getFormat())
        if self._addr != self._chunk.addr or self._format != real_format:
            # Invalidate the cache
            self._value = {}
            self._format = real_format
            self._addr = self._chunk.addr
            self._size = struct.calcsize(self._format)

    def getSize(self):
        self.update()
        return self._size

    def getValue(self, max_size=None):
        self.update()
        if max_size not in self._value:
            data, truncated = self._getRawData(max_size)
            if not truncated:
                data = struct.unpack(self._format, data)
                if not self._isArray(self._format):
                    data = data[0]
            self._value[max_size] = data               
        return self._value[max_size]

class FormatChunk(Chunk):
    def __init__(self, id, description, stream, addr, format, parent):
        Chunk.__init__(self, id, description, stream, addr, 0, parent)
        if not checkFormat(format):
            raise Exception("Invalid FormatChunk format: \"%s\"!" % format)
        self.__format = format
        self._cache = FormatChunkCache(self)

    def getFormat(self):
        return self.__format

    def _getSize(self):
        return self._cache.getSize()
    size = property(_getSize)        

    def getRealFormat(self, format):
        return re.sub(r'\{([^}]+)\}', self.__replaceFieldFormat, format)

    def isString(self):
        return self.__format[-1] == "s"

    def __replaceFieldFormat(self, match):
        id = match.group(1)
        if id == "@end@":
            size = self._stream.getLastPos() - self.addr
        else:
            size = getattr(self._parent, id)
        return str(size)
    
    def convertToStringSize(self, size):
        self.__format = "!%ss" % size

    def setFormat(self, format, method, new_id=None, new_description=None):
        """ Method:
        - split => create new raw array if chunk is smaller
        - rescan => if size changed, rescan chunks"""

        # Check format
        if not checkFormat(format):
            raise Exception("Invalid FormatChunk format: \"%s\"!" % format)
        
        # Check new size
        size = struct.calcsize(self.getRealFormat(format))
        if self._stream.getLastPos() < (self.addr + size - 1):
            raise Exception("Can't set chunk %s to format \"%s\": size too big!" % (self.id, format))

        # Update format
        old_size = self.size
        self.__format = format
        new_size = self.size
        diff_size = new_size - old_size

        # Update id and description
        old_id = self.id
        if new_id != None:
            new_id = self.getParent().getUniqChunkId(new_id)
            self.id = new_id
        old_description = self.description
        if new_description != None:
            self.description = new_description

        # Update filter if needed
        if diff_size != 0:
            if method == "split" and diff_size < 0:
                self._parent.addRawChunk(self, old_id, -diff_size, old_description)
            else:
                self._parent.rescan(self, diff_size, new_id=old_id, new_description=old_description, truncate=True)
        self._parent.updateFormatChunk(self)
   
    def getValue(self, max_size=None):
        return self._cache.getValue(max_size)
    value = property(getValue)

    def getDisplayData(self):
        if self.display != None:
            return self.display
        data = self.getValue(20)
        if type(data)==types.StringType:
            return convertDataToPrintableString(data)
        else:
            return data 
