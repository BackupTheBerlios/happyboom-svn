from libhachoir.field.field import Field

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
 
