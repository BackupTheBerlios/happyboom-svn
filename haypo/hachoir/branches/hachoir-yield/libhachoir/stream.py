from cStringIO import StringIO

class InputStreamError(Exception):
    pass

def FileInputStream(filename):
    input = open(filename, 'r')
    input.seek(0, 2)
    size = input.tell() * 8
    input.seek(0)
    return InputStream(input, filename=filename, size=size)

def StringInputStream(content):
    input = StringIO(content)
    return InputStream(input, filename=None, size=len(content)*8)

class InputStream:
    def __init__(self, input, filename=None, size=None):
        self.filename = filename
        if size == 0:
            raise InputStreamError("Error: input size is nul (filename='%s')!" % filename)
        self._size = size

        # TODO: Doesn't support computation of last byte address with bit
        # address
        assert (self._size % 8) == 0
        self._last_byte_address = self._size / 8 - 1
        self._input = input 
        
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
    
    def _getRawBits(self, address, nb_bits):
        nb_bytes = (nb_bits + (address & 7) + 7) / 8
        self._input.seek(address / 8)
        data = self._input.read(nb_bytes)
        if len(data) != nb_bytes:
            raise InputStreamError(
                "Can't read %u bytes at address %u (got %u bytes)!" % \
                (nb_bytes, address/8, len(data)))
        return data

    def searchBytes(self, needle, start_address=0, end_address=None):
        """
        Search some bytes between start_address and end_address

        Returns the address of the bytes if founded, None else
        """

        if end_address == None:
            end_address = self._last_byte_address * 8
        if end_address < start_address:
            return None
        
        # TODO: Doesn't suppport bit address yet :-(
        assert (start_address % 8) == 0
        assert (end_address % 8) == 0

        size = 2048 
        if size <= len(needle):
            raise InputStreamError("Search string too big.")
        doublesize = size * 2

        address = start_address 
        max = end_address - start_address + 1
        if max<doublesize:
            doublesize = max/8 
            size = 0 
        buffer = self.getBytes(address, doublesize)

        new_address = address + size
        while len(buffer) != 0:
            found = buffer.find(needle)
            if found != -1:
                return address + found*8
            address = new_address
            if end_address < address + size:
                size = end_address - address
            if size == 0:
                break
            buffer = buffer[size:] + self.getBytes(address, size)
            new_address = address + size 
        return None

