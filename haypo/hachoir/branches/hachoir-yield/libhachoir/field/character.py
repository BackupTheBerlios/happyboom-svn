from field import Field
from bit_field import Bits

class Character(Bits):
    def __init__(self, parent, name, description=None):
        Bits.__init__(self, parent, name, 8, description=description)

    def _getValue(self):
        if self._value == None:
            byte = self.parent.stream.readBits(
                self.absolute_address, 8, True) 
            self._value = chr(byte)
        return self._value
    value = property(_getValue, Field._setValue)

