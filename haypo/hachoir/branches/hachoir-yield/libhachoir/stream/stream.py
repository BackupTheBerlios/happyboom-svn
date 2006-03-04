def getFileSize(stream):
    """ Get file size in bits """
    oldpos = stream.tell()
    stream.seek(0,2)
    size = stream.tell() * 8
    stream.seek(oldpos)
    return size

class StreamError(Exception):
    pass

class Stream:
    def __init__(self, input, size, filename=None, copy=None):
        Stream.__init__(self, filename)
        self._input = input 
        self.filename = filename
        if copy == None:
            if self._size == 0:
                raise StreamError("Error: input size is nul (filename='%s')!" % filename)
            self._size = size
        else:
            self._size = copy._size
        
    def _getSize(self):
        return self._size
    size = property(_getSize, doc="Size of the stream in bits")

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

