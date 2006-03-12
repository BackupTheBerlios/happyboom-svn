from cStringIO import StringIO
from libhachoir.bits import countBits

def FileOutputStream(filename, big_endian=True):
    output = open(filename, 'w')
    return OutputStream(output, big_endian=big_endian, filename=filename)

class OutputStream(object):
    def __init__(self, output, big_endian=True, filename=None):
        self._output = output
        self._filename = filename
        self._bit_pos = 0
        self._byte = 0
        self._big_endian = big_endian

    def _getFilename(self):
        return self._filename
    filename = property(_getFilename)

    def writeBit(self, state):
        if self._bit_pos == 7:
            self._bit_pos = 0
            if state:
                if self._big_endian:
                    self._byte |= 1
                else:
                    self._byte |= 128
            self._output.write(chr(self._byte))
            self._byte = 0
        else:
            if state:
                if self._big_endian:
                    self._byte |= (1 << (7-self._bit_pos))
                else:
                    self._byte |= (1 << self._bit_pos)
            self._bit_pos += 1

    def writeBits(self, count, value):
        assert countBits(value) <= count

        # Feed bits to align to byte address
        if self._bit_pos != 0:
            n = 8 - self._bit_pos
            if n <= count:
                count -= n
                if self._big_endian:
                    self._byte |= (value >> count)
                    value &= ((1 << count) - 1)
                else:
                    self._byte |= (value & ((1 << n)-1)) << self._bit_pos
                    value >>= n
                self._output.write(chr(self._byte))
                self._byte = 0
            else:
                if self._big_endian:
                    self._byte |= (value << (7-self._bit_pos-count))
                else:
                    self._byte |= (value << self._bit_pos)
                self._bit_pos += count 
                return

        # Write byte per byte
        while 8 <= count:
            count -= 8
            if self._big_endian:
                byte = (value >> count)
                value &= ((1 << count) - 1)
            else:
                byte = (value & 0xFF)
                value >>= 8
            self._output.write(chr(byte))

        # Keep last bits
        assert 0 <= count and count < 8
        self._bit_pos = count
        if 0 < count:
            assert countBits(value) <= count
            if self._big_endian:
                self._byte = value << (8-count)
            else:
                self._byte = value
        else:
            assert value == 0
            self._byte = 0

    def copyBitsFrom(self, input, address, nb_bits, big_endian):
        if (nb_bits % 8) == 0 and big_endian:
            self.copyBytesFrom(input, address, nb_bits/8)
        else:
            # Arbitrary limit (because we should use a buffer, like copyBytesFrom(),
            # but with endianess problem
            assert nb_bits <= 128
            buffer = input.readBits(address, nb_bits, big_endian)
            self.writeBits(nb_bits, buffer)
    
    def copyBytesFrom(self, input, address, nb_bytes):
        buffer_size = 1 << 16 # 64 KB
        while 0 < nb_bytes:
            # Compute buffer size
            if nb_bytes < buffer_size:
                buffer_size = nb_bytes
                
            # Read
            buffer = input.readBytes(address, buffer_size)
            
            # Write
            self.writeBytes(buffer)

            # Move address
            address += buffer_size*8
            nb_bytes -= buffer_size

    def writeBytes(self, bytes):           
        if self._bit_pos != 0:
            raise NotImplementedError()
        self._output.write(bytes)

    def paddingToByte(self, bit=False):
        n = 0
        while self._bit_pos != 0:
            self.writeBit(bit)
            n += 1
        return n

class StringOutputStream(OutputStream):
    def __init__(self, big_endian=True):
        self.string = StringIO()
        OutputStream.__init__(self, self.string, \
            big_endian=big_endian, filename=None)

