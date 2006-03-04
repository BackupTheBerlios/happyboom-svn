from libhachoir.format import getFormatSize
from libhachoir.text_handler import hexadecimal
from libhachoir.field.bit_field import Bits
  
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

