from bits import sized_long2bin, str2long
from field import Field
from cIOString import IOString
from indexed_dict import IndexedDict

class BitField(Field):
    def __init__(self, parent, name, size, description=None):
        assert 0 < size
        Field.__init__(self, parent, name, None, size, description=description)

    def _getDisplay(self):
        return sized_long2bin(self.size, self.value)
    display = property(_getDisplay)

    def _getValue(self):
        if self._value == None:
            self._value = self.parent.readBits(self.address, self.size)
        return self._value
    value = property(_getValue, Field._setValue)

class BitsSet(object):
    def __init__(self, source, items=None, do_reverse=False):
        self._items = IndexedDict()
        self._size = 0
        self._source = source
        if do_reverse:
            items = reversed(items)
        for item in items:
            field = BitField(self, item[1], item[0], item[2])
            self._items.append(field.name, field)
            self._size += field.size
        assert (0 < self._size) and ((self._size % 8) == 0)

    def newFieldAskAddress(self):
        return self._size

    def readBits(self, address, size):
        data = self._source.readRawContent()
        start = address / 8
        mask = (1 << size) - 1
        byte_size = (size + (address % 8) + 7) / 8
        shift = address - start*8
        data = data[start:start+byte_size]
        value = str2long(data)
        value = (value >> shift) & mask
        if size == 1:
            return value == 1
        else:
            return value

    def _getSize(self):
        return self._size / 8
    size = property(_getSize)

    def __iter__(self):
        return iter(self._items)

class BitsSet(Field):
    is_field_set = True

    def __init__(self, parent, name, bits, description=None):
        self.bits = BitsSet(self, bits)
        Field.__init__(self, parent, name, None, self.bits.size, description=description)

    def __iter__(self):
        return iter(self.bits)

    def __getitem__(self, name):
        return self.bits[name]

    def _getDisplay(self):
        return "<bits>"
    display = property(_getDisplay)

