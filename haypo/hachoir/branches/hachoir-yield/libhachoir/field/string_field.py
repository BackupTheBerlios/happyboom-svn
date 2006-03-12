from field import Field, FieldError
from libhachoir.format import getFormatSize
from libhachoir.tools import convertDataToPrintableString

class RawBytes(Field):
    def __init__(self, parent, name, length, description="Raw data"):
        assert issubclass(parent.__class__, Field)
        Field.__init__(self, parent, name, size=length*8, description=description)
        
    def _getTruncated(self, address, length, max_bytes=20):
        truncated = False
        if self._value == None:
            if max_bytes < length:
                display = self.parent.stream.getBytes( \
                    address, max_bytes)
            else:
                self._value = self.parent.stream.getBytes( \
                    address, length)
                display = self._value
        else:
            display = self._value[:max_bytes]
        return display, max_bytes < length
    
    def _getDisplay(self):
        value, truncated = self._getTruncated(self.absolute_address, self._size/8)
        if truncated:
            value += "(...)"
        return convertDataToPrintableString(value)
    display = property(_getDisplay)        
    
    def _getValue(self):
        if self._value == None:
            assert (self._size % 8) == 0
            self._value = self.parent.stream.getBytes( \
                self.absolute_address, self._size / 8)
        return self._value
    value = property(_getValue, Field._setValue)        

class String(RawBytes):
    def __init__(self, parent, name, format, description=None, \
            strip=None, text_handler=None):
        RawBytes.__init__(self, parent, name, 0, description)
        self._begin_offset = 0 # in bytes
        self._end_offset = 0 # in bytes
        if format == "C":
            self._end_offset = 1
            start = self.absolute_address
            stop = parent.stream.searchBytes("\0", start)
            if stop is None:
                raise FieldError("Can't find end of string %s ('\\0')!" \
                    % self.path)
            self._size = stop - start + 8 
        else:
            self._size = getFormatSize(format) * 8
        self._length = (self._size / 8) - self._begin_offset - self._end_offset
        assert 0 <= self._length
        self.strip = strip
        self.text_handler = text_handler

    def _getLength(self):
        return self._length
    length = property(_getLength)

    def _processData(self, text, truncated):
        if self.strip != None:
            if isinstance(self.strip, str):
                text = text.strip(self.strip)
            else:
                text = text.strip()
        if truncated:
            text += "(...)"
        if self.text_handler != None:
            self.text_handler(self)
        return text        
    
    def _getDisplay(self):
        value, truncated = self._getTruncated( \
            self.absolute_address + self._begin_offset, \
            self._length)
        value = self._processData(value, truncated)
        return convertDataToPrintableString(value)
    display = property(_getDisplay)        

    def _getValue(self):
        if self._value == None:
            assert (self._size % 8) == 0
            self._value = self.parent.stream.getBytes( \
                self.absolute_address + self._begin_offset*8, self._length)
            self._value = self._processData(self._value, False)
        return self._value
    value = property(_getValue, Field._setValue)        

