from field import Field
from libhachoir.format import getFormatSize
from libhachoir.tools import convertDataToPrintableString

class String(Field):
    def __init__(self, parent, name, format, description=None):
        assert issubclass(parent.__class__, Field)
        self.format = format
        size = getFormatSize(format)*8
        Field.__init__(self, parent, name, None, size, description=description)
        
    def _getDisplay(self):
        max = 20
        if self._value == None:
            assert (self.size % 8) == 0
            if max < self._size/8:
                display = self.parent.stream.getBytes( \
                    self.absolute_address, max)
                display += "(...)"
            else:
                self._value = self.parent.stream.getBytes( \
                    self.absolute_address, self._size / 8)
                display = self._value
        else:
            display = self._value[:max]
            if max < self._size/8:
                display += "(...)"
        return convertDataToPrintableString(display)
    display = property(_getDisplay)        
    
    def _getValue(self):
        if self._value == None:
            assert (self.size % 8) == 0
            self._value = self.parent.stream.getBytes( \
                self.absolute_address, self.size / 8)
        return self._value
    value = property(_getValue, Field._setValue)
