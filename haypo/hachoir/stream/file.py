from error import StreamError
from stream import Stream
import os

class FileCacheEntry:
    def __init__(self, index, data):
        self.index = index
        self.data = data

class FileCache:
    def __init__(self, file, file_size):
        self.file = file
        self.file_size = file_size
        self.block_size = 4096
        self.max_block = 100
        self.blocks = {}

    def read(self, position, length):
        block_position = position % self.block_size
        block_index = position / self.block_size
        length_copy = length
        assert position+length <= self.file_size
        
        # TODO: Be able to read two or more blocks
        data = ""
        while 0 < length:
            if block_index not in self.blocks:
                if self.max_block <= len(self.blocks):
                    # TODO: Remove oldest block
                    pass
                self.file.seek(block_index * self.block_size)
                block_data = self.file.read(self.block_size)
                assert (len(block_data) == self.block_size) or self.file.tell() == self.file_size
                self.blocks[block_index] = block_data
            else:
                block_data = self.blocks[block_index]
            if block_position != 0 or length != self.block_size:
                end = block_position+length
                if self.block_size < end:
                    end = self.block_size
                block_data = block_data[block_position:end]
            data = data + block_data
            block_position = 0
            block_index = block_index + 1
            length = length - len(block_data)
        assert len(data) == length_copy
        return data

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
            self._cache = copy._cache
        else:
            self._file.seek(0,2) # Seek to end
            self._size = self._file.tell()
            self._file.seek(0,0) # Seel to beginning
            self._seed = 0
            if self._size != 0:
                self._end = self._size-1
            else:
                self._end = 0
            self._cache = FileCache(self._file, self._size)

    def getType(self):
        return "%s (%s)" % \
            (self.__class__.__name__, self.filename)
        
    def read(self, size, seek=True):
        data = self._cache.read(self._seed, size)
#        self._file.seek(self._seed) ; data = self._file.read(size)
        if seek:
            self._seed = self._seed + len(data)
#            assert self._seed == self._file.tell()
        return data            

    def clone(self):
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
        data = self._cache.read(self._seed, size)
#        self._file.seek(self._seed) ; data = self._file.read(size)
#        if len(data) != size:
#            raise StreamError("Can't read %u bytes in a stream (get %u bytes)." % (size, len(data)))
        if seek:
            self._seed = self._seed + size
#            assert self._seed == self._file.tell()
        return data

    def getSize(self):
        return self._size

    def getLastPos(self):
        return self._end
