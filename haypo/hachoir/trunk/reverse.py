from stream.file import FileStream
from plugins.worms2 import Worms2_Dir_File
from plugins.gzip import GzipFile
from format import getFormatSize
from bits import countBits, long2bin, str2hex
import sys

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
        self.values_list = {}
        self.streams = {}

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
        if not isinstance(value, IntValues):
            value = IntValues(value)
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
                        break
        return ok                    

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
            i += 1
        return ok            

    def addSource(self, stream, fields={}):
        assert not self.started
        self.streams.append(stream)
        for id in fields:
            if id not in self.fields:
                self.fields[id] = Field(id)
            self.fields[id].addValue(stream, fields[id])

def loadGZ(filename):
    f = open(filename, 'r')
    input = FileStream(f, filename)
    return GzipFile(input, None) 

def gzip_size():
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

def int16Bits(value):
    v = []
    for i in range(0,16):
        mask = 1 << i
        if (value & mask) == mask:
            v.append(1)
        else:
            v.append(0)  
    return v

def guessBits(d):    
    for n in d:
        val = d[n]
        data = val[0]
        print "====== n=%u, data set=%u items" % (n, len(val))
        if 1<len(val):
            for i in range(0, 11):
                cst = True
                for bits in val[1:]:
                    if bits[i] != data[i]:
                        cst = False
                        break
                if cst:
                    print "bit %u: const=%s" % (i, data[i])
        else:
            print "(not enough data)"
   
def worms2_sprite(res):    
    #sprite_range = IntValues( (0,73) )
    #sprite_range = IntValues( (0,100) )
    sprite_range = IntValues( (0,100) )
    d = {}
    for i in sprite_range.values():
        sprite = res["res[%u]" % i]["data"]
        flags = sprite["flags_b"]
        w,h = sprite["width[0]"],sprite["height[0]"]
        if w < 10 or 1000<w or h<10 or 1000<h:
            print "res[%u] errone" % i
        else:
            n = sprite.n
            stream = sprite.getStream()
            stream.seek(81*3+1) ; m = stream.getFormat("uint8")-1
            #stream.seek(258) ;  data = stream.getN(14)
            stream.seek(81*3) ;  data = stream.getN(272-243)
            if n not in d:
                d[n] = []
#            d[n].append( (sprite["type"],int16Bits(flags),sprite["width[0]"],sprite["height[0]"],i) )
            d[n].append( (i, m, data) )
#    guessBits(d)        
#    return
        
    for n in d:
        print "======== %s =========" % n
        for data in d[n]:
            print "% 3s] n=% 2s m=% 2s %s" % (data[0], n, data[1], str2hex(data[2]))
#            xxx = "".join(map(str,bits[1]))
#            print "%s] %s (%ux%u), id=res[%u]" % (bits[0], xxx, bits[2], bits[3], bits[4])

def worms2_n(res):
    reverse = Reverse()
    sprite_range = IntValues( (0,72) )
    for i in sprite_range.values():
        sprite = res["res[%u]" % i]["data"]
        #stream = sprite.getStream().createSub(start=sprite.getAddr(), size=sprite.getSize())
        reverse.addSource(stream, {"n": sprite.n})
    header = IntValues( (243, 258) )
    print "Find field in range %s" % header
#    reverse.displayData(header)        
#     reverse.displayConstant(header)
    addr = reverse.findField("n", header)
    print "Address of field n: %s\n(or in %s)" % (addr[0], addr[1])

def worms2_font(res):
    reverse = Reverse()
    sprite_range = IntValues( (713,739) )
    for i in sprite_range.values():
        font = res["res[%u]" % i]["data"]
        reverse.addSource(font.getStream(), {"nb": font["nb_char"]})
    header = IntValues( (0, 600) )
    print "Find field in range %s" % header
#    reverse.displayData(header)        
#     reverse.displayConstant(header)
    addr = reverse.findField("nb", header)
    print "Address of field n: %s" % (addr)
#    print "Address of field n: %s\n(or in %s)" % (addr[0], addr[1])

def worms2():
    f = open('/home/haypo/worms/Gfx.dir', 'r')
    input = FileStream(f, None)
    res = Worms2_Dir_File(input, None)["resources"]
#    worms2_sprite(res)
#    worms2_n(res)
    worms2_font(res)
 
if __name__=="__main__":
    worms2()
#    gzip_size()
