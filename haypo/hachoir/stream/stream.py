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
        self.__stream = stream.clone()
        if start<0:
            start = 0
        if self.__stream.getLastPos() < start+size:
            size = self.__stream.getLastPos()-start
        self.__start = start
        self.__size = size
        self.__end = self.__start + self.__size
        self.__stream.seek(self.__start)

    def search(self, str, size_max=None):
        if self.__end == 0: return -1
        if size_max == None or self.__end-self.tell() < size_max:
            size_max = self.__end-self.tell()
        assert 0<=size_max  and size_max<=self.__size
        return self.__stream.search(str, size_max)

    def getN(self, size, seek=True):
        if self.__start+self.__size<self.__stream.tell()+size:
            raise StreamError("Can't read outsize the stream.")
        return self.__stream.getN(size, seek)

    def tell(self):
        return self.__stream.tell()

    def seek(self, pos, where=0):
        self.__stream.seek(pos, where)
        
    def getSize(self):
        return self.__size
    
    def getLastPos(self):
        return self.__end

    def clone(self):
        return LimitedStream(self.__stream, self.__start, self.__size, self.filename)
