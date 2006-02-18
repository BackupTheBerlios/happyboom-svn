class EventHandler(object):
    _instance = None

    # Singleton design pattern
    def __new__(cls):
        if cls._instance == None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        self.handlers = {}

    def connect(self, event_name, handler):
        if event_name in self.handlers:
            self.handlers[event_name].append(handler)
        else:
            self.handlers[event_name] = [handler]

    def raiseEvent(self, event_name, *args):
        if event_name not in self.handlers:
            return
        for handler in self.handlers[event_name]:
            handler(*args)

class Field(object):
    def __init__(self, parent, key, value, address=None):
        self.parent = parent
        self.key = key
        self._value = value
        if address == None:
            self.address = parent.address
        else:
            self.address = address
        self.size = 4

    def _litValeur(self):
        return self._value
    def _ecritValeur(self, nouvelle):
        self._value = nouvelle
        self.parent.raiseEvent("value-changed", self)
    value = property(_litValeur, _ecritValeur)

    def __str__(self):
        return str(self.value)

class UniqKeyError(KeyError):
    pass

class IndexedDict:
    def __init__(self):
        self._dict = {}
        self._list = []

    def add(self, key, value):
        if key in self._dict:
            raise UniqKeyError("Key '%s' already exists" % key)
        self._dict[key] = value
        self._list.append(value)

    def __len__(self):
        return len(self._list)

    def __contains__(self, key):
        return key in self._dict

    def __iter__(self):
        return iter(self._list)

class FieldSet(Field):
    def __init__(self, parent=None, key="filter"):
        Field.__init__(self, parent, key, self, 0)
        self.fields = IndexedDict()
        self.address = 0
        self._event_handler = None
        self.generator = self.createFields()

    def raiseEvent(self, event_name, *args):
        if self._event_handler == None:
            return
        self._event_handler.raiseEvent(event_name, *args)

    def connect(self, event_name, handler):
        if self._event_handler == None:
            self._event_handler = EventHandler()
        self._event_handler.connect(event_name, handler)

    def __len__(self):
        return len(self.fields)

    # Utilise lorsque le tableau a ete rempli
    def _quickGetItem(self, name):
        print "Quick!"
        if name in self.fields:
            return self.fields[name]
        raise Exception("Le field %s n'existe pas" % name)

    def _feed(self):
        field = self.generator.next()
        self.address += field.size
        self.fields.append(field.key, field)
        return field

    def __getitem__(self, name):
        if name in self.fields:
            return self.fields[name]
        try:
            while True:
                field = self._feed()
                if field.key == name:
                    return field
        except StopIteration:
            self.__getitem__ = self._quickGetItem
            self.generator = None
        raise Exception("Le field %s n'existe pas" % name)

    def __contains__(self, key):
        return key in self.fields

    def __iter__(self):
        if self.generator != None:
            try:
                while True:
                    self._feed()
            except StopIteration:
                pass
        return iter(self.fields)

    def createFields(self):
        raise NotImplementedError

class World3D(FieldSet):
    def __init__(self, parent=None):
        FieldSet.__init__(self, key="world_3d")
        self.connect("value-changed", self.valueChanged)

    def valueChanged(self, field):
        if field.key in ("x", "y"):
            self["sum"].value = self["x"].value + self["y"].value

    def createFields(self):
        yield Field(self, "x", 2)
        yield Field(self, "y", 7)
        yield Field(self, "sum", 7+2)

def displayFieldSet(filtre):
    for field in filtre:
        print "field[%s]=%s (address %s)" % \
            (field.key, field.value, field.address)

def valueChanged(field):
    print "Value of %s changed to %s" % (field.key, field.value)

pouet = World3D()
displayFieldSet(pouet)
pouet.connect("value-changed", valueChanged)
pouet["x"].value = 10
displayFieldSet(pouet)
