from stream.file import FileStream
from plugins.worms2 import Worms2_Dir_File
from plugins.gzip import GzipFile
from format import getFormatSize, getFormatEndian
from bits import countBits, long2bin, str2hex
from error import error, warning
from chunk import FormatChunk
from default import EmptyFilter
import config
import sys

class Pattern:
    def check(self, stream):
        return False
    
class FirstPattern(Pattern):
    def __init__(self, header_size, chunk_size_format, chunk_size_delta):
        self.header_size = header_size
        self.chunk_size_format = chunk_size_format
        self.chunk_size_delta = chunk_size_delta

    def check(self, stream, min_ok=2):
        count, done = self._createFilter(stream, True)
        return done or min_ok <= count

    def testFilter(self, stream):
        return self._createFilter(stream, False)
        
    def _createFilter(self, stream, check):
        count = 0
        done = False
        try:
            stream.seek(0)
            filter = EmptyFilter(stream, None)
            if 0 < self.header_size:
                filter.read("header", "Header", (FormatChunk, "string[%u]" % self.header_size))
            last_ok = stream.tell()                
            while not stream.eof():
                last_ok = stream.tell()                
                size = filter.doRead("chunk_size[]", "Chunk size", (FormatChunk, self.chunk_size_format)).value
                size += self.chunk_size_delta
                filter.read("chunk_data[]", "Chunk data", (FormatChunk, "string[%u]" % size))
                count = count + 1
            last_ok = stream.tell()                
            done = True
        except Exception, msg:
            if config.debug:
                warning("Error when testing a pattern: %s" % msg)
        if check:
            return (count, done) 
        else:
            stream.seek(last_ok)
            filter.addPadding()
            return filter
        
class IntValues:
    def __init__(self, data=None):
        self.items = None
        self.min = None
        self.max = None
        if data != None:
            self.set(data)

    def __hash__(self):
        return hash(self.items)

    def hasValue(self, value):
        return self._in(self.items, value)
        
    def _in(self, values, x):
        if isinstance(values, tuple):
            return values[0] <= x and x <= values[1]
        elif isinstance(values, list):
            result = 0
            for item in values:
                if self._in(item, x):
                    return True
            return False
        elif values != None:        
            return values == x
        else:
            return False

    def set(self, value):
        self.items = None
        self.min = self.max = None
        self.add(value)

    def __str__(self):
        return str(self.items)        

    def isEmpty(self):
        return self.items == None

    def __len__(self):
        return self._length(self.items)
        
    def _length(self, values):
        if isinstance(values, tuple):
            return values[1] - values[0] + 1
        elif isinstance(values, list):
            result = 0
            for item in values:
                result += self._length(item)
            return result
        elif values != None:        
            return 1 
        else:
            return 0

    def values(self):
        return self._values(self.items)
        
    def _values(self, values):
        if isinstance(values, tuple):
            return range(values[0], values[1]+1)
        elif isinstance(values, list):
            result = []
            for item in values:
                result.extend( self._values(item) )
            return result
        elif values != None:        
            return [values]
        else:
            return []

    def add(self, new):
        if isinstance(new, IntValues):
            new = new.items

        # TODO: Fix that!
        if isinstance(new, int):
            if self.min == None or new < self.min:
                self.min = new
            if self.max == None or new > self.max:
                self.max = new
        elif isinstance(new, tuple):
            if self.min == None or new[0] < self.min:
                self.min = new[0]
            if self.max == None or new[1] > self.max:
                self.max = new[1]

        if isinstance(self.items, tuple):
            if isinstance(new, tuple):
                if self.items[0] <= new[0] and new[1] <= self.items[1]:
                    return
                assert False # TODO: Finish ..
            elif isinstance(new, int):
                if (new - self.items[1]) == 1:
                    self.items = (self.items[0], new)
                else:
                    self.items = [self.items, new]
            else:            
                assert False # TODO: Finish ..
            return
        elif isinstance(self.items, list):
            for index in range(0, len(self.items)):
                item = self.items[index]
                if item == new:
                    return
                if isinstance(item, int) and new < item:
                    self.items.insert(index-1, new)
                    return
                if isinstance(item, tuple) and (new-item[1])==1:
                    self.items[index] = (item[0], new)
                    return

            # Can create an interval?
            item = self.items[-1]
            if isinstance(item, int) and (new-item) == 1:
                self.items[-1] = (item, new)
                return

            if isinstance(new, list):
                # Extend current vector
                for item in new:
                    self.add(item)
            else:
                # Just append value to vector
                self.items.append(new)
        elif self.items != None:        
            if isinstance(self.items, int) and isinstance(new, int):
                if (self.items-new) == 1:
                    self.items = (new, self.items)
                    return
                elif (self.items-new) == -1:
                    self.items = (self.items, new)
                    return
            self.items = [self.items]
            self.add(new)
        else:
            self.items = new

    def intersection(self, second):
        first = set( self.values() ) 
        second = set( second.values() )
        result = first.intersection(second)
        if 0 < len(result):
            result = list(result)
        else:
            result = None
        return IntValues(result)

class Field:
    def __init__(self, id, type):
        self.id = id    
        self.values = {}
        self.values_list = {}
        self.streams = {}
        self.type = type

    def getStreamsByValue(self, value):
        return self.streams.get(hash(value), [])

    def getValueByStream(self, stream, default=None):
        return self.values.get(stream, default)

    def getBitSize(self):
        values = self.getValues()
        max_value = max([ value.max for value in values])
        min_value = min([ value.min for value in values])
        return max(countBits(max_value), countBits(min_value))

    def getValues(self):
        return self.values_list.values()

    def addValue(self, stream, value):
        assert type(value) == self.type
        self.values[stream] = value
        if hash(value) not in self.streams:
            self.streams[hash(value)] = []
        self.streams[hash(value)].append(stream)
        if hash(value) not in self.values_list:
            self.values_list[hash(value)] = value

class Reverse:
    def __init__(self):
        self.fields = {}
        self.streams = []

    def _findConstant(self, streams, data_range):
        assert 2 <= len(streams)

        # Find mimimum/maximum stream size
        min_size = streams[0].getSize()
        for stream in streams[1:]:
            size = stream.getSize()
            if size < min_size:
                min_size = size
        assert 1 <= min_size                

        # Verify data range
        if not isinstance(data_range, IntValues):
            data_range = IntValues(data_range)
        assert 0 <= data_range.min and data_range.max < min_size

        # Compare streams ...
        cst_list = IntValues()
        data_list = IntValues()
        input = streams[0] 
        for addr in data_range.values():
            input.seek(addr)
            byte = input.getFormat("uint8")
            cst = True
            for stream in streams[1:]:
                stream.seek(addr)
                if stream.getFormat("uint8") != byte:
                    cst = False
                    break
            if cst:
                cst_list.add(addr)
            else:
                data_list.add(addr)
        return (cst_list, data_list)                

    def displayConstant(self, data_range):
        cst_list, data_list = self._findConstant(self.streams, data_range)
        stream = self.streams[0]
        for addr in cst_list.values():
            stream.seek(addr)
            byte = stream.getFormat("uint8")
            print "Constant %u: %02X" % (addr, byte)

    def displayData(self, data_range):
        cst_list, data_list = self._findConstant(self.streams, data_range)
        for id in self.fields:
            field = self.fields[id]
            data = []
            for stream in self.streams:
                value = field.getValueByStream(stream)
                data.append(value)
            data = [ "%02X" % x for x in data ]
            data = " ".join(data)
            print "       %s: %s" % (id, data)
            
        for addr in data_list.values():
            data = []
            for stream in self.streams:
                stream.seek(addr)
                byte = stream.getFormat("uint8")
                data.append(byte)                    
            data = [ "%02X" % x for x in data ]
            data = " ".join(data)
            print "Data %u: %s" % (addr, data)

    def findInteger(self, stream, value, range, size_bits, endian=None):
        assert size_bits <= 32
        if endian == None:
            formats = ["<uint32", ">uint32"]
        else:            
            formats = [endian+"uint32"]
        if size_bits <= 16:
            if endian == None:
                formats.extend(["<uint16", ">uint16"])
            else:
                formats.append(endian+"uint16")
        if size_bits <= 8:
            formats.append("uint8")
        ok = IntValues()
        endian = {}
        for addr in range.values():
            stream.seek(addr)
            for format in formats:
                size = getFormatSize(format)
                if addr+size <= stream.getLastPos():
                    read = int( stream.getFormat(format, False) )
                    if value.hasValue(read):
                        ok.add(addr)
        return ok       

    def guessPattern(self, stream, min_ok):
        """
        Try differents parameters to obtain pattern like:
           (header, size1, data1, size2, data2, ...)
        
        Notes:
        - header is optionnal
        - sizes may be shifted (ex: size+4) to get data size
        """
        filter = self.guessPatternFormat(stream, "<uint32", min_ok)
        if filter == None:
            filter = self.guessPatternFormat(stream, ">uint32", min_ok)
        if filter == None:
            filter = self.guessPatternFormat(stream, "<uint16", min_ok)
        if filter == None:
            filter = self.guessPatternFormat(stream, ">uint16", min_ok)
        return filter            

    def guessPatternFormat(self, stream, chunk_size_format, min_ok):
        """
        See guessPattern().
        """
        # Config
        max_header_size = 64 
        chunk_size_deltas = IntValues((-20,20))

        # Find possible header sizes
        range = IntValues((0, max_header_size))
        size_bits = getFormatSize(chunk_size_format)*8
        value = IntValues((0, stream.getSize() - size_bits/8))
        endian = getFormatEndian(chunk_size_format)
        header_sizes = self.findInteger(stream, value, range, size_bits, endian)
        print "Possible header sizes: %s" % header_sizes

        # Find chunk size delta
        for header_size in header_sizes.values():
            for chunk_size_delta in chunk_size_deltas.values(): 
                # Try a pattern ...
                pattern = FirstPattern(header_size, chunk_size_format, chunk_size_delta)
                if pattern.check(stream, min_ok):
                    print "Found filter -> header size=%s, chunk size delta=%s (format \"%s\")" % (header_size, chunk_size_delta, chunk_size_format)
                    return pattern.testFilter(stream)

    def findField(self, id, data_range):
        field = self.fields[id]
        ok = data_range
        size_bits = field.getBitSize()
        print "Find integer field \"%s\" (at least %u bits long) ..." % (id, size_bits)
        i = 1
        for stream in self.streams:
            print "  find in stream %u/%u ..." % (i, len(self.streams))
            value = field.getValueByStream(stream)
            addr = self.findInteger(stream, value, data_range, size_bits)
            ok = ok.intersection(addr)
            if ok.isEmpty():
                break
            i += 1
        return ok            

    def addSource(self, stream, fields={}):
        self.streams.append(stream)
        for id in fields:
            value = fields[id]
            if id not in self.fields:
                self.fields[id] = Field(id, type(value))
            self.fields[id].addValue(stream, value)
