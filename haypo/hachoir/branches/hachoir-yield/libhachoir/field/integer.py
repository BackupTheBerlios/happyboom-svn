from field import Field
from libhachoir.format import getFormatSize
from libhachoir.text_handler import hexadecimal

class Bits(Field):
    def __init__(self, parent, name, size, description=None):
        assert issubclass(parent.__class__, Field)
        Field.__init__(self, parent, name, size=size, description=description)
        self.big_endian = True

    def _getValue(self):
        if self._value == None:
            self._value = self.parent.stream.getBits(
                self.absolute_address, self.size, self.big_endian) 
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
                self.absolute_address, 1, True) 
            self._value = (data == 1)
        return self._value
    value = property(_getValue, Field._setValue)
   
class Integer(Bits):
    def __init__(self, parent, name, format, description=None, text_handler=None):
        if format[0] not in "!<>":
            self.format = parent.endian + format
        else:
            self.format = format
        Bits.__init__(self, parent, name, getFormatSize(format)*8, description)
        self.big_endian = (self.format[0] == "<") 
        self.text_handler = text_handler

    def _getDisplay(self):
        if self.text_handler != None:
            return self.text_handler(self)
        else:
            return self.value
    display = property(_getDisplay)

class Enum(Integer):   
    def __init__(self, parent, name, format, enum, description=None, text_handler=None):
        self.enum = enum
        Integer.__init__(self, parent, name, format, description, text_handler)
    
    def _getDisplay(self):
        key = self.value 
        if key in self.enum:
            return self.enum[key]
        else:
            return Integer._getDisplay(self)
    display = property(_getDisplay)

