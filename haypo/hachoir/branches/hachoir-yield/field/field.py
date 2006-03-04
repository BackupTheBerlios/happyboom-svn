class Field(object):
    is_field_set = False
    
    def __init__(self, parent, name, value, size=None, address=None, description=None):
        assert parent == None or issubclass(parent.__class__, Field)
        self.parent = parent
        self._name = name 
        self._value = value
        if address == None:
            if parent != None:
                address = parent.newFieldAskAddress()
            else:
                address = 0
        self.address = address
        self._size = size 
        self.description = description

    def readRawContent(self):
        stream = self.parent.stream
        stream.seek(self.absolute_address)
        return stream.getN(self.size)

    def __str__(self):
        return str(self.display)

    def _getValue(self):
        return self._value
    def _setValue(self, new_value):
        self._value = new_value
        self.parent.raiseEvent("value-changed", self)
    value = property(_getValue, _setValue)

    def _getDisplay(self):
        raise NotImplementedError()
    display = property(_getDisplay)

    def _getName(self):
        return self._name
    name = property(_getName)

    def _getPath(self):
        path = "/"+self.name
        current = self.parent
        while current != None:
            path = "/" + current. name + path
            current = current.parent
        return path
    path = property(_getPath)

    def _getAbsoluteAddress(self):
        address = self.address
        current = self.parent
        while current != None:
            address += current.address
            current = current.parent
        return address
    absolute_address = property(_getAbsoluteAddress)

    def _getSize(self):
        return self._size
    size = property(_getSize)
