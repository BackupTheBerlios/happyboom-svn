import struct
import re
import types
import string

class Chunk(object):
    def __init__(self, id, description, stream, addr, size, parent):
        self._id = id
        self.description = description
        self._size = size
        self._addr = addr
        self._parent = parent
        self._stream = stream

    def update(self):
        raise Exception("Chunk of type %s doesn't implement the method update()!" % self.__class__)

    def __str__(self):
        return "Chunk(%s) <addr=%s, size=%s, id=%s, description=%s>" % \
            (self.__class__, self._addr, self.size, self._id, self.description)
        
    def getRawData(self, max_size=None):
        return None
        
    def getStream(self):
        return self._stream

    def getData(self, max_size=None):
        return None

    def getDisplayData(self):
        return self.getData()

    def getParent(self): return self._parent
    def _setAddr(self, addr): self._addr = addr
    def _getAddr(self): return self._addr
    def _getSize(self): return self._size
    def _getId(self): return self._id
    def _setId(self, id):
        print "Set id to %s" % id
        if not self._parent.updateChunkId(self, id):
            print "Can't set chunk identifier to \"%s\" (maybe already used)." % id
            return
        self._id = id
    addr = property(_getAddr, _setAddr)        
    size = property(_getSize)        
    id = property(_getId, _setId)
    
class ArrayChunk(Chunk):
    def __init__(self, id, description, stream, array, parent):
        Chunk.__init__(self, id, description, stream, stream.tell(), 0, parent)
        self._array = array

    def update(self):
        prev_chunk = None
        pos = 0
        try:
            for chunk in self._array:
                if prev_chunk != None:
                    chunk.addr = prev_chunk.addr + prev_chunk.size
                else:
                    chunk.addr = self.addr
                chunk.update()
                prev_chunk = chunk
                pos = pos + 1
        except Exception, msg:
            print "Exception while updating an array:\n%s" % msg
            chunk = self._array[pos]
            addr = chunk.addr
            size = self._stream.getSize() - addr
            del self._array[pos:]
            if size != 0:
                chunk = FormatChunk("raw", "Raw data", chunk.getStream(), addr, "!%us" % size, self)
                self._array.append(chunk)

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

    def update(self):
        filter_class = self._filter.__class__
        stream = self._filter.getStream()
        stream.seek(self.addr)
        self._filter = filter_class(stream, self._filter.getParent())
        self._filter.updateParent(self)
        
    def _getSize(self):
        return self._filter.getSize()
    size = property(_getSize)        
        
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

    def update(self):
        # Don't need to do anything
        pass

    def _getSize(self):
        return struct.calcsize(self.getRealFormat())
    size = property(_getSize)        

    def getRealFormat(self):
        return re.sub(r'\{([^}]+)\}', self.__replaceFieldFormat, self.__format)

    def getFormat(self): return self.__format
    
    def checkFormat(self, format):
        m = re.compile("^[!<>]?([0-9]+|\{[a-z_]+\})?[BHLs]$").match(format)
        return (m != None)
        
    def setFormat(self, format, method, new_id=None, new_description=None):
        """ Method:
        - split => create new raw array if chunk is smaller
        - rescan => if size changed, rescan chunks"""
        old_size = self.size
        if not self.checkFormat(format):
            print "Wrong format: \"%s\"!" % format
            return
        self.__format = format
        new_size = self.size
        diff_size = new_size - old_size
        if diff_size != 0:
            if method == "split" and diff_size < 0:
                self._parent.addRawChunk(self, new_id, -diff_size, new_description)
            else:
                self._parent.rescan(self)
        self._parent.redisplay()

    def isArray(self):
        if self.isString(): return False
        m = re.compile("^.?([0-9]+)[^0-9]+$").match(self.__format)
        if m == None: return False
        return m.group(1) != "1"
        
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
            format = self.getRealFormat()
            data = struct.unpack(format, data)
            if not self.isArray():
                data = data[0]
        return data

    def getDisplayData(self):
#        if self.id == None: return "-"
        data = self.getData(20)
        if type(data)==types.StringType:
            if len(data) == 0:
                return "(empty)"
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
