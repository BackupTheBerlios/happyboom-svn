from error import StreamError
from stream import Stream
import os

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

    def getType(self):
        return "%s (%s)" % \
            (self.__class__.__name__, self.filename)
        
    def read(self, size, seek=True):
        data = self.__file.read(size)
        if seek==False:
            self.seek(-len(data), 1)
        return data            

    def clone(self):
        # TODO: Don't copy low-level file IO,
        # but only copy seed :-)
        # => use internal seed + cache
        file_copy = open(self.filename)
        return FileStream(file_copy, self.filename)

    def seek(self, pos, where=0):
        """ Read file seek document to understand where. """
        self.__file.seek(pos, where)
        if self.__size < self.tell():
            raise StreamError("Error when seek to (%s,%s) in a stream." % (pos, where))

    def tell(self):
        return self.__file.tell()

    def getN(self, size, seek=True):
        data = self.__file.read(size)
        if len(data) != size:
            raise StreamError("Can't read %u bytes in a stream (get %u bytes)." % (size, len(data)))
        if not seek:
            self.__file.seek(-size, 1)
        return data

    def getSize(self):
        return self.__size

    def getLastPos(self):
        return self.__size-1
