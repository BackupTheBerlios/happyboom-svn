import struct
from StringIO import StringIO

class StreamError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

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

def StringStream(data):
    file = StringIO(data)
    return FileStream(file)

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

class FileStream(Stream):
    def __init__(self, file, filename=None):
        """
        Endian: See setEndian function. 
        """

        Stream.__init__(self, filename)
        self.__file = file 
        self.__file.seek(0,2) # Seek to end
        self.__size = self.__file.tell()
        self.__file.seek(0,0) # Seel to beginning

    def clone(self):
        return FileStream(self.__file, self.filename)

    def seek(self, pos, where=0):
        """ Read file seek document to understand where. """
        self.__file.seek(pos, where)
        if self.__size < self.tell():
            raise StreamError("Error when seek to (%s,%s) in a stream." % (pos, where))

    def tell(self):
        return self.__file.tell()

    def __doSearch(self, binary_string, pos_max):
        """
        pos_max: Position of last tested byte
        """
        if 2048<=len(binary_string):
            raise StreamError("Search string too big.")
        size = 2048 
        doublesize = size * 2
        oldpos = self.tell()
        if pos_max-oldpos+1<doublesize:
            doublesize = pos_max-oldpos
            size = 0 
        buffer = self.__file.read(doublesize)
        newpos = oldpos + size
        while len(buffer) != 0:
            pos = buffer.find(binary_string)
            if pos != -1: return oldpos + pos
            oldpos = newpos
            if pos_max < oldpos + size:
                size = pos_max - oldpos
            if size == 0:
                break
            buffer = buffer[size:] + self.__file.read(size)
            newpos = oldpos + size 
        return -1 
  
    def search(self, binary_string, size_max=None):
        if self.__size == 0: return -1
        if size_max != None:
            pos_max = self.tell()+size_max
            if self.__size <= pos_max:
                pos_max = sel.__size-1
        else:
            pos_max = self.__size-1
        assert 0<=pos_max  and pos_max<self.__size
        oldpos = self.tell()
        pos = self.__doSearch(binary_string, pos_max)
        self.seek(oldpos)
        return pos

    def getN(self, size, seek=True):
        data = self.__file.read(size)
        if len(data) != size:
            raise StreamError("Can't read %u bytes in a stream (get %u bytes)." % (size, len(data)))
        if not seek:
            self.__file.seek(-size, 1)
        return data

    def getEnd(self):
        """
        Read everything until the end.
        """
        
        data = self.__file.read()
        return data

    def destroy(self):
        self.__file.close()

    def getSize(self):
        return self.__size

    def getLastPos(self):
        return self.__size-1
