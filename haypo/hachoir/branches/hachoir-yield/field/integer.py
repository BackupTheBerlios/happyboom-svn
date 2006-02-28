from field import Field
from format import getFormatSize
from text_handler import hexadecimal

class Bits(Field):
    def __init__(self, parent, name, size, description=None):
        Field.__init__(self, parent, name, None, size, description=description)

    def _getValue(self):
        if self._value == None:
            self._value = self.parent.stream.getBits(
                self.absolute_address, self.size, True) 
        return self._value
    value = property(_getValue, Field._setValue)
   
    def _getDisplay(self):
        return self.value
    display = property(_getDisplay)

class Bit(Bits):
    def __init__(self, parent, name, description=None):
        Bits.__init__(self, parent, name, 1, description=description)

    def _getValue(self):
        if self._value == None:
            data = self.parent.stream.getBits(
                self.absolute_address, self.size, True) 
            self._value = (data == 1)
        return self._value
    value = property(_getValue, Field._setValue)
   
class Integer(Field):
    def __init__(self, parent, name, format, description=None):
        if format[0] not in "!<>":
            self.format = parent.endian + format
        else:
            self.format = format
        size = getFormatSize(format)*8
        Field.__init__(self, parent, name, None, size, description=description)

    def _getValue(self):
        if self._value == None:
            self._value = self.parent.stream.getBits(
                self.absolute_address, self.size, self.parent.endian=="<")
        return self._value
    value = property(_getValue, Field._setValue)
   
    def _getDisplay(self):
        return self.value
    display = property(_getDisplay)

class IntegerHex(Integer):   
    def _getDisplay(self):
        return hexadecimal(self)
    display = property(_getDisplay)

