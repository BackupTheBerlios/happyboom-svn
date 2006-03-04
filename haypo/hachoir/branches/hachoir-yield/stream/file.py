import os
from error import StreamError
from stream import Stream
#from config import config

class FileStream(Stream):
    def __init__(self, file, filename=None, copy=None, use_cache=True):
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
            self._size = self._file.tell() * 8
            self._file.seek(0,0) # Seel to beginning
            if self._size == 0:
                raise Exception("Error: file %s is empty!" % filename)
            self._seed = 0
            if self._size != 0:
                self._end = self._size-1
            else:
                self._end = 0

#           TODO: Re-enable that                
#            if use_cache:
            if False:
                self._cache = FileCache(self._file, self._size, \
                    config.file_cache_block_size, config.file_cache_block_count)
            else:
                self._cache = None

    def getType(self):
        return "%s (%s)" % \
            (self.__class__.__name__, self.filename)
        
    def read(self, size, seek=True):
        if self._cache != None:
            if self._size < self._seed + size:
                size = self._size - self._seed
            data = self._cache.read(self._seed, size)
        else:
            self._file.seek(self._seed)
            data = self._file.read(size)
        if seek:
            self._seed = self._seed + len(data)
        return data            

    def seek(self, pos, where=0):
        """ Read file seek document to understand where. """
        if where==0:
            self._seed = pos
        elif where==1:
            self._seed = self._seed + pos
        else:
            self._seed = self._size - pos
        if self._seed < 0 or self._size < self._seed:
            raise StreamError("Error when seek to (%s,%s) in a stream." % (pos, where))

    def tell(self):
        return self._seed

    def getBits(self, address, nbits, big_endian=False):
        data = self._getRawBits(address, nbits)        
        if (address % 8) != 0 or (nbits % 8) != 0:
            mask = (1 << nbits) - 1
            shift = address & 7 
        else:
            shift = 0
            mask = None
        value = 0
        if not big_endian:
            if shift != 0:
                byte = ord(data[0])
                value += (byte >> shift)
                data = data[1:]
                shift = nbits-shift
            else:
                shift = nbits-8
                if shift < 0:
                    shift += 8
            for character in data:
                byte = ord(character)
                value += (byte << shift) 
                shift -= 8
        else:
            if shift != 0:
                byte = ord(data[0])
                value += (byte >> shift)
                data = data[1:]
            for character in data:
                byte = ord(character)
                value += (byte << shift) 
                shift += 8
        if mask != None:
            value = value & mask
        return value

    def getBytes(self, address, nbytes):
        if address % 8 != 0:
            data = self._getRawBits(address, nbytes*8)
            nbits = address % 8
            shift1 = nbits
            shift2 = 8 - nbits
            mask = (1 << nbits) - 1
            newdata = ""
            for i in range(0, len(data)-1):
                byte1 = ord(data[i])
                byte2 = ord(data[i+1])
                new = chr((byte1 >> shift1) + ((byte2 & mask) << shift2))
                newdata += new 
            data = newdata
        else:
            data = self._getRawBits(address, nbytes*8)
        return data
    
    def _getRawBits(self, address, nbits):
        nbytes = (nbits + (address & 7) + 7) / 8
        self.seek(address / 8)
        return self.getN(nbytes)
        
    def getN(self, size, seek=True):
        if self._cache != None:
            data = self._cache.read(self._seed, size)
        else:
            self._file.seek(self._seed)
            data = self._file.read(size)
        if len(data) != size:
            raise StreamError("Can't read %u bytes in a stream (get %u bytes)." % (size, len(data)))
        if seek:
            self._seed = self._seed + size
        return data

    def getSize(self):
        """ Size of the stream in bits """
        return self._size

    def getLastPos(self):
        return self._end
