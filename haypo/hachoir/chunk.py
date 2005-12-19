import struct, re, types
import config
from format import checkFormat, splitFormat, getFormatSize 
from error import warning, error
from tools import convertDataToPrintableString

class Chunk(object):
    def __init__(self, id, description, stream, addr, size, parent):
        self._id = id
        self.description = description
        self._size = size
        self._addr = addr
        self._parent = parent
        self._stream = stream
        self.post_process = None
        self.display = None

    def clone(self):
        raise Exception("%s doesn't implement clone() method!" % self)

    def postProcess(self):        
        if self.post_process != None:
            self.display = self.post_process(self)

    def getFormat(self):
        return self.__class__

    def update(self):
        self.display = None
        self.postProcess()

    def getStream(self):
        return self._stream

    def getStringValue(self):
        value = self.getDisplayData()
        if type(value) == types.TupleType:
            return "(%s)" % ", ".join( map(str,value) )
        else:
            return "%s" % value

    def getRaw(self, max_size=None):
        oldpos = self._stream.tell()
        self._stream.seek(self.addr)
        size = self._size
        if max_size != None and max_size<size:
            size = max_size
        data = self._stream.getN(size)
        self._stream.seek(oldpos)
        return data

    def getValue(self, max_size=None):
        return self.getRaw(max_size)

    def getDisplayData(self):
        if self.display != None:
            return self.display
        else:
            return self.getRaw(40)

    def setParent(self, parent):
        self._parent = parent
    def getParent(self): return self._parent
    def _setAddr(self, addr): self._addr = addr
    def _getAddr(self): return self._addr
    def _getSize(self): return self._size
    def _getId(self): return self._id
    def _setId(self, id):
        if self._id == id: return
        self._parent.updateChunkId(self, id)
        self._id = id
    addr = property(_getAddr, _setAddr)        
    size = property(_getSize)        
    id = property(_getId, _setId)
    value = property(getValue)
    raw = property(getRaw)
    
class FilterChunk(Chunk):
    def __init__(self, id, filter, parent, parent_addr):
        self._description = None
        self.parent_addr = parent_addr
        self._filter = filter
        self._filter.filter_chunk = self
        self._parent = None
        Chunk.__init__(self, id, \
            filter.getDescription(), filter.getStream(), filter.getAddr(), \
            filter.getSize(), parent)
        self._description = filter.getDescription()
    
    def clone(self, addr=None):
        filter_copy = self._filter.clone(addr=addr)
        # TODO: Is it always alright? (or use parent_addr = self.parent_addr)
        parent_addr = addr
        return FilterChunk(self.id, filter_copy, self.getParent(), parent_addr)
    
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

    def _setId(self, id):
        Chunk._setId(self, id)
        self._filter.setId(id)
    id = property(Chunk._getId, _setId)

    def _getDescription(self):
        return self._description
    def _setDescription(self, description):
        if self._description != None:
            self._description = description
            self._filter.setDescription(description)
            self._parent.updateChunkDescription(self._id, description)
    description = property(_getDescription, _setDescription)

class StringChunk(Chunk):
    regex_eol_nr = re.compile("[\n\r]")
    names = {
        "C": "c-string",
        "MacLine": "mac line",
        "UnixLine": "unix line",
        "AutoLine": "line",
        "Pascal16": "pascal16",
        "Pascal32": "pascal32",
        "WindowsLine": "windows line"
    }

    def __init__(self, id, description, stream, str_type, parent, strip=None):
        """
        Strip: if strip=None, call read text.strip()
               if strip is a string, call read text.strip(self.strip)
        """
        assert str_type in StringChunk.names
        Chunk.__init__(self, id, description, stream, stream.tell(), 0, parent)
        self._str_type = str_type
        self.eol = None
        self._findSize()
        self._cache_addr = None
        self._cache_max_size = None
        self._cache_value = None
        self.strip = strip

    def getFormat(self):
        assert self._str_type in StringChunk.names
        return StringChunk.names[self._str_type]

    def _findSize(self):
        self._stream.seek(self.addr)
        if self._str_type == "Pascal16":
            self.length = self._stream.getFormat("!H")[0]
            self._size = 2 + self.length
            self.eol = ""
            return
        if self._str_type == "Pascal32":
            self.length = self._stream.getFormat("!L")[0]
            self._size = 4 + self.length
            self.eol = ""
            return
            
        if self._str_type == "AutoLine":
            self._size = self._stream.searchLength(StringChunk.regex_eol_nr, True)
            assert self._size != -1
            self._stream.seek(self.addr + self._size-1)
            self.eol = self._stream.getN(1)
            if self.eol == "\r" and self._stream.read(1) == "\n":
                self.eol = "\r\n"
                self._size = self._size + 1
            self.length = self._size - len(self.eol)
            return

        if self._str_type == "UnixLine":
            self.eol = "\n"
        elif self._str_type == "WindowsLine":
            self.eol = "\r\n"
        elif self._str_type == "MacLine":
            self.eol = "\r"
        else: 
            self.eol = "\0"
        self._size = self._stream.searchLength(self.eol, True)
        assert self._size != -1
        self.length = self._size - len(self.eol)
        self._stream.seek(self.addr + self._size)
        
    def _read(self, max_size):
        if self._cache_addr==self.addr and self._cache_max_size==max_size:
            return self._cache_value
        self._cache_addr = self.addr
        self._cache_max_size = max_size

        self._stream.seek(self.addr)
        if self._str_type == "Pascal32":
            self._stream.seek(4,1)
            size = self.length
        elif self._str_type == "Pascal16":
            self._stream.seek(2,1)
            size = self.length
        else:
            size = self._size - len(self.eol)
        if max_size != None and max_size<size:
            text = self._stream.getN(max_size)+"(...)"
        else:
            text = self._stream.getN(size)
        self._stream.seek(self.addr + self._size)
        if self.strip != None:
            if self.strip == True:
                text = text.strip()
            else:
                text = text.strip(self.strip)
        self._cache_value = text
        return text

    def update(self):
        Chunk.update(self)
        self._findSize()

    def getValue(self, max_size=None):
        return self._read(None)
    value = property(getValue)

    def getDisplayData(self):
        if self.display != None:
            return self.display
        else:
            text = self._read(config.max_string_length)
            return convertDataToPrintableString(text)
        
class FormatChunk(Chunk):
    regex_sub_format = re.compile(r'\{([^}]+)\}')

    def __init__(self, id, description, stream, addr, format, parent):
        Chunk.__init__(self, id, description, stream, addr, None, parent)
        self._format = None
        self._doSetFormat(format)

    def _doSetFormat(self, format):
        if format == self._format:
            return
        self._format = format
        self._is_string = self.isString()
        if not self._is_string:
            count = splitFormat(self._format)[1]
            self._is_array = (count != 1)
        else:
            self._is_array = False
        self._size = getFormatSize(self._format)
        self._value = {}
       
    def clone(self, addr=None):
        if addr == None:
            addr = self._addr
        return FormatChunk(self.id, self.description, self._stream, addr, self._format, self._parent)

    def _setAddr(self, addr):
        self._addr = addr
        self._value = {}
    addr = property(Chunk._getAddr, _setAddr)

    def getFormat(self):
        return self._format

    def isString(self):
        return self._format[-1] == "s"

    def convertToStringSize(self, size):
        self._doSetFormat("%us" % size)

    def setFormat(self, format, method, new_id=None, new_description=None):
        """ Method:
        - split => create new raw array if chunk is smaller
        - rescan => if size changed, rescan chunks"""

        # Check format
        if not checkFormat(format):
            raise Exception("Invalid FormatChunk format: \"%s\"!" % format)
        
        # Check new size
        size = getFormatSize(format)
        if self._stream.getLastPos() < (self.addr + size - 1):
            raise Exception("Can't set chunk %s to format \"%s\": size too big!" % (self.id, format))
        self._cache.setFormat(format)

        # Update format
        old_size = self._size
        self._doSetFormat(format)
        new_size = self._size
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

    def _getRawData(self, max_size=None):
        oldpos = self._stream.tell()
        self._stream.seek(self._addr)
        if (max_size == None or self._size<=max_size) or not self._is_string:
            data = self._stream.getN(self._size, False)
            self._stream.seek(oldpos)
            return data, False
        else:
            data = self._stream.getN(max_size, False)
            self._stream.seek(oldpos)
            return data, True

    def getRaw(self, max_size=None):
        return self._getRawData(max_size)[0]
    raw = property(getRaw)
   
    def getValue(self, max_size=None):
        if max_size not in self._value:
            data, truncated = self._getRawData(max_size)
            if not truncated:
                data = struct.unpack(self._format, data)
                if not self._is_array:
                    data = data[0]
            else:
                data = data + "(...)"
            self._value[max_size] = data
        return self._value[max_size]
    value = property(getValue)

    def getDisplayData(self):
        if self.display != None:
            return self.display
        data = self.getValue(config.max_string_length)
        if type(data)==types.StringType:
            return convertDataToPrintableString(data)
        else:
            return data 
