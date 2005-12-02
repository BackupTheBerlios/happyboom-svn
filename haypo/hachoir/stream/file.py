from error import StreamError
from stream import Stream
import os

class FileStream(Stream):
    def __init__(self, file, filename=None, copy=None):
        """
        Endian: See setEndian function. 
        """

        Stream.__init__(self, filename)
        self._file = file 
        if copy != None:
            self._size = copy._size
            self._seed = copy._seed
            self._end = copy._end
        else:
            self._file.seek(0,2) # Seek to end
            self._size = self._file.tell()
            self._file.seek(0,0) # Seel to beginning
            self._seed = 0
            if self._size != 0:
                self._end = self._size-1
            else:
                self._end = 0

    def getType(self):
        return "%s (%s)" % \
            (self.__class__.__name__, self.filename)
        
    def read(self, size, seek=True):
        self._file.seek(self._seed)
        data = self._file.read(size)
        if seek:
            self._seed = self._seed + len(data)
            assert self._seed == self._file.tell()
        return data            

    def clone(self):
        # TODO: Don't copy low-level file IO,
        # but only copy seed :-)
        # => use internal seed + cache
        return FileStream(self._file, self.filename, copy=self)

    def seek(self, pos, where=0):
        """ Read file seek document to understand where. """
        # TODO: Don't really seek
        if where==0:
            self._seed = pos
        elif where==1:
            self._seed = self._seed + pos
        else:
            self._seed = self._size - pos
        if self._size < self._seed:
            raise StreamError("Error when seek to (%s,%s) in a stream." % (pos, where))

    def tell(self):
        return self._seed

    def getN(self, size, seek=True):
        self._file.seek(self._seed)
        data = self._file.read(size)
        if len(data) != size:
            raise StreamError("Can't read %u bytes in a stream (get %u bytes)." % (size, len(data)))
        if seek:
            self._seed = self._seed + size
            assert self._seed == self._file.tell()
        return data

    def getSize(self):
        return self._size

    def getLastPos(self):
        return self._end
