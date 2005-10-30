import struct
from StringIO import StringIO

class Stream:
    def __init__(self):
        pass

    def get16(self):
        return None

    def eof(self):
        return self.getLastPos() <= self.tell() 

    def tell(self):
        return 0

    def searchLength(self, str, include_str, size_max=None):        
        pos = self.search(str, size_max)
        if pos == -1: return -1
        lg = pos - self.tell()
        if include_str: lg = lg + len(str)
        return lg
    
    def search(self, str, size_max=None):
        return -1

def StringStream(data, endian="!"):
    file = StringIO(data)
    return FileStream(file, endian)

class LimitedFileStream(Stream):
    def __init__(self, filename, start=0, size=0, endian="<"):
        self.__stream = FileStream(filename)
        if start<0: start = 0
        if self.__stream.getSize() < start+size: size = self.__stream.getSize()-start
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

    def getN(self, size):
        if self.__start+self.__size<self.__stream.tell()+size:
            raise Exception("Can't read outsize the stream.")
        return self.__stream.getN(size)

    def tell(self):
        return self.__stream.tell()

    def seek(self, pos, where=0):
        self.__stream.seek(pos, where)
        
    def getSize(self):
        return self.__size
    
    def getLastPos(self):
        return self.__end
    
class FileStream(Stream):
    def __init__(self, filename, endian="<"):
        """
        Endian: See setEndian function. 
        """

        Stream.__init__(self)
        self.__file = open(filename, 'r')
        self.filename = filename
        self.__file.seek(0,2) # Seek to end
        self.__size = self.__file.tell()
        self.__file.seek(0,0) # Seel to beginning
        self.setEndian(endian)

    def seek(self, pos, where=0):
        """ Read file seek document to understand where. """
        self.__file.seek(pos, where)
        assert self.tell() <= self.__size

    def tell(self):
        return self.__file.tell()

    def __doSearch(self, binary_string, pos_max):
        """
        pos_max: Position of last tested byte
        """
        # TODO: Use max ...
        if 2048<=len(binary_string):
            raise Exception("Search string too big.")
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

    def setEndian(self, endian):
        """
        Endian: "<" for little endian, ">" for big endian, "!" for network endian.
        """

        self.__endian = endian
        self.__unpack8u = "B"
        self.__unpack16u = "%sH" % self.__endian
        self.__unpack32u = "%sI" % self.__endian

    def get8(self):
        data = self.__file.read(1)
        data = struct.unpack(self.__unpack8u, data)
        return data[0]

    def get16(self):
        data = self.__file.read(2)
        data = struct.unpack(self.__unpack16u, data)
        return data[0]

    def get32(self):
        data = self.__file.read(4)
        data = struct.unpack(self.__unpack32u, data)
        return data[0]

    def getN(self, size):
        data = self.__file.read(size)
        assert len(data) == size
        return data

    def getEnd(self):
        """
        Read everything until the end.
        """
        
        data = self.__file.read()
        # Do endian things
        return data

    def destroy(self):
        self.__file.close()

    def getSize(self):
        return self.__size

    def getLastPos(self):
        return self.__size-1
