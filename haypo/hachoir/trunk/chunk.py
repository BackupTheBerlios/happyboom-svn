import struct, re, types
import config
from format import checkFormat, splitFormat, getFormatSize, getRealFormat, formatIsString, formatIsArray, formatIsInteger, formatIsArray
from error import warning, error
from tools import convertDataToPrintableString
from bits import str2long

class Chunk(object):
    """
    A chunk address is fixed. If you want to move the chunk, delete it :-P
    """
    def __init__(self, id, description, stream, addr, size, parent):
        self._id = id
        self.description = description
        self._size = size
        self._addr = addr
        self._parent = parent
        self._stream = stream
        self.post_process = None
        self.display = None

    def getStaticSize(stream, args):
        return None
    getStaticSize = staticmethod(getStaticSize)

    def postProcess(self):        
        if self.post_process != None:
            self.display = self.post_process(self)

    def getFormat(self):
        return self.__class__.__name__

    def getSmallFormat(self):
        return self.__class__.__name__

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
    def _getAddr(self): return self._addr
    def _getSize(self): return self._size
    def _getId(self):
        return self._id
    def _setId(self, new_id):
        old_id = self.id
        if new_id == old_id:
            return
        self._id = new_id
        self._parent.updateChunkId(old_id, new_id)
    addr = property(_getAddr)
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
    
    def getFormat(self):
        return self.__class__.__name__ + " (%s)" % self._filter.__class__.__name__

    def getSmallFormat(self):
        return self._filter.__class__.__name__

    def setFilter(self, filter):
        self._filter = filter
        self._filter.updateParent(self)
    
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

    def _setId(self, new_id):
        if new_id == self.id:
            return
        self._filter.setId(new_id)
        Chunk._setId(self, new_id)
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
    regex_not_ascii = re.compile("[^\x00-\x7F]")
    names = {
        "C": "c-string",
        "MacLine": "mac line",
        "UnixLine": "unix line",
        "AutoLine": "line",
        "Pascal16": "pascal16",
        "Pascal32": "pascal32",
        "WindowsLine": "windows line",
        "Fixed": "fixed"
    }

    def __init__(self, id, description, stream, str_type, parent, strip=None, charset="ascii", size=None):
        """
        Strip: if strip=None, call read text.strip()
               if strip is a string, call read text.strip(self.strip)
        """
        assert str_type in StringChunk.names
        Chunk.__init__(self, id, description, stream, stream.tell(), 0, parent)
        self._str_type = str_type
        self.eol = None
        self._findSize(size)
        self.strip = strip
        self.charset = charset

    def getFormat(self):
        return "%s (%s)" % (\
            StringChunk.names[self._str_type],
            self.charset)
    getSmallFormat = getFormat

    def _findSize(self, size):
        self._stream.seek(self.addr)
        if self._str_type == "Fixed":
            self.length = size 
            self._size = size
            self.eol = ""
        elif self._str_type == "Pascal16":
            self.length = self._stream.getFormat("!uint16")
            self._size = 2 + self.length
            self.eol = ""
        elif self._str_type == "Pascal32":
            self.length = self._stream.getFormat("!uint32")
            self._size = 4 + self.length
            self.eol = ""
        elif self._str_type == "AutoLine":
            self._size = self._stream.searchLength(StringChunk.regex_eol_nr, True)
            assert self._size != -1
            self._stream.seek(self.addr + self._size-1)
            self.eol = self._stream.getN(1)
            if self.eol == "\r" and self._stream.read(1) == "\n":
                self.eol = "\r\n"
                self._size = self._size + 1
            self.length = self._size - len(self.eol)
        else:            
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
        if self.charset != "ascii":
            try:                
                text = unicode(text, self.charset)
            except:
                self.charset = "ascii"
                text = StringChunk.regex_not_ascii.sub(".", text)
                text = unicode(text, "ascii")
        return text

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
    def __init__(self, id, description, stream, format, parent):
        Chunk.__init__(self, id, description, stream, stream.tell(), None, parent)
        self._format = None
        self._doSetFormat(format)
        stream.seek(self.size, 1)

    def getStaticSize(stream, args):
        return getFormatSize(args[0])
    getStaticSize = staticmethod(getStaticSize)

    def _doSetFormat(self, format):
        if format == self._format:
            return

        # Add endian if needed
        splited = splitFormat(format)
        if splited[0] == None and splited[2] not in "scbB":
            endian = self._parent.endian
            assert endian != None
            format = endian + format
            
        self._format = format
        self._real_format = getRealFormat(format)
        self._is_string = formatIsString(self._format)
        self._is_array = formatIsArray(format)
        self._size = getFormatSize(self._format)
        self._value = {}
       
    def getFormat(self):
        return self.__class__.__name__ + " (%s)" % self._format

    def getSmallFormat(self):
        return self._format

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
                data = struct.unpack(self._real_format, data)
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

class EnumChunk(FormatChunk):
    def __init__(self, id, description, stream, format, dict, parent):
        assert not formatIsArray(format)
        FormatChunk.__init__(self, id, description, stream, format, parent)
        self._dict = dict
#        value = self.getValue()
#        self.description = self.description + ": " + self._dict.get(value, "Unknow (%s)" % value)

    def getDisplayData(self):
        value = self.getValue()
        return self._dict.get(value, "Unknow (%s)" % value)

class BitsStruct(object):
    def __init__(self, items=None, do_reverse=False):
        self._items_list = []
        self._items_dict = {}
        self._size = 0
        self._source = None
        if items != None:
            if do_reverse:
                items = reversed(items)
            for item in items:
                if 3<len(item):
                    type = item[3]
                else:
                    type = None
                self.add(item[0], item[1], item[2], type)
            assert self.isValid()

    def isValid(self):
        return (0 < self._size) and ((self._size % 8) == 0)

    def add(self, bits, id, description, type=None):
        # TODO: (Maybe) Generate new id if another already exist
        assert id not in self._items_dict
        assert 0<bits
        assert bits <= 32
        if type == None:
            if 1<bits:
                type = "bits"
            else:
                type = "bit"
        self._items_list.append(id)
        self._items_dict[id] = (self._size, bits, type, description)
        self._size += bits

    def __getitem__(self, id):
        assert self.isValid() 
        item = self._items_dict[id]
        addr = item[0]
        size = item[1]
        data = self._source.getRaw()
        start = addr / 8
        mask = (1 << size) - 1
        byte_size = (size + (addr % 8) + 7) / 8
        shift = addr - start*8
        data = data[start:start+byte_size]
        value = str2long(data)
        value = (value >> shift) & mask
        if size == 1:
            return value == 1
        else:
            return value

    def setSource(self, source):
        self._source = source

    def _getSize(self):
        assert self.isValid() 
        return self._size / 8
    size = property(_getSize)

    def display(self, ui, parent):
        for id in self._items_list:
            item = self._items_dict[id]
            addr = item[0]
            size = item[1]
            format = item[2]
            desc = item[3]
            display = self[id]
            ui.add_table(parent, addr, size, format, id, desc, display)

class BitsChunk(Chunk):
    def __init__(self, id, description, stream, struct, parent):
        Chunk.__init__(self, id, description, stream, stream.tell(), struct.size, parent)
        self._struct = struct
        self._struct.setSource(self)
        stream.seek(self.size, 1)

    def uiDisplay(self, ui):
        path = ui.add_table(None, self.addr, self.size, "bits", self.id, self.description, "*bits*")
        self._struct.display(ui, path)

    def __getitem__(self, id):
        return self._struct[id]
