import struct
from error import StreamError

class Stream:
    def __init__(self, filename):
        self.filename = filename
    
    def getSize(self):
        return 0

    def clone(self):
        return None
    
    def getLastPos(self):
        return 0

    def eof(self):
        return self.getLastPos() <= self.tell() 

    def tell(self):
        return 0

    def createSub(self, start, size):
        return SubStream(self, start, size, self.filename)

    def createLimited(self, start, size):
        return LimitedStream(self, start, size, self.filename)
    
    def getN(self, size, seek=True):
        return None

    def getFormat(self, format, seek=True):
        size = struct.calcsize(format)
        data = self.getN(size, seek)
        return struct.unpack(format, data)

    def searchLength(self, str, include_str, size_max=None):        
        pos = self.search(str, size_max)
        if pos == -1: return -1
        lg = pos - self.tell()
        if include_str: lg = lg + len(str)
        return lg
    
    def search(self, str, size_max=None):
        return -1

class LimitedStream(Stream):
    def __init__(self, stream, start=0, size=0, filename=None):
        Stream.__init__(self, filename)
        self._stream = stream.clone()
        if start<0:
            start = 0
        if self._stream.getLastPos() < start+size:
            size = self._stream.getLastPos()-start
        self._start = start
        self._size = size
        self._end = self._start + self._size
        self._stream.seek(self._start)

    def search(self, str, size_max=None):
        if self._end == 0: return -1
        if size_max == None or self._end-self.tell() < size_max:
            size_max = self._end-self.tell()
        assert 0<=size_max  and size_max<=self._size
        return self._stream.search(str, size_max)

    def getN(self, size, seek=True):
        if self._start+self._size<self._stream.tell()+size:
            raise StreamError( \
                "Can't read outsize the stream\n"
                +"(try to read %u byte(s) from position %s, where stream in limited in [%u;%u])" \
                % (size, self._stream.tell(), self._start, self._end))
        return self._stream.getN(size, seek)

    def tell(self):
        return self._stream.tell()

    def seek(self, pos, where=0):
        self._stream.seek(pos, where)
        
    def getSize(self):
        return self._size
    
    def getLastPos(self):
        return self._end

    def clone(self):
        return LimitedStream(self._stream, self._start, self._size, self.filename)

class SubStream(LimitedStream):
    def search(self, str, size_max=None):
        if self._end == 0: return -1
        max = self._end-self.tell()-self._start-1
        if size_max == None or max < size_max:
            size_max = max
        assert 0<=size_max  and size_max<=self._size
        pos = self._stream.search(str, size_max)
        if pos != -1:
            pos = pos - self._start
        return pos

    def seek(self, pos, where=0):
        if where==2:
            pos = pos - self._start
        else:
            pos = pos + self._start
        self._stream.seek(pos, where)

    def tell(self):
        return self._stream.tell() - self._start
    
    def getLastPos(self):
        return self._end - self._start

    def clone(self):
        return SubStream(self._stream, self._start, self._size, self.filename)
