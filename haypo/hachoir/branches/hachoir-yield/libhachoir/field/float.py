from libhachoir.field.field import Field
from libhachoir.format import getFormatSize, getRealFormat
import struct

class Float(Field):
    def __init__(self, parent, name, format, description=None):
        assert issubclass(parent.__class__, Field)
        assert format.endswith("float")
        if format[0] not in "!<>":
            format = parent.endian + format
        self.format = getRealFormat(format)
        size = getFormatSize(format)*8
        Field.__init__(self, parent, name, size=size, description=description)

    def _getValue(self):
        if self._value == None:
            assert (self._size % 8) == 0
            raw = self.parent.stream.readBytes(
                self.absolute_address, self._size/8)
            raw = struct.unpack(self.format, raw)
            assert len(raw) == 1
            self._value = raw[0]
        return self._value
    value = property(_getValue, Field._setValue)
   
    def _getDisplay(self):
        return self.value
    display = property(_getDisplay)

