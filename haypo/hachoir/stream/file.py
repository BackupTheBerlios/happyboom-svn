from error import StreamError
from stream import Stream

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
