from stream.file import FileStream
from plugins.worms2 import Worms2_Dir_File
from plugins.gzip import GzipFile
from format import getFormatSize
from bits import countBits
import sys

class IntValues:
    def __init__(self, data=None):
        self.items = None
        self.min = None
        self.max = None
        if data != None:
            self.set(data)

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
                if new < item:
                    self.items.insert(index-1, new)
                    return
 #               if isinstance(item, tuple):
#                    ...
            if isinstance(new, list):
                for item in new:
                    self.add(item)
            else:
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
        result = list(result)
        return IntValues(result)

class Field:
    def __init__(self, id):
        self.id = id    
        self.values = {}
        self.streams = {}

    def getStreamsByValue(self, value):
        return self.streams.get(value, [])

    def getValueByStream(self, stream, default=None):
        return self.values.get(stream, default)

    def getValues(self):
        return self.streams.keys()

    def addValue(self, stream, value):
        self.values[stream] = value
        if value not in self.streams:
            self.streams[value] = []
        self.streams[value].append(stream)

class Reverse:
    def __init__(self):
        self.fields = {}
        self.streams = []
        
        # Feeded after analyse
        self.started = False
        self.min_size, self.max_size = None, None
        self.data_range = None
        self.cst_list = None
        self.data_list = None

    def _initAnalyse(self, data_range):
        if self.started:
            assert data_range == self.data_range
            return
        assert 0 < len(self.streams)
        self.started = True        
        self.data_range = data_range

        # Find mimimum/maximum stream size
        self.min_size = self.max_size = self.streams[0].getSize()
        for stream in self.streams[1:]:
            size = stream.getSize()
            if size < self.min_size:
                self.min_size = size
            if size > self.max_size:
                self.max_size = size            
        assert 1 <= self.min_size                

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

    def OLDfindField(self, id, data_range):
        self.cst_list, self.data_list = self._findConstant(self.streams, data_range)
        field = self.fields[id]
        values = field.getValues()
        addr = IntValues()
        possible_addr = self.data_list
        first = True
        for value in values:
            streams = field.getStreamsByValue(value)
            if 1<len(streams):
                cst_list, data_list = self._findConstant(streams, self.data_list)
            else:
                cst_list = self.data_list
            if first:
                addr.add(cst_list)
                first = False
            else:
                addr = addr.intersection(cst_list)
            if addr.isEmpty():
                break            
        return (addr, possible_addr)

    def findInteger(self, stream, value, range, size_bits):
        assert size_bits <= 32
        formats = ["<uint32", ">uint32"]
        if size_bits <= 16:
            formats.extend(["<uint16", ">uint16"])
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

    def findField(self, id, data_range):
        field = self.fields[id]
        ok = data_range
        max_values = map(lambda x: x.max, field.getValues())
        min_values = map(lambda x: x.min, field.getValues())
        size_bits = max(countBits(max(max_values)), countBits(min(min_values)))
        print size_bits
        for stream in self.streams:
            value = field.getValueByStream(stream)
            addr = self.findInteger(stream, value, data_range, size_bits)
            ok = ok.intersection(addr)
        return ok            

    def addSource(self, stream, fields={}):
        assert not self.started
        self.streams.append(stream)
        for id in fields:
            if id not in self.fields:
                self.fields[id] = Field(id)
            self.fields[id].addValue(stream, fields[id])

def main():
    name = '/home/haypo/worms/Gfx.dir'
    f = open(name, 'r')
    input = FileStream(f, name)
    root = Worms2_Dir_File(input, None)
    res = root["resources"]
    reverse = Reverse()
#    sprite_range = IntValues( [(0,13), 67, 72] )
    sprite_range = IntValues( (0,72) )
    for i in sprite_range.values():
        sprite = res["res[%u]" % i]["data"]
        stream = sprite.getStream().createSub(start=sprite.getAddr(), size=sprite.getSize())
#        assert sprite.n < 5
        reverse.addSource(stream, {"n": sprite.n})
    header = IntValues( (243, 258) )
    print "Find field in range %s" % header
#    reverse.displayData(header)        
#     reverse.displayConstant(header)
    addr = reverse.findField("n", header)
    print "Address of field n: %s\n(or in %s)" % (addr[0], addr[1])

def loadGZ(filename):
    f = open(filename, 'r')
    input = FileStream(f, filename)
    return GzipFile(input, None) 

def main():
    reverse = Reverse()
    for filename in sys.argv[1:]:
        g = loadGZ(filename)
        stream = g.getStream()
        sub = stream.createSub(start=stream.getSize()-50)
        size = int(g["size"])
        size = IntValues( (size-30, size+30) )
        reverse.addSource(sub, {"size": size})
    header = IntValues( (0,49) )
#    reverse.displayConstant(header)
    addr = reverse.findField("size", header)
    print "Address of field n: %s" % addr 

if __name__=="__main__":
    main()
