from format import getFormatSize, getFormatEndian
from bits import countBits
from error import error, warning
from chunk import FormatChunk
from default import EmptyFilter
from tools import humanFilesize
from int_values import IntValues
import config
import math

def entropy(stream):
    assert 0 < stream.getSize()
    # Create list of 
    count = {}
    for i in range(0, 256):
        count[ chr(i) ] = 0
    p = []
    if 1024 * 1024 < stream.getSize():
        size = humanFilesize(stream.getSize())
        warning("Warning: Computing entropy of %s of data is slow, please be patient ..." % size)
    stream.seek(0)
    n = 0
    while not stream.eof():
        raw = stream.read(config.best_stream_buffer_size)
        n += len(raw)
        for i in raw:
            count[i] = count[i] + 1
    length = stream.getSize()
    for i in range(0, 256):
        i = chr(i)
        if count[i] != 0:
            p.append( float(count[i]) / length )
    h = 0
    n = len(p)
    for p_i in p:
        h += p_i * math.log(p_i, 2)
    return -h

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
        chunk_size_deltas = IntValues((-20, 20))

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

    def findField(self, id, data_range, size_bits=None, endian=None):
        field = self.fields[id]
        ok = data_range
        if size_bits == None:
            size_bits = field.getBitSize()
        print "Find integer field \"%s\" (at least %u bits long) ..." % (id, size_bits)
        i = 1
        for stream in self.streams:
            print "  find in stream %u/%u ..." % (i, len(self.streams))
            value = field.getValueByStream(stream)
            addr = self.findInteger(stream, value, data_range, size_bits, endian)
            ok = ok.intersection(addr)
            if ok.isEmpty():
                break
            i += 1
        return ok            

    def addSource(self, stream, fields={}):
        self.streams.append(stream)
        for id in fields:
            value = fields[id]
            if isinstance(value, int) or isinstance(value, tuple):
                value = IntValues(value)
            if id not in self.fields:
                self.fields[id] = Field(id, type(value))
            self.fields[id].addValue(stream, value)
